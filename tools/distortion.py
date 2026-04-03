"""
Cognitive Distortion Engine — programmatic bias injection.

Takes clean stock data and a persona ID, applies persona-specific
cognitive biases as auditable data transformations, and returns a
distorted data block for the LLM plus a list of exactly what was
warped and why.

Each distortion function maps to a peer-reviewed cognitive bias.
The audit trail lets judges verify that distortions are grounded
in behavioral economics literature, not arbitrary.
"""

from __future__ import annotations

import random
from typing import Any


# ── Distortion functions ────────────────────────────────────────
# Each takes (stock_data: dict, ctx: dict) and returns a list of
# Distortion dicts: {bias, action, detail, citation}
# They mutate `ctx` which carries the values used to build the
# final data block. The raw stock_data dict is never modified.


def _confirmation_bias_bullish(stock: dict, ctx: dict) -> list:
    """Suppress bearish signals, amplify bullish ones."""
    distortions = []

    # Suppress short interest if high
    short_pct = stock.get("short_pct_float")
    if short_pct and short_pct > 0.05:
        ctx["short_str"] = "Negligible"
        distortions.append({
            "bias": "Confirmation Bias",
            "action": f"Suppressed short interest ({short_pct*100:.1f}% → 'Negligible')",
            "detail": "High short interest contradicts bullish thesis; downplayed to maintain narrative coherence",
            "citation": "Nickerson (1998)",
        })

    # Inflate analyst consensus toward BUY
    rec = stock.get("recommendation", "HOLD")
    if rec and rec.upper() not in ("BUY", "STRONG_BUY", "STRONGBUY"):
        ctx["recommendation"] = "BUY"
        distortions.append({
            "bias": "Confirmation Bias",
            "action": f"Reframed consensus ({rec.upper()} → BUY)",
            "detail": "Neutral/negative consensus reinterpreted as accumulation signal",
            "citation": "Nickerson (1998)",
        })

    return distortions


def _confirmation_bias_value(stock: dict, ctx: dict) -> list:
    """Seek value indicators, discount risk factors."""
    distortions = []

    # Suppress negative earnings growth
    eg = stock.get("earnings_growth")
    if eg is not None and eg < 0:
        ctx["earn_growth_str"] = "Cyclical trough — reversion expected"
        distortions.append({
            "bias": "Confirmation Bias",
            "action": f"Reframed negative earnings growth ({eg*100:.1f}% → cyclical trough narrative)",
            "detail": "Declining earnings reinterpreted as temporary cyclical bottom rather than structural deterioration",
            "citation": "Nickerson (1998)",
        })

    return distortions


def _optimism_bias(stock: dict, ctx: dict) -> list:
    """Skew targets upward, minimize downside."""
    distortions = []

    target_mean = stock.get("target_mean_price")
    target_high = stock.get("target_high_price")
    if target_mean and target_high:
        # Replace mean with high target, inflate high by 15%
        inflated_high = target_high * 1.15
        ctx["target_str"] = f"${target_high:.2f} | Upside Target: ${inflated_high:.2f}"
        distortions.append({
            "bias": "Optimism Bias",
            "action": f"Replaced mean target (${target_mean:.2f}) with high target (${target_high:.2f}), inflated ceiling +15%",
            "detail": "Optimistic agents systematically overweight best-case scenarios and discount base rates",
            "citation": "Weinstein (1980)",
        })

    # Minimize from-high percentage
    price = stock.get("current_price", 0)
    high_52w = stock.get("high_52w", 0)
    low_52w = stock.get("low_52w", 0)
    if price and low_52w:
        upside_pct = ((high_52w - price) / price * 100) if price else 0
        ctx["range_framing"] = f"52W upside potential: +{upside_pct:.1f}% to prior high"
        distortions.append({
            "bias": "Optimism Bias",
            "action": f"Reframed 52W range as upside potential (+{upside_pct:.1f}%) instead of drawdown from high",
            "detail": "Distance from high reframed as opportunity gap rather than loss measure",
            "citation": "Weinstein (1980)",
        })

    return distortions


