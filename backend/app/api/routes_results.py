"""API routes for results and run history."""

from fastapi import APIRouter, HTTPException, Query
from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime
from app.models.sku import AnalysisResult

router = APIRouter(prefix="/results", tags=["results"])

# In-memory storage for MVP (replace with DB later)
_results_store: dict[str, AnalysisResult] = {}
_run_history: list[dict] = []


class RunSummary(BaseModel):
    """Summary of an analysis run."""
    run_id: str
    wine_name: str
    vintage: Optional[str]
    verdict: str
    confidence: float
    has_image: bool
    created_at: datetime


class RunListResponse(BaseModel):
    """Response for listing runs."""
    runs: List[RunSummary]
    total: int
    page: int
    page_size: int


class RunDetail(BaseModel):
    """Detailed run information."""
    run_id: str
    result: AnalysisResult
    candidates_count: int = 0
    processing_time_ms: Optional[int] = None


@router.get("/", response_model=RunListResponse)
async def list_results(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    verdict: Optional[str] = Query(None, description="Filter by verdict (PASS, FAIL, NO_IMAGE)"),
    wine_name: Optional[str] = Query(None, description="Search by wine name"),
):
    """
    List analysis run history.

    - **page**: Page number (1-indexed)
    - **page_size**: Items per page (1-100)
    - **verdict**: Filter by verdict status
    - **wine_name**: Search by wine name (partial match)
    """
    runs = list(_run_history)

    # Apply filters
    if verdict:
        runs = [r for r in runs if r.get("verdict") == verdict]

    if wine_name:
        runs = [r for r in runs if wine_name.lower() in r.get("wine_name", "").lower()]

    # Sort by created_at desc
    runs.sort(key=lambda x: x.get("created_at", datetime.min), reverse=True)

    # Paginate
    total = len(runs)
    start_idx = (page - 1) * page_size
    end_idx = start_idx + page_size
    page_runs = runs[start_idx:end_idx]

    # Convert to RunSummary
    summaries = [
        RunSummary(
            run_id=r["run_id"],
            wine_name=r["wine_name"],
            vintage=r.get("vintage"),
            verdict=r["verdict"],
            confidence=r["confidence"],
            has_image=r.get("has_image", False),
            created_at=r["created_at"],
        )
        for r in page_runs
    ]

    return RunListResponse(
        runs=summaries,
        total=total,
        page=page,
        page_size=page_size,
    )


@router.get("/{run_id}", response_model=RunDetail)
async def get_result(run_id: str):
    """
    Get detailed result for a specific run.

    - **run_id**: The run ID
    """
    if run_id not in _results_store:
        raise HTTPException(status_code=404, detail=f"Run {run_id} not found")

    result = _results_store[run_id]

    return RunDetail(
        run_id=run_id,
        result=result,
        candidates_count=len(result.top_candidates),
    )


@router.get("/{run_id}/export/json")
async def export_result_json(run_id: str):
    """
    Export a single result as JSON.

    - **run_id**: The run ID
    """
    if run_id not in _results_store:
        raise HTTPException(status_code=404, detail=f"Run {run_id} not found")

    return _results_store[run_id]


@router.get("/export/csv")
async def export_results_csv(
    run_ids: Optional[str] = Query(None, description="Comma-separated list of run IDs (omit for all)"),
):
    """
    Export results as CSV.

    - **run_ids**: Optional comma-separated list of run IDs
    """
    from fastapi.responses import PlainTextResponse

    # Get results to export
    if run_ids:
        ids = [r.strip() for r in run_ids.split(",")]
        results = [_results_store.get(rid) for rid in ids if rid in _results_store]
    else:
        results = list(_results_store.values())

    if not results:
        raise HTTPException(status_code=404, detail="No results found")

    # Build CSV
    headers = [
        "wine_name",
        "vintage",
        "format",
        "region",
        "producer",
        "appellation",
        "vineyard",
        "verdict",
        "confidence",
        "selected_image_url",
        "reason",
        "analyzer_mode",
        "created_at",
    ]

    lines = [",".join(headers)]

    for r in results:
        row = [
            r.input.wine_name,
            r.input.vintage or "",
            r.input.format or "",
            r.input.region or "",
            r.parsed_sku.producer or "",
            r.parsed_sku.appellation or "",
            r.parsed_sku.vineyard or "",
            r.verdict,
            str(r.confidence),
            r.selected_image_url or "",
            r.reason,
            r.analyzer_mode,
            r.created_at.isoformat() if r.created_at else "",
        ]
        escaped = []
        for c in row:
            s = str(c).replace('"', '""')
            escaped.append(f'"{s}"')
        lines.append(",".join(escaped))

    csv_content = "\n".join(lines)

    return PlainTextResponse(
        content=csv_content,
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=results.csv"},
    )


# Helper function to store results (called by pipeline)
def store_result(run_id: str, result: AnalysisResult) -> None:
    """Store a result in the results store."""
    _results_store[run_id] = result

    # Add to history
    _run_history.append({
        "run_id": run_id,
        "wine_name": result.input.wine_name,
        "vintage": result.input.vintage,
        "verdict": result.verdict,
        "confidence": result.confidence,
        "has_image": result.selected_image_url is not None,
        "created_at": result.created_at,
    })

    # Limit history size (keep last 1000)
    if len(_run_history) > 1000:
        oldest = _run_history.pop(0)
        if oldest["run_id"] in _results_store:
            del _results_store[oldest["run_id"]]
