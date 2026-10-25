import datetime
from sqlalchemy import Column, String, Integer, Float, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from ..database import Base

class CartProposal(Base):
    __tablename__ = "cart_proposals"

    id = Column(String(64), primary_key=True, index=True)
    check_id = Column(String(64), ForeignKey("checks.id", ondelete="CASCADE"), nullable=False)
    product_sku = Column(String(64), nullable=False)
    quantity = Column(Integer, default=1)
    cart_id = Column(String(64), nullable=False)
    rationale = Column(Text, nullable=False)
    version = Column(Integer, default=1)
    status = Column(String(50), default="AWAITING_APPROVAL") # PROPOSED, AWAITING_APPROVAL, EXECUTED, EXPIRED, REJECTED
    expires_at = Column(DateTime, nullable=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    check = relationship("Check", back_populates="proposals")
    approvals = relationship("Approval", back_populates="proposal", cascade="all, delete-orphan")
    actions = relationship("CartAction", back_populates="proposal", cascade="all, delete-orphan")

class Approval(Base):
    __tablename__ = "approvals"

    id = Column(String(64), primary_key=True, index=True)
    proposal_id = Column(String(64), ForeignKey("cart_proposals.id", ondelete="CASCADE"), nullable=False)
    user_identifier = Column(String(100), default="human_operator")
    approved_at = Column(DateTime, default=datetime.datetime.utcnow)
    approval_token = Column(String(128), nullable=False)
    idempotency_key = Column(String(128), unique=True, nullable=False, index=True)

    proposal = relationship("CartProposal", back_populates="approvals")

class CartAction(Base):
    __tablename__ = "cart_actions"

    id = Column(String(64), primary_key=True, index=True)
    proposal_id = Column(String(64), ForeignKey("cart_proposals.id", ondelete="CASCADE"), nullable=False)
    action_type = Column(String(50), default="ADD_ITEM")
    status = Column(String(50), default="PENDING") # PENDING, EXECUTED, FAILED
    request_payload_json = Column(Text, nullable=False)
    response_payload_json = Column(Text, nullable=True)
    executed_at = Column(DateTime, default=datetime.datetime.utcnow)

    proposal = relationship("CartProposal", back_populates="actions")
    verification = relationship("VerificationResult", back_populates="action", uselist=False, cascade="all, delete-orphan")

class VerificationResult(Base):
    __tablename__ = "verification_results"

    id = Column(String(64), primary_key=True, index=True)
    action_id = Column(String(64), ForeignKey("cart_actions.id", ondelete="CASCADE"), nullable=False, unique=True)
    cart_id = Column(String(64), nullable=False)
    expected_sku = Column(String(64), nullable=False)
    expected_qty = Column(Integer, nullable=False)
    observed_sku = Column(String(64), nullable=True)
    observed_qty = Column(Integer, default=0)
    status = Column(String(50), nullable=False) # VERIFIED, FAILED, PENDING
    verified_at = Column(DateTime, default=datetime.datetime.utcnow)
    details = Column(Text, nullable=False)

    action = relationship("CartAction", back_populates="verification")
