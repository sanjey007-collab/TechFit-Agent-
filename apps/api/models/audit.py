import datetime
from sqlalchemy import Column, String, Integer, Float, Text, DateTime
from ..database import Base

class AuditEvent(Base):
    __tablename__ = "audit_events"

    id = Column(String(64), primary_key=True, index=True)
    correlation_id = Column(String(64), nullable=False, index=True)
    event_type = Column(String(100), nullable=False, index=True)
    actor = Column(String(100), default="system")
    payload_json = Column(Text, nullable=False)
    timestamp = Column(DateTime, default=datetime.datetime.utcnow)

class TestRun(Base):
    __tablename__ = "test_runs"

    id = Column(String(64), primary_key=True, index=True)
    test_case_id = Column(String(64), nullable=False, index=True)
    test_name = Column(String(150), nullable=False)
    expected_verdict = Column(String(50), nullable=False)
    actual_verdict = Column(String(50), nullable=False)
    expected_cart_status = Column(String(50), nullable=False)
    actual_cart_status = Column(String(50), nullable=False)
    pass_fail = Column(String(20), nullable=False) # PASS or FAIL
    logs_json = Column(Text, nullable=False)
    duration_ms = Column(Float, default=0.0)
    executed_at = Column(DateTime, default=datetime.datetime.utcnow)
