"""Shared yfinance data fetching logic for ingest and live refresh."""

import json
from datetime import datetime, timezone
from typing import Dict, Any, Optional

import requests
import yfinance as yf

# query1.finance.yahoo.com blocks datacenter IPs with 429.
# query2 v8/finance/chart works from datacenter IPs — use this for price history.
_YF_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "application/json",
}
_YF_CHART_URL = "https://query2.finance.yahoo.com/v8/finance/chart/{ticker}?interval=1wk&range=2y"

# Fallback fundamentals for when Yahoo Finance quoteSummary is blocked (401/429).
# Prices updated 2026-04-03 from live query2 chart endpoint.
DEMO_DATA = {
    "AAPL": {
        "name": "Apple Inc.",
        "sector": "Technology",
        "current_price": 255.92,
        "market_cap": 3850000000000,
        "pe_ratio": 30.5,
        "forward_pe": 27.8,
        "trailing_eps": 8.39,
        "forward_eps": 9.20,
        "dividend_yield": 0.0044,
        "volume": 52000000,
        "avg_volume": 51000000,
        "high_52w": 288.62,
        "low_52w": 169.21,
        "beta": 1.25,
        "revenue_growth": 0.045,
        "earnings_growth": 0.082,
        "profit_margins": 0.26,
        "short_ratio": 0.008,
        "short_pct_float": 0.008,
        "target_mean_price": 275.0,
        "target_high_price": 310.0,
        "target_low_price": 220.0,
        "analyst_count": 48,
        "recommendation": "buy",
        "long_description": "Apple Inc. designs, manufactures, and markets smartphones, personal computers, tablets, wearables, and accessories worldwide.",
        "earnings_date": "2026-07-31",
    },
    "MSFT": {
        "name": "Microsoft Corporation",
        "sector": "Technology",
        "current_price": 373.46,
        "market_cap": 2780000000000,
        "pe_ratio": 31.8,
        "forward_pe": 28.4,
        "trailing_eps": 11.74,
        "forward_eps": 13.15,
        "dividend_yield": 0.0085,
        "volume": 18000000,
        "avg_volume": 19000000,
        "high_52w": 555.45,
        "low_52w": 344.79,
        "beta": 0.91,
        "revenue_growth": 0.158,
        "earnings_growth": 0.124,
        "profit_margins": 0.35,
        "short_ratio": 0.005,
        "short_pct_float": 0.005,
        "target_mean_price": 480.0,
        "target_high_price": 560.0,
        "target_low_price": 380.0,
        "analyst_count": 52,
        "recommendation": "buy",
        "long_description": "Microsoft Corporation develops, licenses, and supports software, services, devices, and solutions worldwide.",
        "earnings_date": "2026-04-30",
    },
    "NVDA": {
        "name": "NVIDIA Corporation",
        "sector": "Technology",
        "current_price": 177.39,
        "market_cap": 4320000000000,
        "pe_ratio": 38.2,
        "forward_pe": 28.5,
        "trailing_eps": 4.64,
        "forward_eps": 6.23,
        "dividend_yield": 0.00003,
        "volume": 280000000,
        "avg_volume": 350000000,
        "high_52w": 212.19,
        "low_52w": 86.62,
        "beta": 1.98,
        "revenue_growth": 0.781,
        "earnings_growth": 1.430,
        "profit_margins": 0.55,
        "short_ratio": 0.004,
        "short_pct_float": 0.004,
        "target_mean_price": 210.0,
        "target_high_price": 250.0,
        "target_low_price": 135.0,
        "analyst_count": 58,
        "recommendation": "buy",
        "long_description": "NVIDIA designs and manufactures GPUs for gaming, professional visualization, data centers, and AI applications.",
        "earnings_date": "2026-05-28",
    },
    "TSLA": {
        "name": "Tesla, Inc.",
        "sector": "Consumer Cyclical",
        "current_price": 268.48,
        "market_cap": 864000000000,
        "pe_ratio": 98.3,
        "forward_pe": 72.1,
        "trailing_eps": 2.73,
        "forward_eps": 3.72,
        "dividend_yield": 0.0,
        "volume": 95000000,
        "avg_volume": 100000000,
        "high_52w": 488.54,
        "low_52w": 138.80,
        "beta": 2.34,
        "revenue_growth": 0.021,
        "earnings_growth": -0.710,
        "profit_margins": 0.073,
        "short_ratio": 0.012,
        "short_pct_float": 0.030,
        "target_mean_price": 290.0,
        "target_high_price": 500.0,
        "target_low_price": 115.0,
        "analyst_count": 50,
        "recommendation": "hold",
        "long_description": "Tesla designs, develops, manufactures, and sells electric vehicles, energy generation and storage systems.",
        "earnings_date": "2026-04-22",
    },
    "META": {
        "name": "Meta Platforms, Inc.",
        "sector": "Technology",
        "current_price": 541.56,
        "market_cap": 1370000000000,
        "pe_ratio": 22.8,
        "forward_pe": 19.5,
        "trailing_eps": 23.76,
        "forward_eps": 27.78,
        "dividend_yield": 0.0036,
        "volume": 14000000,
        "avg_volume": 16000000,
        "high_52w": 740.91,
        "low_52w": 479.62,
        "beta": 1.22,
        "revenue_growth": 0.210,
        "earnings_growth": 0.374,
        "profit_margins": 0.38,
        "short_ratio": 0.007,
        "short_pct_float": 0.007,
        "target_mean_price": 720.0,
        "target_high_price": 850.0,
        "target_low_price": 550.0,
        "analyst_count": 55,
        "recommendation": "buy",
        "long_description": "Meta Platforms operates Facebook, Instagram, WhatsApp, and develops AR/VR hardware.",
        "earnings_date": "2026-04-30",
    },
    "AMZN": {
        "name": "Amazon.com, Inc.",
        "sector": "Technology",
        "current_price": 189.59,
        "market_cap": 2010000000000,
        "pe_ratio": 37.2,
        "forward_pe": 29.8,
        "trailing_eps": 5.10,
        "forward_eps": 6.36,
        "dividend_yield": 0.0,
        "volume": 42000000,
        "avg_volume": 45000000,
        "high_52w": 242.52,
        "low_52w": 151.61,
        "beta": 1.15,
        "revenue_growth": 0.109,
        "earnings_growth": 0.861,
        "profit_margins": 0.098,
        "short_ratio": 0.005,
        "short_pct_float": 0.005,
        "target_mean_price": 250.0,
        "target_high_price": 290.0,
        "target_low_price": 195.0,
        "analyst_count": 65,
        "recommendation": "buy",
        "long_description": "Amazon engages in e-commerce, cloud computing (AWS), digital streaming, and AI.",
        "earnings_date": "2026-05-01",
    },
    "GOOGL": {
        "name": "Alphabet Inc.",
        "sector": "Technology",
        "current_price": 155.49,
        "market_cap": 1910000000000,
        "pe_ratio": 18.9,
        "forward_pe": 16.2,
        "trailing_eps": 8.23,
        "forward_eps": 9.59,
        "dividend_yield": 0.005,
        "volume": 25000000,
        "avg_volume": 28000000,
        "high_52w": 207.05,
        "low_52w": 140.53,
        "beta": 1.05,
        "revenue_growth": 0.121,
        "earnings_growth": 0.288,
        "profit_margins": 0.307,
        "short_ratio": 0.005,
        "short_pct_float": 0.005,
        "target_mean_price": 210.0,
        "target_high_price": 250.0,
        "target_low_price": 165.0,
        "analyst_count": 60,
        "recommendation": "buy",
        "long_description": "Alphabet is the parent of Google, operating in search, advertising, cloud, and hardware.",
        "earnings_date": "2026-04-29",
    },
    "JPM": {
        "name": "JPMorgan Chase & Co.",
        "sector": "Financial Services",
        "current_price": 234.12,
        "market_cap": 664000000000,
        "pe_ratio": 12.1,
        "forward_pe": 11.4,
        "trailing_eps": 19.36,
        "forward_eps": 20.54,
        "dividend_yield": 0.024,
        "volume": 10000000,
        "avg_volume": 10000000,
        "high_52w": 280.25,
        "low_52w": 183.56,
        "beta": 1.12,
        "revenue_growth": 0.121,
        "earnings_growth": 0.180,
        "profit_margins": 0.30,
        "short_ratio": 0.009,
        "short_pct_float": 0.009,
        "target_mean_price": 275.0,
        "target_high_price": 310.0,
        "target_low_price": 225.0,
        "analyst_count": 28,
        "recommendation": "buy",
        "long_description": "JPMorgan Chase is the largest US bank, providing investment banking and financial services.",
        "earnings_date": "2026-07-15",
    },
    "GS": {
        "name": "The Goldman Sachs Group, Inc.",
        "sector": "Financial Services",
        "current_price": 489.22,
        "market_cap": 163000000000,
        "pe_ratio": 12.8,
        "forward_pe": 11.5,
        "trailing_eps": 38.22,
        "forward_eps": 42.54,
        "dividend_yield": 0.021,
        "volume": 2000000,
        "avg_volume": 2100000,
        "high_52w": 672.19,
        "low_52w": 386.38,
        "beta": 1.38,
        "revenue_growth": 0.160,
        "earnings_growth": 0.685,
        "profit_margins": 0.25,
        "short_ratio": 0.011,
        "short_pct_float": 0.011,
        "target_mean_price": 620.0,
        "target_high_price": 720.0,
        "target_low_price": 490.0,
        "analyst_count": 22,
        "recommendation": "buy",
        "long_description": "Goldman Sachs is a global investment banking, securities, and investment management firm.",
        "earnings_date": "2026-07-14",
    },
    "BA": {
        "name": "The Boeing Company",
        "sector": "Industrials",
        "current_price": 171.24,
        "market_cap": 131000000000,
        "pe_ratio": None,
        "forward_pe": 42.3,
        "trailing_eps": -14.32,
        "forward_eps": 4.05,
        "dividend_yield": 0.0,
        "volume": 8000000,
        "avg_volume": 8500000,
        "high_52w": 216.20,
        "low_52w": 128.13,
        "beta": 1.41,
        "revenue_growth": 0.153,
        "earnings_growth": None,
        "profit_margins": -0.072,
        "short_ratio": 0.020,
        "short_pct_float": 0.020,
        "target_mean_price": 200.0,
        "target_high_price": 260.0,
        "target_low_price": 130.0,
        "analyst_count": 25,
        "recommendation": "hold",
        "long_description": "Boeing designs and manufactures commercial jetliners, military aircraft, and space systems.",
        "earnings_date": "2026-04-23",
    },
    "XOM": {
        "name": "Exxon Mobil Corporation",
        "sector": "Energy",
        "current_price": 108.16,
        "market_cap": 458000000000,
        "pe_ratio": 13.4,
        "forward_pe": 13.1,
        "trailing_eps": 8.07,
        "forward_eps": 8.26,
        "dividend_yield": 0.037,
        "volume": 18000000,
        "avg_volume": 19000000,
        "high_52w": 126.34,
        "low_52w": 97.59,
        "beta": 0.84,
        "revenue_growth": 0.026,
        "earnings_growth": -0.115,
        "profit_margins": 0.08,
        "short_ratio": 0.013,
        "short_pct_float": 0.013,
        "target_mean_price": 122.0,
        "target_high_price": 145.0,
        "target_low_price": 97.0,
        "analyst_count": 28,
        "recommendation": "buy",
        "long_description": "ExxonMobil explores, produces, and refines petroleum products and chemicals globally.",
        "earnings_date": "2026-05-02",
    },
    "LMT": {
        "name": "Lockheed Martin Corporation",
        "sector": "Industrials",
        "current_price": 468.90,
        "market_cap": 109000000000,
        "pe_ratio": 16.5,
        "forward_pe": 15.8,
        "trailing_eps": 28.42,
        "forward_eps": 29.68,
        "dividend_yield": 0.030,
        "volume": 1000000,
        "avg_volume": 1100000,
        "high_52w": 614.78,
        "low_52w": 416.84,
        "beta": 0.52,
        "revenue_growth": 0.052,
        "earnings_growth": -0.011,
        "profit_margins": 0.105,
        "short_ratio": 0.018,
        "short_pct_float": 0.018,
        "target_mean_price": 550.0,
        "target_high_price": 640.0,
        "target_low_price": 450.0,
        "analyst_count": 18,
        "recommendation": "buy",
        "long_description": "Lockheed Martin is a global defense and aerospace company, maker of the F-35 fighter jet.",
        "earnings_date": "2026-04-22",
    },
    "UNH": {
        "name": "UnitedHealth Group Incorporated",
        "sector": "Healthcare",
        "current_price": 491.28,
        "market_cap": 450000000000,
        "pe_ratio": 19.6,
        "forward_pe": 14.8,
        "trailing_eps": 25.07,
        "forward_eps": 33.19,
        "dividend_yield": 0.020,
        "volume": 4000000,
        "avg_volume": 3800000,
        "high_52w": 630.73,
        "low_52w": 411.36,
        "beta": 0.57,
        "revenue_growth": 0.087,
        "earnings_growth": -0.413,
        "profit_margins": 0.035,
        "short_ratio": 0.014,
        "short_pct_float": 0.014,
        "target_mean_price": 600.0,
        "target_high_price": 700.0,
        "target_low_price": 440.0,
        "analyst_count": 25,
        "recommendation": "buy",
        "long_description": "UnitedHealth Group is a diversified health care company offering health benefits and services.",
        "earnings_date": "2026-04-17",
    },
    "V": {
        "name": "Visa Inc.",
        "sector": "Financial Services",
        "current_price": 334.02,
        "market_cap": 710000000000,
        "pe_ratio": 30.2,
        "forward_pe": 26.5,
        "trailing_eps": 11.07,
        "forward_eps": 12.60,
        "dividend_yield": 0.0083,
        "volume": 6000000,
        "avg_volume": 6200000,
        "high_52w": 370.00,
        "low_52w": 252.70,
        "beta": 0.93,
        "revenue_growth": 0.102,
        "earnings_growth": 0.143,
        "profit_margins": 0.544,
        "short_ratio": 0.008,
        "short_pct_float": 0.008,
        "target_mean_price": 385.0,
        "target_high_price": 420.0,
        "target_low_price": 310.0,
        "analyst_count": 35,
        "recommendation": "buy",
        "long_description": "Visa operates the world's largest retail electronic payments network.",
        "earnings_date": "2026-04-29",
    },
    "GME": {
        "name": "GameStop Corp.",
        "sector": "Retail",
        "current_price": 23.36,
        "market_cap": 10900000000,
        "pe_ratio": None,
        "forward_pe": None,
        "trailing_eps": -0.18,
        "forward_eps": None,
        "dividend_yield": 0.0,
        "volume": 8000000,
        "avg_volume": 6000000,
        "high_52w": 35.81,
        "low_52w": 19.93,
        "beta": 1.65,
        "revenue_growth": -0.19,
        "earnings_growth": None,
        "profit_margins": -0.04,
        "short_ratio": 2.1,
        "short_pct_float": 0.12,
        "target_mean_price": 10.0,
        "target_high_price": 15.0,
        "target_low_price": 7.0,
        "analyst_count": 6,
        "recommendation": "sell",
        "long_description": "GameStop Corp. is an American video game, consumer electronics, and collectibles retailer.",
        "earnings_date": "2026-06-05",
    },
}


