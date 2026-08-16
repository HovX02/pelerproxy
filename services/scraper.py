"""
PelerProxy Bot — Async Scraper
Cloudscraper wrapper with async support and optional proxy routing.
"""
import asyncio
from concurrent.futures import ThreadPoolExecutor

import requests
import cloudscraper


class AsyncScraper:
    """Async wrapper around synchronous cloudscraper with proxy support."""

    def __init__(self, proxy: str | None = None):
        self._scraper = None
        self._proxy = proxy
        self._executor = ThreadPoolExecutor(max_workers=1)

    def _get_scraper(self):
        if self._scraper is None:
            kwargs = {
                "browser": {"browser": "chrome", "platform": "windows", "mobile": False, "desktop": True},
            }
            if self._proxy:
                # Parse proxy_string: host:port:user:pass -> http://user:pass@host:port
                parts = self._proxy.split(":")
                if len(parts) == 4:
                    host, port, user, pw = parts
                    proxy_url = f"http://{user}:{pw}@{host}:{port}"
                else:
                    proxy_url = f"http://{self._proxy}"
                sess = requests.Session()
                sess.proxies = {"http": proxy_url, "https": proxy_url}
                kwargs["sess"] = sess
            self._scraper = cloudscraper.create_scraper(**kwargs)
        return self._scraper

    async def get(self, url, **kwargs):
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(self._executor, lambda: self._get_scraper().get(url, **kwargs))

    async def post(self, url, **kwargs):
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(self._executor, lambda: self._get_scraper().post(url, **kwargs))

    def close(self):
        if self._scraper:
            self._scraper.close()
        self._executor.shutdown(wait=False)