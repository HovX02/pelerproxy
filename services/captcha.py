"""
PelerProxy Bot — CAPTCHA Service
Solves reCAPTCHA v2 via configurable providers (AZCaptcha / 2Captcha).
"""
import asyncio
import logging

import config
import database

log = logging.getLogger("pelerproxy.captcha")


async def solve_recaptcha(session, query=None) -> str | None:
    """
    Solve a reCAPTCHA v2 challenge using the active captcha provider.
    Args:
        session: AsyncScraper instance
        query: Optional Telegram callback query for progress updates
    Returns:
        reCAPTCHA response token, or None on failure
    """
    # Get active provider info
    info = database.get_captcha_provider_info()
    provider_name = info["name"]
    api_url = info["api_url"]
    result_url = info["result_url"]
    api_key = info["api_key"]

    if not api_key:
        log.error(f"[CAPTCHA] No API key set for {provider_name}")
        return None

    log.info(f"[{provider_name}] Solving reCAPTCHA...")

    submit_data = {
        "key": api_key,
        "method": "userrecaptcha",
        "googlekey": config.WEBSHARE_RECAPTCHA_SITEKEY,
        "pageurl": config.WEBSHARE_REGISTER_URL,
        "json": 1,
    }

    try:
        resp = await session.post(api_url, data=submit_data, timeout=30)
        result = resp.json()
        if result.get("status") != 1:
            log.error(f"[{provider_name}] Submit failed: {result}")
            return None
        captcha_id = result["request"]
        log.info(f"[{provider_name}] Task ID: {captcha_id}")
    except Exception as e:
        log.error(f"[{provider_name}] Submit error: {e}")
        return None

    # Poll for result — animate progress 50% → 70%
    progress = 50
    for _ in range(60):
        await asyncio.sleep(5)
        try:
            resp = await session.get(
                result_url,
                params={
                    "key": api_key,
                    "action": "get",
                    "id": captcha_id,
                    "json": 1,
                },
                timeout=15,
            )
            data = resp.json()
            if data.get("status") == 1:
                log.info(f"[{provider_name}] Solved!")
                if query:
                    from ui.messages import update_progress
                    await update_progress(query, 75, "Captcha solved! Registering account...")
                return data["request"]
            if "CAPCHA_NOT_READY" not in str(data.get("request", "")):
                log.warning(f"[{provider_name}] Error: {data}")
                return None
            # Slowly tick progress bar while waiting
            if query and progress < 70:
                progress += 2
                from ui.messages import update_progress
                await update_progress(query, progress, "Solving captcha... please wait ☕")
        except Exception as e:
            log.error(f"[{provider_name}] Poll error: {e}")

    log.error(f"[{provider_name}] Timeout")
    return None