def _get_likeliest_sector(ticker: str) -> str:
    """Map ticker to likely sector if Yahoo fails."""
    tech = {"AAPL", "MSFT", "GOOGL", "AMZN", "META", "NVDA", "TSLA", "AMD", "INTC", "CRM", "ADBE", "NFLX", "PYPL", "SQ", "PLTR", "SNOW", "CRWD"}
    finance = {"JPM", "BAC", "GS", "V", "MA"}
    healthcare = {"JNJ", "UNH", "LLY"}
    consumer = {"WMT", "HD", "NKE", "MCD"}
    energy = {"XOM", "CVX"}
    industrial = {"BA", "CAT", "LMT"}
    crypto = {"COIN"}
    retail = {"GME"}

    ticker_upper = ticker.upper()
    if ticker_upper in tech:
        return "Technology"
    elif ticker_upper in finance:
        return "Financial Services"
    elif ticker_upper in healthcare:
        return "Healthcare"
    elif ticker_upper in consumer:
        return "Consumer Cyclical"
    elif ticker_upper in energy:
        return "Energy"
    elif ticker_upper in industrial:
        return "Industrials"
    elif ticker_upper in crypto:
        return "Cryptocurrency"
    elif ticker_upper in retail:
        return "Retail"
    return "Unknown"


