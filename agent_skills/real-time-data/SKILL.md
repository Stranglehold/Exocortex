---
name: "real-time-data"
description: "Live market prices for stocks, ETFs, indices via yfinance and cryptocurrency prices via ccxt. Use for current prices, historical OHLCV data, and market dashboards."
author: "agent"
---

# Real-Time Data Skill

## Overview
Access to live stock market data via yfinance and cryptocurrency prices via ccxt. Both libraries are free and open-source.

## Installation
```bash
pip install yfinance ccxt
```

---

## Stock Market Data (yfinance)

### Quick Start
```python
import yfinance as yf

# Get current price of a single stock
ticker = yf.Ticker("AAPL")
data = ticker.history(period="1d")
current_price = data["Close"].iloc[-1]
print(f"AAPL: ${current_price:.2f}")
```

### Available Tickers
- **US Stocks**: AAPL, GOOGL, MSFT, TSLA, AMZN, etc.
- **ETFs**: SPY, QQQ, IWM, DIA
- **Indices**: ^GSPC (S&P 500), ^DJI (Dow Jones), ^IXIC (NASDAQ)
- **International**: Use exchange prefix (e.g., "VOW3.DE" for Volkswagen on XETRA)

### Key Functions

#### Get Historical Data
```python
import yfinance as yf

def get_stock_history(ticker_symbol, period="1mo"):
    """
    Period options: 1d, 5d, 1mo, 3mo, 6mo, 1y, 2y, 5y, 10y, ytd, max
    """
    ticker = yf.Ticker(ticker_symbol)
    return ticker.history(period=period)

# Example: Get Apple's last month of data
df = get_stock_history("AAPL", period="1mo")
print(df.head())
```

#### Get Current Price and Key Metrics
```python
def get_stock_info(ticker_symbol):
    ticker = yf.Ticker(ticker_symbol)
    info = ticker.info

    return {
        "symbol": ticker_symbol,
        "name": info.get("shortName", "Unknown"),
        "current_price": info.get("currentPrice"),
        "previous_close": info.get("previousClose"),
        "open": info.get("open"),
        "day_high": info.get("dayHigh"),
        "day_low": info.get("dayLow"),
        "volume": info.get("volume"),
        "market_cap": info.get("marketCap"),
        "pe_ratio": info.get("trailingPE"),
        "dividend_yield": info.get("dividendYield")
    }

# Example
info = get_stock_info("AAPL")
print(f"{info['name']}: ${info['current_price']:.2f}")
```

#### Get Multiple Stocks at Once
```python
def get_multiple_stocks(tickers):
    """
    Fetch data for multiple tickers efficiently
    """
    data = yf.download(tickers, period="1d", group_by="ticker")
    return data

# Example: Get tech stocks
tech_stocks = ["AAPL", "GOOGL", "MSFT", "META", "NVDA"]
data = get_multiple_stocks(tech_stocks)
print(data[["Close"]])
```

#### Calculate Price Change Percentage
```python
def get_price_change(ticker_symbol, period="1d"):
    ticker = yf.Ticker(ticker_symbol)
    hist = ticker.history(period=period)

    if len(hist) < 2:
        return None

    current = hist["Close"].iloc[-1]
    previous = hist["Close"].iloc[-2] if period == "1d" else hist["Open"].iloc[0]

    change_pct = ((current - previous) / previous) * 100
    return {
        "symbol": ticker_symbol,
        "current_price": current,
        "previous_price": previous,
        "change": current - previous,
        "change_percent": change_pct
    }

# Example
result = get_price_change("AAPL")
print(f"AAPL: ${result['current_price']:.2f} ({result['change_percent']:+.2f}%)")
```

---

## Cryptocurrency Data (ccxt)

### Quick Start
```python
import ccxt

# Get Bitcoin price from Kraken
exchange = ccxt.kraken()
ticker = exchange.fetch_ticker("BTC/USD", params={"type": "spot"})
print(f"Bitcoin: ${ticker['last']:.2f}")
```

### Supported Exchanges
ccxt supports 100+ exchanges. Common ones:
- **Kraken**: `ccxt.kraken()` - Reliable, fewer geo-restrictions
- **Coinbase**: `ccxt.coinbase()` - US-based, reliable
- **Binance**: `ccxt.binance()` - Largest volume (may have restrictions)
- **KuCoin**: `ccxt.kucoin()`
- **Bybit**: `ccxt.bybit()`

### Key Functions