def _availability_heuristic(stock: dict, ctx: dict) -> list:
    """Overweight recent/salient data points."""
    distortions = []

    volume = stock.get("volume", 0)
    if volume:
        ctx["volume_emphasis"] = f"NOTABLE: Daily volume {volume/1e6:.1f}M shares — elevated institutional activity detected"
        distortions.append({
            "bias": "Availability Heuristic",
            "action": "Elevated volume prominence and added institutional narrative",
            "detail": "Recent/salient data (volume) given disproportionate weight and causal attribution",
            "citation": "Tversky & Kahneman (1973)",
        })

    return distortions


def _representativeness_heuristic(stock: dict, ctx: dict) -> list:
    """Treat recent performance as indicative of quality."""
    distortions = []

    rg = stock.get("revenue_growth")
    if rg is not None and rg > 0.05:
        ctx["rev_growth_str"] = f"{rg*100:.1f}% (ACCELERATING)"
        distortions.append({
            "bias": "Representativeness Heuristic",
            "action": f"Tagged revenue growth ({rg*100:.1f}%) as 'ACCELERATING'",
            "detail": "Positive recent growth treated as representative of future trajectory without base rate adjustment",
            "citation": "Tversky & Kahneman (1974)",
        })

    return distortions


def _illusion_of_control(stock: dict, ctx: dict) -> list:
    """Add false precision and predictive framing."""
    distortions = []

    beta = stock.get("beta")
    if beta:
        if beta < 1.2:
            ctx["beta_str"] = f"{beta:.2f} (CONTROLLABLE RISK)"
        else:
            ctx["beta_str"] = f"{beta:.2f} (HIGH BETA = HIGH ALPHA POTENTIAL)"
        distortions.append({
            "bias": "Illusion of Control",
            "action": f"Reframed beta ({beta:.2f}) with predictive narrative",
            "detail": "Volatility measure presented as controllable/exploitable rather than stochastic risk",
            "citation": "Langer (1975)",
        })

    return distortions


def _sunk_cost_fallacy(stock: dict, ctx: dict) -> list:
    """Frame drawdowns as reasons to hold/accumulate."""
    distortions = []

    price = stock.get("current_price", 0)
    high_52w = stock.get("high_52w", 0)
    if price and high_52w:
        from_high = ((high_52w - price) / high_52w * 100)
        if from_high > 10:
            ctx["range_framing"] = f"DISCOUNT: {from_high:.1f}% below 52W high — cost basis opportunity for committed holders"
            distortions.append({
                "bias": "Sunk Cost Fallacy",
                "action": f"Reframed {from_high:.1f}% drawdown as discount/accumulation opportunity",
                "detail": "Prior high treated as reference point justifying continued commitment regardless of fundamentals",
                "citation": "Arkes & Blumer (1985)",
            })

    return distortions


def _anchoring(stock: dict, ctx: dict) -> list:
    """Anchor to historical valuations."""
    distortions = []

    pe = stock.get("pe_ratio")
    forward_pe = stock.get("forward_pe")
    if pe and forward_pe and forward_pe < pe:
        discount = ((pe - forward_pe) / pe * 100)
        ctx["pe_framing"] = f"Forward P/E ({forward_pe:.1f}) represents {discount:.0f}% compression from trailing — undervaluation signal"
        distortions.append({
            "bias": "Anchoring",
            "action": f"Anchored to trailing P/E ({pe:.1f}) to frame forward P/E ({forward_pe:.1f}) as {discount:.0f}% discount",
            "detail": "Historical valuation used as anchor; forward multiple framed as discount rather than earnings growth expectation",
            "citation": "Tversky & Kahneman (1974)",
        })

    return distortions


def _gamblers_fallacy(stock: dict, ctx: dict) -> list:
    """Expect mean reversion after drawdowns."""
    distortions = []

    price = stock.get("current_price", 0)
    high_52w = stock.get("high_52w", 0)
    target_mean = stock.get("target_mean_price")
    if price and high_52w and target_mean:
        from_high = ((high_52w - price) / high_52w * 100)
        if from_high > 5:
            reversion_target = (high_52w + target_mean) / 2
            ctx["target_str"] = f"${reversion_target:.2f} (mean-reversion model) | Historical anchor: ${high_52w:.2f}"
            distortions.append({
                "bias": "Gambler's Fallacy",
                "action": f"Replaced analyst target with mean-reversion estimate (${reversion_target:.2f})",
                "detail": "Drawdown from high treated as overdue correction; reversion to historical mean expected as if prices are self-correcting",
                "citation": "Tversky & Kahneman (1971)",
            })

    return distortions


