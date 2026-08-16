"""
PelerProxy Bot — Admin Handler
Full admin panel: stats, broadcast, user management, ban/unban, reset limits.
"""
import asyncio
import logging

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
from ui.keyboards import (
    admin_menu,
    admin_captcha_menu,
    admin_proxy_menu,
    admin_user_pagination,
    admin_user_detail,
    back_to_menu,
    confirm_cancel,
)
from ui.messages import admin_stats_message, user_detail_message, error_message

log = logging.getLogger("pelerproxy.admin")

# Broadcast state
WAITING_BROADCAST = 100


# ==================== GUARD ====================

def _admin_only(query_or_update, context) -> bool:
    """Check if user is admin. Returns True if admin, False if not."""
    user_id = None
    if hasattr(query_or_update, "from_user"):
        user_id = query_or_update.from_user.id
    elif hasattr(query_or_update, "effective_user"):
        user_id = query_or_update.effective_user.id

    if not database.is_admin(user_id):
        return False
    return True


# ==================== MENU ====================

async def admin_menu_handler(query, context):
    """Show admin panel menu."""
    if not _admin_only(query, context):
        await query.edit_message_text("⛔ Access denied.", reply_markup=back_to_menu())
        return

    await query.edit_message_text(
        "🛡️ *Admin Panel*\n\nSelect an action:",
        parse_mode="Markdown",
        reply_markup=admin_menu(),
    )


# ==================== DISPATCHER ====================

