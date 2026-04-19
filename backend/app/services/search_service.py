import asyncio
import hashlib
from typing import List, Optional, Dict, Any
import httpx
from urllib.parse import urlparse, quote
from playwright.async_api import async_playwright

from app.models.sku import ParsedSKU, SearchQuery
from app.models.candidate import ImageCandidate
from app.core.config import settings
from app.core.constants import SOURCE_TRUST_RANKING
from app.services.browser_manager import BrowserManager


# Parallelism cap for concurrent Bing query pages (per SKU)
_BING_CONCURRENCY = 3


class SearchService:
    def __init__(self):
        self.provider = settings.SEARCH_PROVIDER
        self.api_key = settings.SEARCH_API_KEY or settings.SERPAPI_KEY
        self.client = httpx.AsyncClient(timeout=30.0)
    
    async def search_candidates(
        self,
        parsed_sku: ParsedSKU,
        queries: List[SearchQuery]
    ) -> List[ImageCandidate]:
        # Run all queries concurrently (capped by semaphore) instead of
        # sequentially with 2s sleeps. Saves ~10s per SKU.
        sem = asyncio.Semaphore(_BING_CONCURRENCY)

        async def run(q: SearchQuery):
            async with sem:
                try:
                    return await self._search_with_query(q, parsed_sku)
                except Exception as e:
                    print(f"Search error for query '{q.query}': {e}")
                    return []

        results = await asyncio.gather(*[run(q) for q in queries])

        all_candidates: List[ImageCandidate] = []
        for r in results:
            all_candidates.extend(r)

        # Fallback: if auto mode returned nothing, try Playwright on first 2 queries
        if not all_candidates and self.provider == "auto":
            print("No candidates from primary search, trying Playwright fallback...")
            for query in queries[:2]:
                try:
                    candidates = await self._search_playwright(query, parsed_sku)
                    all_candidates.extend(candidates)
                    if all_candidates:
                        break
                except Exception as e:
                    print(f"Playwright fallback error: {e}")

        deduplicated = self._deduplicate_candidates(all_candidates)
        ranked = self._rank_by_source(deduplicated)

        # Cap total candidates to reduce downstream OCR/VLM cost
        return ranked[:settings.MAX_TOTAL_CANDIDATES]
    
    async def _search_with_query(
        self,
        query: SearchQuery,
        parsed_sku: ParsedSKU
    ) -> List[ImageCandidate]:
        # Use serpapi if api_key available and provider is serpapi or auto
        if self.provider == "serpapi" or (self.provider == "auto" and self.api_key):
            return await self._search_serpapi(query, parsed_sku)
        elif self.provider == "playwright":
            return await self._search_playwright(query, parsed_sku)
        elif self.provider == "bing":
            return await self._search_bing(query, parsed_sku)
        elif self.provider == "mock":
            return await self._search_mock(query, parsed_sku)
        else:
            return await self._search_duckduckgo(query, parsed_sku)
    
    async def _search_serpapi(
        self,
        query: SearchQuery,
        parsed_sku: ParsedSKU
    ) -> List[ImageCandidate]:
        if not self.api_key:
            return []
        
        url = "https://serpapi.com/search"
        params = {
            "engine": "google_images",
            "q": query.query,
            "api_key": self.api_key,
            "num": settings.MAX_CANDIDATES_PER_QUERY,
        }
        
        try:
            response = await self.client.get(url, params=params)
            response.raise_for_status()
            data = response.json()
            
            candidates = []
            for result in data.get("images_results", []):
                image_url = result.get("original")
                if not image_url:
                    continue
                
                source_url = result.get("source", "")
                domain = self._extract_domain(source_url)
                
                candidate = ImageCandidate(
                    id=self._generate_id(image_url),
                    source_query=query.query,
                    source_page=source_url,
                    source_domain=domain,
                    image_url=image_url,
                    width=result.get("original_width"),
                    height=result.get("original_height"),
                    source_trust_score=self._calculate_trust(domain)
                )
                candidates.append(candidate)
            
            return candidates
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 429:
                print(f"SerpAPI rate limit (429) for query: {query.query[:50]}...")
            else:
                print(f"SerpAPI HTTP error {e.response.status_code}: {e}")
            return []
        except Exception as e:
            print(f"SerpAPI error: {e}")
            return []
    
    async def _search_playwright(
        self,
        query: SearchQuery,
        parsed_sku: ParsedSKU
    ) -> List[ImageCandidate]:
        """Use Playwright to scrape Google Images."""
        candidates = []
        
        try:
            async with async_playwright() as p:
                # Launch browser in headless mode
                browser = await p.webkit.launch(headless=True)
                context = await browser.new_context(
                    user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15"
                )
                page = await context.new_page()
                
                # Construct Google Images search URL
                search_url = f"https://www.google.com/search?q={quote(query.query)}&tbm=isch"
                
                await page.goto(search_url, wait_until="networkidle")
                
                # Wait for images to load
                await page.wait_for_selector("img", timeout=10000)
                
                # Extract image data
                # Google Images uses a complex structure, we'll extract what we can
                image_data = await page.evaluate("""
                    () => {
                        const images = [];
                        const imgElements = document.querySelectorAll('img');
                        
                        imgElements.forEach(img => {
                            const src = img.src;
                            if (src && src.startsWith('http') && !src.includes('google')) {
                                const width = img.naturalWidth || img.width || 0;
                                const height = img.naturalHeight || img.height || 0;
                                
                                // Try to find source link
                                let sourceUrl = '';
                                let parent = img.closest('a');
                                if (parent && parent.href) {
                                    sourceUrl = parent.href;
                                }
                                
                                images.push({
                                    src: src,
                                    width: width,
                                    height: height,
                                    source: sourceUrl
                                });
                            }
                        });
                        
                        return images.slice(0, 20);
                    }
                """)
                
                await browser.close()
                
                # Convert to candidates
                for idx, img in enumerate(image_data):
                    if not img.get('src'):
                        continue
                    
                    domain = self._extract_domain(img.get('source', ''))
                    
                    candidate = ImageCandidate(
                        id=self._generate_id(img['src'] + str(idx)),
                        source_query=query.query,
                        source_page=img.get('source', ''),
                        source_domain=domain,
                        image_url=img['src'],
                        width=img.get('width'),
                        height=img.get('height'),
                        source_trust_score=self._calculate_trust(domain)
                    )
                    candidates.append(candidate)
                
                print(f"Playwright found {len(candidates)} candidates for query: {query.query}")
                
        except Exception as e:
            print(f"Playwright search error: {e}")
            return []
        
        return candidates[:settings.MAX_CANDIDATES_PER_QUERY]
    
    async def _search_bing(
        self,
        query: SearchQuery,
        parsed_sku: ParsedSKU
    ) -> List[ImageCandidate]:
        return []
    
    async def _search_duckduckgo(
        self,
        query: SearchQuery,
        parsed_sku: ParsedSKU
    ) -> List[ImageCandidate]:
        """Bing image search using a shared Playwright browser."""
        candidates: List[ImageCandidate] = []

        try:
            bm = await BrowserManager.get()
            page = await bm.new_page()
            try:
                search_url = f"https://www.bing.com/images/search?q={quote(query.query)}"
                await page.goto(search_url, wait_until="domcontentloaded", timeout=30000)
                await page.evaluate("window.scrollTo(0, 500)")
                # Short wait for thumbnails to lazy-load (was 3s)
                await asyncio.sleep(1.2)

                image_data = await page.evaluate("""
                    () => {
                        const images = [];
                        const imgElements = document.querySelectorAll('img[src*="th.bing.com"], img[src*="thf.bing.com"]');

                        imgElements.forEach(img => {
                            const src = img.src;
                            if (src && src.includes('w=42&h=42')) {
                                const largeSrc = src.replace('w=42&h=42', 'w=800&h=1000');
                                images.push({
                                    src: largeSrc,
                                    width: 800,
                                    height: 1000,
                                    source: 'bing'
                                });
                            }
                        });

                        return images.slice(0, 10);
                    }
                """)
            finally:
                await page.close()

            for idx, img in enumerate(image_data):
                if not img.get('src'):
                    continue

                candidate = ImageCandidate(
                    id=self._generate_id(img['src'] + str(idx)),
                    source_query=query.query,
                    source_page=img.get('source', ''),
                    source_domain='bing',
                    image_url=img['src'],
                    width=img.get('width'),
                    height=img.get('height'),
                    source_trust_score=SOURCE_TRUST_RANKING["unknown"]
                )
                candidates.append(candidate)

        except Exception as e:
            print(f"Bing search error: {e}")
            return []

        return candidates[:settings.MAX_CANDIDATES_PER_QUERY]

    async def _search_mock(
        self,
        query: SearchQuery,
        parsed_sku: ParsedSKU
    ) -> List[ImageCandidate]:
        """Mock search for testing - returns sample image URLs."""
        import random

        # Sample wine images for testing
        mock_images = [
            {
                "url": "https://images.vivino.com/thumbs/5a_Q4C3tR1K9a1G2x3y4w5_thumb.jpg",
                "domain": "vivino.com",
                "width": 400,
                "height": 600
            },
            {
                "url": "https://cdn.wine-searcher.com/images/labels/12/34/56/1234567890.jpg",
                "domain": "wine-searcher.com",
                "width": 300,
                "height": 500
            },
            {
                "url": "https://www.wine.com/product/images/12345678901234.jpg",
                "domain": "wine.com",
                "width": 350,
                "height": 550
            }
        ]

        candidates = []
        for idx, img in enumerate(mock_images):
            candidate = ImageCandidate(
                id=self._generate_id(img["url"] + str(idx)),
                source_query=query.query,
                source_page=f"https://{img['domain']}/wine/test",
                source_domain=img["domain"],
                image_url=img["url"],
                width=img["width"],
                height=img["height"],
                source_trust_score=self._calculate_trust(img["domain"])
            )
            candidates.append(candidate)

        # Simulate network delay
        await asyncio.sleep(0.5)

        return candidates

    def _extract_domain(self, url: str) -> str:
        try:
            parsed = urlparse(url)
            domain = parsed.netloc.lower()
            if domain.startswith('www.'):
                domain = domain[4:]
            return domain
        except:
            return "unknown"
    
    def _calculate_trust(self, domain: str) -> int:
        domain_lower = domain.lower()
        
        winery_indicators = ['domaine', 'chateau', 'weingut', 'winery', 'vineyard']
        if any(ind in domain_lower for ind in winery_indicators):
            return SOURCE_TRUST_RANKING["winery"]
        
        merchant_indicators = ['wine.com', 'klwines', 'vivino', 'wine-searcher', 'astorwines']
        if any(ind in domain_lower for ind in merchant_indicators):
            return SOURCE_TRUST_RANKING["merchant"]
        
        review_indicators = ['robertparker', 'wineadvocate', 'jancisrobinson', 'vinous', 'burghound']
        if any(ind in domain_lower for ind in review_indicators):
            return SOURCE_TRUST_RANKING["review_site"]
        
        auction_indicators = ['winebid', 'klang', 'zachys', 'spectrum', 'crusewine']
        if any(ind in domain_lower for ind in auction_indicators):
            return SOURCE_TRUST_RANKING["auction"]
        
        return SOURCE_TRUST_RANKING["unknown"]
    
    def _deduplicate_candidates(self, candidates: List[ImageCandidate]) -> List[ImageCandidate]:
        seen_hashes = set()
        unique = []
        
        for candidate in candidates:
            url_hash = hashlib.md5(candidate.image_url.encode()).hexdigest()[:16]
            if url_hash not in seen_hashes:
                seen_hashes.add(url_hash)
                unique.append(candidate)
        
        return unique
    
    def _rank_by_source(self, candidates: List[ImageCandidate]) -> List[ImageCandidate]:
        return sorted(
            candidates,
            key=lambda c: (
                -c.source_trust_score,
                -(c.width or 0) * (c.height or 0)
            )
        )
    
    def _generate_id(self, url: str) -> str:
        return hashlib.md5(url.encode()).hexdigest()[:12]
    
    async def close(self):
        await self.client.aclose()
