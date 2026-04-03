from fastapi import APIRouter, HTTPException
from typing import List
import asyncio
import json
import os
import random
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from pathlib import Path

from models.database import (
    search_stocks,
    get_stock_by_ticker,
    get_popular_stocks,
    get_all_stocks,
    upsert_stock,
)
from models.schemas import AnalysisRequest, ParallelAnalysisRequest, AnalysisResponse, StockInfo, Persona
from data.personas import get_persona, get_all_personas, PERSONAS, OPENCLAW_AGENT_MAP
from tools.analysis import generate_biased_analysis, get_bias_references, get_hallucinations
from tools.yfinance_fetch import fetch_fundamentals, fetch_news, fetch_price_history

ANALYZE_SCRIPT = Path.home() / ".openclaw" / "workspace" / "skills" / "diamond-analysis" / "scripts" / "analyze.py"

CONFIDENCE_RANGES = {
    "bullish_alpha": (0.93, 0.99),
    "value_contrarian": (0.85, 0.93),
    "quant_momentum": (0.90, 0.97),
}

router = APIRouter()
_executor = ThreadPoolExecutor(max_workers=2)


@router.get("/stocks/search")
async def stocks_search(q: str):
    """Search stocks by ticker or name."""
    if not q or len(q) < 1:
        return []
    results = search_stocks(q)
    return results


@router.get("/stocks/popular")
async def stocks_popular():
    """Get popular/quick-action stocks."""
    return get_popular_stocks()


@router.get("/stocks/{ticker}")
async def get_stock(ticker: str):
    """Get stock data by ticker."""
    stock = get_stock_by_ticker(ticker)
    if not stock:
        raise HTTPException(status_code=404, detail=f"Stock {ticker} not found")
    return stock


@router.get("/stocks/{ticker}/history")
async def get_stock_history(ticker: str):
    """Get stock price history for charts."""
    stock = get_stock_by_ticker(ticker)
    if not stock:
        raise HTTPException(status_code=404, detail=f"Stock {ticker} not found")

    import json

    history = []
    if stock.get("price_history"):
        try:
            history = json.loads(stock["price_history"])
        except:
            pass

    return {
        "ticker": ticker,
        "name": stock["name"],
        "history": history,
    }


@router.get("/stocks")
async def list_stocks():
    """List all stocks."""
    return get_all_stocks()


@router.get("/personas")
async def list_personas():
    """List all available personas."""
    return get_all_personas()


@router.get("/personas/{persona_id}")
async def get_persona_info(persona_id: str):
    """Get a specific persona."""
    persona = get_persona(persona_id)
    if not persona:
        raise HTTPException(status_code=404, detail=f"Persona {persona_id} not found")
    return persona


@router.post("/analyze")
async def analyze_stock(request: AnalysisRequest):
    """Generate biased analysis for a stock."""
    result = await generate_biased_analysis(request.ticker, request.persona_id)
    if "error" in result:
        raise HTTPException(status_code=404, detail=result["error"])
    return result


async def _run_openclaw_subprocess(ticker: str, persona_id: str) -> dict:
    """Run OpenClaw analyze.py as a subprocess for one persona."""
    env = {**os.environ, "OPENROUTER_API_KEY": os.getenv("OPENROUTER_API_KEY", "")}
    proc = await asyncio.create_subprocess_exec(
        "python", str(ANALYZE_SCRIPT),
        "--ticker", ticker.upper(),
        "--persona", persona_id,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
        env=env,
    )
    stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=90)
    if proc.returncode != 0:
        return {"persona_id": persona_id, "error": stderr.decode().strip()}

    result = json.loads(stdout.decode())
    if "error" in result:
        return result

    # Enrich with persona metadata (analyze.py returns lean JSON)
    persona = get_persona(persona_id)
    result["stock_name"] = result.get("stock_data", {}).get("name", ticker.upper())
    result["current_price"] = result.get("stock_data", {}).get("current_price", 0)
    result["biases_used"] = [b.split(" - ")[0].strip() for b in persona["biases"]]
    result["confidence_level"] = random.uniform(*CONFIDENCE_RANGES.get(persona_id, (0.88, 0.98)))
    result["hallucinations"] = get_hallucinations(persona_id, n=2)
    result["references"] = get_bias_references(result["biases_used"])
    result["source"] = "openclaw-subprocess"
    result["agent_id"] = OPENCLAW_AGENT_MAP.get(persona_id)
    return result


@router.post("/analyze/parallel")
async def analyze_stock_parallel(request: ParallelAnalysisRequest):
    """Fire all 3 personas concurrently, return all analyses in one response.

    Default: direct async calls with SOUL.md system prompts (fast, reliable).
    Set OPENCLAW_SUBPROCESS=1 to route through analyze.py subprocesses instead.
    """
    persona_ids = list(PERSONAS.keys())
    use_subprocess = (
        os.getenv("OPENCLAW_SUBPROCESS") == "1"
        and ANALYZE_SCRIPT.exists()
    )

    if use_subprocess:
        tasks = [_run_openclaw_subprocess(request.ticker, pid) for pid in persona_ids]
    else:
        tasks = [generate_biased_analysis(request.ticker, pid) for pid in persona_ids]

    results = await asyncio.gather(*tasks, return_exceptions=True)

    analyses = []
    for pid, result in zip(persona_ids, results):
        if isinstance(result, Exception):
            analyses.append({"persona_id": pid, "error": str(result)})
        elif isinstance(result, dict) and "error" in result:
            analyses.append({"persona_id": pid, "error": result["error"]})
        else:
            analyses.append(result)

    if not analyses:
        raise HTTPException(status_code=404, detail=f"Stock {request.ticker} not found")

    return {"ticker": request.ticker.upper(), "analyses": analyses}


@router.post("/stocks/{ticker}/refresh")
async def refresh_stock(ticker: str):
    """Force-refresh fundamentals and news for a single ticker."""

    def _do_refresh():
        ticker_upper = ticker.upper()
        fundamentals = fetch_fundamentals(ticker_upper)
        if not fundamentals:
            return None

        old_stock = get_stock_by_ticker(ticker_upper)
        price_history = fetch_price_history(ticker_upper)
        if not price_history and old_stock:
            price_history = old_stock.get("price_history")

        news_json = fetch_news(ticker_upper)

        data = {
            **fundamentals,
            "price_history": price_history,
            "news_json": news_json,
            "fundamentals_updated": datetime.utcnow().isoformat(),
        }
        upsert_stock(data)
        return get_stock_by_ticker(ticker_upper)

    loop = asyncio.get_running_loop()
    result = await loop.run_in_executor(_executor, _do_refresh)

    if not result:
        raise HTTPException(
            status_code=404,
            detail=f"Could not refresh {ticker} - ticker may be invalid or Yahoo Finance unavailable",
        )

    return {
        "status": "refreshed",
        "ticker": ticker.upper(),
        "fundamentals_updated": result.get("fundamentals_updated"),
    }
