"""Market ticker monitor for NASDAQ and Dow Jones Industrial Average."""
import json
import os
import time
import urllib.request
from typing import Dict, Any

CACHE_FILE = os.path.expanduser("~/.cache/spi1-sysmon/market_cache.json")


def _ensure_cache_dir():
    cache_dir = os.path.dirname(CACHE_FILE)
    if not os.path.exists(cache_dir):
        try:
            os.makedirs(cache_dir, exist_ok=True)
        except Exception:
            pass


def load_cached_quotes() -> Dict[str, Any]:
    """Load previously cached market data from disk."""
    if os.path.exists(CACHE_FILE):
        try:
            with open(CACHE_FILE, "r") as f:
                return json.load(f)
        except Exception:
            pass
    # Default fallback data if no cache exists
    return {
        "^IXIC": {
            "symbol": "^IXIC",
            "name": "NDX",
            "price": 18200.0,
            "change": 0.0,
            "percent_change": 0.0,
            "updated_at": 0,
        },
        "^DJI": {
            "symbol": "^DJI",
            "name": "DOW",
            "price": 42100.0,
            "change": 0.0,
            "percent_change": 0.0,
            "updated_at": 0,
        }
    }


def save_cached_quotes(quotes: Dict[str, Any]):
    """Save latest market data to disk."""
    _ensure_cache_dir()
    try:
        with open(CACHE_FILE, "w") as f:
            json.dump(quotes, f, indent=2)
    except Exception:
        pass


def fetch_symbol_quote(symbol: str, display_name: str) -> Dict[str, Any]:
    """Fetch live quote from Yahoo Finance API for a symbol."""
    encoded = urllib.parse.quote(symbol)
    url = f"https://query1.finance.yahoo.com/v8/finance/chart/{encoded}?interval=1d&range=1d"
    req = urllib.request.Request(
        url,
        headers={"User-Agent": "Mozilla/5.0 (X11; Linux aarch64) AppleWebKit/537.36"}
    )

    with urllib.request.urlopen(req, timeout=4) as resp:
        data = json.loads(resp.read().decode("utf-8"))
        result = data.get("chart", {}).get("result", [])
        if not result:
            raise ValueError(f"No chart result for {symbol}")

        meta = result[0].get("meta", {})
        price = meta.get("regularMarketPrice")
        prev_close = meta.get("chartPreviousClose") or meta.get("previousClose")

        if price is None:
            raise ValueError(f"No regularMarketPrice for {symbol}")

        if prev_close and prev_close > 0:
            change = price - prev_close
            pct_change = (change / prev_close) * 100.0
        else:
            change = 0.0
            pct_change = 0.0

        return {
            "symbol": symbol,
            "name": display_name,
            "price": round(float(price), 2),
            "change": round(float(change), 2),
            "percent_change": round(float(pct_change), 2),
            "updated_at": int(time.time()),
        }


def get_market_quotes(symbols_config: Dict[str, str] = None) -> Dict[str, Any]:
    """
    Get quotes for symbols (e.g. {'^IXIC': 'NDX', '^DJI': 'DOW'}).
    Uses cached values if network request fails.
    """
    if symbols_config is None:
        symbols_config = {"^IXIC": "NDX", "^DJI": "DOW"}

    cached = load_cached_quotes()
    updated = dict(cached)

    for symbol, name in symbols_config.items():
        try:
            quote = fetch_symbol_quote(symbol, name)
            updated[symbol] = quote
        except Exception:
            # Keep cached quote for this symbol if network fails
            if symbol not in updated:
                updated[symbol] = {
                    "symbol": symbol,
                    "name": name,
                    "price": 0.0,
                    "change": 0.0,
                    "percent_change": 0.0,
                    "updated_at": 0,
                }

    save_cached_quotes(updated)
    return updated


if __name__ == "__main__":
    quotes = get_market_quotes()
    for sym, q in quotes.items():
        print(f"{q['name']} ({sym}): {q['price']:,.2f} ({q['change']:+.2f}, {q['percent_change']:+.2f}%)")