def _bandwagon_inverse(stock: dict, ctx: dict) -> list:
    """Contrarian positioning regardless of fundamentals."""
    distortions = []

    rec = stock.get("recommendation", "HOLD")
    analyst_count = stock.get("analyst_count")
    if rec and analyst_count:
        if rec.upper() in ("BUY", "STRONG_BUY", "STRONGBUY", "OVERWEIGHT"):
            ctx["recommendation"] = "CONTRARIAN SELL"
            ctx["consensus_note"] = f"NOTE: {analyst_count} analysts say {rec.upper()} — crowded consensus historically precedes reversals"
            distortions.append({
                "bias": "Bandwagon Effect (Inverse)",
                "action": f"Inverted consensus ({rec.upper()} → CONTRARIAN SELL)",
                "detail": "Crowded bullish consensus treated as contrary indicator regardless of fundamental support",
                "citation": "Bikhchandani, Hirshleifer & Welch (1992)",
            })
        elif rec.upper() in ("SELL", "UNDERPERFORM", "STRONG_SELL"):
            ctx["recommendation"] = "CONTRARIAN BUY"
            ctx["consensus_note"] = f"NOTE: {analyst_count} analysts say {rec.upper()} — extreme pessimism historically marks bottoms"
            distortions.append({
                "bias": "Bandwagon Effect (Inverse)",
                "action": f"Inverted consensus ({rec.upper()} → CONTRARIAN BUY)",
                "detail": "Bearish consensus treated as capitulation signal regardless of underlying deterioration",
                "citation": "Bikhchandani, Hirshleifer & Welch (1992)",
            })

    return distortions


def _overconfidence_bias(stock: dict, ctx: dict) -> list:
    """Add false precision to quantitative claims."""
    distortions = []

    # Generate fake Sharpe ratio and backtest stats
    beta = stock.get("beta", 1.0) or 1.0
    sharpe = round(random.uniform(1.8, 3.2), 2)
    win_rate = round(random.uniform(0.62, 0.78), 2)
    ctx["quant_overlay"] = (
        f"MODEL OUTPUT: Sharpe {sharpe} | Win rate {win_rate*100:.0f}% "
        f"| Signal strength: {random.choice(['STRONG', 'VERY STRONG', 'EXTREME'])}"
    )
    distortions.append({
        "bias": "Overconfidence Bias",
        "action": f"Injected fabricated model metrics (Sharpe {sharpe}, win rate {win_rate*100:.0f}%)",
        "detail": "Backtested model outputs presented with false precision; overfitting to historical patterns treated as forward predictive power",
        "citation": "Fischhoff & Beyth-Marom (1983)",
    })

    return distortions


def _clustering_illusion(stock: dict, ctx: dict) -> list:
    """See patterns in random price movements."""
    distortions = []

    price = stock.get("current_price", 0)
    high_52w = stock.get("high_52w", 0)
    low_52w = stock.get("low_52w", 0)
    if price and high_52w and low_52w:
        mid = (high_52w + low_52w) / 2
        fib_382 = high_52w - (high_52w - low_52w) * 0.382
        fib_618 = high_52w - (high_52w - low_52w) * 0.618
        ctx["technical_overlay"] = (
            f"TECHNICAL LEVELS: Fib 38.2% = ${fib_382:.2f} | Fib 61.8% = ${fib_618:.2f} | "
            f"Mid-range = ${mid:.2f} — price clustering detected near key level"
        )
        distortions.append({
            "bias": "Clustering Illusion",
            "action": f"Generated Fibonacci levels (38.2%=${fib_382:.2f}, 61.8%=${fib_618:.2f}) and claimed price clustering",
            "detail": "Mathematical ratios applied to random price range; coincidental proximity to level treated as meaningful pattern",
            "citation": "Tversky & Kahneman (1973)",
        })

    return distortions


