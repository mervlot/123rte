import os
from dotenv import load_dotenv

# Load .env file
load_dotenv()

# Access variables
BOT_TOKEN = os.getenv("TELEGRAM_TOKEN")
import json
from datetime import datetime
import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

from mervscrape import (
    StockScraper,
    CryptoScraper,
    ForexScraper,
    NewsScraper,
    CommodityScraper,
    COMMODITY_SYMBOLS,
)

# ── Config ────────────────────────────────────────────────────────────────────
bot = telebot.TeleBot(BOT_TOKEN)

# ── Scrapers ──────────────────────────────────────────────────────────────────
stock = StockScraper()
crypto = CryptoScraper()
forex = ForexScraper()
news = NewsScraper()
commodity = CommodityScraper()

# ── State tracking (user_id → awaiting action) ────────────────────────────────
user_state: dict[int, str] = {}

# ── User tracking ─────────────────────────────────────────────────────────────
USER_FILE = "users.json"


def load_users():
    if not os.path.exists(USER_FILE):
        return {}
    try:
        with open(USER_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError):
        return {}


def save_users(data):
    with open(USER_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)


users_db = load_users()


def track_user(user):
    uid = str(user.id)
    now = datetime.now().isoformat(timespec="seconds")

    if uid not in users_db:
        users_db[uid] = {
            "id": user.id,
            "username": user.username,
            "first_name": user.first_name,
            "last_name": user.last_name,
            "is_bot": user.is_bot,
            "language_code": getattr(user, "language_code", None),
            "joined_at": now,
            "last_seen": now,
            "requests": 1,
        }
        print(f"[NEW USER] {user.first_name} (@{user.username}) | ID: {user.id}")
    else:
        users_db[uid]["username"] = user.username
        users_db[uid]["first_name"] = user.first_name
        users_db[uid]["last_name"] = user.last_name
        users_db[uid]["is_bot"] = user.is_bot
        users_db[uid]["language_code"] = getattr(user, "language_code", None)
        users_db[uid]["last_seen"] = now
        users_db[uid]["requests"] = int(users_db[uid].get("requests", 0)) + 1
        print(f"[RETURNING] {user.first_name} (@{user.username}) | ID: {user.id}")

    save_users(users_db)


# ── Keyboards ─────────────────────────────────────────────────────────────────
def main_menu_kb():
    kb = InlineKeyboardMarkup(row_width=2)
    kb.add(
        InlineKeyboardButton("📊 Stocks", callback_data="menu_stock"),
        InlineKeyboardButton("💰 Crypto", callback_data="menu_crypto"),
        InlineKeyboardButton("💱 Forex", callback_data="menu_forex"),
        InlineKeyboardButton("📰 News", callback_data="menu_news"),
        InlineKeyboardButton("🪙 Commodities", callback_data="menu_commodities"),
    )
    return kb


def back_kb():
    kb = InlineKeyboardMarkup()
    kb.add(InlineKeyboardButton("🏠 Main Menu", callback_data="menu_main"))
    return kb


def crypto_mode_kb():
    kb = InlineKeyboardMarkup(row_width=2)
    kb.add(
        InlineKeyboardButton("🔍 Search coin", callback_data="crypto_search"),
        InlineKeyboardButton("🏆 Top coins", callback_data="crypto_top"),
        InlineKeyboardButton("🏠 Main Menu", callback_data="menu_main"),
    )
    return kb


def commodity_kb():
    kb = InlineKeyboardMarkup(row_width=3)
    labels = {
        "gold": "🥇 Gold",
        "silver": "🥈 Silver",
        "oil_wti": "🛢 Oil WTI",
        "oil_brent": "🛢 Oil Brent",
        "natural_gas": "🔥 Nat. Gas",
        "copper": "🟤 Copper",
        "wheat": "🌾 Wheat",
        "corn": "🌽 Corn",
        "platinum": "💿 Platinum",
    }
    buttons = [
        InlineKeyboardButton(label, callback_data=f"commodity_{key}")
        for key, label in labels.items()
    ]
    kb.add(*buttons)
    kb.add(InlineKeyboardButton("🏠 Main Menu", callback_data="menu_main"))
    return kb


