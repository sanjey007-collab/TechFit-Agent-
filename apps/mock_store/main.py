import os
import json
from contextlib import asynccontextmanager
from typing import Optional, List
from fastapi import FastAPI, Depends, HTTPException, Header, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from .database import engine, Base, get_db
from .models import StoreProduct, StoreCart, StoreCartItem, StoreIdempotencyRecord
from .seed import seed_mock_store

SERVICE_TOKEN = os.getenv("MOCK_STORE_SERVICE_TOKEN", "techfit_sec_token_a984b2c1f0e478d1")

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Ensure tables exist and seed default inventory
    await seed_mock_store()
    yield

app = FastAPI(
    title="TechFit Mock Shopping Store",
    version="1.0.0",
    description="Independent eCommerce Store API with real isolated cart state",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def verify_token(authorization: Optional[str] = Header(None)):
    if not authorization:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing Authorization header"
        )
    scheme, _, token = authorization.partition(" ")
    if scheme.lower() != "bearer" or token != SERVICE_TOKEN:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid service token for mock store"
        )
    return token

class AddCartItemPayload(BaseModel):
    sku: str
    quantity: int = Field(1, ge=1)
    idempotency_key: str = Field(..., description="Unique client key preventing duplicate additions")

class CartItemResponse(BaseModel):
    sku: str
    title: str
    brand: str
    category: str
    quantity: int
    price_per_unit: float
    total_price: float

class CartResponse(BaseModel):
    cart_id: str
    item_count: int
    subtotal: float
    items: List[CartItemResponse]

@app.get("/healthz")
async def health_check():
    return {"status": "ok", "service": "techfit-mock-store"}

@app.get("/store/products")
async def list_products(
    category: Optional[str] = None,
    q: Optional[str] = None,
    db: AsyncSession = Depends(get_db)
):
    stmt = select(StoreProduct)
    if category:
        stmt = stmt.where(StoreProduct.category == category.upper())
    res = await db.execute(stmt)
    products = res.scalars().all()
    if q:
        q_lower = q.lower()
        products = [p for p in products if q_lower in p.title.lower() or q_lower in p.sku.lower() or (p.description and q_lower in p.description.lower())]
    
    return [
        {
            "sku": p.sku,
            "title": p.title,
            "brand": p.brand,
            "category": p.category,
            "price": p.price,
            "stock": p.stock,
            "specs": json.loads(p.specs_json) if p.specs_json else {},
            "description": p.description
        }
        for p in products
    ]

@app.get("/store/products/{sku}")
async def get_product(sku: str, db: AsyncSession = Depends(get_db)):
    stmt = select(StoreProduct).where(StoreProduct.sku == sku)
    res = await db.execute(stmt)
    product = res.scalar_one_or_none()
    if not product:
        raise HTTPException(status_code=404, detail=f"Product with SKU '{sku}' not found")
    return {
        "sku": product.sku,
        "title": product.title,
        "brand": product.brand,
        "category": product.category,
        "price": product.price,
        "stock": product.stock,
        "specs": json.loads(product.specs_json) if product.specs_json else {},
        "description": product.description
    }

async def _build_cart_response(cart_id: str, db: AsyncSession) -> CartResponse:
    stmt = (
        select(StoreCart)
        .options(selectinload(StoreCart.items).selectinload(StoreCartItem.product))
        .where(StoreCart.cart_id == cart_id)
    )
    res = await db.execute(stmt)
    cart = res.scalar_one_or_none()
    if not cart:
        return CartResponse(cart_id=cart_id, item_count=0, subtotal=0.0, items=[])

    items_out = []
    subtotal = 0.0
    total_qty = 0
    for item in cart.items:
        line_total = item.quantity * item.price_per_unit
        subtotal += line_total
        total_qty += item.quantity
        items_out.append(CartItemResponse(
            sku=item.sku,
            title=item.product.title if item.product else item.sku,
            brand=item.product.brand if item.product else "Unknown",
            category=item.product.category if item.product else "UNKNOWN",
            quantity=item.quantity,
            price_per_unit=item.price_per_unit,
            total_price=round(line_total, 2)
        ))

    return CartResponse(
        cart_id=cart_id,
        item_count=total_qty,
        subtotal=round(subtotal, 2),
        items=items_out
    )

