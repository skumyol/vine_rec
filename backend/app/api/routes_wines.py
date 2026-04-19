"""API routes for wine management and VinoBuzz integration."""

from fastapi import APIRouter, HTTPException, Query
from typing import List, Optional
from pydantic import BaseModel

from app.services.vinobuzz_service import VinoBuzzService

router = APIRouter(prefix="/wines", tags=["wines"])


class WineOut(BaseModel):
    """Wine output model."""
    id: str
    sku: str
    name: str
    vintage: Optional[str] = None
    producer: str
    region: Optional[str] = None
    country: Optional[str] = None
    price_hkd: float
    type: Optional[str] = None
    image: Optional[str] = None
    url: Optional[str] = None
    stock: Optional[int] = None


class WineSearchResponse(BaseModel):
    """Response for wine search."""
    wines: List[WineOut]
    count: int
    query: Optional[str] = None


@router.get("/search", response_model=WineSearchResponse)
async def search_wines(
    q: Optional[str] = Query(None, description="Search query"),
    limit: int = Query(20, ge=1, le=100, description="Maximum results"),
):
    """
    Search wines from VinoBuzz marketplace.

    - **q**: Search query string (optional)
    - **limit**: Maximum number of results (1-100, default 20)

    Returns matching wines from VinoBuzz.
    """
    service = VinoBuzzService()

    try:
        if q:
            wines = await service.search_wines(query=q, limit=limit)
        else:
            wines = await service.fetch_wines(page=0, page_size=limit)

        return WineSearchResponse(
            wines=[WineOut(**wine.to_dict()) for wine in wines],
            count=len(wines),
            query=q,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        await service.close()


@router.get("/", response_model=WineSearchResponse)
async def list_wines(
    page: int = Query(0, ge=0, description="Page number"),
    page_size: int = Query(60, ge=1, le=100, description="Items per page"),
):
    """
    List wines from VinoBuzz marketplace.

    - **page**: Page number (0-indexed)
    - **page_size**: Items per page (1-100, default 60)

    Returns wines from VinoBuzz.
    """
    service = VinoBuzzService()

    try:
        wines = await service.fetch_wines(page=page, page_size=page_size)

        return WineSearchResponse(
            wines=[WineOut(**wine.to_dict()) for wine in wines],
            count=len(wines),
            query=None,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        await service.close()


@router.get("/all", response_model=WineSearchResponse)
async def list_all_wines(
    max_pages: int = Query(5, ge=1, le=20, description="Maximum pages to fetch"),
):
    """
    Fetch all wines from VinoBuzz marketplace.

    - **max_pages**: Maximum number of pages to fetch (1-20, default 5)

    Returns all wines from VinoBuzz (may be slow).
    """
    service = VinoBuzzService()

    try:
        wines = await service.fetch_all_wines(max_pages=max_pages)

        return WineSearchResponse(
            wines=[WineOut(**wine.to_dict()) for wine in wines],
            count=len(wines),
            query=None,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        await service.close()