def fetch_price_history(ticker: str, use_demo: bool = False) -> Optional[str]:
    """
    Fetch 2-year weekly price history via Yahoo Finance query2 chart API.
    This endpoint works from datacenter IPs unlike query1/yf.download().
    Falls back to synthetic history only if the request fails.
    """
    try:
        url = _YF_CHART_URL.format(ticker=ticker.upper())
        resp = requests.get(url, headers=_YF_HEADERS, timeout=15)
        resp.raise_for_status()
        data = resp.json()

        result = data["chart"]["result"][0]
        timestamps = result.get("timestamp", [])
        quotes = result["indicators"]["quote"][0]
        opens   = quotes.get("open",   [])
        highs   = quotes.get("high",   [])
        lows    = quotes.get("low",    [])
        closes  = quotes.get("close",  [])
        volumes = quotes.get("volume", [])

        if not timestamps or not closes:
            raise ValueError("Empty chart data from Yahoo Finance")

        history = []
        for i, ts in enumerate(timestamps):
            c = closes[i] if i < len(closes) else None
            if c is None:
                continue
            date_str = datetime.fromtimestamp(ts, tz=timezone.utc).strftime("%Y-%m-%d")
            history.append({
                "date":   date_str,
                "open":   round(float(opens[i]),   2) if i < len(opens)   and opens[i]   else round(float(c), 2),
                "high":   round(float(highs[i]),   2) if i < len(highs)   and highs[i]   else round(float(c), 2),
                "low":    round(float(lows[i]),    2) if i < len(lows)    and lows[i]    else round(float(c), 2),
                "close":  round(float(c), 2),
                "volume": int(volumes[i]) if i < len(volumes) and volumes[i] else 0,
            })

        if history:
            return json.dumps(history[-104:])  # last 2 years

    except Exception as e:
        print(f"  WARNING: Could not fetch live chart for {ticker}: {e}")

    # Fallback: generate synthetic history from demo base price
    if use_demo or ticker.upper() in DEMO_DATA:
        base = DEMO_DATA.get(ticker.upper(), {}).get("current_price", 100)
        return _generate_demo_price_history(ticker, base)
    return None


