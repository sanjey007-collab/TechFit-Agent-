import datetime
from sqlalchemy import Column, String, Float, Integer, Boolean, Text, DateTime
from ..database import Base

class Product(Base):
    __tablename__ = "products"

    id = Column(String(64), primary_key=True, index=True)
    sku = Column(String(64), unique=True, nullable=False, index=True)
    name = Column(String(255), nullable=False)
    brand = Column(String(100), nullable=False)
    category = Column(String(50), nullable=False, index=True) # RAM or CHARGER
    specs_json = Column(Text, nullable=True) # Normalized specs
    price = Column(Float, nullable=False)
    in_stock = Column(Boolean, default=True)
    stock_quantity = Column(Integer, default=0)
    evidence_notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
