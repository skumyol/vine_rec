"""Background job models for async batch processing."""

from datetime import datetime
from typing import List, Optional, Dict, Any
from pydantic import BaseModel
from enum import Enum


class JobStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class BatchJob(BaseModel):
    """Background batch analysis job."""
    id: str
    status: JobStatus
    total_wines: int
    completed_wines: int = 0
    results: List[Dict[str, Any]] = []
    errors: List[str] = []
    created_at: datetime
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    analyzer_mode: str
