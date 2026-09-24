# 🔐 PelerProxy Bot

<p align="center">
  <strong>Telegram bot for creating Webshare proxy accounts — automated captcha solving, proxy pool, and admin panel.</strong>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/python-3.11+-blue.svg" alt="Python 3.11+">
  <img src="https://img.shields.io/badge/telegram-bot-blue.svg" alt="Telegram Bot">
  <img src="https://img.shields.io/badge/license-MIT-green.svg" alt="License MIT">
</p>

---

## ✨ Features

- **🚀 One-click account creation** — auto generates email, solves captcha, registers on Webshare
- **🧩 Multi-provider captcha** — AZCaptcha & 2Captcha support, switchable via admin panel
- **🎛 Proxy pool** — admin-created proxies used for routing registrations, with health checking
- **🛡️ Admin panel** — stats, user management, broadcast, ban/unban, proxy settings
- **⏱ Rate limiting** — 1 registration per user per day (admin unlimited)
- **📋 Proxy fetching** — retrieve saved proxies from your accounts anytime
- **💾 SQLite** — zero-dependency local storage with WAL mode

## 🏗 Architecture

```
config.toml          → credentials & settings (gitignored)
config.py            → loads config.toml into constants
database.py          → SQLite layer (users, registrations, proxies, settings)
bot.py               → entry point, registers handlers
handlers/
  start.py           → /start, main menu dispatcher
  register.py        → auto + manual registration flows
  admin.py           → admin panel (stats, broadcast, users, proxy, captcha)
  proxies.py         → fetch proxies from saved accounts
services/
  scraper.py         → cloudscraper wrapper with proxy support
  captcha.py         → multi-provider captcha solver
  webshare.py        → Webshare API (register + fetch proxies)
  email_gen.py       → nullz email generation
  proxy_checker.py   → proxy health checking + pool management
ui/
  keyboards.py       → all inline keyboard builders
  messages.py        → message templates
utils/
  rate_limit.py      → daily rate limit checker
  validators.py      → email/password validation
```

## 🚀 Quick Start

### Running Locally

```bash
# 1. Clone
git clone https://github.com/hirotomasato/pelerproxy.git
cd pelerproxy

# 2. Virtual environment
python -m venv venv
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows

# 3. Install dependencies
pip install -r requirements.txt

# 4. Configure
cp config.example.toml config.toml
# Edit config.toml with your bot token and admin IDs

# 5. Run
python bot.py
```

### 🐳 Running with Docker

You can configure the bot using environment variables or a `config.toml` file.

**Option A: Using Environment Variables**

```bash
docker run -d \
  --name pelerproxy-bot \
  -e BOT_TOKEN="your_bot_token" \
  -e ADMIN_IDS="123456789" \
  -e TWOCAPTCHA_API_KEY="your_api_key" \
  -v $(pwd)/data:/app/data \
  pelerproxy
```

Or using Docker Compose with an `.env` file or environment variables:

```bash
BOT_TOKEN="your_token" ADMIN_IDS="123456789" docker compose up -d
```

**Option B: Using `config.toml`**

```bash
# 1. Prepare configuration
cp config.example.toml config.toml
# Edit config.toml with your bot token and admin IDs

# 2. Run with Docker Compose
docker compose up -d
```

## ⚙️ Configuration

Settings can be set via Environment Variables or in `config.toml` (environment variables take precedence):

| Environment Variable | TOML `[section] key` | Description | Default |
|----------------------|----------------------|-------------|---------|
| `BOT_TOKEN` | `[bot] token` | Telegram bot token from [@BotFather](https://t.me/botfather) | *Required* |
| `ADMIN_IDS` | `[admin] ids` | Comma-separated admin Telegram IDs (e.g. `123,456`) | `[]` |
| `AZCAPTCHA_API_KEY` | `[captcha.azcaptcha] api_key` | AZCaptcha API key | `""` |
| `TWOCAPTCHA_API_KEY` | `[captcha.2captcha] api_key` | 2Captcha API key | `""` |
| `CAPTCHA_DEFAULT_PROVIDER` | `[captcha] default_provider` | Default captcha provider (`azcaptcha` / `2captcha`) | `"2captcha"` |
| `MAX_REGISTRATIONS_PER_DAY` | `[limits] max_registrations_per_day` | Daily limit per user | `1` |

## 🤖 Commands

### User
| Command | Description |
|---------|-------------|
| `/start` | Show main menu |
| `🚀 Create Account (Auto)` | Auto-generate email, solve captcha, register |
| `✍️ Register with Your Email` | Manual registration with your own email |
| `📋 Get My Proxies` | Fetch proxies from your last account |

### Admin
| Command | Description |
|---------|-------------|
| `🛡️ Admin Panel` | Access admin dashboard |
| `📊 Statistics` | View user/proxy stats |
| `🧩 Captcha Settings` | Switch provider, set API key |
| `🎛 Proxy Settings` | Toggle proxy mode, check/clean pool |
| `👥 List Users` | Paginated user list with details |
| `📢 Broadcast` | Send message to all users |
| `🔨 Ban / Unban` | Manage user bans |
| `🔄 Reset Limit` | Reset daily limit for a user |

## 📄 License

MIT — see [LICENSE](LICENSE) for details.