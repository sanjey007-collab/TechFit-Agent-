import json
from typing import Optional, List
from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from ..database import get_db
from ..models import Product

router = APIRouter(prefix="/api/products", tags=["Products"])

@router.get("")
async def search_products(
    category: Optional[str] = Query(None, description="RAM or CHARGER"),
    q: Optional[str] = Query(None, description="Search term"),
    db: AsyncSession = Depends(get_db)
):
    stmt = select(Product)
    if category:
        stmt = stmt.where(Product.category == category.upper())
    res = await db.execute(stmt)
    products = res.scalars().all()
    if q:
        q_lower = q.lower()
        products = [
            p for p in products
            if q_lower in p.name.lower() or q_lower in p.sku.lower() or (p.evidence_notes and q_lower in p.evidence_notes.lower())
        ]

    return [
        {
            "sku": p.sku,
            "name": p.name,
            "brand": p.brand,
            "category": p.category,
            "price": p.price,
            "in_stock": p.in_stock,
            "stock_quantity": p.stock_quantity,
            "specs": json.loads(p.specs_json) if p.specs_json else {},
            "evidence_notes": p.evidence_notes
        }
        for p in products
    ]

@router.get("/{sku}")
async def get_product_by_sku(sku: str, db: AsyncSession = Depends(get_db)):
    stmt = select(Product).where(Product.sku == sku)
    res = await db.execute(stmt)
    product = res.scalar_one_or_none()
    if not product:
        return {"error": f"Product with SKU '{sku}' not found"}
    return {
        "sku": product.sku,
        "name": product.name,
        "brand": product.brand,
        "category": product.category,
        "price": product.price,
        "in_stock": product.in_stock,
        "stock_quantity": product.stock_quantity,
        "specs": json.loads(product.specs_json) if product.specs_json else {},
        "evidence_notes": product.evidence_notes
    }
