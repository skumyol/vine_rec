from fastapi import APIRouter, HTTPException, BackgroundTasks
from typing import List, Optional
import asyncio

from app.models.sku import AnalysisRequest, AnalysisResult, BatchAnalysisRequest
from app.services.pipeline import AnalysisPipeline

router = APIRouter(prefix="/analyze", tags=["analysis"])


@router.post("/", response_model=AnalysisResult)
async def analyze_single(request: AnalysisRequest):
    """
    Analyze a single wine SKU and find the best matching image.
    
    Returns the verified image URL or null if no image could be verified.
    """
    pipeline = AnalysisPipeline()
    
    try:
        result = await pipeline.analyze(request)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        await pipeline.cleanup()


@router.post("/batch", response_model=List[AnalysisResult])
async def analyze_batch(request: BatchAnalysisRequest):
    """
    Analyze multiple wine SKUs in batch.
    
    Processes each wine sequentially to avoid rate limiting.
    """
    pipeline = AnalysisPipeline()
    results = []
    
    try:
        for wine_input in request.wines:
            analysis_request = AnalysisRequest(
                wine_name=wine_input.wine_name,
                vintage=wine_input.vintage,
                format=wine_input.format,
                region=wine_input.region,
                analyzer_mode=request.analyzer_mode
            )
            
            result = await pipeline.analyze(analysis_request)
            results.append(result)
            
            await asyncio.sleep(0.5)
        
        return results
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        await pipeline.cleanup()
