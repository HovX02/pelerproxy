"""
PelerProxy Bot — Inline Keyboards
All keyboard builders return InlineKeyboardMarkup objects.
"""
from telegram import InlineKeyboardButton, InlineKeyboardMarkup


def main_menu(is_admin: bool = False) -> InlineKeyboardMarkup:
    """Main menu with all registration options."""
    keyboard = [
        [InlineKeyboardButton("🚀 Create Account (Auto)", callback_data="auto")],
        [InlineKeyboardButton("✍️ Register with Your Email", callback_data="manual")],
        [InlineKeyboardButton("📋 Get My Proxies", callback_data="proxies")],
    ]
    if is_admin:
        keyboard.append([InlineKeyboardButton("🛡️ Admin Panel", callback_data="admin")])
    return InlineKeyboardMarkup(keyboard)


def admin_menu() -> InlineKeyboardMarkup:
    """Admin panel menu."""
    keyboard = [
        [InlineKeyboardButton("📊 Statistics", callback_data="admin_stats")],
        [InlineKeyboardButton("🧩 Captcha Settings", callback_data="admin_captcha_menu")],
        [InlineKeyboardButton("🎛 Proxy Settings", callback_data="admin_proxy_menu")],
        [InlineKeyboardButton("👥 List Users", callback_data="admin_users")],
        [InlineKeyboardButton("📢 Broadcast", callback_data="admin_broadcast")],
        [InlineKeyboardButton("🔨 Ban / Unban User", callback_data="admin_ban_menu")],
        [InlineKeyboardButton("🔄 Reset User Limit", callback_data="admin_reset")],
        [InlineKeyboardButton("« Back to Menu", callback_data="start")],
    ]
    return InlineKeyboardMarkup(keyboard)


def admin_proxy_menu(proxy_mode: bool, stats: dict) -> InlineKeyboardMarkup:
    """Proxy settings sub-menu."""
    status = "🟢 ON" if proxy_mode else "🔴 OFF"
    keyboard = [
        [InlineKeyboardButton(f"⏺ Proxy Mode: {status}", callback_data="admin_proxy_toggle")],
        [InlineKeyboardButton(f"🔍 Check All Proxies", callback_data="admin_proxy_check")],
        [InlineKeyboardButton(f"🗑 Delete Dead Proxies", callback_data="admin_proxy_prune")],
        [InlineKeyboardButton("« Admin Menu", callback_data="admin")],
    ]
    return InlineKeyboardMarkup(keyboard)


def admin_captcha_menu(info: dict) -> InlineKeyboardMarkup:
    """Captcha settings sub-menu."""
    provider_name = info["name"]
    key_masked = info.get("api_key_masked", "not set")

    keyboard = [
        [InlineKeyboardButton(f"🔑 Provider: {provider_name} ✅", callback_data="admin_captcha_switch")],
        [InlineKeyboardButton(f"🔐 API Key: {key_masked}", callback_data="admin_captcha_key")],
        [InlineKeyboardButton("« Admin Menu", callback_data="admin")],
    ]
    return InlineKeyboardMarkup(keyboard)


def back_to_menu() -> InlineKeyboardMarkup:
    """Simple back button."""
    keyboard = [[InlineKeyboardButton("« Back to Menu", callback_data="start")]]
    return InlineKeyboardMarkup(keyboard)


def admin_user_pagination(users: list[dict], page: int, total_pages: int) -> InlineKeyboardMarkup:
    """Paginated user list for admin."""
    keyboard = []
    for u in users:
        uid = u["user_id"]
        name = u.get("first_name") or u.get("username") or f"ID:{uid}"
        status = ""
        if u.get("is_banned"):
            status = " 🚫"
        elif u.get("is_admin"):
            status = " ⭐"
        keyboard.append([InlineKeyboardButton(f"👤 {name}{status}", callback_data=f"admin_user_{uid}")])

    nav = []
    if page > 0:
        nav.append(InlineKeyboardButton("◀️ Prev", callback_data=f"admin_users_p{page - 1}"))
    if page < total_pages - 1:
        nav.append(InlineKeyboardButton("Next ▶️", callback_data=f"admin_users_p{page + 1}"))
    if nav:
        keyboard.append(nav)

    keyboard.append([InlineKeyboardButton("« Admin Menu", callback_data="admin")])
    return InlineKeyboardMarkup(keyboard)


def admin_user_detail(user_id: int) -> InlineKeyboardMarkup:
    """Actions for a specific user."""
    keyboard = [
        [InlineKeyboardButton("🔨 Ban User", callback_data=f"admin_ban_{user_id}")],
        [InlineKeyboardButton("✅ Unban User", callback_data=f"admin_unban_{user_id}")],
        [InlineKeyboardButton("🔄 Reset Today's Limit", callback_data=f"admin_reset_{user_id}")],
        [InlineKeyboardButton("« Admin Menu", callback_data="admin")],
    ]
    return InlineKeyboardMarkup(keyboard)


def confirm_cancel(action: str) -> InlineKeyboardMarkup:
    """Yes/No confirmation."""
    keyboard = [
        [
            InlineKeyboardButton("✅ Yes", callback_data=action),
            InlineKeyboardButton("❌ No", callback_data="start"),
        ]
    ]
    return InlineKeyboardMarkup(keyboard)


def after_register() -> InlineKeyboardMarkup:
    """Shown after a successful registration."""
    keyboard = [
        [InlineKeyboardButton("📋 Get My Proxies", callback_data="proxies")],
        [InlineKeyboardButton("« Back to Menu", callback_data="start")],
    ]
    return InlineKeyboardMarkup(keyboard)


def proxy_pool_menu() -> InlineKeyboardMarkup:
    """Choose proxy source for registration."""
    keyboard = [
        [InlineKeyboardButton("🎲 Random Proxy from Pool", callback_data="auto_proxy_confirm")],
        [InlineKeyboardButton("📝 Use Specific Proxy", callback_data="auto_proxy_custom")],
        [InlineKeyboardButton("« Back", callback_data="start")],
    ]
    return InlineKeyboardMarkup(keyboard)