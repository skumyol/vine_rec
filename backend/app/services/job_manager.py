"""Simple in-memory job manager for batch processing."""

import uuid
import asyncio
from datetime import datetime
from typing import Dict, Optional, List, Any
from app.models.job import BatchJob, JobStatus
from app.models.sku import AnalysisRequest, BatchAnalysisRequest, WineSKUInput
from app.services.pipeline import AnalysisPipeline


class JobManager:
    """Manages background batch analysis jobs."""
    
    _instance = None
    _jobs: Dict[str, BatchJob] = {}
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def create_job(self, request: BatchAnalysisRequest) -> str:
        """Create a new batch job and return job ID."""
        job_id = str(uuid.uuid4())[:8]
        job = BatchJob(
            id=job_id,
            status=JobStatus.PENDING,
            total_wines=len(request.wines),
            created_at=datetime.now(),
            analyzer_mode=request.analyzer_mode
        )
        self._jobs[job_id] = job
        
        # Start background processing
        asyncio.create_task(self._process_job(job_id, request))
        
        return job_id
    
    def get_job(self, job_id: str) -> Optional[BatchJob]:
        """Get job status and results."""
        return self._jobs.get(job_id)
    
    async def _process_job(self, job_id: str, request: BatchAnalysisRequest):
        """Process batch job in background."""
        job = self._jobs.get(job_id)
        if not job:
            return
        
        job.status = JobStatus.RUNNING
        job.started_at = datetime.now()
        
        pipeline = AnalysisPipeline()
        
        try:
            for i, wine_input in enumerate(request.wines):
                try:
                    analysis_request = AnalysisRequest(
                        wine_name=wine_input.wine_name,
                        vintage=wine_input.vintage,
                        format=wine_input.format,
                        region=wine_input.region,
                        analyzer_mode=request.analyzer_mode
                    )
                    
                    result = await pipeline.analyze(analysis_request)
                    job.results.append(result.model_dump())
                    job.completed_wines += 1
                    
                except Exception as e:
                    job.errors.append(f"Wine {i+1} ({wine_input.wine_name}): {str(e)}")
                
                await asyncio.sleep(0.1)
            
            job.status = JobStatus.COMPLETED
            job.completed_at = datetime.now()
            
        except Exception as e:
            job.status = JobStatus.FAILED
            job.errors.append(str(e))
            job.completed_at = datetime.now()
        
        finally:
            await pipeline.cleanup()
    
    def list_jobs(self) -> List[BatchJob]:
        """List all jobs."""
        return list(self._jobs.values())


# Singleton instance
job_manager = JobManager()
