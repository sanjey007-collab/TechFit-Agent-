import datetime
from sqlalchemy import Column, String, Integer, Float, Boolean, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from .database import Base

class StoreProduct(Base):
    __tablename__ = "store_products"

    sku = Column(String(64), primary_key=True, index=True)
    title = Column(String(255), nullable=False)
    brand = Column(String(100), nullable=False)
    category = Column(String(50), nullable=False) # RAM, CHARGER, etc.
    price = Column(Float, nullable=False)
    stock = Column(Integer, default=0)
    specs_json = Column(Text, nullable=True) # JSON string of attributes
    description = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

class StoreCart(Base):
    __tablename__ = "store_carts"

    cart_id = Column(String(64), primary_key=True, index=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)

    items = relationship("StoreCartItem", back_populates="cart", cascade="all, delete-orphan")

class StoreCartItem(Base):
    __tablename__ = "store_cart_items"

    id = Column(Integer, primary_key=True, autoincrement=True)
    cart_id = Column(String(64), ForeignKey("store_carts.cart_id", ondelete="CASCADE"), nullable=False)
    sku = Column(String(64), ForeignKey("store_products.sku"), nullable=False)
    quantity = Column(Integer, default=1)
    price_per_unit = Column(Float, nullable=False)
    added_at = Column(DateTime, default=datetime.datetime.utcnow)

    cart = relationship("StoreCart", back_populates="items")
    product = relationship("StoreProduct")

class StoreIdempotencyRecord(Base):
    __tablename__ = "store_idempotency_records"

    idempotency_key = Column(String(128), primary_key=True, index=True)
    cart_id = Column(String(64), nullable=False)
    sku = Column(String(64), nullable=False)
    quantity = Column(Integer, nullable=False)
    response_json = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
