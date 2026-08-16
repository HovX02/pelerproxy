"""
PelerProxy Bot — Registration Handler
Auto + manual registration flows with rate limiting.
"""
import asyncio
import logging
import random
import time

from telegram import Update
from telegram.ext import (
    ContextTypes,
    ConversationHandler,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    filters,
)

import config
import database
from services.scraper import AsyncScraper
from services.webshare import register_webshare, fetch_proxies
from services.email_gen import create_nullz_email
from services.proxy_checker import get_proxy_for_registration
from ui.keyboards import after_register, back_to_menu
from ui.messages import (
    update_progress,
    account_created_message,
    proxy_list_message,
    error_message,
    rate_limit_message,
)
from utils.rate_limit import check_rate_limit
from utils.validators import validate_email, validate_password

log = logging.getLogger("pelerproxy.register")

# Conversation states
WAITING_EMAIL, WAITING_PASSWORD = range(2)


# ==================== RATE LIMIT GUARD ====================

def _guard(user_id: int) -> tuple[bool, str]:
    """Check rate limit + ban. Admin bypasses all limits."""
    if database.is_admin(user_id):
        return True, ""
    can_register, reason = check_rate_limit(user_id)
    if not can_register:
        return False, rate_limit_message(reason)
    return True, ""


# ==================== AUTO REGISTRATION ====================

async def run_auto(query, context):
    """Automatic registration — checks proxy mode, picks alive proxy, falls back to direct."""
    user_id = query.from_user.id

    allowed, err_msg = _guard(user_id)
    if not allowed:
        await query.edit_message_text(err_msg, parse_mode="Markdown", reply_markup=back_to_menu())
        return

    await update_progress(query, 0, "Starting up...")

    # Step 1: Get proxy (if proxy mode is ON)
    await update_progress(query, 5, "Checking proxy settings...")
    proxy, proxy_msg = await get_proxy_for_registration()
    await update_progress(query, 10, proxy_msg)

    session = AsyncScraper(proxy=proxy)
    try:
        await update_progress(query, 15, "Initializing...")
        await asyncio.sleep(0.3)

        # Generate email
        await update_progress(query, 25, "Generating account details...")
        email, password = await create_nullz_email()

        # Submit captcha + register
        proxy_label = f" via proxy" if proxy else " (direct)"
        await update_progress(query, 50, f"Submitting captcha request{proxy_label}...")

        acc = await register_webshare(session, email, password, query)
        if not acc:
            await query.edit_message_text(
                error_message("Registration failed. Please try again later."),
                reply_markup=back_to_menu(),
            )
            return

        # Save to DB immediately (account is created, even if proxy fetch fails)
        reg_id = database.add_registration(
            user_id, acc["email"], acc["password"], acc["token"], 0
        )

        # Fetch proxies
        await update_progress(query, 85, "Fetching your proxies...")

        proxies = await fetch_proxies(session, acc["token"])
        proxy_count = len(proxies)

        if proxies:
            database.add_proxies(reg_id, proxies)

        # Also save to proxies.txt
        _save_proxies_to_file(proxies, email)

        # Done
        await update_progress(query, 100, "All done! ✅")
        await asyncio.sleep(0.5)

        # Build response
        if proxy:
            proxy_host = proxy.split(":")[0] if ":" in proxy else proxy
            prefix = f"🔄 *Created via Proxy*\n🌐 Via: `{proxy_host}`\n\n"
        else:
            prefix = f"🔗 *Created Direct*\n\n"

        if proxies:
            text = prefix + account_created_message(email, password, acc["token"], proxy_count)
            text += "\n" + proxy_list_message(proxies)
            await query.edit_message_text(
                text,
                parse_mode="Markdown",
                reply_markup=after_register(),
            )
        else:
            await query.edit_message_text(
                prefix + account_created_message(email, password, acc["token"], 0) + "\n⚠️ No proxies returned.",
                parse_mode="Markdown",
                reply_markup=after_register(),
            )

    except Exception as e:
        log.error(f"Auto error: {e}")
        await query.edit_message_text(
            error_message(f"Something went wrong: {str(e)[:200]}"),
            reply_markup=back_to_menu(),
        )
    finally:
        session.close()


# ==================== MANUAL REGISTRATION ====================

async def manual_entry(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Enter manual registration from button callback."""
    query = update.callback_query
    await query.answer()
    await query.edit_message_text("📧 Please send your *email* address:", parse_mode="Markdown")
    return WAITING_EMAIL


async def receive_email(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Receive manual email from user."""
    email = update.message.text.strip()

    valid, err = validate_email(email)
    if not valid:
        await update.message.reply_text(err)
        return WAITING_EMAIL

    context.user_data["manual_email"] = email
    await update.message.reply_text("🔑 Now send your *password*:", parse_mode="Markdown")
    return WAITING_PASSWORD


async def receive_password(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Receive manual password and complete registration."""
    user_id = update.effective_user.id
    password = update.message.text.strip()

    valid, err = validate_password(password)
    if not valid:
        await update.message.reply_text(err)
        return WAITING_PASSWORD

    # Rate limit check
    allowed, err_msg = _guard(user_id)
    if not allowed:
        await update.message.reply_text(err_msg, parse_mode="Markdown", reply_markup=back_to_menu())
        return ConversationHandler.END

    email = context.user_data.get("manual_email")

    await update.message.reply_text(
        "⏳ Registering...\nSolving captcha, please wait (1-5 min)...",
        parse_mode="Markdown",
    )

    session = AsyncScraper()
    try:
        acc = await register_webshare(session, email, password)
        if not acc:
            await update.message.reply_text(
                error_message("Registration failed. Try again later or use different email."),
                reply_markup=back_to_menu(),
            )
            return ConversationHandler.END

        database.add_registration(user_id, acc["email"], acc["password"], acc["token"], 0)

        await update.message.reply_text("✅ Account created! Fetching proxies...")

        proxies = await fetch_proxies(session, acc["token"])
        if proxies:
            reg = database.get_recent_registration(user_id)
            if reg:
                database.add_proxies(reg["id"], proxies)
            _save_proxies_to_file(proxies, email)
            text = proxy_list_message(proxies, email)
            await update.message.reply_text(text, parse_mode="Markdown")
        else:
            await update.message.reply_text(
                "✅ Account created but failed to fetch proxies.",
                reply_markup=back_to_menu(),
            )
    except Exception as e:
        log.error(f"Manual error: {e}")
        await update.message.reply_text(
            error_message(f"Error: {str(e)[:200]}"),
            reply_markup=back_to_menu(),
        )
    finally:
        session.close()

    return ConversationHandler.END


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Cancel the manual registration flow."""
    await update.message.reply_text("❌ Cancelled.", reply_markup=back_to_menu())
    return ConversationHandler.END


# ==================== BUILD CONVERSATION HANDLER ====================

def build_conv_handler() -> ConversationHandler:
    """Build the ConversationHandler for manual registration."""
    return ConversationHandler(
        entry_points=[CallbackQueryHandler(manual_entry, pattern="^manual$")],
        states={
            WAITING_EMAIL: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_email)],
            WAITING_PASSWORD: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_password)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
        per_chat=True,
        per_message=False,
    )


# ==================== HELPERS ====================

def _save_proxies_to_file(proxies: list[str], email: str = None):
    """Append proxies to proxies.txt log file."""
    timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
    lines = [f"\n{'=' * 50}", f"# {timestamp}"]
    if email:
        lines.append(f"# Email: {email}")
    lines.extend(proxies)
    with open(config.PROXIES_FILE, "a", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")