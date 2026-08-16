"""
PelerProxy Bot — Start Handler
/start command and main menu button dispatcher.
"""
import logging
from telegram import Update
from telegram.ext import ContextTypes, ConversationHandler

import database
from ui.keyboards import main_menu, back_to_menu
from ui.messages import welcome_message, banned_message

log = logging.getLogger("pelerproxy.start")


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /start command — show main menu."""
    user = update.effective_user
    user_id = user.id

    # Register or update user in DB
    db_user = database.get_or_create_user(
        user_id,
        username=user.username,
        first_name=user.first_name,
    )

    if db_user.get("is_banned"):
        await update.message.reply_text(banned_message(), parse_mode="Markdown")
        return

    is_admin = database.is_admin(user_id)
    await update.message.reply_text(
        welcome_message(is_admin),
        reply_markup=main_menu(is_admin),
        parse_mode="Markdown",
    )


async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Main menu button dispatcher.
    Handles: auto, manual, proxies, admin, auto_proxy, start (back to menu)
    """
    query = update.callback_query
    await query.answer()

    user_id = update.effective_user.id

    # Check ban
    if database.is_banned(user_id):
        await query.edit_message_text(banned_message(), parse_mode="Markdown")
        return

    data = query.data

    if data == "auto":
        from handlers.register import run_auto
        await run_auto(query, context)

    elif data == "manual":
        # ConversationHandler entry — switch to email input
        await query.edit_message_text("📧 Please send your *email* address:", parse_mode="Markdown")
        return ConversationHandler.END  # Will be picked up by the conv handler

    elif data == "proxies":
        from handlers.proxies import run_get_proxies
        await run_get_proxies(query, context)

    elif data == "admin":
        from handlers.admin import admin_menu_handler
        await admin_menu_handler(query, context)

    elif data == "start":
        # Back to menu
        is_admin = database.is_admin(user_id)
        await query.edit_message_text(
            welcome_message(is_admin),
            reply_markup=main_menu(is_admin),
            parse_mode="Markdown",
        )


async def go_back_to_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Helper to return to main menu from any callback."""
    query = update.callback_query
    if query:
        await query.answer()
        user_id = update.effective_user.id
        is_admin = database.is_admin(user_id)
        await query.edit_message_text(
            welcome_message(is_admin),
            reply_markup=main_menu(is_admin),
            parse_mode="Markdown",
        )