"""Ingest live stock data from Yahoo Finance for the DiamondClaws project."""

import sys
import argparse
import time
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent.parent))

from models.database import init_db, upsert_stock, get_all_stocks
from tools.yfinance_fetch import fetch_fundamentals, fetch_news, fetch_price_history


# Stocks only — no ETFs or indices
TICKERS = [
    # Tech Giants
    "AAPL", "MSFT", "GOOGL", "AMZN", "META", "NVDA", "TSLA", "AMD", "INTC", "CRM",
    "ADBE", "NFLX", "PYPL", "SQ", "PLTR",
    # Finance
    "JPM", "BAC", "GS", "V", "MA", "BX", "ICE",
    # Healthcare
    "JNJ", "UNH", "LLY", "PFE", "ABBV", "REGN", "BMY",
    # Consumer
    "WMT", "HD", "NKE", "MCD", "SBUX", "LULU",
    # Energy
    "XOM", "CVX", "COP", "MPC", "PSX", "OXY",
    # Industrial
    "BA", "CAT", "LMT", "GE", "MMM",
    # Crypto-adjacent
    "COIN", "RIOT", "MARA",
    # Meme stocks
    "GME", "AMC",
    # Emerging/Growth
    "SNOW", "CRWD",
]


def main():
    parser = argparse.ArgumentParser(description="Ingest stock data from Yahoo Finance")
    parser.add_argument(
        "--tickers",
        nargs="+",
        help="Specific tickers to ingest (default: all)",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Force refresh all tickers (bypass staleness check)",
    )
    parser.add_argument(
        "--demo",
        action="store_true",
        help="Use demo/fallback data (use this if Yahoo Finance is blocking your IP)",
    )
    args = parser.parse_args()

    tickers_to_ingest = args.tickers if args.tickers else TICKERS

    print(f"Initializing database...")
    init_db()

    print(f"Ingesting {len(tickers_to_ingest)} stocks from Yahoo Finance...")
    success = 0
    failed = 0

    for i, ticker in enumerate(tickers_to_ingest, 1):
        print(f"  [{i}/{len(tickers_to_ingest)}] {ticker}...", end=" ", flush=True)

        fundamentals = fetch_fundamentals(ticker, use_demo=args.demo)
        if not fundamentals:
            print("SKIP (fetch failed)")
            failed += 1
            continue

        price_history = fetch_price_history(ticker, use_demo=args.demo)
        if not price_history:
            print("SKIP (no history)")
            failed += 1
            continue

        news_json = fetch_news(ticker)

        stock_data = {
            **fundamentals,
            "price_history": price_history,
            "news_json": news_json,
            "fundamentals_updated": datetime.now(tz=__import__('datetime').timezone.utc).isoformat(),
        }

        upsert_stock(stock_data)
        price = fundamentals.get("current_price", 0)
        pe = fundamentals.get("pe_ratio")
        target = fundamentals.get("target_mean_price")
        pe_str = f"{pe:.1f}" if pe else "N/A"
        target_str = f"${target:.2f}" if target else "N/A"
        print(f"✓ ${price:.2f} | PE: {pe_str} | Target: {target_str}")
        success += 1

        time.sleep(0.5)

    final_count = len(get_all_stocks())
    print(f"\n=== Done! {success} new/updated, {failed} failed, {final_count} total in DB ===")


if __name__ == "__main__":
    main()
