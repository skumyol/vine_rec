"""Pipeline stage timing utilities."""

import time
from typing import Dict, Optional
from contextlib import contextmanager
from dataclasses import dataclass, field


@dataclass
class PipelineTiming:
    """Timing data for pipeline stages."""
    retrieval_ms: Optional[int] = None
    download_ms: Optional[int] = None
    opencv_ms: Optional[int] = None
    ocr_ms: Optional[int] = None
    verification_ms: Optional[int] = None
    scoring_ms: Optional[int] = None
    total_ms: Optional[int] = None

    def to_dict(self) -> Dict[str, Optional[int]]:
        return {
            "retrieval_ms": self.retrieval_ms,
            "download_ms": self.download_ms,
            "opencv_ms": self.opencv_ms,
            "ocr_ms": self.ocr_ms,
            "verification_ms": self.verification_ms,
            "scoring_ms": self.scoring_ms,
            "total_ms": self.total_ms,
        }


class PipelineTimer:
    """Timer for tracking pipeline stage durations."""

    def __init__(self):
        self.timing = PipelineTiming()
        self._stage_start: Dict[str, float] = {}

    @contextmanager
    def stage(self, stage_name: str):
        """Context manager to time a pipeline stage."""
        start = time.perf_counter()
        try:
            yield
        finally:
            elapsed_ms = int((time.perf_counter() - start) * 1000)
            setattr(self.timing, f"{stage_name}_ms", elapsed_ms)

    def start_stage(self, stage_name: str):
        """Start timing a stage."""
        self._stage_start[stage_name] = time.perf_counter()

    def end_stage(self, stage_name: str) -> int:
        """End timing a stage and return elapsed ms."""
        if stage_name not in self._stage_start:
            return 0
        elapsed_ms = int((time.perf_counter() - self._stage_start[stage_name]) * 1000)
        setattr(self.timing, f"{stage_name}_ms", elapsed_ms)
        return elapsed_ms

    def set_total(self, total_ms: int):
        """Set total pipeline time."""
        self.timing.total_ms = total_ms

    def get_timing(self) -> PipelineTiming:
        """Get timing data."""
        return self.timing
