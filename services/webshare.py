"""
PelerProxy Bot — Webshare API Service
Account registration and proxy fetching.
"""
import time
import logging

import config

log = logging.getLogger("pelerproxy.webshare")


async def register_webshare(session, email: str, password: str, query=None) -> dict | None:
    """
    Register a new Webshare account.
    Args:
        session: AsyncScraper instance
        email: Account email
        password: Account password
        query: Optional Telegram callback query for progress updates
    Returns:
        Account dict {email, password, token, registered_at} or None on failure
    """
    from services.captcha import solve_recaptcha

    token = await solve_recaptcha(session, query)
    if not token:
        return None

    payload = {
        "email": email,
        "password": password,
        "recaptcha": token,
        "tos_accepted": True,
        "marketing_email_accepted": False,
    }

    try:
        resp = await session.post(
            f"{config.API_BASE}/register/",
            json=payload,
            headers={
                "Content-Type": "application/json",
                "Origin": "https://proxy.webshare.io",
                "Referer": "https://proxy.webshare.io/register",
            },
            timeout=25,
        )
        if resp.status_code in (200, 201):
            data = resp.json()
            api_token = data.get("token")
            if api_token:
                log.info(f"[REGISTER] Success: {email}")
                return {
                    "email": email,
                    "password": password,
                    "token": api_token,
                    "registered_at": int(time.time()),
                }
        log.warning(f"[REGISTER] Failed {resp.status_code}: {resp.text[:200]}")
    except Exception as e:
        log.error(f"[REGISTER] Exception: {e}")
    return None


async def fetch_proxies(session, token: str, count: int = None) -> list[str]:
    """
    Fetch proxies for a Webshare account.
    Args:
        session: AsyncScraper instance
        token: Webshare API token
        count: Number of proxies to fetch (default: from config)
    Returns:
        List of proxy strings in format host:port:user:pass
    """
    if count is None:
        count = config.MAX_PROXIES_PER_FETCH

    try:
        resp = await session.get(
            f"{config.API_BASE}/proxy/list/",
            params={"mode": "direct", "page": 1, "page_size": max(count, 25)},
            headers={"Authorization": f"Token {token}"},
            timeout=20,
        )
        if resp.status_code == 200:
            results = resp.json().get("results", [])
            proxies = []
            for p in results:
                user = p.get("username", "")
                pw = p.get("password", "")
                host = p.get("proxy_address", "")
                port = p.get("port", "")
                if user and pw and host and port:
                    proxies.append(f"{host}:{port}:{user}:{pw}")
                if len(proxies) >= count:
                    break
            return proxies
    except Exception as e:
        log.error(f"[FETCH] Error: {e}")
    return []