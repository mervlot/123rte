import requests
import xml.etree.ElementTree as ET
import re


# ─── STOCK ────────────────────────────────────────────────────────────────────
def scrape_stock():
    symbol = input("  Enter stock symbol (e.g AAPL, TSLA, NVDA): ").strip().upper()
    url = f"https://stooq.com/q/l/?s={symbol}.us&f=sd2t2ohlcv&h&e=csv"
    res = requests.get(url, timeout=10)
    rows = res.text.strip().split("\n")

    if len(rows) < 2:
        print("  ❌ No data returned.")
        return

    data = rows[1].split(",")
    if not data or data[0] == "N/D" or data[1] == "N/D":
        print("  ❌ Invalid symbol or no data found.")
        return

    try:
        open_p  = float(data[3])
        high_p  = float(data[4])
        low_p   = float(data[5])
        close_p = float(data[6])
        volume  = int(float(data[7]))
        change     = close_p - open_p
        change_pct = (change / open_p) * 100
        arrow = "▲" if change >= 0 else "▼"

        print(f"\n  {'='*44}")
        print(f"  📊  {symbol} — Stock Data")
        print(f"  {'='*44}")
        print(f"  Date      : {data[1]}")
        print(f"  Open      : ${open_p:>10.2f}")
        print(f"  High      : ${high_p:>10.2f}")
        print(f"  Low       : ${low_p:>10.2f}")
        print(f"  Close     : ${close_p:>10.2f}")
        print(f"  Change    : {arrow} {abs(change):.2f}  ({abs(change_pct):.2f}%)")
        print(f"  Volume    : {volume:>14,}")
        print(f"  {'='*44}\n")
    except (ValueError, IndexError):
        print("  ❌ Error parsing data.")


# ─── CRYPTO ───────────────────────────────────────────────────────────────────
def scrape_crypto():
    print("\n  [1] Search by coin  [2] Top coins by market cap")
    choice = input("  Choice: ").strip()

    if choice == "1":
        query = input("  Coin name/id (e.g bitcoin, solana): ").strip().lower()
        url = (
            f"https://api.coingecko.com/api/v3/coins/markets"
            f"?vs_currency=usd&ids={query}&order=market_cap_desc"
        )
        coins = requests.get(url, timeout=10).json()
        if not coins:
            print("  ❌ Coin not found.")
            return
    else:
        n_raw = input("  How many top coins? (default 10): ").strip()
        n = int(n_raw) if n_raw.isdigit() else 10
        url = (
            f"https://api.coingecko.com/api/v3/coins/markets"
            f"?vs_currency=usd&order=market_cap_desc&per_page={n}&page=1"
        )
        coins = requests.get(url, timeout=10).json()

    print(f"\n  {'='*54}")
    print(f"  💰  Crypto Market Data (USD)")
    print(f"  {'='*54}")

    for coin in coins:
        change = coin.get("price_change_percentage_24h") or 0
        arrow  = "▲" if change >= 0 else "▼"
        price  = coin["current_price"]
        fmt    = f"{price:,.6f}" if price < 1 else f"{price:,.2f}"

        print(f"  #{coin['market_cap_rank']}  {coin['name']} ({coin['symbol'].upper()})")
        print(f"  Price      : ${fmt}")
        print(f"  24h Change : {arrow} {abs(change):.2f}%")
        print(f"  Market Cap : ${coin['market_cap']:>18,.0f}")
        print(f"  24h High   : ${coin['high_24h']:,.2f}   Low: ${coin['low_24h']:,.2f}")
        print(f"  Volume     : ${coin['total_volume']:>18,.0f}")
        print(f"  {'-'*52}")
    print()


# ─── FOREX ────────────────────────────────────────────────────────────────────
TOP_PAIRS = ["USD", "EUR", "GBP", "JPY", "NGN", "CAD", "AUD", "CHF", "CNY", "INR"]

def scrape_forex():
    base   = input("  Base currency (e.g USD, EUR, GBP): ").strip().upper()
    target = input("  Target currency (leave blank for top pairs): ").strip().upper()

    url = f"https://api.frankfurter.app/latest?from={base}"
    res = requests.get(url, timeout=10)

    if res.status_code != 200:
        print("  ❌ Invalid currency or API error.")
        return

    data  = res.json()
    rates = data.get("rates", {})
    date  = data.get("date", "N/A")

    print(f"\n  {'='*44}")
    print(f"  💱  {base} Forex Rates  ({date})")
    print(f"  {'='*44}")

    if target and target != base:
        if target in rates:
            print(f"  1 {base} = {rates[target]:.4f} {target}")
        else:
            print(f"  ⚠️  {target} not available (API doesn't include all currencies).")
            print(f"  Showing top pairs instead:\n")
            for cur in TOP_PAIRS:
                if cur in rates:
                    print(f"  1 {base} = {rates[cur]:>12.4f}  {cur}")
    else:
        for cur in TOP_PAIRS:
            if cur in rates:
                print(f"  1 {base} = {rates[cur]:>12.4f}  {cur}")

    print(f"  {'='*44}\n")