# ── Formatters ─────────────────────────────────────────────────────────────────
def fmt_stock(d: dict) -> str:
    arrow = "▲" if d["change"] >= 0 else "▼"
    return (
        f"📊 *{d['symbol']} — Stock*\n"
        f"━━━━━━━━━━━━━━━━━━\n"
        f"📅 Date    : `{d['date']}`\n"
        f"🔓 Open    : `${d['open']:.2f}`\n"
        f"📈 High    : `${d['high']:.2f}`\n"
        f"📉 Low     : `${d['low']:.2f}`\n"
        f"🔒 Close   : `${d['close']:.2f}`\n"
        f"{'🟢' if d['change'] >= 0 else '🔴'} Change   : `{arrow} {abs(d['change']):.2f} ({abs(d['change_pct']):.2f}%)`\n"
        f"📦 Volume  : `{d['volume']:,}`"
    )


def fmt_coin(d: dict) -> str:
    arrow = "▲" if d["change_24h"] >= 0 else "▼"
    price = f"{d['price']:,.6f}" if d["price"] < 1 else f"{d['price']:,.2f}"
    return (
        f"💰 *{d['name']} ({d['symbol']})* —  #{d['rank']}\n"
        f"━━━━━━━━━━━━━━━━━━\n"
        f"💵 Price      : `${price}`\n"
        f"{'🟢' if d['change_24h'] >= 0 else '🔴'} 24h Change : `{arrow} {abs(d['change_24h']):.2f}%`\n"
        f"🏦 Market Cap : `${d['market_cap']:,.0f}`\n"
        f"📊 Volume     : `${d['volume_24h']:,.0f}`\n"
        f"📈 24h High   : `${d['high_24h']:,.2f}`\n"
        f"📉 24h Low    : `${d['low_24h']:,.2f}`"
    )


def fmt_forex(d: dict) -> str:
    if "target" in d:
        return (
            f"💱 *Forex Rate*\n"
            f"━━━━━━━━━━━━━━━━━━\n"
            f"📅 Date : `{d['date']}`\n"
            f"1 {d['base']} = `{d['rate']:.4f} {d['target']}`"
        )
    top = ["USD", "EUR", "GBP", "JPY", "NGN", "CAD", "AUD", "CHF", "CNY", "INR"]
    lines = [f"💱 *{d['base']} Rates* —  📅 `{d['date']}`\n━━━━━━━━━━━━━━━━━━"]
    for cur in top:
        if cur in d["rates"]:
            lines.append(f"`1 {d['base']} = {d['rates'][cur]:.4f} {cur}`")
    return "\n".join(lines)


def fmt_news(articles: list) -> str:
    if not articles:
        return "❌ No articles found."
    lines = []
    for i, a in enumerate(articles, 1):
        lines.append(
            f"*{i}. {a['title']}*\n"
            f"🏢 {a['source']}  |  📅 {a['date']}\n"
            f"📝 _{a['snippet']}_\n"
            f"🔗 [Read full article]({a['link']})"
        )
    return "\n\n".join(lines)


def fmt_commodity(d: dict) -> str:
    arrow = "▲" if d["change"] >= 0 else "▼"
    return (
        f"🪙 *{d['symbol']} — Commodity*\n"
        f"━━━━━━━━━━━━━━━━━━\n"
        f"📅 Date    : `{d['date']}`\n"
        f"🔓 Open    : `{d['open']:.4f}`\n"
        f"📈 High    : `{d['high']:.4f}`\n"
        f"📉 Low     : `{d['low']:.4f}`\n"
        f"🔒 Close   : `{d['close']:.4f}`\n"
        f"{'🟢' if d['change'] >= 0 else '🔴'} Change   : `{arrow} {abs(d['change']):.4f} ({abs(d['change_pct']):.2f}%)`"
    )


# ── /start & /menu ─────────────────────────────────────────────────────────────
@bot.message_handler(commands=["start", "menu"])
def cmd_start(msg):
    track_user(msg.from_user)
    user_state.pop(msg.from_user.id, None)
    bot.send_message(
        msg.chat.id,
        "👋 *Welcome to MervX Bot!*\n\nWhat do you want to scrape?",
        parse_mode="Markdown",
        reply_markup=main_menu_kb(),
    )


