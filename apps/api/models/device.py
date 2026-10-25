import datetime
from sqlalchemy import Column, String, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from ..database import Base

class Device(Base):
    __tablename__ = "devices"

    id = Column(String(64), primary_key=True, index=True)
    brand = Column(String(100), nullable=False, index=True)
    model_family = Column(String(150), nullable=False, index=True)
    description = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    variants = relationship("DeviceVariant", back_populates="device", cascade="all, delete-orphan")

class DeviceVariant(Base):
    __tablename__ = "device_variants"

    id = Column(String(64), primary_key=True, index=True)
    device_id = Column(String(64), ForeignKey("devices.id", ondelete="CASCADE"), nullable=False)
    variant_code = Column(String(100), nullable=False, index=True)
    full_name = Column(String(200), nullable=False)
    form_factor = Column(String(50), default="Laptop")
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    device = relationship("Device", back_populates="variants")
    spec_facts = relationship("SpecFact", back_populates="variant", cascade="all, delete-orphan")