async def admin_callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle all admin callback queries."""
    query = update.callback_query
    await query.answer()

    if not _admin_only(query, context):
        await query.edit_message_text("⛔ Access denied.", reply_markup=back_to_menu())
        return

    data = query.data

    if data == "admin_stats":
        await _show_stats(query)

    elif data == "admin_users":
        await _show_users(query, 0)

    elif data.startswith("admin_users_p"):
        page = int(data.split("p")[1])
        await _show_users(query, page)

    elif data.startswith("admin_user_") and not data.startswith("admin_users"):
        user_id = int(data.replace("admin_user_", ""))
        await _show_user_detail(query, user_id)

    elif data == "admin_broadcast":
        await _start_broadcast(query, context)

    elif data == "admin_ban_menu":
        await query.edit_message_text(
            "🔨 *Ban / Unban User*\n\nSend the user ID you want to manage:",
            parse_mode="Markdown",
            reply_markup=back_to_menu(),
        )
        return WAITING_BROADCAST  # Reuse as input state

    elif data == "admin_reset":
        await query.edit_message_text(
            "🔄 *Reset User Limit*\n\nSend the user ID to reset today's registration limit:",
            parse_mode="Markdown",
            reply_markup=back_to_menu(),
        )
        return WAITING_BROADCAST

    elif data.startswith("admin_ban_"):
        user_id = int(data.replace("admin_ban_", ""))
        database.ban_user(user_id)
        await query.edit_message_text(
            f"✅ User `{user_id}` has been *banned*.",
            parse_mode="Markdown",
            reply_markup=admin_menu(),
        )

    elif data.startswith("admin_unban_"):
        user_id = int(data.replace("admin_unban_", ""))
        database.unban_user(user_id)
        await query.edit_message_text(
            f"✅ User `{user_id}` has been *unbanned*.",
            parse_mode="Markdown",
            reply_markup=admin_menu(),
        )

    elif data.startswith("admin_reset_"):
        user_id = int(data.replace("admin_reset_", ""))
        database.delete_today_registrations(user_id)
        await query.edit_message_text(
            f"✅ User `{user_id}`'s daily limit has been *reset*.",
            parse_mode="Markdown",
            reply_markup=admin_menu(),
        )

    elif data == "admin_proxy_menu":
        await _show_proxy_menu(query)

    elif data == "admin_proxy_toggle":
        await _toggle_proxy_mode(query)

    elif data == "admin_proxy_check":
        await _check_all_proxies(query)

    elif data == "admin_proxy_prune":
        await _prune_dead_proxies(query)

    elif data == "admin_captcha_menu":
        await _show_captcha_menu(query)

    elif data == "admin_captcha_switch":
        await _switch_captcha_provider(query)

    elif data == "admin_captcha_key":
        await _prompt_captcha_key(query, context)


# ==================== CAPTCHA ====================

async def _show_captcha_menu(query):
    """Show captcha settings sub-menu."""
    info = database.get_captcha_provider_info()
    await query.edit_message_text(
        f"🧩 *Captcha Settings*\n\n"
        f"Active: *{info['name']}*\n"
        f"API Key: `{info['api_key_masked']}`\n\n"
        f"Click to switch provider or set API key.",
        parse_mode="Markdown",
        reply_markup=admin_captcha_menu(info),
    )


async def _switch_captcha_provider(query):
    """Switch between azcaptcha and 2captcha."""
    current = database.get_captcha_provider()
    new = "2captcha" if current == "azcaptcha" else "azcaptcha"
    database.set_captcha_provider(new)
    info = database.get_captcha_provider_info()
    await query.answer(f"Switched to {info['name']}")
    await _show_captcha_menu(query)


async def _prompt_captcha_key(query, context):
    """Prompt admin to enter new API key."""
    context.user_data["admin_action"] = "captcha_key"
    await query.edit_message_text(
        "🔐 *Set API Key*\n\n"
        "Send the new API key for the current captcha provider:",
        parse_mode="Markdown",
        reply_markup=back_to_menu(),
    )
    return WAITING_BROADCAST


# ==================== STATS ====================

async def _show_stats(query):
    stats = database.get_stats()
    await query.edit_message_text(
        admin_stats_message(stats),
        parse_mode="Markdown",
        reply_markup=admin_menu(),
    )


# ==================== USERS ====================

async def _show_users(query, page: int):
    per_page = 5
    users = database.get_all_users(limit=per_page, offset=page * per_page)
    total = database.count_users()
    total_pages = max(1, (total + per_page - 1) // per_page)

    await query.edit_message_text(
        f"👥 *Users* (Page {page + 1}/{total_pages})\n\nSelect a user to manage:",
        parse_mode="Markdown",
        reply_markup=admin_user_pagination(users, page, total_pages),
    )


async def _show_user_detail(query, user_id: int):
    user = database.get_or_create_user(user_id)
    registrations = database.get_user_registrations(user_id)
    await query.edit_message_text(
        user_detail_message(user, registrations),
        parse_mode="Markdown",
        reply_markup=admin_user_detail(user_id),
    )


# ==================== PROXY SETTINGS ====================

async def _show_proxy_menu(query):
    """Show proxy settings sub-menu."""
    proxy_mode = database.get_proxy_mode()
    stats = database.get_stats()
    await query.edit_message_text(
        "🎛 *Proxy Pool Settings*\n\n"
        "Pool source: *Admin accounts only*\n"
        f"Mode: {'🟢 ON' if proxy_mode else '🔴 OFF'}\n"
        f"Auto-create will {'use proxy from pool' if proxy_mode else 'connect directly'}\n"
        f"Alive: *{stats['alive_proxies']}* / Total: *{stats['total_proxies']}*",
        parse_mode="Markdown",
        reply_markup=admin_proxy_menu(proxy_mode, stats),
    )


async def _toggle_proxy_mode(query):
    """Toggle proxy mode ON/OFF."""
    new_state = database.toggle_proxy_mode()
    status = "🟢 ON" if new_state else "🔴 OFF"
    await query.answer(f"Proxy mode: {status}")
    await _show_proxy_menu(query)


async def _check_all_proxies(query):
    """Check all proxies in pool for health."""
    from services.proxy_checker import refresh_proxy_pool

    await query.edit_message_text("🔍 *Checking all proxies...*\n\nThis may take a while...", parse_mode="Markdown")

    async def progress_cb(pct, status):
        try:
            await query.edit_message_text(
                f"🔍 *Checking proxies...*\n\n`{status}`\nProgress: {pct}%",
                parse_mode="Markdown",
            )
        except Exception:
            pass

    result = await refresh_proxy_pool(progress_callback=progress_cb)

    await query.edit_message_text(
        f"✅ *Proxy Check Complete!*\n\n"
        f"Total checked: *{result['total']}*\n"
        f"💚 Alive: *{result['alive']}*\n"
        f"💀 Dead: *{result['dead']}*\n"
        f"🗑 Deleted: *{result['deleted']}*",
        parse_mode="Markdown",
        reply_markup=admin_menu(),
    )


async def _prune_dead_proxies(query):
    """Delete all dead proxies from pool."""
    deleted = database.delete_dead_proxies()
    await query.edit_message_text(
        f"🗑 *Dead Proxies Purged!*\n\nDeleted: *{deleted}* proxies from pool.",
        parse_mode="Markdown",
        reply_markup=admin_menu(),
    )


# ==================== BROADCAST ====================

async def _start_broadcast(query, context):
    context.user_data["admin_action"] = "broadcast"
    await query.edit_message_text(
        "📢 *Broadcast*\n\nSend the message you want to broadcast to all users:",
        parse_mode="Markdown",
        reply_markup=back_to_menu(),
    )
    return WAITING_BROADCAST


async def handle_broadcast_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Receive and broadcast a message to all users."""
    user_id = update.effective_user.id
    if not database.is_admin(user_id):
        await update.message.reply_text("⛔ Access denied.")
        return ConversationHandler.END

    action = context.user_data.get("admin_action", "")

    if action == "broadcast":
        msg = update.message.text
        users = database.get_all_users(limit=1000)

        sent = 0
        failed = 0
        for user in users:
            try:
                await context.bot.send_message(
                    chat_id=user["user_id"],
                    text=f"📢 *Broadcast from Admin*\n\n{msg}",
                    parse_mode="Markdown",
                )
                sent += 1
                await asyncio.sleep(0.05)  # Rate limit prevention
            except Exception:
                failed += 1

        await update.message.reply_text(
            f"✅ Broadcast complete!\n\n📤 Sent: {sent}\n❌ Failed: {failed}",
            reply_markup=back_to_menu(),
        )

    else:
        # Ban/unban/reset by user ID
        try:
            target_id = int(update.message.text.strip())
        except ValueError:
            await update.message.reply_text(
                "❌ Invalid user ID. Send a numeric ID.",
                reply_markup=back_to_menu(),
            )
            return ConversationHandler.END

        if action == "ban":
            database.ban_user(target_id)
            await update.message.reply_text(
                f"✅ User `{target_id}` banned.",
                parse_mode="Markdown",
                reply_markup=admin_menu(),
            )
        elif action == "reset":
            database.delete_today_registrations(target_id)
            await update.message.reply_text(
                f"✅ User `{target_id}`'s limit reset.",
                parse_mode="Markdown",
                reply_markup=admin_menu(),
            )

        elif action == "captcha_key":
            new_key = update.message.text.strip()
            provider = database.get_captcha_provider()
            database.set_captcha_api_key(provider, new_key)
            info = database.get_captcha_provider_info()
            await update.message.reply_text(
                f"✅ API key for *{info['name']}* updated!\n"
                f"Key: `{info['api_key_masked']}`",
                parse_mode="Markdown",
                reply_markup=admin_menu(),
            )

    return ConversationHandler.END


# ==================== BUILD ADMIN CONVERSATION ====================

def build_admin_conv_handler() -> ConversationHandler:
    """Build ConversationHandler for admin text input actions."""
    return ConversationHandler(
        entry_points=[
            CallbackQueryHandler(admin_callback_handler, pattern="^admin_"),
        ],
        states={
            WAITING_BROADCAST: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, handle_broadcast_message),
            ],
        },
        fallbacks=[CommandHandler("cancel", _cancel_admin)],
        per_chat=True,
        per_message=False,
    )


async def _cancel_admin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("❌ Cancelled.", reply_markup=admin_menu())
    return ConversationHandler.END