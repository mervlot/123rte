import requests
import xml.etree.ElementTree as ET
import re


class StockScraper:
    BASE_URL = "https://stooq.com/q/l/?s={symbol}.us&f=sd2t2ohlcv&h&e=csv"

    def get(self, symbol: str) -> dict:
        url = self.BASE_URL.format(symbol=symbol.lower())
        res = requests.get(url, timeout=10)
        rows = res.text.strip().split("\n")

        if len(rows) < 2:
            raise ValueError(f"No data returned for {symbol}")

        data = rows[1].split(",")
        if not data or data[0] == "N/D" or data[1] == "N/D":
            raise ValueError(f"Invalid symbol or no data: {symbol}")

        open_p  = float(data[3])
        close_p = float(data[6])
        change  = close_p - open_p

        return {
            "symbol":     symbol.upper(),
            "date":       data[1],
            "open":       open_p,
            "high":       float(data[4]),
            "low":        float(data[5]),
            "close":      close_p,
            "volume":     int(float(data[7])),
            "change":     round(change, 4),
            "change_pct": round((change / open_p) * 100, 2),
        }


class CryptoScraper:
    BASE_URL = "https://api.coingecko.com/api/v3/coins/markets"

    def get(self, coin_id: str) -> dict:
        """Get data for a single coin by CoinGecko id (e.g 'bitcoin')."""
        res = requests.get(
            self.BASE_URL,
            params={"vs_currency": "usd", "ids": coin_id},
            timeout=10,
        )
        data = res.json()
        if not data:
            raise ValueError(f"Coin not found: {coin_id}")
        return self._format(data[0])

    def top(self, n: int = 10) -> list[dict]:
        """Get top N coins by market cap."""
        res = requests.get(
            self.BASE_URL,
            params={"vs_currency": "usd", "order": "market_cap_desc", "per_page": n, "page": 1},
            timeout=10,
        )
        return [self._format(c) for c in res.json()]

    def _format(self, coin: dict) -> dict:
        return {
            "id":          coin["id"],
            "name":        coin["name"],
            "symbol":      coin["symbol"].upper(),
            "rank":        coin["market_cap_rank"],
            "price":       coin["current_price"],
            "change_24h":  coin.get("price_change_percentage_24h") or 0,
            "market_cap":  coin["market_cap"],
            "volume_24h":  coin["total_volume"],
            "high_24h":    coin["high_24h"],
            "low_24h":     coin["low_24h"],
        }


class ForexScraper:
    BASE_URL = "https://api.frankfurter.app/latest"

    def get(self, base: str, target: str = None) -> dict:
        """
        Get rates from base currency.
        If target is provided, returns just that pair.
        Otherwise returns all available rates.
        """
        res = requests.get(self.BASE_URL, params={"from": base.upper()}, timeout=10)
        if res.status_code != 200:
            raise ValueError(f"Invalid currency: {base}")

        data  = res.json()
        rates = data["rates"]
        date  = data["date"]

        if target:
            target = target.upper()
            if target not in rates:
                raise KeyError(f"{target} not available from {base}")
            return {"base": base.upper(), "target": target, "rate": rates[target], "date": date}

        return {"base": base.upper(), "date": date, "rates": rates}


class NewsScraper:
    RSS_URL = "https://news.google.com/rss/search"

    def get(self, query: str, limit: int = 5) -> list[dict]:
        """Fetch news articles for a query topic."""
        res = requests.get(
            self.RSS_URL,
            params={"q": query, "hl": "en-US", "gl": "US", "ceid": "US:en"},
            headers={"User-Agent": "Mozilla/5.0"},
            timeout=10,
        )
        root  = ET.fromstring(res.content)
        items = root.findall(".//item")

        if not items:
            return []

        results = []
        for item in items[:limit]:
            desc_raw = item.findtext("description", "")
            clean    = re.sub(r"<[^>]+>", "", desc_raw).strip()
            clean    = re.sub(r"^.{0,120}\s{2,}", "", clean).strip()

            results.append({
                "title":   item.findtext("title",   ""),
                "link":    item.findtext("link",    ""),
                "source":  item.findtext("source",  "Unknown"),
                "date":    item.findtext("pubDate", ""),
                "snippet": (clean[:220] + "…") if len(clean) > 220 else clean,
            })

        return results


COMMODITY_SYMBOLS = {
    "gold":        "xauusd",
    "silver":      "xagusd",
    "oil_wti":     "cl.f",
    "oil_brent":   "lcousd",
    "natural_gas": "ng.f",
    "copper":      "hg.f",
    "wheat":       "w.f",
    "corn":        "c.f",
    "platinum":    "xptusd",
}

class CommodityScraper:
    BASE_URL = "https://stooq.com/q/l/?s={symbol}&f=sd2t2ohlcv&h&e=csv"

    def get(self, commodity: str) -> dict:
        """
        Pass a preset key (e.g 'gold', 'oil_wti')
        or a raw stooq symbol (e.g 'xauusd').
        """
        symbol = COMMODITY_SYMBOLS.get(commodity.lower(), commodity.lower())
        res    = requests.get(self.BASE_URL.format(symbol=symbol), timeout=10)
        rows   = res.text.strip().split("\n")

        if len(rows) < 2:
            raise ValueError(f"No data for: {commodity}")

        data = rows[1].split(",")
        if not data or data[1] == "N/D":
            raise ValueError(f"No data found for: {commodity}")

        open_p  = float(data[3])
        close_p = float(data[6])
        change  = close_p - open_p

        return {
            "symbol":     symbol.upper(),
            "label":      commodity,
            "date":       data[1],
            "open":       open_p,
            "high":       float(data[4]),
            "low":        float(data[5]),
            "close":      close_p,
            "change":     round(change, 4),
            "change_pct": round((change / open_p) * 100, 2),
        }

    @staticmethod
    def available() -> list[str]:
        return list(COMMODITY_SYMBOLS.keys())
