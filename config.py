"""
PelerProxy Bot — Configuration
Loads settings from environment variables with fallback to config.toml (if present).
"""
import os
import tomllib
from pathlib import Path

# ==================== PATHS ====================

BASE_DIR = Path(__file__).parent
DATA_DIR = BASE_DIR / "data"
ACCOUNTS_FILE = BASE_DIR / "webshare_accounts.json"
PROXIES_FILE = BASE_DIR / "proxies.txt"
DB_PATH = DATA_DIR / "pelerproxy.db"
CONFIG_FILE = BASE_DIR / "config.toml"

# ==================== LOAD CONFIG ====================

def _load_config() -> dict:
    """Load config.toml if available, otherwise return empty dict."""
    if CONFIG_FILE.exists():
        try:
            return tomllib.loads(CONFIG_FILE.read_text(encoding="utf-8"))
        except Exception:
            return {}
    return {}

_cfg = _load_config()

def _get_env_or_cfg(env_var: str, section: str, key: str, default=None):
    """Retrieve setting from env var, then config.toml, then default."""
    if env_var in os.environ and os.environ[env_var] != "":
        return os.environ[env_var]
    if section in _cfg and key in _cfg[section]:
        return _cfg[section][key]
    return default

# ==================== BOT ====================

BOT_TOKEN = _get_env_or_cfg("BOT_TOKEN", "bot", "token")
if not BOT_TOKEN or BOT_TOKEN == "YOUR_BOT_TOKEN_HERE":
    raise ValueError(
        "BOT_TOKEN is not configured!\n"
        "Please set the BOT_TOKEN environment variable or provide it in config.toml."
    )

# ==================== ADMIN ====================

def _parse_admin_ids() -> list[int]:
    env_admin = os.environ.get("ADMIN_IDS")
    if env_admin:
        try:
            return [int(x.strip()) for x in env_admin.split(",") if x.strip()]
        except ValueError:
            pass
    return _cfg.get("admin", {}).get("ids", [])

ADMIN_IDS: list[int] = _parse_admin_ids()

# ==================== CAPTCHA PROVIDERS ====================

CAPTCHA_DEFAULT_PROVIDER = _get_env_or_cfg("CAPTCHA_DEFAULT_PROVIDER", "captcha", "default_provider", "2captcha")

AZCAPTCHA_KEY = os.environ.get("AZCAPTCHA_API_KEY") or _cfg.get("captcha", {}).get("azcaptcha", {}).get("api_key", "")
TWOCAPTCHA_KEY = os.environ.get("TWOCAPTCHA_API_KEY") or _cfg.get("captcha", {}).get("2captcha", {}).get("api_key", "")

CAPTCHA_PROVIDERS = {
    "azcaptcha": {
        "name": "AZCaptcha",
        "api_url": "https://azcaptcha.com/in.php",
        "result_url": "https://azcaptcha.com/res.php",
        "api_key": AZCAPTCHA_KEY,
    },
    "2captcha": {
        "name": "2Captcha",
        "api_url": "https://2captcha.com/in.php",
        "result_url": "https://2captcha.com/res.php",
        "api_key": TWOCAPTCHA_KEY,
    },
}

# ==================== WEBSHARE ====================

FIXED_PASSWORD = _get_env_or_cfg("WEBSHARE_FIXED_PASSWORD", "webshare", "fixed_password", "Pasardigital#26")
WEBSHARE_RECAPTCHA_SITEKEY = _get_env_or_cfg("WEBSHARE_RECAPTCHA_SITEKEY", "webshare", "recaptcha_sitekey", "6LeHZ6UUAAAAAKat_YS--O2tj_by3gv3r_l03j9d")
WEBSHARE_REGISTER_URL = _get_env_or_cfg("WEBSHARE_REGISTER_URL", "webshare", "register_url", "https://proxy.webshare.io/register")
API_BASE = _get_env_or_cfg("WEBSHARE_API_BASE", "webshare", "api_base", "https://proxy.webshare.io/api/v2")

# ==================== PROXY SETTINGS ====================

def _get_bool(env_var: str, section: str, key: str, default: bool) -> bool:
    val = os.environ.get(env_var)
    if val is not None:
        return val.lower() in ("true", "1", "yes")
    return _cfg.get(section, {}).get(key, default)

def _get_int(env_var: str, section: str, key: str, default: int) -> int:
    val = os.environ.get(env_var)
    if val is not None:
        try:
            return int(val)
        except ValueError:
            pass
    return _cfg.get(section, {}).get(key, default)

PROXY_MODE_DEFAULT = _get_bool("PROXY_MODE_DEFAULT", "proxy", "mode_default", True)
PROXY_CHECK_TIMEOUT = _get_int("PROXY_CHECK_TIMEOUT", "proxy", "check_timeout", 15)
PROXY_CHECK_URL = _get_env_or_cfg("PROXY_CHECK_URL", "proxy", "check_url", "http://httpbin.org/ip")
PROXY_MAX_RETRIES = _get_int("PROXY_MAX_RETRIES", "proxy", "max_retries", 5)

# ==================== LIMITS ====================

MAX_REGISTRATIONS_PER_DAY = _get_int("MAX_REGISTRATIONS_PER_DAY", "limits", "max_registrations_per_day", 1)
MAX_PROXIES_PER_FETCH = _get_int("MAX_PROXIES_PER_FETCH", "limits", "max_proxies_per_fetch", 10)
MAX_ACCOUNTS_KEPT = _get_int("MAX_ACCOUNTS_KEPT", "limits", "max_accounts_kept", 20)
