"""API routes for batch job management."""

from fastapi import APIRouter, HTTPException
from typing import List, Optional
from app.models.sku import BatchAnalysisRequest
from app.models.job import BatchJob, JobStatus
from app.services.job_manager import job_manager

router = APIRouter(prefix="/jobs", tags=["jobs"])


@router.post("/batch", response_model=dict)
async def create_batch_job(request: BatchAnalysisRequest):
    """
    Create a new async batch analysis job.
    
    Returns immediately with job ID. Poll GET /jobs/{id} for status.
    """
    job_id = job_manager.create_job(request)
    return {
        "job_id": job_id,
        "status": "pending",
        "message": f"Processing {len(request.wines)} wines. Poll /api/jobs/{job_id} for results."
    }


@router.get("/{job_id}", response_model=Optional[BatchJob])
async def get_job_status(job_id: str):
    """Get batch job status and results."""
    job = job_manager.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return job


@router.get("/", response_model=List[BatchJob])
async def list_jobs():
    """List all batch jobs."""
    return job_manager.list_jobs()