# ── Direct commands ────────────────────────────────────────────────────────────
@bot.message_handler(commands=["stock"])
def cmd_stock(msg):
    user_state[msg.from_user.id] = "await_stock"
    bot.send_message(
        msg.chat.id,
        "📊 Enter stock symbol (e.g. `AAPL`, `TSLA`):",
        parse_mode="Markdown",
    )


@bot.message_handler(commands=["crypto"])
def cmd_crypto(msg):
    bot.send_message(
        msg.chat.id,
        "💰 *Crypto* — Choose mode:",
        parse_mode="Markdown",
        reply_markup=crypto_mode_kb(),
    )


@bot.message_handler(commands=["forex"])
def cmd_forex(msg):
    user_state[msg.from_user.id] = "await_forex_base"
    bot.send_message(
        msg.chat.id,
        "💱 Enter base currency (e.g. `USD`, `EUR`, `NGN`):",
        parse_mode="Markdown",
    )


@bot.message_handler(commands=["news"])
def cmd_news(msg):
    user_state[msg.from_user.id] = "await_news"
    bot.send_message(
        msg.chat.id,
        "📰 Enter a news topic (e.g. `bitcoin`, `AI`, `nigeria`):",
        parse_mode="Markdown",
    )


@bot.message_handler(commands=["commodities"])
def cmd_commodities(msg):
    bot.send_message(msg.chat.id, "🪙 Pick a commodity:", reply_markup=commodity_kb())


# ── Callback queries (inline buttons) ─────────────────────────────────────────
@bot.callback_query_handler(func=lambda c: True)
def handle_callback(call):
    track_user(call.from_user)
    uid = call.from_user.id
    cid = call.message.chat.id
    data = call.data
    bot.answer_callback_query(call.id)

    # Main menu
    if data == "menu_main":
        user_state.pop(uid, None)
        bot.send_message(
            cid,
            "🏠 *Main Menu* — What do you want to scrape?",
            parse_mode="Markdown",
            reply_markup=main_menu_kb(),
        )

    elif data == "menu_stock":
        user_state[uid] = "await_stock"
        bot.send_message(
            cid, "📊 Enter stock symbol (e.g. `AAPL`, `TSLA`):", parse_mode="Markdown"
        )

    elif data == "menu_crypto":
        bot.send_message(
            cid,
            "💰 *Crypto* — Choose mode:",
            parse_mode="Markdown",
            reply_markup=crypto_mode_kb(),
        )

    elif data == "crypto_search":
        user_state[uid] = "await_crypto_search"
        bot.send_message(
            cid,
            "🔍 Enter coin id (e.g. `bitcoin`, `solana`, `ethereum`):",
            parse_mode="Markdown",
        )

    elif data == "crypto_top":
        user_state[uid] = "await_crypto_top"
        bot.send_message(
            cid, "🏆 How many top coins? (e.g. `10`):", parse_mode="Markdown"
        )

    elif data == "menu_forex":
        user_state[uid] = "await_forex_base"
        bot.send_message(
            cid,
            "💱 Enter base currency (e.g. `USD`, `EUR`, `NGN`):",
            parse_mode="Markdown",
        )

    elif data == "menu_news":
        user_state[uid] = "await_news"
        bot.send_message(
            cid,
            "📰 Enter a news topic (e.g. `bitcoin`, `AI`, `nigeria`):",
            parse_mode="Markdown",
        )

    elif data == "menu_commodities":
        bot.send_message(cid, "🪙 Pick a commodity:", reply_markup=commodity_kb())

    elif data.startswith("commodity_"):
        key = data.replace("commodity_", "")
        try:
            result = commodity.get(key)
            bot.send_message(
                cid,
                fmt_commodity(result),
                parse_mode="Markdown",
                reply_markup=back_kb(),
            )
        except Exception as e:
            bot.send_message(cid, f"❌ {e}", reply_markup=back_kb())

    elif data.startswith("forex_skip_target_"):
        base = data.replace("forex_skip_target_", "")
        try:
            result = forex.get(base)
            bot.send_message(
                cid, fmt_forex(result), parse_mode="Markdown", reply_markup=back_kb()
            )
        except Exception as e:
            bot.send_message(cid, f"❌ {e}", reply_markup=back_kb())


