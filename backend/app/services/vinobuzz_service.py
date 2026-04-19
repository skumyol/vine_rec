"""Service to fetch wines from VinoBuzz marketplace."""

import httpx
from typing import List, Optional, Dict, Any
from app.core.config import settings

BASE_URL = "https://vinobuzz.ai"


class VinoBuzzWine:
    """Represents a wine from VinoBuzz."""

    def __init__(self, data: Dict[str, Any]):
        self.id: str = data.get("id") or data.get("sku", "")
        self.sku: str = data.get("sku", "")
        self.name: str = data.get("name") or data.get("title", "")
        self.vintage: Optional[str] = None
        if data.get("vintage"):
            self.vintage = str(data.get("vintage"))
        self.producer: str = data.get("producer") or data.get("winery", "")
        self.region: Optional[str] = data.get("region")
        self.country: Optional[str] = data.get("country")
        self.price_hkd: float = 0.0
        price_val = data.get("price") or data.get("price_hkd", "0")
        try:
            self.price_hkd = float(price_val)
        except (ValueError, TypeError):
            self.price_hkd = 0.0
        self.type: Optional[str] = data.get("type") or data.get("category")
        self.image: Optional[str] = data.get("image") or data.get("image_url")
        self.url: Optional[str] = data.get("url")
        self.stock: Optional[int] = data.get("stock")

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "sku": self.sku,
            "name": self.name,
            "vintage": self.vintage,
            "producer": self.producer,
            "region": self.region,
            "country": self.country,
            "price_hkd": self.price_hkd,
            "type": self.type,
            "image": self.image,
            "url": self.url,
            "stock": self.stock,
        }


class VinoBuzzService:
    """Service to interact with VinoBuzz marketplace API."""

    def __init__(self):
        self.session_id: Optional[str] = getattr(settings, "VINOBUZZ_SESSION_ID", None)
        self.client = httpx.AsyncClient(timeout=30.0)

    async def fetch_wines(
        self,
        page: int = 0,
        page_size: int = 60,
        search: Optional[str] = None,
        sort: str = "name_asc",
    ) -> List[VinoBuzzWine]:
        """Fetch wines from VinoBuzz marketplace.

        Args:
            page: Page number (0-indexed)
            page_size: Number of items per page
            search: Optional search query
            sort: Sort order (e.g., 'name_asc', 'price_asc')

        Returns:
            List of VinoBuzzWine objects
        """
        if not self.session_id:
            return []

        # Build URL with query params
        url = f"{BASE_URL}/api/v1/store/skus/search"
        params: Dict[str, Any] = {
            "page": page,
            "page_size": page_size,
            "sort": sort,
            "ai_search": "true",
        }
        if search:
            params["search"] = search

        headers = {
            "Accept": "application/json, text/plain, */*",
            "User-Agent": (
                "Mozilla/5.0 (iPhone; CPU iPhone OS 18_5 like Mac OS X) "
                "AppleWebKit/605.1.15 (KHTML, like Gecko) Version/18.5 "
                "Mobile/15E148 Safari/604.1"
            ),
            "Referer": "https://vinobuzz.ai/",
            "Cookie": f"session_id={self.session_id}",
        }

        try:
            response = await self.client.get(url, params=params, headers=headers)
            response.raise_for_status()
            data = response.json()

            # Extract wines from response
            items = data.get("data", {}).get("skus", [])
            if not items:
                items = data.get("skus", [])
            if not items:
                items = data.get("results", [])

            wines = [VinoBuzzWine(item) for item in items]
            return wines

        except httpx.HTTPError as e:
            print(f"HTTP error fetching wines: {e}")
            return []
        except Exception as e:
            print(f"Error fetching wines: {e}")
            return []

    async def fetch_all_wines(self, max_pages: int = 5) -> List[VinoBuzzWine]:
        """Fetch all wines across multiple pages.

        Args:
            max_pages: Maximum number of pages to fetch

        Returns:
            List of all VinoBuzzWine objects
        """
        all_wines: List[VinoBuzzWine] = []

        for page in range(max_pages):
            wines = await self.fetch_wines(page=page)
            if not wines:
                break
            all_wines.extend(wines)

        # Deduplicate by SKU
        seen_skus = set()
        unique_wines = []
        for wine in all_wines:
            if wine.sku not in seen_skus:
                seen_skus.add(wine.sku)
                unique_wines.append(wine)

        return unique_wines

    async def search_wines(self, query: str, limit: int = 20) -> List[VinoBuzzWine]:
        """Search wines by query string.

        Args:
            query: Search query
            limit: Maximum number of results

        Returns:
            List of matching VinoBuzzWine objects
        """
        if not query or not self.session_id:
            return []

        wines = await self.fetch_wines(page=0, page_size=limit, search=query)
        return wines[:limit]

    async def close(self):
        """Close the HTTP client."""
        await self.client.aclose()
