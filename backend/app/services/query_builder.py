"""Query builder for generating search queries from parsed SKU."""

from typing import List
from app.models.sku import ParsedSKU, SearchQuery


class QueryBuilder:
    """Builds search queries for wine image retrieval."""

    def build_queries(self, parsed_sku: ParsedSKU) -> List[SearchQuery]:
        """
        Build a list of search queries with varying specificity.

        Returns queries in priority order:
        1. Exact match with bottle keyword
        2. Exact match with wine keyword
        3. Exact match with label keyword
        4. Relaxed match with bottle keyword
        5. Relaxed base query
        6. Without vintage (if vintage present)
        """
        queries = []

        exact_base = self._build_exact_base(parsed_sku)
        if exact_base:
            queries.append(SearchQuery(
                query=f'{exact_base} bottle',
                query_type='exact',
                priority=1
            ))
            queries.append(SearchQuery(
                query=f'{exact_base} wine',
                query_type='exact',
                priority=2
            ))
            queries.append(SearchQuery(
                query=f'{exact_base} label',
                query_type='exact',
                priority=3
            ))

        relaxed_base = self._build_relaxed_base(parsed_sku)
        if relaxed_base:
            queries.append(SearchQuery(
                query=f'{relaxed_base} bottle',
                query_type='relaxed',
                priority=4
            ))
            queries.append(SearchQuery(
                query=relaxed_base,
                query_type='relaxed',
                priority=5
            ))

            if parsed_sku.vintage:
                without_vintage = relaxed_base.replace(parsed_sku.vintage, '').strip()
                if without_vintage != relaxed_base:
                    queries.append(SearchQuery(
                        query=f'{without_vintage} bottle',
                        query_type='vintage_fallback',
                        priority=6
                    ))

        return queries[:6]

    def _build_exact_base(self, parsed_sku: ParsedSKU) -> str:
        """Build exact search query with all available fields."""
        parts = []

        if parsed_sku.producer:
            parts.append(parsed_sku.producer)
        if parsed_sku.vineyard:
            parts.append(parsed_sku.vineyard)
        # Only add appellation if different from vineyard to avoid duplication
        if parsed_sku.appellation and parsed_sku.appellation != parsed_sku.vineyard:
            parts.append(parsed_sku.appellation)
        if parsed_sku.vintage:
            parts.append(parsed_sku.vintage)
        if parsed_sku.classification:
            parts.append(parsed_sku.classification)

        return ' '.join(parts)

    def _build_relaxed_base(self, parsed_sku: ParsedSKU) -> str:
        """Build relaxed search query with essential fields only."""
        parts = []

        if parsed_sku.producer:
            parts.append(parsed_sku.producer)
        if parsed_sku.appellation:
            parts.append(parsed_sku.appellation)
        if parsed_sku.vintage:
            parts.append(parsed_sku.vintage)

        return ' '.join(parts)

    def build_reverse_image_search_query(self, parsed_sku: ParsedSKU) -> str:
        """Build query optimized for reverse image search."""
        parts = []

        if parsed_sku.producer:
            parts.append(parsed_sku.producer)
        if parsed_sku.vineyard:
            parts.append(parsed_sku.vineyard)
        if parsed_sku.appellation:
            parts.append(parsed_sku.appellation)

        return ' '.join(parts)
