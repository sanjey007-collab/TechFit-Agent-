import datetime
from sqlalchemy import Column, String, Text, Boolean, Float, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from ..database import Base

class Source(Base):
    __tablename__ = "sources"

    id = Column(String(64), primary_key=True, index=True)
    url = Column(String(500), nullable=False)
    title = Column(String(255), nullable=False)
    domain = Column(String(100), nullable=False, index=True)
    author = Column(String(150), nullable=True)
    is_official = Column(Boolean, default=True)
    retrieval_timestamp = Column(DateTime, default=datetime.datetime.utcnow)
    excerpt = Column(Text, nullable=False)
    applicability = Column(String(200), nullable=False)

    spec_facts = relationship("SpecFact", back_populates="source", cascade="all, delete-orphan")

class SpecFact(Base):
    __tablename__ = "spec_facts"

    id = Column(String(64), primary_key=True, index=True)
    device_variant_id = Column(String(64), ForeignKey("device_variants.id", ondelete="CASCADE"), nullable=False)
    source_id = Column(String(64), ForeignKey("sources.id", ondelete="CASCADE"), nullable=False)
    category = Column(String(50), nullable=False) # RAM or CHARGER
    field_name = Column(String(100), nullable=False, index=True) # ddr_generation, form_factor, max_capacity, wattage, connector, etc.
    raw_value = Column(Text, nullable=False)
    normalized_value = Column(String(100), nullable=False)
    excerpt = Column(Text, nullable=False)
    confidence = Column(Float, default=1.0)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    variant = relationship("DeviceVariant", back_populates="spec_facts")
    source = relationship("Source", back_populates="spec_facts")
