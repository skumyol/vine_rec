import asyncio
import json
import re
from dataclasses import dataclass, asdict
from typing import Optional, List, Dict, Any
from urllib.parse import quote_plus, urljoin, urlparse

from playwright.async_api import async_playwright, Page, BrowserContext, TimeoutError as PlaywrightTimeoutError

# ----------------------------
# Config
# ----------------------------

SEARCH_ENGINE = "bing"
HEADLESS = True
NAV_TIMEOUT_MS = 30000
RESULT_WAIT_MS = 8000
MAX_SEARCH_RESULTS = 8
MAX_IMAGES_PER_PAGE = 12
MAX_CONCURRENT_PAGES = 3  # Reduced for WebKit stability

BAD_IMAGE_PATTERNS = (
    "placeholder", "no-image", "no_image", "default",
    "sprite", "icon", "logo", "avatar", "banner", "thumb",
)

BAD_IMAGE_EXTENSIONS = (".svg",)

PREFERRED_IMAGE_HINTS = ("product", "bottle", "wine", "vin", "image", "photo")

# Minimum dimensions for usable images
MIN_IMAGE_WIDTH = 300
MIN_IMAGE_HEIGHT = 300

# ----------------------------
# Data models
# ----------------------------

@dataclass
class SearchResult:
    title: str
    url: str
    domain: str
    rank: int
    query: str


@dataclass
class CandidateImage:
    image_url: str
    source_page: str
    source_domain: str
    source_title: str
    alt_text: str
    width: Optional[int]
    height: Optional[int]
    rank_on_page: int
    source_result_rank: int
    query: str
    extraction_method: str


# ----------------------------
# Helpers
# ----------------------------

def extract_domain(url: str) -> str:
    try:
        return urlparse(url).netloc.lower()
    except Exception:
        return ""


def is_http_url(url: Optional[str]) -> bool:
    return bool(url and url.startswith(("http://", "https://")))


def looks_like_bad_image(url: str) -> bool:
    u = url.lower()
    if any(p in u for p in BAD_IMAGE_PATTERNS):
        return True
    if any(u.endswith(ext) for ext in BAD_IMAGE_EXTENSIONS):
        return True
    return False


def score_image_hint(src: str, alt_text: str, width: Optional[int], height: Optional[int]) -> int:
    score = 0
    s = (src or "").lower()
    a = (alt_text or "").lower()

    for hint in PREFERRED_IMAGE_HINTS:
        if hint in s:
            score += 2
        if hint in a:
            score += 1

    if width and height:
        # Prefer vertical-ish images for bottle candidates
        if height > width:
            score += 3
        if height >= 400:
            score += 2
        if width >= 300:
            score += 1

    return score


def normalize_image_url(src: Optional[str], base_url: str) -> Optional[str]:
    if not src:
        return None
    src = src.strip()

    # handle protocol-relative URLs
    if src.startswith("//"):
        src = "https:" + src

    # handle relative URLs
    if src.startswith("/"):
        src = urljoin(base_url, src)

    if not is_http_url(src):
        return None

    return src


def build_search_url(query: str) -> str:
    q = quote_plus(query)
    if SEARCH_ENGINE == "bing":
        return f"https://www.bing.com/images/search?q={q}"
    raise ValueError(f"Unsupported search engine: {SEARCH_ENGINE}")


async def safe_text(locator, timeout: int = 1000) -> str:
    try:
        return (await locator.inner_text(timeout=timeout)).strip()
    except Exception:
        return ""


async def dismiss_common_popups(page: Page) -> None:
    candidates = [
        page.get_by_role("button", name=re.compile(r"accept|agree|allow", re.I)),
        page.get_by_role("button", name=re.compile(r"close|dismiss|got it", re.I)),
    ]
    for locator in candidates:
        try:
            if await locator.first.is_visible(timeout=1000):
                await locator.first.click(timeout=1000)
                return
        except Exception:
            continue


# ----------------------------
# Search result extraction
# ----------------------------

async def collect_search_results(page: Page, query: str, max_results: int = MAX_SEARCH_RESULTS) -> list[SearchResult]:
    url = build_search_url(query)
    await page.goto(url, wait_until="domcontentloaded", timeout=NAV_TIMEOUT_MS)
    await dismiss_common_popups(page)
    
    # Wait for image results to load
    await page.wait_for_selector(".iusc, .mimg, img", timeout=RESULT_WAIT_MS)

    results: list[SearchResult] = []

    # Bing Images: extract from image containers
    # Try different selectors for different Bing layouts
    selectors = [
        ".iusc",  # Main image container
        ".img_cont",  # Alternative container
        "[data-idx]",  # Indexed results
    ]
    
    seen = set()
    rank = 0
    
    for selector in selectors:
        try:
            items = page.locator(selector)
            count = min(await items.count(), 20)
            
            for i in range(count):
                item = items.nth(i)
                try:
                    # Try to get image URL from various attributes
                    href = await item.get_attribute("href")
                    murl = await item.get_attribute("murl")  # Bing's image URL attribute
                    
                    # Get source page URL
                    src_url = None
                    if href:
                        src_url = normalize_image_url(href, url)
                    
                    # Get actual image URL
                    img_url = murl or await item.locator("img").first.get_attribute("src")
                    
                    if not img_url:
                        continue
                        
                    if img_url in seen:
                        continue
                    seen.add(img_url)
                    
                    domain = extract_domain(src_url or img_url)
                    if not domain or "bing.com" in domain:
                        continue
                    
                    rank += 1
                    results.append(
                        SearchResult(
                            title=f"Bing result {rank}",
                            url=src_url or f"https://{domain}",
                            domain=domain,
                            rank=rank,
                            query=query,
                        )
                    )
                    
                    if len(results) >= max_results:
                        break
                except Exception:
                    continue
            
            if len(results) >= max_results:
                break
        except Exception:
            continue

    return results[:max_results]


