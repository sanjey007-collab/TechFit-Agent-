import datetime
from sqlalchemy import Column, String, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from ..database import Base

class Check(Base):
    __tablename__ = "checks"

    id = Column(String(64), primary_key=True, index=True)
    request_id = Column(String(64), nullable=False, index=True)
    user_input_json = Column(Text, nullable=False)
    resolved_device_id = Column(String(64), ForeignKey("devices.id", ondelete="SET NULL"), nullable=True)
    resolved_variant_id = Column(String(64), ForeignKey("device_variants.id", ondelete="SET NULL"), nullable=True)
    identity_status = Column(String(50), nullable=False) # RESOLVED, AMBIGUOUS, NOT_FOUND, INSUFFICIENT_INPUT
    part_type = Column(String(50), nullable=False) # RAM, CHARGER
    verdict = Column(String(50), nullable=False) # COMPATIBLE, INCOMPATIBLE, UNCERTAIN, MORE_INFO_REQUIRED, NOT_TRUSTED
    verdict_summary = Column(Text, nullable=False)
    detailed_explanation = Column(Text, nullable=False)
    next_action_instructions = Column(Text, nullable=False)
    recommended_sku = Column(String(64), nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)

    rule_results = relationship("RuleResult", back_populates="check", cascade="all, delete-orphan")
    proposals = relationship("CartProposal", back_populates="check", cascade="all, delete-orphan")

class RuleResult(Base):
    __tablename__ = "rule_results"

    id = Column(String(64), primary_key=True, index=True)
    check_id = Column(String(64), ForeignKey("checks.id", ondelete="CASCADE"), nullable=False)
    rule_name = Column(String(100), nullable=False)
    field_name = Column(String(100), nullable=False)
    required_value = Column(String(100), nullable=False)
    observed_value = Column(String(100), nullable=False)
    status = Column(String(20), nullable=False) # PASS, FAIL, UNKNOWN
    evidence_source_id = Column(String(64), ForeignKey("sources.id", ondelete="SET NULL"), nullable=True)
    explanation = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    check = relationship("Check", back_populates="rule_results")