# ── Text message handler (state machine) ──────────────────────────────────────
@bot.message_handler(func=lambda m: True)
def handle_text(msg):
    track_user(msg.from_user)
    uid = msg.from_user.id
    cid = msg.chat.id
    text = msg.text.strip()
    state = user_state.get(uid)

    if not state:
        bot.send_message(
            cid, "Use /menu or /start to begin.", reply_markup=main_menu_kb()
        )
        return

    # ── Stock ──
    if state == "await_stock":
        user_state.pop(uid)
        bot.send_chat_action(cid, "typing")
        try:
            result = stock.get(text)
            bot.send_message(
                cid, fmt_stock(result), parse_mode="Markdown", reply_markup=back_kb()
            )
        except Exception as e:
            bot.send_message(cid, f"❌ {e}", reply_markup=back_kb())

    # ── Crypto search ──
    elif state == "await_crypto_search":
        user_state.pop(uid)
        bot.send_chat_action(cid, "typing")
        try:
            result = crypto.get(text.lower())
            bot.send_message(
                cid, fmt_coin(result), parse_mode="Markdown", reply_markup=back_kb()
            )
        except Exception as e:
            bot.send_message(cid, f"❌ {e}", reply_markup=back_kb())

    # ── Crypto top N ──
    elif state == "await_crypto_top":
        user_state.pop(uid)
        bot.send_chat_action(cid, "typing")
        try:
            n = int(text) if text.isdigit() else 10
            coins = crypto.top(min(n, 20))
            for coin in coins:
                bot.send_message(cid, fmt_coin(coin), parse_mode="Markdown")
            bot.send_message(cid, "✅ Done.", reply_markup=back_kb())
        except Exception as e:
            bot.send_message(cid, f"❌ {e}", reply_markup=back_kb())

    # ── Forex base ──
    elif state == "await_forex_base":
        user_state[uid] = f"await_forex_target_{text.upper()}"
        kb = InlineKeyboardMarkup()
        kb.add(
            InlineKeyboardButton(
                "⏭ Skip — show all pairs",
                callback_data=f"forex_skip_target_{text.upper()}",
            )
        )
        bot.send_message(
            cid,
            f"💱 Base: `{text.upper()}`\nEnter target currency (e.g. `NGN`) or skip to see all pairs:",
            parse_mode="Markdown",
            reply_markup=kb,
        )

    # ── Forex target ──
    elif state and state.startswith("await_forex_target_"):
        base = state.replace("await_forex_target_", "")
        user_state.pop(uid)
        bot.send_chat_action(cid, "typing")
        try:
            result = forex.get(base, text.upper())
            bot.send_message(
                cid, fmt_forex(result), parse_mode="Markdown", reply_markup=back_kb()
            )
        except KeyError:
            # Target not found, show all
            try:
                result = forex.get(base)
                bot.send_message(
                    cid,
                    f"⚠️ `{text.upper()}` not available. Showing all pairs:\n\n{fmt_forex(result)}",
                    parse_mode="Markdown",
                    reply_markup=back_kb(),
                )
            except Exception as e:
                bot.send_message(cid, f"❌ {e}", reply_markup=back_kb())
        except Exception as e:
            bot.send_message(cid, f"❌ {e}", reply_markup=back_kb())

    # ── News ──
    elif state == "await_news":
        user_state.pop(uid)
        bot.send_chat_action(cid, "typing")
        try:
            articles = news.get(text, limit=5)
            bot.send_message(
                cid,
                fmt_news(articles),
                parse_mode="Markdown",
                disable_web_page_preview=True,
                reply_markup=back_kb(),
            )
        except Exception as e:
            bot.send_message(cid, f"❌ {e}", reply_markup=back_kb())


# ── Run ───────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    print("🤖 MervX Bot running...")
    bot.infinity_polling()