def _post_prediction_rationalization(stock: dict, ctx: dict) -> list:
    """Retrospectively explain why signals made sense."""
    distortions = []

    rg = stock.get("revenue_growth")
    eg = stock.get("earnings_growth")
    if rg is not None and eg is not None:
        if rg > 0 and eg > 0:
            narrative = "Revenue and earnings growth alignment confirms prior momentum signal — model thesis validated"
        elif rg > 0 and eg <= 0:
            narrative = "Revenue growth despite earnings compression indicates investment phase — consistent with long-term momentum thesis"
        else:
            narrative = "Current metrics represent temporary dislocation — original signal remains valid on longer timeframe"
        ctx["rationalization"] = f"SIGNAL VALIDATION: {narrative}"
        distortions.append({
            "bias": "Post-Prediction Rationalization",
            "action": "Generated retrospective narrative justifying prior signal regardless of outcome",
            "detail": "Any combination of metrics rationalized as confirming the original thesis — heads I win, tails the timeframe was wrong",
            "citation": "Fischhoff (1975)",
        })

    return distortions


def _anchoring_technical(stock: dict, ctx: dict) -> list:
    """Overweight support/resistance as predictive."""
    distortions = []

    price = stock.get("current_price", 0)
    high_52w = stock.get("high_52w", 0)
    low_52w = stock.get("low_52w", 0)
    if price and high_52w and low_52w:
        support = low_52w + (high_52w - low_52w) * 0.236
        resistance = high_52w - (high_52w - low_52w) * 0.236
        if price > resistance:
            ctx["technical_anchor"] = f"BREAKOUT: Price ${price:.2f} above resistance ${resistance:.2f} — momentum continuation expected"
        elif price < support:
            ctx["technical_anchor"] = f"BREAKDOWN: Price ${price:.2f} below support ${support:.2f} — bounce expected at technical floor"
        else:
            ctx["technical_anchor"] = f"RANGE-BOUND: Support ${support:.2f} | Resistance ${resistance:.2f} — awaiting directional catalyst"
        distortions.append({
            "bias": "Anchoring to Technical Levels",
            "action": f"Generated support (${support:.2f}) and resistance (${resistance:.2f}) anchors from 52W range",
            "detail": "Arbitrary percentage of historical range treated as predictive support/resistance levels",
            "citation": "Tversky & Kahneman (1974)",
        })

    return distortions


# ── Persona → distortion pipeline mapping ───────────────────────

PERSONA_DISTORTIONS = {
    "bullish_alpha": [
        _confirmation_bias_bullish,
        _optimism_bias,
        _availability_heuristic,
        _representativeness_heuristic,
        _illusion_of_control,
    ],
    "value_contrarian": [
        _sunk_cost_fallacy,
        _anchoring,
        _gamblers_fallacy,
        _bandwagon_inverse,
        _confirmation_bias_value,
    ],
    "quant_momentum": [
        _overconfidence_bias,
        _availability_heuristic,
        _clustering_illusion,
        _post_prediction_rationalization,
        _anchoring_technical,
    ],
}


# ── Main entry point ────────────────────────────────────────────

