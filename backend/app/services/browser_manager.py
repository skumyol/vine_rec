"""Shared Playwright browser for the whole process.

Launching WebKit costs ~5-8s per SKU. By reusing one browser + context across
every call in the batch we save ~50-100s on a 10-SKU run.
"""

import asyncio
from typing import Optional
from playwright.async_api import async_playwright, Browser, BrowserContext, Playwright


class BrowserManager:
    _instance: Optional["BrowserManager"] = None
    _lock = asyncio.Lock()

    def __init__(self):
        self._pw: Optional[Playwright] = None
        self._browser: Optional[Browser] = None
        self._context: Optional[BrowserContext] = None

    @classmethod
    async def get(cls) -> "BrowserManager":
        if cls._instance is None:
            async with cls._lock:
                if cls._instance is None:
                    inst = cls()
                    await inst._start()
                    cls._instance = inst
        return cls._instance

    async def _start(self):
        self._pw = await async_playwright().start()
        self._browser = await self._pw.webkit.launch(headless=True)
        self._context = await self._browser.new_context(
            user_agent=(
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                "AppleWebKit/605.1.15"
            ),
            ignore_https_errors=True
        )

    async def new_page(self):
        if self._context is None:
            await self._start()
        return await self._context.new_page()

    async def shutdown(self):
        try:
            if self._context:
                await self._context.close()
            if self._browser:
                await self._browser.close()
            if self._pw:
                await self._pw.stop()
        finally:
            self._pw = None
            self._browser = None
            self._context = None
            BrowserManager._instance = None