#### Get Single Crypto Price
```python
def get_crypto_price(symbol, exchange_name="kraken"):
    """
    symbol format: "BTC/USD", "ETH/USDT", etc.
    """
    exchanges = {
        "kraken": ccxt.kraken,
        "coinbase": ccxt.coinbase,
        "binance": ccxt.binance,
        "kucoin": ccxt.kucoin
    }

    try:
        exchange = exchanges[exchange_name]()
        ticker = exchange.fetch_ticker(symbol, params={"type": "spot"})
        return {
            "symbol": symbol,
            "price": ticker.get("last"),
            "high_24h": ticker.get("high"),
            "low_24h": ticker.get("low"),
            "volume_24h": ticker.get("baseVolume"),
            "bid": ticker.get("bid"),
            "ask": ticker.get("ask")
        }
    except Exception as e:
        return {"error": str(e)}

# Example
btc_price = get_crypto_price("BTC/USD", "kraken")
print(f"Bitcoin: ${btc_price['price']:.2f}")
```

#### Get Multiple Crypto Prices
```python
def get_multiple_crypto_prices(pairs, exchange_name="kraken"):
    """
    pairs: list like ["BTC/USD", "ETH/USD", "SOL/USD"]
    """
    exchanges = {"kraken": ccxt.kraken, "coinbase": ccxt.coinbase}
    exchange = exchanges[exchange_name]()

    results = {}
    for pair in pairs:
        try:
            ticker = exchange.fetch_ticker(pair, params={"type": "spot"})
            results[pair] = {
                "price": ticker.get("last"),
                "change_24h_pct": ticker.get("percentage")
            }
        except Exception as e:
            results[pair] = {"error": str(e)}

    return results

# Example
crypto_pairs = ["BTC/USD", "ETH/USD", "SOL/USD"]
prices = get_multiple_crypto_prices(crypto_pairs, "kraken")
for pair, data in prices.items():
    print(f"{pair}: ${data['price']:.2f}")
```

#### Get OHLCV (Candlestick) Data
```python
def get_crypto_ohlcv(symbol, timeframe="1h", limit=24, exchange_name="kraken"):
    """
    Returns candlestick data: [timestamp, open, high, low, close, volume]
    Timeframes: 1m, 5m, 15m, 30m, 1h, 4h, 1d, 1w, 1M
    """
    exchanges = {"kraken": ccxt.kraken, "binance": ccxt.binance}
    exchange = exchanges[exchange_name]()

    ohlcv = exchange.fetch_ohlcv(symbol, timeframe=timeframe, limit=limit)
    return ohlcv

# Example: Get last 24 hours of Bitcoin hourly data
ohlcv = get_crypto_ohlcv("BTC/USD", "1h", 24, "kraken")
latest_candle = ohlcv[-1]
print(f"Latest hour - Open: ${latest_candle[1]:.2f}, Close: ${latest_candle[4]:.2f}")
```

#### Get Order Book
```python
def get_order_book(symbol, limit=10, exchange_name="kraken"):
    """
    Get bid/ask order book
    """
    exchanges = {"kraken": ccxt.kraken, "coinbase": ccxt.coinbase}
    exchange = exchanges[exchange_name]()

    orderbook = exchange.fetch_order_book(symbol, limit=limit)
    return {
        "symbol": symbol,
        "bids": orderbook.get("bids", [])[:5],  # Top 5 bids
        "asks": orderbook.get("asks", [])[:5]   # Top 5 asks
    }

# Example
orderbook = get_order_book("BTC/USD", exchange_name="kraken")
print(f"Best bid: ${orderbook['bids'][0][0]:.2f}")
print(f"Best ask: ${orderbook['asks'][0][0]:.2f}")
```

---

## Combined Market Dashboard

```python
import yfinance as yf
import ccxt
from datetime import datetime

def market_dashboard():
    """
    Comprehensive real-time market dashboard
    """
    print(f"
{'='*60}")
    print(f"MARKET DASHBOARD - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'='*60}
")

    # === STOCK MARKET ===
    print("📈 STOCK MARKET")
    print("-" * 40)

    stocks = {
        "AAPL": "Apple",
        "GOOGL": "Alphabet",
        "MSFT": "Microsoft",
        "TSLA": "Tesla",
        "SPY": "S&P 500 ETF"
    }

    for symbol, name in stocks.items():
        try:
            ticker = yf.Ticker(symbol)
            info = ticker.info
            price = info.get("currentPrice") or info.get("regularMarketPrice")
            prev_close = info.get("previousClose")

            if price and prev_close:
                change_pct = ((price - prev_close) / prev_close) * 100
                print(f"{symbol:6} {name:15} ${price:>12.2f} ({change_pct:+6.2f}%)")
        except Exception as e:
            print(f"{symbol}: Error - {e}")

    # === CRYPTOCURRENCY ===
    print("
₿ CRYPTOCURRENCY")
    print("-" * 40)

    crypto_pairs = ["BTC/USD", "ETH/USD", "SOL/USD"]
    exchange = ccxt.kraken()

    for pair in crypto_pairs:
        try:
            ticker = exchange.fetch_ticker(pair, params={"type": "spot"})
            price = ticker.get("last")
            change_pct = ticker.get("percentage", 0)
            name = pair.split("/")[0]
            print(f"{name:6} {'Price':15} ${price:>12.2f} ({change_pct:+6.2f}%)")
        except Exception as e:
            print(f"{pair}: Error - {e}")

    print(f"
{'='*60}
")

# Run dashboard
market_dashboard()
```