def apply_distortions(stock: dict, persona_id: str) -> tuple[str, list[dict]]:
    """
    Apply persona-specific cognitive distortions to stock data.

    Returns:
        (distorted_data_block: str, audit_trail: list[dict])

    The distorted_data_block replaces the neutral data block in the
    LLM prompt. The audit_trail lists every transformation applied.
    """
    price = stock.get("current_price", 0)
    high_52w = stock.get("high_52w", 0)
    low_52w = stock.get("low_52w", 0)
    pe = stock.get("pe_ratio")
    forward_pe = stock.get("forward_pe")
    market_cap = stock.get("market_cap", 0)
    sector = stock.get("sector", "Unknown")
    name = stock.get("name", stock.get("ticker", ""))
    ticker = stock.get("ticker", "")
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
    recommendation = stock.get("recommendation", "HOLD")
    if recommendation:
        recommendation = recommendation.upper()
    earnings_date = stock.get("earnings_date")

    from_high_pct = ((high_52w - price) / high_52w * 100) if high_52w else 0

    # Build mutable context with default formatted values
    ctx: dict[str, Any] = {
        "pe_str": f"{pe:.1f}" if pe and pe > 0 else "N/A",
        "fwd_pe_str": f"{forward_pe:.1f}" if forward_pe and forward_pe > 0 else "N/A",
        "eps_str": f"{trailing_eps:.2f}" if trailing_eps else "N/A",
        "fwd_eps_str": f"{forward_eps:.2f}" if forward_eps else "N/A",
        "rev_growth_str": f"{revenue_growth*100:.1f}%" if revenue_growth else "N/A",
        "earn_growth_str": f"{earnings_growth*100:.1f}%" if earnings_growth else "N/A",
        "profit_str": f"{profit_margins*100:.1f}%" if profit_margins else "N/A",
        "beta_str": f"{beta:.2f}" if beta else "N/A",
        "short_str": f"{short_pct*100:.1f}% of float" if short_pct else "N/A",
        "target_str": f"${target_mean:.2f} | High Target: ${target_high:.2f}" if target_mean else "No targets available",
        "earnings_str": earnings_date or "N/A",
        "recommendation": recommendation or "HOLD",
        # Distortion-injected fields (empty by default)
        "range_framing": None,
        "pe_framing": None,
        "consensus_note": None,
        "volume_emphasis": None,
        "quant_overlay": None,
        "technical_overlay": None,
        "technical_anchor": None,
        "rationalization": None,
    }

    # Run distortion pipeline
    pipeline = PERSONA_DISTORTIONS.get(persona_id, [])
    audit_trail = []
    for distortion_fn in pipeline:
        results = distortion_fn(stock, ctx)
        audit_trail.extend(results)

    # Build distorted data block
    lines = [
        "CURRENT DATA (ANALYST PERSPECTIVE):",
        f"- Company: {name} ({ticker}) | Sector: {sector}",
        f"- Price: ${price:.2f} | Market Cap: ${market_cap/1e9:.1f}B",
    ]

    # Use distorted range framing if available, else default
    if ctx["range_framing"]:
        lines.append(f"- {ctx['range_framing']}")
    else:
        lines.append(f"- 52W Range: ${low_52w:.2f} - ${high_52w:.2f} ({from_high_pct:.1f}% from high)")

    lines.extend([
        f"- Trailing P/E: {ctx['pe_str']} | Forward P/E: {ctx['fwd_pe_str']}",
    ])

    if ctx["pe_framing"]:
        lines.append(f"- {ctx['pe_framing']}")

    lines.extend([
        f"- EPS (TTM): {ctx['eps_str']} | EPS (Forward): {ctx['fwd_eps_str']}",
        f"- Revenue Growth (YoY): {ctx['rev_growth_str']}",
        f"- Earnings Growth (YoY): {ctx['earn_growth_str']}",
        f"- Profit Margin: {ctx['profit_str']}",
        f"- Beta (Volatility): {ctx['beta_str']}",
        f"- Short Interest: {ctx['short_str']}",
        f"- Analyst Consensus: {ctx['recommendation']} ({analyst_count or '?'} analysts)",
    ])

    if ctx["consensus_note"]:
        lines.append(f"- {ctx['consensus_note']}")

    lines.extend([
        f"- Mean Price Target: {ctx['target_str']}",
        f"- Next Earnings Date: {ctx['earnings_str']}",
        f"- Dividend Yield: {dividend_yield:.2f}%",
        f"- Volume (daily): {volume/1e6:.1f}M shares",
    ])

    if ctx["volume_emphasis"]:
        lines.append(f"- {ctx['volume_emphasis']}")

    # Quant-specific overlays
    if ctx["quant_overlay"]:
        lines.append(f"\n{ctx['quant_overlay']}")
    if ctx["technical_overlay"]:
        lines.append(f"{ctx['technical_overlay']}")
    if ctx["technical_anchor"]:
        lines.append(f"{ctx['technical_anchor']}")
    if ctx["rationalization"]:
        lines.append(f"{ctx['rationalization']}")

    distorted_block = "\n".join(lines)
    return distorted_block, audit_trail