# ─── NEWS ─────────────────────────────────────────────────────────────────────
def scrape_news():
    query = input("  News topic (e.g bitcoin, AI, nigeria, tech): ").strip()
    n_raw = input("  How many articles? (default 5): ").strip()
    n     = int(n_raw) if n_raw.isdigit() else 5

    rss_url = (
        f"https://news.google.com/rss/search"
        f"?q={query.replace(' ', '+')}&hl=en-US&gl=US&ceid=US:en"
    )
    res  = requests.get(rss_url, timeout=10, headers={"User-Agent": "Mozilla/5.0"})
    root = ET.fromstring(res.content)
    items = root.findall(".//item")

    if not items:
        print("  ❌ No articles found.")
        return

    count = min(n, len(items))
    print(f"\n  {'='*60}")
    print(f"  📰  News: \"{query}\"  —  {count} result(s)")
    print(f"  {'='*60}")

    for i, item in enumerate(items[:n], 1):
        title    = item.findtext("title",       "No title")
        link     = item.findtext("link",        "No link")
        pub_date = item.findtext("pubDate",     "")
        desc_raw = item.findtext("description", "")
        source   = item.findtext("source",      "Unknown")

        # Strip HTML tags from description
        clean = re.sub(r"<[^>]+>", "", desc_raw).strip()
        # Google News descriptions sometimes repeat the title — trim those
        clean = re.sub(r"^.{0,120}\s{2,}", "", clean).strip()
        snippet = (clean[:220] + "…") if len(clean) > 220 else clean

        print(f"\n  [{i}] {title}")
        print(f"       🏢 {source}   📅 {pub_date}")
        if snippet:
            print(f"       📝 {snippet}")
        print(f"       🔗 {link}")
        print(f"  {'-'*58}")

    print()


# ─── COMMODITIES ──────────────────────────────────────────────────────────────
COMMODITIES = {
    "1": ("Gold",           "xauusd"),
    "2": ("Silver",         "xagusd"),
    "3": ("Oil — WTI",      "cl.f"),
    "4": ("Oil — Brent",    "lcousd"),
    "5": ("Natural Gas",    "ng.f"),
    "6": ("Copper",         "hg.f"),
    "7": ("Wheat",          "w.f"),
    "8": ("Corn",           "c.f"),
    "9": ("Platinum",       "xptusd"),
}

def scrape_commodities():
    print("\n  Available commodities:")
    for k, (name, _) in COMMODITIES.items():
        print(f"  [{k}] {name}")
    print("  [0] Custom stooq symbol")

    choice = input("\n  Choice: ").strip()

    if choice == "0":
        symbol = input("  Enter stooq symbol: ").strip().lower()
        label  = symbol.upper()
    elif choice in COMMODITIES:
        label, symbol = COMMODITIES[choice]
    else:
        print("  ❌ Invalid choice.")
        return

    url  = f"https://stooq.com/q/l/?s={symbol}&f=sd2t2ohlcv&h&e=csv"
    res  = requests.get(url, timeout=10)
    rows = res.text.strip().split("\n")

    if len(rows) < 2:
        print("  ❌ No data.")
        return

    data = rows[1].split(",")
    if not data or data[1] == "N/D":
        print("  ❌ No data found for this commodity.")
        return

    try:
        open_p  = float(data[3])
        high_p  = float(data[4])
        low_p   = float(data[5])
        close_p = float(data[6])
        change     = close_p - open_p
        change_pct = (change / open_p) * 100
        arrow = "▲" if change >= 0 else "▼"

        print(f"\n  {'='*44}")
        print(f"  🪙  {label} — Commodity Data")
        print(f"  {'='*44}")
        print(f"  Date   : {data[1]}")
        print(f"  Open   : {open_p:>12.4f}")
        print(f"  High   : {high_p:>12.4f}")
        print(f"  Low    : {low_p:>12.4f}")
        print(f"  Close  : {close_p:>12.4f}")
        print(f"  Change : {arrow} {abs(change):.4f}  ({abs(change_pct):.2f}%)")
        print(f"  {'='*44}\n")
    except (ValueError, IndexError):
        print("  ❌ Error parsing data.")


# ─── MAIN MENU ────────────────────────────────────────────────────────────────
MENU = {
    "1": ("📊 Stocks",       scrape_stock),
    "2": ("💰 Crypto",       scrape_crypto),
    "3": ("💱 Forex",        scrape_forex),
    "4": ("📰 News",         scrape_news),
    "5": ("🪙 Commodities",  scrape_commodities),
}

def main():
    print("\n" + "  " + "="*42)
    print("    🌐  MervScrape — Market & News CLI")
    print("  " + "="*42)

    while True:
        print("\n  What do you want to scrape?\n")
        for k, (label, _) in MENU.items():
            print(f"  [{k}] {label}")
        print("  [0] Exit\n")

        choice = input("  → ").strip()

        if choice == "0":
            print("\n  👋 Bye!\n")
            break
        elif choice in MENU:
            try:
                MENU[choice][1]()
            except requests.exceptions.ConnectionError:
                print("  ❌ Connection error. Check your internet.")
            except requests.exceptions.Timeout:
                print("  ❌ Request timed out.")
            except Exception as e:
                print(f"  ❌ Error: {e}")
        else:
            print("  ⚠️  Invalid choice, try again.")


if __name__ == "__main__":
    main()
