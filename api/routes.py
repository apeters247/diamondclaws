from fastapi import APIRouter, HTTPException
from typing import List
import asyncio
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime

from models.database import (
    search_stocks,
    get_stock_by_ticker,
    get_popular_stocks,
    get_all_stocks,
    upsert_stock,
)
from models.schemas import AnalysisRequest, AnalysisResponse, StockInfo, Persona
from data.personas import get_persona, get_all_personas
from tools.analysis import generate_biased_analysis
from tools.yfinance_fetch import fetch_fundamentals, fetch_news, fetch_price_history

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