def fetch_fundamentals(ticker: str, use_demo: bool = False) -> Optional[Dict[str, Any]]:
    """
    Fetch fundamental stock data.

    Primary path: yf.Ticker().info (works on residential IPs, blocked on datacenter).
    Fallback: DEMO_DATA fundamentals + live price/52w patched from query2 chart endpoint.
    """
    if not use_demo:
        try:
            t = yf.Ticker(ticker)
            info = t.info

            if not info or info.get("regularMarketPrice") is None:
                raise ValueError("No price data from yfinance")

            earnings_ts = info.get("earningsTimestamp")
            earnings_date = None
            if earnings_ts:
                try:
                    earnings_date = datetime.fromtimestamp(earnings_ts, tz=timezone.utc).strftime("%Y-%m-%d")
                except (ValueError, TypeError):
                    pass

            return {
                "ticker": ticker.upper(),
                "name": info.get("longName") or info.get("shortName") or ticker,
                "sector": info.get("sector") or info.get("quoteType") or _get_likeliest_sector(ticker),
                "current_price": info.get("regularMarketPrice") or info.get("currentPrice"),
                "market_cap": info.get("marketCap"),
                "pe_ratio": info.get("trailingPE"),
                "forward_pe": info.get("forwardPE"),
                "trailing_eps": info.get("trailingEps"),
                "forward_eps": info.get("forwardEps"),
                "dividend_yield": info.get("dividendYield") or 0.0,
                "volume": info.get("regularMarketVolume") or info.get("volume"),
                "avg_volume": info.get("averageVolume"),
                "high_52w": info.get("fiftyTwoWeekHigh"),
                "low_52w": info.get("fiftyTwoWeekLow"),
                "beta": info.get("beta"),
                "revenue_growth": info.get("revenueGrowth"),
                "earnings_growth": info.get("earningsGrowth"),
                "profit_margins": info.get("profitMargins"),
                "short_ratio": info.get("shortRatio"),
                "short_pct_float": info.get("shortPercentOfFloat"),
                "target_mean_price": info.get("targetMeanPrice"),
                "target_high_price": info.get("targetHighPrice"),
                "target_low_price": info.get("targetLowPrice"),
                "analyst_count": info.get("numberOfAnalystOpinions"),
                "recommendation": info.get("recommendationKey"),
                "long_description": info.get("longBusinessSummary"),
                "description": info.get("longName") or ticker,
                "earnings_date": earnings_date,
            }
        except Exception as e:
            print(f"  WARNING: yfinance fundamentals failed for {ticker}: {e}")

    # Fallback: demo fundamentals + live price patch from query2
    demo = DEMO_DATA.get(ticker.upper())
    if not demo:
        # Generate synthetic demo data for ticker not in DEMO_DATA
        sector = _get_likeliest_sector(ticker)
        demo = {
            "name": f"{ticker} Corp.",
            "sector": sector,
            "current_price": 100.0,
            "market_cap": 1000000000000,
            "pe_ratio": 25.0,
            "forward_pe": 22.0,
            "trailing_eps": 4.0,
            "forward_eps": 4.5,
            "dividend_yield": 0.02,
            "volume": 50000000,
            "avg_volume": 48000000,
            "high_52w": 120.0,
            "low_52w": 75.0,
            "beta": 1.0,
            "revenue_growth": 0.08,
            "earnings_growth": 0.10,
            "profit_margins": 0.15,
            "short_ratio": 0.01,
            "short_pct_float": 0.01,
            "target_mean_price": 110.0,
            "target_high_price": 130.0,
            "target_low_price": 85.0,
            "analyst_count": 10,
            "recommendation": "hold",
            "long_description": f"Placeholder fundamental data for {ticker}",
            "earnings_date": "2026-07-31",
        }

    result = {
        "ticker": ticker.upper(),
        **demo,
        "description": demo.get("long_description", ""),
    }

    # Patch live price + 52w range from the chart endpoint (works on datacenter IPs)
    try:
        url = _YF_CHART_URL.format(ticker=ticker.upper())
        resp = requests.get(url, headers=_YF_HEADERS, timeout=10)
        resp.raise_for_status()
        meta = resp.json()["chart"]["result"][0]["meta"]
        if meta.get("regularMarketPrice"):
            result["current_price"] = meta["regularMarketPrice"]
        if meta.get("fiftyTwoWeekHigh"):
            result["high_52w"] = meta["fiftyTwoWeekHigh"]
        if meta.get("fiftyTwoWeekLow"):
            result["low_52w"] = meta["fiftyTwoWeekLow"]
        if meta.get("regularMarketVolume"):
            result["volume"] = meta["regularMarketVolume"]
        if meta.get("longName"):
            result["name"] = meta["longName"]
            result["description"] = meta["longName"]
    except Exception as e:
        print(f"  NOTE: Could not patch live price for {ticker}: {e}")

    return result


