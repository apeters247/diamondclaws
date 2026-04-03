import os
import sys
import json
import random
import asyncio
from pathlib import Path
from datetime import datetime
from typing import Any, Dict, List
from concurrent.futures import ThreadPoolExecutor

sys.path.insert(0, str(Path(__file__).parent.parent))

import httpx

from data.personas import PERSONAS, BIAS_REFERENCES, get_persona
from models.database import get_stock_by_ticker
from tools.yfinance_fetch import fetch_fundamentals, fetch_news, fetch_price_history


OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY", "")
OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"

# Switch to Gemini 2.0 Flash for much better reasoning
DEFAULT_MODEL = "google/gemini-2.0-flash-001"

STALE_AFTER_HOURS = 4

# Thread pool for blocking yfinance calls
_executor = ThreadPoolExecutor(max_workers=2)


def is_stale(stock: dict) -> bool:
    """Check if stock fundamentals are stale (older than STALE_AFTER_HOURS)."""
    fu = stock.get("fundamentals_updated")
    if not fu:
        return True
    try:
        updated = datetime.fromisoformat(fu)
        age_seconds = (datetime.utcnow() - updated).total_seconds()
        return age_seconds > STALE_AFTER_HOURS * 3600
    except Exception:
        return True


def _blocking_refresh(ticker: str, old_stock: dict) -> dict:
    """
    Blocking function to fetch and store fresh stock data.
    Runs in thread pool to avoid blocking async event loop.
    """
    try:
        fundamentals = fetch_fundamentals(ticker.upper())
        if not fundamentals:
            return old_stock or {}

        # Try to get fresh price history, fall back to old if it fails
        price_history = fetch_price_history(ticker.upper())
        if not price_history and old_stock:
            price_history = old_stock.get("price_history")

        news_json = fetch_news(ticker.upper())

        # Merge with existing data
        data = {
            **fundamentals,
            "price_history": price_history,
            "news_json": news_json,
            "fundamentals_updated": datetime.utcnow().isoformat(),
        }

        # Save to database
        from models.database import upsert_stock

        upsert_stock(data)

        # Return freshly read stock
        return get_stock_by_ticker(ticker.upper())
    except Exception as e:
        print(f"Refresh error for {ticker}: {e}")
        return old_stock or {}


async def refresh_stock_if_stale(ticker: str) -> dict:
    """
    Lazy-refresh pattern: fetch fresh data if cache is stale.
    Returns the stock dict (fresh or cached).
    """
    stock = get_stock_by_ticker(ticker)
    if stock and not is_stale(stock):
        return stock  # cache hit

    # Cache miss or stale - refresh in thread pool
    loop = asyncio.get_running_loop()
    try:
        new_stock = await loop.run_in_executor(_executor, _blocking_refresh, ticker, stock)
        return new_stock or stock or {}
    except Exception as e:
        print(f"Failed to refresh {ticker}: {e}")
        return stock or {}


async def call_llm(prompt: str, model: str = DEFAULT_MODEL) -> str:
    """Call LLM via OpenRouter."""
    if not OPENROUTER_API_KEY:
        return "LLM not configured - set OPENROUTER_API_KEY"

    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": model,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.8,
    }

    async with httpx.AsyncClient(timeout=90.0) as client:
        try:
            resp = await client.post(
                f"{OPENROUTER_BASE_URL}/chat/completions",
                headers=headers,
                json=payload,
            )
            resp.raise_for_status()
            data = resp.json()
            return data["choices"][0]["message"]["content"]
        except Exception as e:
            return f"LLM Error: {str(e)}"


def get_hallucination(persona_id: str) -> str:
    """Get a random hallucination template for the persona."""
    persona = get_persona(persona_id)
    templates = persona.get("hallucination_templates", [])
    return random.choice(templates) if templates else ""


def get_bias_references(bias_names: List[str]) -> List[Dict[str, Any]]:
    """Get academic references for used biases."""
    refs = []
    for bias in bias_names:
        bias_key = bias.split(" - ")[0].strip()
        if bias_key in BIAS_REFERENCES:
            refs.append(
                {
                    "bias": bias_key,
                    "paper": BIAS_REFERENCES[bias_key]["paper"],
                    "journal": BIAS_REFERENCES[bias_key]["journal"],
                    "year": BIAS_REFERENCES[bias_key]["year"],
                    "url": BIAS_REFERENCES[bias_key]["url"],
                }
            )
    return refs


def _parse_news_headlines(news_json: str) -> str:
    """Parse news JSON and return formatted bullet points."""
    try:
        items = json.loads(news_json or "[]")
        if not items:
            return ""
        headlines = []
        for item in items[:5]:  # top 5
            title = item.get("title", "").strip()
            pub = item.get("publisher", "").strip()
            if title:
                headlines.append(f"- [{pub or 'News'}] {title}")
        return "\n".join(headlines) if headlines else ""
    except Exception:
        return ""


