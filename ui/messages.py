"""
PelerProxy Bot — Message Templates
Reusable message builders and progress bar.
"""
import textwrap

from telegram import Update


# ==================== PROGRESS BAR ====================

def make_progress_bar(percent: int) -> str:
    """Build a 10-block ASCII progress bar."""
    filled = int(percent / 10)
    empty = 10 - filled
    return f"[{'█' * filled}{'░' * empty}] {percent}%"


async def update_progress(query, percent: int, status: str):
    """Edit a message to show a progress bar with status."""
    bar = make_progress_bar(percent)
    text = (
        f"⚙️ *Processing...*\n\n"
        f"`{bar}`\n\n"
        f"📌 {status}"
    )
    try:
        await query.edit_message_text(text, parse_mode="Markdown")
    except Exception:
        pass


# ==================== MESSAGES ====================

def welcome_message(is_admin: bool = False) -> str:
    """Welcome /start message."""
    msg = (
        "🌐 *PelerProxy Bot*\n\n"
        "Automated Webshare proxy account creator.\n"
        "Get fresh SOCKS5 proxies in seconds.\n\n"
        "📌 *Choose an option:*"
    )
    return msg


def account_created_message(email: str, password: str, token: str, proxy_count: int) -> str:
    """Message shown after successful account creation."""
    return (
        f"✅ *Account Created!*\n\n"
        f"📧 `{email}`\n"
        f"🔑 `{password}`\n"
        f"🔐 `{token[:20]}...`\n"
        f"🪪 {proxy_count} proxies fetched\n"
    )


def proxy_list_message(proxies: list[str], email: str = None) -> str:
    """Formatted proxy list output."""
    text = f"✅ *Got {len(proxies)} Proxies*\n\n"
    if email:
        text += f"📧 `{email}`\n\n"
    for p in proxies:
        text += f"`{p}`\n"
    return text


def error_message(text: str) -> str:
    """Error message template."""
    return f"❌ {text}"


def rate_limit_message(reason: str) -> str:
    """Rate limit message."""
    return f"⏳ *Rate Limited*\n\n{reason}"


def banned_message() -> str:
    """Banned user message."""
    return "🚫 *Access Denied*\n\nYou have been banned from using this bot."


def admin_stats_message(stats: dict) -> str:
    """Admin statistics display."""
    proxy_mode = "🟢 ON" if stats.get("proxy_mode", True) else "🔴 OFF"
    return (
        f"📊 *Bot Statistics*\n\n"
        f"👥 Total Users: *{stats['total_users']}*\n"
        f"📝 Today's Registrations: *{stats['today_registrations']}*\n"
        f"🪪 Total Proxies: *{stats['total_proxies']}*\n"
        f"💚 Alive Proxies: *{stats.get('alive_proxies', 0)}*\n"
        f"🎛 Proxy Mode: *{proxy_mode}*\n"
    )


def user_detail_message(user: dict, registrations: list[dict]) -> str:
    """User detail for admin."""
    username = user.get("username") or "N/A"
    first = user.get("first_name") or "N/A"
    banned = "Yes 🚫" if user.get("is_banned") else "No"
    admin = "Yes ⭐" if user.get("is_admin") else "No"

    msg = (
        f"👤 *User #{user['user_id']}*\n\n"
        f"Name: {first}\n"
        f"Username: @{username}\n"
        f"Banned: {banned}\n"
        f"Admin: {admin}\n\n"
        f"📝 *Recent Registrations:*\n"
    )
    if registrations:
        for r in registrations[:5]:
            msg += f"• `{r['email']}`\n"
    else:
        msg += "• None\n"
    return msg