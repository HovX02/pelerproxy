"""
PelerProxy Bot — Proxies Handler
Fetch and display proxies from saved accounts.
"""
import logging

from telegram import Update
from telegram.ext import ContextTypes

import database
from services.scraper import AsyncScraper
from services.webshare import fetch_proxies
from ui.keyboards import back_to_menu
from ui.messages import proxy_list_message, error_message

log = logging.getLogger("pelerproxy.proxies")


async def run_get_proxies(query, context):
    """Fetch proxies from the user's most recent registration."""
    user_id = query.from_user.id

    # Try DB first
    reg = database.get_recent_registration(user_id)
    if not reg:
        await query.edit_message_text(
            error_message("No accounts found. Register first using /start"),
            reply_markup=back_to_menu(),
        )
        return

    await query.edit_message_text("🔍 Fetching your proxies...")

    session = AsyncScraper()
    try:
        proxies = await fetch_proxies(session, reg["token"])
        if proxies:
            # Also save to DB
            database.add_proxies(reg["id"], proxies)
            text = proxy_list_message(proxies, reg["email"])
            await query.edit_message_text(
                text,
                parse_mode="Markdown",
                reply_markup=back_to_menu(),
            )
        else:
            await query.edit_message_text(
                error_message("Failed to fetch proxies. Token may be expired."),
                reply_markup=back_to_menu(),
            )
    except Exception as e:
        log.error(f"Get proxies error: {e}")
        await query.edit_message_text(
            error_message(f"Error: {str(e)[:200]}"),
            reply_markup=back_to_menu(),
        )
    finally:
        session.close()


async def get_proxies_by_reg_id(query, reg_id: int):
    """Get proxies for a specific registration ID."""
    proxies = database.get_proxies_for_registration(reg_id)
    if proxies:
        text = proxy_list_message(proxies)
        await query.edit_message_text(text, parse_mode="Markdown", reply_markup=back_to_menu())
    else:
        await query.edit_message_text(
            error_message("No proxies found for this registration."),
            reply_markup=back_to_menu(),
        )