# ----------------------------
# Source page image extraction
# ----------------------------

async def extract_images_from_source_page(
    page: Page,
    result: SearchResult,
    max_images: int = MAX_IMAGES_PER_PAGE,
) -> list[CandidateImage]:
    try:
        await page.goto(result.url, wait_until="domcontentloaded", timeout=NAV_TIMEOUT_MS)
        await dismiss_common_popups(page)
    except PlaywrightTimeoutError:
        return []
    except Exception:
        return []

    page_title = await page.title()
    images = page.locator("img")
    
    try:
        img_count = min(await images.count(), 40)
    except Exception:
        return []

    raw_candidates: list[CandidateImage] = []

    for i in range(img_count):
        img = images.nth(i)
        try:
            src = await img.get_attribute("src")
            src = normalize_image_url(src, result.url)
            if not src:
                continue
            if looks_like_bad_image(src):
                continue

            alt_text = (await img.get_attribute("alt")) or ""
            
            # Try to get dimensions
            width = None
            height = None
            try:
                width_attr = await img.get_attribute("width")
                height_attr = await img.get_attribute("height")
                width = int(width_attr) if width_attr and width_attr.isdigit() else None
                height = int(height_attr) if height_attr and height_attr.isdigit() else None
            except Exception:
                pass
            
            # Skip tiny images
            if width and height:
                if width < MIN_IMAGE_WIDTH or height < MIN_IMAGE_HEIGHT:
                    continue

            raw_candidates.append(
                CandidateImage(
                    image_url=src,
                    source_page=result.url,
                    source_domain=result.domain,
                    source_title=page_title[:300],
                    alt_text=alt_text[:300],
                    width=width,
                    height=height,
                    rank_on_page=i + 1,
                    source_result_rank=result.rank,
                    query=result.query,
                    extraction_method="img_tag",
                )
            )
        except Exception:
            continue

    # rank candidates by heuristic usefulness
    deduped: dict[str, CandidateImage] = {}
    for c in raw_candidates:
        if c.image_url not in deduped:
            deduped[c.image_url] = c

    ranked = sorted(
        deduped.values(),
        key=lambda c: score_image_hint(c.image_url, c.alt_text, c.width, c.height),
        reverse=True,
    )

    return ranked[:max_images]


# ----------------------------
# Concurrency orchestration
# ----------------------------

async def extract_from_one_result(
    context: BrowserContext,
    sem: asyncio.Semaphore,
    result: SearchResult,
) -> list[CandidateImage]:
    async with sem:
        page = await context.new_page()
        try:
            return await extract_images_from_source_page(page, result)
        finally:
            await page.close()


async def collect_candidates_for_query(query: str) -> dict:
    async with async_playwright() as p:
        # Use WebKit instead of Chromium (Chromium crashes on this Mac)
        browser = await p.webkit.launch(headless=HEADLESS)
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15"
        )

        search_page = await context.new_page()
        try:
            search_results = await collect_search_results(search_page, query)
        finally:
            await search_page.close()

        sem = asyncio.Semaphore(MAX_CONCURRENT_PAGES)
        tasks = [extract_from_one_result(context, sem, r) for r in search_results]
        image_lists = await asyncio.gather(*tasks, return_exceptions=True)

        candidates: list[CandidateImage] = []
        for item in image_lists:
            if isinstance(item, Exception):
                continue
            candidates.extend(item)

        # global dedupe
        deduped: dict[str, CandidateImage] = {}
        for c in candidates:
            if c.image_url not in deduped:
                deduped[c.image_url] = c

        final_candidates = list(deduped.values())

        await browser.close()

        return {
            "query": query,
            "search_results": [asdict(r) for r in search_results],
            "candidates": [asdict(c) for c in final_candidates],
            "candidate_count": len(final_candidates),
        }


# ----------------------------
# Wrapper for pipeline integration
# ----------------------------

async def search_with_playwright(wine_name: str, vintage: Optional[str] = None) -> List[Dict[str, Any]]:
    """Search for wine bottle images using Playwright."""
    query = wine_name
    if vintage and vintage != "NV":
        query += f" {vintage}"
    query += " bottle"
    
    result = await collect_candidates_for_query(query)
    
    # Convert to pipeline ImageCandidate format
    candidates = []
    for c in result.get("candidates", []):
        candidates.append({
            "image_url": c["image_url"],
            "source_page": c["source_page"],
            "source_domain": c["source_domain"],
            "width": c.get("width"),
            "height": c.get("height"),
            "alt_text": c.get("alt_text", ""),
        })
    
    return candidates


if __name__ == "__main__":
    query = "Domaine Arlaud Morey St Denis Monts Luisants 1er Cru 2019 bottle"
    data = asyncio.run(collect_candidates_for_query(query))
    print(json.dumps(data, indent=2, ensure_ascii=False))