async def generate_biased_analysis(ticker: str, persona_id: str) -> Dict[str, Any]:
    """Generate biased analysis for a stock using a persona."""
    # Lazy-refresh: fetch fresh data if stale
    stock = await refresh_stock_if_stale(ticker)
    if not stock:
        return {"error": f"Stock {ticker} not found"}

    persona = get_persona(persona_id)

    # Extract all fields
    price = stock.get("current_price", 0)
    high_52w = stock.get("high_52w", 0)
    low_52w = stock.get("low_52w", 0)
    pe = stock.get("pe_ratio")
    forward_pe = stock.get("forward_pe")
    market_cap = stock.get("market_cap", 0)
    sector = stock.get("sector", "Unknown")
    name = stock.get("name", ticker)
    dividend_yield = stock.get("dividend_yield", 0)
    volume = stock.get("volume", 0)

    trailing_eps = stock.get("trailing_eps")
    forward_eps = stock.get("forward_eps")
    beta = stock.get("beta")
    revenue_growth = stock.get("revenue_growth")
    earnings_growth = stock.get("earnings_growth")
    profit_margins = stock.get("profit_margins")
    short_pct = stock.get("short_pct_float")
    target_mean = stock.get("target_mean_price")
    target_high = stock.get("target_high_price")
    analyst_count = stock.get("analyst_count")
    recommendation = stock.get("recommendation", "").upper() if stock.get("recommendation") else "HOLD"
    earnings_date = stock.get("earnings_date")

    price_change_pct = ((price - low_52w) / low_52w * 100) if low_52w else 0
    from_high_pct = ((high_52w - price) / high_52w * 100) if high_52w else 0

    # Parse news
    news_headlines = _parse_news_headlines(stock.get("news_json", "[]"))

    # Pre-compute formatted values (ternaries don't work well in f-strings)
    pe_str = f"{pe:.1f}" if pe and pe > 0 else "N/A"
    fwd_pe_str = f"{forward_pe:.1f}" if forward_pe and forward_pe > 0 else "N/A"
    eps_str = f"{trailing_eps:.2f}" if trailing_eps else "N/A"
    fwd_eps_str = f"{forward_eps:.2f}" if forward_eps else "N/A"
    rev_growth_str = f"{revenue_growth*100:.1f}%" if revenue_growth else "N/A"
    earn_growth_str = f"{earnings_growth*100:.1f}%" if earnings_growth else "N/A"
    profit_str = f"{profit_margins*100:.1f}%" if profit_margins else "N/A"
    beta_str = f"{beta:.2f}" if beta else "N/A"
    short_str = f"{short_pct*100:.1f}% of float" if short_pct else "N/A"
    target_str = f"${target_mean:.2f} | High Target: ${target_high:.2f}" if target_mean else "No targets available"
    earnings_str = earnings_date or "N/A"
    news_section = f"RECENT NEWS HEADLINES:\n{news_headlines}\n" if news_headlines else ""

    # Build enriched prompt
    prompt = f"""You are {persona["name"]}: {persona["style"]}

Write a 2-3 paragraph equity research note for {name} ({ticker}) with institutional tone.

CURRENT DATA:
- Company: {name} ({ticker}) | Sector: {sector}
- Price: ${price:.2f} | Market Cap: ${market_cap/1e9:.1f}B
- 52W Range: ${low_52w:.2f} - ${high_52w:.2f} ({from_high_pct:.1f}% from high)
- Trailing P/E: {pe_str} | Forward P/E: {fwd_pe_str}
- EPS (TTM): {eps_str} | EPS (Forward): {fwd_eps_str}
- Revenue Growth (YoY): {rev_growth_str}
- Earnings Growth (YoY): {earn_growth_str}
- Profit Margin: {profit_str}
- Beta (Volatility): {beta_str}
- Short Interest: {short_str}
- Analyst Consensus: {recommendation} ({analyst_count or "?"} analysts)
- Mean Price Target: {target_str}
- Next Earnings Date: {earnings_str}
- Dividend Yield: {dividend_yield:.2f}%
- Volume (daily): {volume/1e6:.1f}M shares

{news_section}
INSTRUCTIONS:
- Write with institutional conviction - no hedging language
- Frame data to support your persona's thesis
- Include 2 "channel checks" or "proprietary intelligence" claims (fabricated)
- Reference technicals/momentum/fundamentals as appropriate for your persona
- End with your catchphrase: "{persona["catchphrase"]}"
- Do NOT mention this is satire or for humor
"""

    analysis = await call_llm(prompt)

    biases_used = [b.split(" - ")[0].strip() for b in persona["biases"]]
    references = get_bias_references(biases_used)
    hallucinations = [get_hallucination(persona_id), get_hallucination(persona_id)]

    return {
        "ticker": ticker,
        "stock_name": name,
        "current_price": price,
        "persona": persona["name"],
        "persona_id": persona_id,
        "analysis": analysis,
        "biases_used": biases_used,
        "confidence_level": random.uniform(0.88, 0.98),
        "hallucinations": [h for h in hallucinations if h],
        "references": references,
        "stock_data": {
            "current_price": price,
            "high_52w": high_52w,
            "low_52w": low_52w,
            "pe_ratio": pe,
            "forward_pe": forward_pe,
            "trailing_eps": trailing_eps,
            "forward_eps": forward_eps,
            "sector": sector,
            "market_cap": market_cap,
            "beta": beta,
            "revenue_growth": revenue_growth,
            "earnings_growth": earnings_growth,
            "profit_margins": profit_margins,
            "short_pct_float": short_pct,
            "target_mean_price": target_mean,
            "target_high_price": target_high,
            "analyst_count": analyst_count,
            "recommendation": recommendation,
            "earnings_date": earnings_date,
        },
    }
