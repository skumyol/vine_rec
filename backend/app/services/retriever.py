"""Image retriever service for finding candidate wine images."""

from typing import List
from app.models.sku import ParsedSKU, SearchQuery
from app.models.candidate import ImageCandidate
from app.services.search_service import SearchService
from app.core.config import settings


class ImageRetriever:
    """Retrieves candidate images for a wine SKU."""

    def __init__(self):
        self.search_service = SearchService()
        self.max_candidates_per_query = settings.MAX_CANDIDATES_PER_QUERY

    async def retrieve_candidates(
        self,
        parsed_sku: ParsedSKU,
        queries: List[SearchQuery]
    ) -> List[ImageCandidate]:
        """
        Retrieve candidate images using multiple search queries.

        Args:
            parsed_sku: Parsed wine identity
            queries: List of search queries to execute

        Returns:
            List of unique image candidates ranked by quality
        """
        all_candidates: List[ImageCandidate] = []

        for query in queries:
            try:
                candidates = await self._search_with_query(query, parsed_sku)
                all_candidates.extend(candidates)
            except Exception as e:
                print(f"Retrieval error for query '{query.query}': {e}")
                continue

        # Deduplicate by URL
        seen_urls = set()
        unique_candidates = []
        for c in all_candidates:
            if c.image_url not in seen_urls:
                seen_urls.add(c.image_url)
                unique_candidates.append(c)

        # Sort by source trust score
        unique_candidates.sort(key=lambda x: -x.source_trust_score)

        return unique_candidates[:15]

    async def _search_with_query(
        self,
        query: SearchQuery,
        parsed_sku: ParsedSKU
    ) -> List[ImageCandidate]:
        """Execute a single search query."""
        return await self.search_service.search_candidates(parsed_sku, [query])

    async def close(self):
        """Clean up resources."""
        await self.search_service.close()