---

## Error Handling and Best Practices

### Robust Stock Price Fetcher
```python
def safe_get_stock_price(symbol, retries=3):
    """
    Safely fetch stock price with error handling and retries
    """
    import time

    for attempt in range(retries):
        try:
            ticker = yf.Ticker(symbol)
            info = ticker.info

            # Try multiple possible keys for current price
            price = (
                info.get("currentPrice") or
                info.get("regularMarketPrice") or
                info.get("previousClose")
            )

            if price:
                return {"success": True, "price": price, "symbol": symbol}
            else:
                return {"success": False, "error": "No price data available", "symbol": symbol}

        except Exception as e:
            if attempt < retries - 1:
                time.sleep(2)  # Wait before retry
                continue
            return {"success": False, "error": str(e), "symbol": symbol}
```

### Robust Crypto Price Fetcher with Fallback Exchanges
```python
def safe_get_crypto_price(symbol, retries=3):
    """
    Safely fetch crypto price with exchange fallback
    """
    import time

    exchanges_to_try = ["kraken", "coinbase"]  # Add more if needed

    for attempt in range(retries):
        for exchange_name in exchanges_to_try:
            try:
                exchange_class = getattr(ccxt, exchange_name)
                exchange = exchange_class()
                ticker = exchange.fetch_ticker(symbol, params={"type": "spot"})

                price = ticker.get("last") or ticker.get("close")
                if price:
                    return {
                        "success": True,
                        "price": price,
                        "symbol": symbol,
                        "exchange": exchange_name
                    }

            except Exception as e:
                continue  # Try next exchange

        if attempt < retries - 1:
            time.sleep(2)

    return {"success": False, "error": "All exchanges failed", "symbol": symbol}
```

### Check if Stock is Delisted or Invalid
```python
def validate_ticker(symbol):
    """
    Check if a ticker symbol is valid and actively traded
    """
    try:
        ticker = yf.Ticker(symbol)
        info = ticker.info

        # Check for common indicators of invalid/delisted stocks
        if not info or info.get("symbol") != symbol:
            return {"valid": False, "reason": "Symbol mismatch or no data"}

        if info.get("quoteType") == "Unknown":
            return {"valid": False, "reason": "Unknown quote type (possibly delisted)"}

        if not info.get("currentPrice") and not info.get("previousClose"):
            return {"valid": False, "reason": "No price data available"}

        return {"valid": True, "name": info.get("shortName", "Unknown")}

    except Exception as e:
        return {"valid": False, "reason": str(e)}

# Example
print(validate_ticker("AAPL"))   # Valid
print(validate_ticker("INVALID"))  # Invalid
```

---

## Notes and Limitations

### yfinance (Stocks)
- **Free tier**: No API key required, rate limits apply
- **Data delay**: Typically 15-20 minute delay for real-time prices
- **Market hours**: After-hours prices may differ from regular market close
- **Delisted stocks**: May return empty data or errors

### ccxt (Crypto)
- **Free tier**: No API key required for public endpoints
- **Real-time**: Cryptocurrency markets are 24/7 with live prices
- **Exchange availability**: Some exchanges may have geo-restrictions
- **Rate limits**: Vary by exchange; implement delays if needed

### Rate Limiting Best Practice
```python
def rate_limited_fetch(func, delay=1.0):
    """
    Decorator to add rate limiting between API calls
    """
    import time
    from functools import wraps

    @wraps(func)
    def wrapper(*args, **kwargs):
        result = func(*args, **kwargs)
        time.sleep(delay)
        return result

    return wrapper
```

---

## Quick Reference

| Data Type | Library | Example Call | Returns |
|-----------|---------|--------------|----------|
| Stock Price | yfinance | `yf.Ticker("AAPL").info["currentPrice"]` | Float |
| Stock History | yfinance | `yf.download("AAPL", period="1mo")` | DataFrame |
| Crypto Price | ccxt | `exchange.fetch_ticker("BTC/USD")` | Dict |
| Crypto OHLCV | ccxt | `exchange.fetch_ohlcv("BTC/USD", "1h")` | List |

---

## Real-World Example Output

```
MARKET DASHBOARD - 2024-01-15 14:30:00
============================================================

📈 STOCK MARKET
----------------------------------------
AAPL   Apple             $    185.92 (+0.45%)
GOOGL  Alphabet          $    142.56 (-0.23%)
MSFT   Microsoft         $    388.47 (+1.12%)
TSLA   Tesla             $    219.34 (-2.15%)
SPY    S&P 500 ETF       $    478.23 (+0.34%)

₿ CRYPTOCURRENCY
----------------------------------------
BTC    Price             $  42,567.89 (+1.23%)
ETH    Price             $   2,567.45 (-0.45%)
SOL    Price             $     98.76 (+3.45%)

============================================================
```