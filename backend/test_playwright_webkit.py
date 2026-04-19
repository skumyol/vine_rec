#!/usr/bin/env python3
"""Test if Playwright WebKit works on this system."""

import asyncio
from playwright.async_api import async_playwright

async def test_webkit():
    """Test WebKit browser."""
    try:
        async with async_playwright() as p:
            print("Launching WebKit...")
            browser = await p.webkit.launch(headless=True)
            print(f"Browser launched: {browser}")
            
            context = await browser.new_context()
            page = await context.new_page()
            
            print("Navigating to google.com...")
            await page.goto("https://www.google.com", timeout=30000)
            print(f"Page title: {await page.title()}")
            
            await browser.close()
            print("✓ WebKit test PASSED")
            return True
            
    except Exception as e:
        print(f"✗ WebKit test FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    result = asyncio.run(test_webkit())
    exit(0 if result else 1)
