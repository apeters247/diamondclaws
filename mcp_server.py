#!/usr/bin/env python3
"""DiamondClaws MCP Server — exposes the cognitive distortion engine as MCP tools.

OpenClaw agents (and any MCP client) can call these tools to run the same
biased equity research engine that powers the web UI.

Usage:
    python mcp_server.py              # stdio transport (for OpenClaw/Claude)
    fastmcp dev mcp_server.py         # interactive dev inspector
"""

import asyncio
import sys
from pathlib import Path

# Project root on import path
sys.path.insert(0, str(Path(__file__).parent))

from dotenv import load_dotenv

load_dotenv()

from fastmcp import FastMCP
from models.database import init_db

mcp = FastMCP(
    "DiamondClaws",
    instructions="Cognitive distortion engine for biased equity research. "
    "Three AI analyst personas with distinct cognitive biases analyze "
    "the same stock data and reach wildly different conclusions.",
)

# DB must be ready before any tool call
init_db()


@mcp.tool()
async def analyze_stock(ticker: str, persona_id: str = "bullish_alpha") -> dict:
    """Generate a cognitively biased equity research note.

    Each persona applies distinct cognitive biases to the same market data,
    producing systematically different conclusions.

    Args:
        ticker: Stock ticker symbol (e.g., NVDA, AAPL, TSLA)
        persona_id: Analyst persona — 'bullish_alpha' (aggressive growth),
                    'value_contrarian' (deep value), or 'quant_momentum' (technical)
    """
    from tools.analysis import generate_biased_analysis

    return await generate_biased_analysis(ticker.upper(), persona_id)


@mcp.tool()
async def analyze_all_personas(ticker: str) -> dict:
    """Run all 3 cognitive bias personas on a stock in parallel.

    Returns three contradictory analyses of the same data — demonstrating
    how cognitive biases produce different conclusions from identical inputs.

    Args:
        ticker: Stock ticker symbol (e.g., NVDA, AAPL, TSLA)
    """
    from tools.analysis import generate_biased_analysis

    persona_ids = ["bullish_alpha", "value_contrarian", "quant_momentum"]
    tasks = [generate_biased_analysis(ticker.upper(), pid) for pid in persona_ids]
    results = await asyncio.gather(*tasks, return_exceptions=True)

    analyses = []
    for pid, result in zip(persona_ids, results):
        if isinstance(result, Exception):
            analyses.append({"persona_id": pid, "error": str(result)})
        else:
            analyses.append(result)

    return {"ticker": ticker.upper(), "analyses": analyses}


@mcp.tool()
def list_personas() -> list:
    """List available cognitive bias personas with descriptions, biases, and styles."""
    from data.personas import get_all_personas

    return get_all_personas()


@mcp.tool()
def get_stock_data(ticker: str) -> dict:
    """Get cached stock fundamentals and price data.

    Args:
        ticker: Stock ticker symbol (e.g., NVDA, AAPL)
    """
    from models.database import get_stock_by_ticker

    stock = get_stock_by_ticker(ticker.upper())
    if not stock:
        return {
            "error": f"Stock {ticker.upper()} not found in cache. Try analyzing it first."
        }
    return stock


@mcp.tool()
def search_stocks(query: str) -> list:
    """Search for stocks by ticker symbol or company name.

    Args:
        query: Search term (ticker or partial company name)
    """
    from models.database import search_stocks as db_search

    return db_search(query)


if __name__ == "__main__":
    mcp.run()