@app.get("/store/cart/{cart_id}", response_model=CartResponse)
async def get_cart(
    cart_id: str,
    db: AsyncSession = Depends(get_db),
    _token: str = Depends(verify_token)
):
    return await _build_cart_response(cart_id, db)

@app.post("/store/cart/{cart_id}/items", response_model=CartResponse)
async def add_item_to_cart(
    cart_id: str,
    payload: AddCartItemPayload,
    db: AsyncSession = Depends(get_db),
    _token: str = Depends(verify_token)
):
    # 1. Check idempotency record
    idemp_stmt = select(StoreIdempotencyRecord).where(
        StoreIdempotencyRecord.idempotency_key == payload.idempotency_key
    )
    idemp_res = await db.execute(idemp_stmt)
    existing_idemp = idemp_res.scalar_one_or_none()
    if existing_idemp:
        # Idempotent replay: return current cart state without duplicating addition
        return await _build_cart_response(cart_id, db)

    # 2. Check product existence and inventory
    prod_stmt = select(StoreProduct).where(StoreProduct.sku == payload.sku)
    prod_res = await db.execute(prod_stmt)
    product = prod_res.scalar_one_or_none()
    if not product:
        raise HTTPException(status_code=404, detail=f"Cannot add non-existent SKU '{payload.sku}'")
    if product.stock < payload.quantity:
        raise HTTPException(status_code=400, detail=f"Insufficient inventory for SKU '{payload.sku}' (available: {product.stock})")

    # 3. Ensure cart exists
    cart_stmt = select(StoreCart).where(StoreCart.cart_id == cart_id)
    cart_res = await db.execute(cart_stmt)
    cart = cart_res.scalar_one_or_none()
    if not cart:
        cart = StoreCart(cart_id=cart_id)
        db.add(cart)
        await db.flush()

    # 4. Check if item already in cart
    item_stmt = select(StoreCartItem).where(
        StoreCartItem.cart_id == cart_id,
        StoreCartItem.sku == payload.sku
    )
    item_res = await db.execute(item_stmt)
    cart_item = item_res.scalar_one_or_none()
    if cart_item:
        cart_item.quantity += payload.quantity
    else:
        cart_item = StoreCartItem(
            cart_id=cart_id,
            sku=payload.sku,
            quantity=payload.quantity,
            price_per_unit=product.price
        )
        db.add(cart_item)

    # 5. Record idempotency key
    idemp_record = StoreIdempotencyRecord(
        idempotency_key=payload.idempotency_key,
        cart_id=cart_id,
        sku=payload.sku,
        quantity=payload.quantity,
        response_json=json.dumps({"status": "added", "sku": payload.sku, "qty": payload.quantity})
    )
    db.add(idemp_record)
    await db.commit()

    return await _build_cart_response(cart_id, db)

@app.delete("/store/cart/{cart_id}/items/{sku}", response_model=CartResponse)
async def remove_item_from_cart(
    cart_id: str,
    sku: str,
    db: AsyncSession = Depends(get_db),
    _token: str = Depends(verify_token)
):
    stmt = delete(StoreCartItem).where(
        StoreCartItem.cart_id == cart_id,
        StoreCartItem.sku == sku
    )
    await db.execute(stmt)
    await db.commit()
    return await _build_cart_response(cart_id, db)

@app.delete("/store/cart/{cart_id}")
async def clear_cart(
    cart_id: str,
    db: AsyncSession = Depends(get_db),
    _token: str = Depends(verify_token)
):
    stmt = delete(StoreCartItem).where(StoreCartItem.cart_id == cart_id)
    await db.execute(stmt)
    await db.commit()
    return {"status": "cleared", "cart_id": cart_id}

@app.post("/store/reset")
async def reset_store(
    db: AsyncSession = Depends(get_db),
    _token: str = Depends(verify_token)
):
    await db.execute(delete(StoreCartItem))
    await db.execute(delete(StoreCart))
    await db.execute(delete(StoreIdempotencyRecord))
    await db.commit()
    await seed_mock_store()
    return {"status": "reset_complete"}
