"""
PelerProxy Bot — Proxy Health Checker
Tests proxies before use, marks dead/alive in DB.
"""
import asyncio
import logging

import requests

import config
import database

log = logging.getLogger("pelerproxy.proxy_checker")


def check_single_proxy(proxy_string: str) -> bool:
    """
    Synchronous check: test if a proxy is alive.
    Proxy format: host:port:user:pass
    Returns True if proxy responds, False otherwise.
    """
    try:
        # Parse proxy_string: host:port:user:pass
        parts = proxy_string.split(":")
        if len(parts) == 4:
            host, port, user, pw = parts
            proxy_url = f"http://{user}:{pw}@{host}:{port}"
        else:
            # Simple host:port format
            proxy_url = f"http://{proxy_string}"

        proxies = {
            "http": proxy_url,
            "https": proxy_url,
        }
        resp = requests.get(
            config.PROXY_CHECK_URL,
            proxies=proxies,
            timeout=config.PROXY_CHECK_TIMEOUT,
        )
        if resp.status_code == 200:
            return True
    except Exception:
        pass
    return False


async def check_proxy_async(proxy_string: str) -> bool:
    """Async wrapper for proxy check."""
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, check_single_proxy, proxy_string)


async def pick_alive_proxy(max_retries: int = None) -> str | None:
    """
    Pick a random proxy from the alive pool, verify it, and return it.
    If max_retries is reached, returns None.
    """
    if max_retries is None:
        max_retries = config.PROXY_MAX_RETRIES

    tried = set()
    for attempt in range(max_retries):
        # Get alive proxies from DB
        proxies = database.get_alive_proxies(100)
        if not proxies:
            log.warning("[PROXY-CHECK] No alive proxies in pool")
            return None

        # Pick one we haven't tried
        available = [p for p in proxies if p not in tried]
        if not available:
            log.warning("[PROXY-CHECK] Exhausted all proxies")
            return None

        proxy = available[0]
        tried.add(proxy)

        # Verify it's actually alive
        log.info(f"[PROXY-CHECK] Testing proxy (#{attempt + 1}): {proxy[:30]}...")
        is_alive = await check_proxy_async(proxy)

        if is_alive:
            database.mark_proxy_alive(proxy)
            log.info(f"[PROXY-CHECK] Proxy alive: {proxy[:30]}...")
            return proxy
        else:
            database.mark_proxy_dead(proxy)
            log.info(f"[PROXY-CHECK] Proxy dead: {proxy[:30]}...")

    return None


async def get_proxy_for_registration() -> tuple[str | None, str]:
    """
    Get a proxy for registration. Falls back gracefully.
    Returns (proxy_string, status_message).
    """
    # Check if proxy mode is on
    if not database.get_proxy_mode():
        return None, "Proxy mode OFF — using direct connection"

    # Try to get alive proxy
    proxy = await pick_alive_proxy()

    if proxy:
        host = proxy.split(":")[0] if ":" in proxy else proxy
        return proxy, f"Proxy ready: {host}"

    # No proxy available
    return None, "No alive proxies — fallback to direct"


async def refresh_proxy_pool(progress_callback=None) -> dict:
    """
    Check all proxies in pool, update their status.
    Returns {total, alive, dead, deleted}.
    """
    from database import get_recent_proxies

    all_proxies = get_recent_proxies(500)
    total = len(all_proxies)
    alive = 0
    dead = 0

    if progress_callback:
        await progress_callback(0, f"Checking {total} proxies...")

    for i, proxy in enumerate(all_proxies):
        is_ok = await check_proxy_async(proxy)
        if is_ok:
            database.mark_proxy_alive(proxy)
            alive += 1
        else:
            database.mark_proxy_dead(proxy)
            dead += 1

        if progress_callback and i % 5 == 0:
            pct = int((i + 1) / total * 100)
            await progress_callback(pct, f"Checked {i + 1}/{total}... Alive: {alive}")

    deleted = database.delete_dead_proxies()

    return {
        "total": total,
        "alive": alive,
        "dead": dead,
        "deleted": deleted,
    }