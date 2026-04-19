"""SQLAlchemy database models."""

from sqlalchemy import Column, String, Integer, Float, DateTime, JSON, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from app.db.session import Base


class Run(Base):
    """Analysis run record."""
    __tablename__ = "runs"

    id = Column(String(32), primary_key=True)
    analyzer_mode = Column(String(50), nullable=False)

    # Input fields
    wine_name = Column(String(500), nullable=False)
    vintage = Column(String(10))
    format = Column(String(50))
    region = Column(String(200))

    # Parsed fields
    producer = Column(String(300))
    appellation = Column(String(300))
    vineyard = Column(String(300))
    classification = Column(String(100))

    # Results
    verdict = Column(String(20), nullable=False, default="FAIL")
    confidence = Column(Float, default=0.0)
    selected_image_url = Column(String(1000))
    reason = Column(String(500))

    # Raw storage
    input_payload = Column(JSON)
    parsed_payload = Column(JSON)

    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    candidates = relationship("Candidate", back_populates="run", cascade="all, delete-orphan")


class Candidate(Base):
    """Image candidate record."""
    __tablename__ = "candidates"

    id = Column(String(32), primary_key=True)
    run_id = Column(String(32), ForeignKey("runs.id"), nullable=False)

    # Source info
    image_url = Column(String(1000), nullable=False)
    source_page = Column(String(1000))
    source_domain = Column(String(200))
    source_query = Column(String(500))

    # File info
    local_path = Column(String(500))
    file_hash = Column(String(64))
    perceptual_hash = Column(String(32))
    width = Column(Integer)
    height = Column(Integer)
    file_size = Column(Integer)

    # Quality scores
    sharpness_score = Column(Float)
    source_trust_score = Column(Integer)

    # Analysis results
    opencv_result = Column(JSON)
    ocr_result = Column(JSON)
    match_result = Column(JSON)
    hard_fail_reasons = Column(JSON)

    # Final scores
    total_score = Column(Float)
    final_verdict = Column(String(20))

    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    run = relationship("Run", back_populates="candidates")
