#!/usr/bin/env python3
"""Test if Playwright works on this system."""

import asyncio
from playwright.async_api import async_playwright

async def test_playwright():
    """Test basic Playwright functionality."""
    try:
        async with async_playwright() as p:
            print("Launching browser...")
            browser = await p.chromium.launch(
                headless=True,
                args=['--no-sandbox', '--disable-setuid-sandbox']
            )
            print(f"Browser launched: {browser}")
            
            context = await browser.new_context()
            page = await context.new_page()
            
            print("Navigating to google.com...")
            await page.goto("https://www.google.com", timeout=30000)
            print(f"Page title: {await page.title()}")
            
            await browser.close()
            print("✓ Playwright test PASSED")
            return True
            
    except Exception as e:
        print(f"✗ Playwright test FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    result = asyncio.run(test_playwright())
    exit(0 if result else 1)