def fetch_news(ticker: str) -> str:
    """
    Fetch recent news headlines for a ticker via yfinance.
    Returns JSON string of up to 8 news items.
    """
    try:
        t = yf.Ticker(ticker)
        raw_news = t.get_news()

        headlines = []
        if raw_news:
            for item in raw_news[:8]:
                headlines.append({
                    "title": item.get("title", ""),
                    "publisher": item.get("publisher", ""),
                    "published": item.get("providerPublishTime", 0),
                    "link": item.get("link", ""),
                })

        return json.dumps(headlines)
    except Exception as e:
        print(f"  WARNING: Could not fetch news for {ticker}: {e}")
        return json.dumps([])


def _generate_demo_price_history(ticker: str, base_price: float) -> str:
    """Generate synthetic but realistic 2-year weekly price history as last resort."""
    import random
    from datetime import timedelta

    history = []
    price = base_price * 0.65
    start_date = datetime.now(tz=timezone.utc) - timedelta(weeks=104)

    for week in range(104):
        date = start_date + timedelta(weeks=week)
        change = random.gauss(0.002, 0.025)
        price = price * (1 + change)
        price = max(price, base_price * 0.4)
        price = min(price, base_price * 1.6)
        history.append({
            "date": date.strftime("%Y-%m-%d"),
            "close": round(price, 2),
            "volume": random.randint(10000000, 100000000),
        })

    return json.dumps(history[-104:])
