#!/usr/bin/env python3
"""Test Bing image search directly."""

import asyncio
from playwright.async_api import async_playwright

async def test_bing():
    query = "Chateau Fonroque Saint-Emilion 2016 bottle"
    url = f"https://www.bing.com/images/search?q={query.replace(' ', '+')}"
    
    print(f"Navigating to: {url}")
    
    async with async_playwright() as p:
        browser = await p.webkit.launch(headless=True)
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15"
        )
        page = await context.new_page()
        
        await page.goto(url, wait_until="domcontentloaded", timeout=30000)
        print("Page loaded")
        
        # Scroll down to load more images
        await page.evaluate("window.scrollTo(0, 500)")
        await asyncio.sleep(2)
        
        # Take screenshot for debugging
        await page.screenshot(path="/tmp/bing_screenshot.png", full_page=True)
        print("Screenshot saved to /tmp/bing_screenshot.png")
        
        # Try to find actual result images (not SVG icons)
        images = page.locator("img[src^='http']")
        count = await images.count()
        print(f"Found {count} img elements")
        
        for i in range(min(count, 5)):
            img = images.nth(i)
            src = await img.get_attribute("src")
            width = await img.get_attribute("width") or "?"
            height = await img.get_attribute("height") or "?"
            print(f"  img {i}: {src[:60] if src else 'no src'}... ({width}x{height})")
        
        # Try to get larger images by modifying thumbnail URLs
        print("\nExtracting image URLs...")
        image_urls = []
        for i in range(min(count, 15)):
            img = images.nth(i)
            src = await img.get_attribute("src")
            if src and ('th.bing.com' in src or 'thf.bing.com' in src):
                # Try to get larger version by changing w/h params
                large_src = src.replace('w=42&h=42', 'w=800&h=1000')
                image_urls.append(large_src)
                print(f"  {i}: {large_src[:70]}...")
        
        # Try clicking first image to get full size
        print("\nClicking first image...")
        try:
            await images.nth(0).click()
            await asyncio.sleep(2)
            await page.screenshot(path="/tmp/bing_detail.png", full_page=True)
            print("Detail screenshot saved to /tmp/bing_detail.png")
            
            # Look for full-size image
            full_img = page.locator("img.nofocus").first
            if await full_img.is_visible(timeout=5000):
                full_src = await full_img.get_attribute("src")
                print(f"Full image from detail: {full_src[:80] if full_src else 'none'}...")
        except Exception as e:
            print(f"Click failed: {e}")
        
        await browser.close()

if __name__ == "__main__":
    asyncio.run(test_bing())
