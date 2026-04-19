"""Wine-Searcher image search alternative."""

import asyncio
from typing import List, Dict, Any, Optional
from urllib.parse import quote
from playwright.async_api import async_playwright


class WineSearcherClient:
    """Search for wine images on Wine-Searcher."""
    
    async def search(
        self, 
        producer: str, 
        appellation: Optional[str] = None,
        vintage: Optional[str] = None,
        max_results: int = 10
    ) -> List[Dict[str, Any]]:
        """Search Wine-Searcher for wine bottle images."""
        
        # Build search query
        query_parts = [producer]
        if vintage and vintage != "NV":
            query_parts.append(vintage)
        if appellation:
            query_parts.append(appellation)
        
        query = " ".join(query_parts)
        search_url = f"https://www.wine-searcher.com/find/{quote(query.replace(' ', '+'))}"
        
        candidates = []
        
        try:
            async with async_playwright() as p:
                browser = await p.webkit.launch(headless=True)
                context = await browser.new_context(
                    user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15"
                )
                page = await context.new_page()
                
                await page.goto(search_url, wait_until="domcontentloaded", timeout=30000)
                await asyncio.sleep(3)
                
                # Extract wine images from results
                image_data = await page.evaluate("""
                    () => {
                        const images = [];
                        // Look for wine bottle images in search results
                        const selectors = [
                            'img[src*="wine"]', 
                            'img[src*="bottle"]',
                            '.wine-image img',
                            '[data-testid="wine-image"] img',
                            'img[alt*="bottle"]'
                        ];
                        
                        selectors.forEach(selector => {
                            document.querySelectorAll(selector).forEach(img => {
                                const src = img.src || img.getAttribute('data-src');
                                if (src && src.startsWith('http') && 
                                    (src.includes('.jpg') || src.includes('.jpeg') || src.includes('.png'))) {
                                    images.push({
                                        src: src,
                                        width: img.naturalWidth || 400,
                                        height: img.naturalHeight || 600,
                                        alt: img.alt || ''
                                    });
                                }
                            });
                        });
                        
                        return images.slice(0, 10);
                    }
                """)
                
                await browser.close()
                
                for idx, img in enumerate(image_data):
                    if img.get('src'):
                        candidates.append({
                            "image_url": img['src'],
                            "source_page": search_url,
                            "source_domain": "wine-searcher.com",
                            "width": img.get('width', 400),
                            "height": img.get('height', 600),
                            "alt_text": img.get('alt', '')
                        })
                        
        except Exception as e:
            print(f"Wine-Searcher search error: {e}")
            
        return candidates[:max_results]
