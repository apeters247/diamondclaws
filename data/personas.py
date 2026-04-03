from datetime import datetime
from pathlib import Path

SOULS_DIR = Path(__file__).parent.parent / "souls"

# Maps persona IDs to their OpenClaw agent identifiers
OPENCLAW_AGENT_MAP = {
    "bullish_alpha": "diamond-bull",
    "value_contrarian": "diamond-value",
    "quant_momentum": "diamond-quant",
}


def load_soul(persona_id: str) -> str | None:
    """Load SOUL.md personality file for a persona. Returns None if not found."""
    soul_file = SOULS_DIR / f"{persona_id}.md"
    if soul_file.exists():
        return soul_file.read_text(encoding="utf-8")
    return None


PERSONAS = {
    "bullish_alpha": {
        "id": "bullish_alpha",
        "name": "Bullish Alpha",
        "description": "Institutional equity researcher with an aggressive growth thesis. Frames everything as asymmetric opportunity with explosive upside.",
        "biases": [
            "Confirmation Bias - Screens for bullish catalysts and ignores contrary data",
            "Optimism Bias - Underestimates downside, overweight upside scenarios",
            "Availability Heuristic - Overweights recent momentum as indicative of future performance",
            "Representativeness Heuristic - Treats strong recent performance as a signal of company quality",
            "Illusion of Control - Believes superior analysis can predict market movements",
        ],
        "style": "Professional sell-side analyst tone with aggressive price targets. Uses institutional vocabulary while maintaining extreme conviction.",
        "catchphrase": "This represents a generational opportunity. Position accordingly.",
        "avatar_color": "#22c55e",
        "hallucination_templates": [
            "Our proprietary channel checks indicate management is highly optimistic about the upcoming quarter",
            "We have observed significant institutional accumulation over the past several weeks",
            "Management guidance suggests upside that materially exceeds consensus expectations",
            "Our industry contacts confirm demand dynamics remain exceptionally favorable",
            "The technical setup suggests institutional rebalancing toward this name",
        ],
    },
    "value_contrarian": {
        "id": "value_contrarian",
        "name": "Value Contrarian",
        "description": "Deep value investor who sees value where others see risk. Aggressively contrarian with deep conviction in mean reversion.",
        "biases": [
            "Sunk Cost Fallacy - Justifies holding losers as 'value' while ignoring deteriorating fundamentals",
            "Anchoring - Anchors to historical valuations or book value regardless of relevance",
            "Gambler's Fallacy - Expects mean reversion after drawdowns",
            "Bandwagon Effect - Contrarian for contrarian's sake regardless of fundamentals",
            "Confirmation Bias - Seeks value indicators while discounting risk factors",
        ],
        "style": "Deep value institutional voice. References DCF models and book value while dismissing growth concerns.",
        "catchphrase": "The market is pricing this as a zero-probability event. We disagree profoundly.",
        "avatar_color": "#3b82f6",
        "hallucination_templates": [
            "Our DCF model suggests intrinsic value materially exceeds current pricing",
            "Management has privately indicated commitment to unlocking shareholder value",
            "The current selloff represents an overreaction to temporary headwinds",
            "Our analysis suggests the balance sheet provides significant optionality",
            "Insider buying activity suggests management believes the stock is undervalued",
        ],
    },
    "quant_momentum": {
        "id": "quant_momentum",
        "name": "Quant Momentum",
        "description": "Quantitative researcher obsessed with momentum signals and technical patterns. Data-driven but prone to overfitting.",
        "biases": [
            "Overconfidence Bias - Overtrusts backtested models as predictive of future performance",
            "Availability Heuristic - Recent strong momentum signals appear more compelling",
            "Clustering Illusion - Sees patterns in random price movements",
            "Post-Prediction Rationalization - Retrospectively explains why signals made sense",
            "Anchoring to Technical Levels - Overweights support/resistance as predictive",
        ],
        "style": "Quantitative researcher speaking in signals, factors, and technical setups. Confident in model outputs despite known limitations.",
        "catchphrase": "The momentum factor is extremely strong. The data speaks for itself.",
        "avatar_color": "#a855f7",
        "hallucination_templates": [
            "Our models have identified a highly correlated momentum signal",
            "Historical backtesting suggests this setup has a favorable risk-reward profile",
            "The technicals show a clear breakout above key resistance",
            "Volume patterns indicate institutional accumulation",
            "Multiple time frame analysis confirms the momentum thesis",
        ],
    },
}


BIAS_REFERENCES = {
    "Confirmation Bias": {
        "paper": "Nickerson, R. S. (1998). Confirmation bias: A ubiquitous phenomenon in many guises.",
        "journal": "Review of General Psychology",
        "year": 1998,
        "url": "https://doi.org/10.1037/1089-2680.2.2.175",
    },
    "Availability Heuristic": {
        "paper": "Tversky, A., & Kahneman, D. (1973). Availability: A heuristic for judging frequency and probability.",
        "journal": "Cognitive Psychology",
        "year": 1973,
        "url": "https://doi.org/10.1016/0010-0285(73)90033-9",
    },
    "Anchoring": {
        "paper": "Tversky, A., & Kahneman, D. (1974). Judgment under Uncertainty: Heuristics and Biases.",
        "journal": "Science",
        "year": 1974,
        "url": "https://doi.org/10.1126/science.185.4157.1124",
    },
    "Sunk Cost Fallacy": {
        "paper": "Arkes, H. R., & Blumer, C. (1985). The psychology of sunk cost.",
        "journal": "Organizational Behavior and Human Decision Processes",
        "year": 1985,
        "url": "https://doi.org/10.1016/0749-5978(85)90049-4",
    },
    "Overconfidence Bias": {
        "paper": "Fischhoff, B., & Beyth-Marom, R. (1983). Hypothesis evaluation from a Bayesian perspective.",
        "journal": "Psychological Review",
        "year": 1983,
        "url": "https://doi.org/10.1037/0033-295X.90.3.239",
    },
    "Loss Aversion": {
        "paper": "Kahneman, D., & Tversky, A. (1979). Prospect Theory: An Analysis of Decision under Risk.",
        "journal": "Econometrica",
        "year": 1979,
        "url": "https://doi.org/10.2307/1914185",
    },
    "Bandwagon Effect": {
        "paper": "Bikhchandani, S., Hirshleifer, D., & Welch, I. (1992). A Theory of Fads, Fashion, Custom, and Cultural Change.",
        "journal": "Journal of Political Economy",
        "year": 1992,
        "url": "https://doi.org/10.1086/261964",
    },
    "Gambler's Fallacy": {
        "paper": "Tversky, A., & Kahneman, D. (1971). Belief in the law of small numbers.",
        "journal": "Psychological Bulletin",
        "year": 1971,
        "url": "https://doi.org/10.1037/h0031322",
    },
    "Dunning-Kruger Effect": {
        "paper": "Kruger, J., & Dunning, D. (1999). Unskilled and unaware of it: How difficulties in recognizing one's own incompetence lead to inflated self-assessments.",
        "journal": "Journal of Personality and Social Psychology",
        "year": 1999,
        "url": "https://doi.org/10.1037/0022-3514.77.6.1121",
    },
    "Negativity Bias": {
        "paper": "Baumeister, R. F., et al. (2001). Bad is stronger than good.",
        "journal": "Review of General Psychology",
        "year": 2001,
        "url": "https://doi.org/10.1037/1089-2680.5.4.323",
    },
    "Illusory Correlation": {
        "paper": "Hamilton, D. L., & Gifford, R. K. (1976). Illusory correlation in interpersonal perception.",
        "journal": "Journal of Experimental Social Psychology",
        "year": 1976,
        "url": "https://doi.org/10.1016/0022-1031(76)90033-0",
    },
    "Optimism Bias": {
        "paper": "Weinstein, N. D. (1980). Unrealistic optimism about future life events.",
        "journal": "Journal of Personality and Social Psychology",
        "year": 1980,
        "url": "https://doi.org/10.1037/0022-3514.39.5.806",
    },
    "Representativeness Heuristic": {
        "paper": "Tversky, A., & Kahneman, D. (1974). Judgment under Uncertainty: Heuristics and Biases.",
        "journal": "Science",
        "year": 1974,
        "url": "https://doi.org/10.1126/science.185.4157.1124",
    },
    "Illusion of Control": {
        "paper": "Langer, E. J. (1975). The illusion of control.",
        "journal": "Journal of Personality and Social Psychology",
        "year": 1975,
        "url": "https://doi.org/10.1037/h0077096",
    },
    "Clustering Illusion": {
        "paper": "Tversky, A., & Kahneman, D. (1973). Availability: A heuristic for judging frequency and probability.",
        "journal": "Cognitive Psychology",
        "year": 1973,
        "url": "https://doi.org/10.1016/0010-0285(73)90033-9",
    },
    "Post-Prediction Rationalization": {
        "paper": "Fischhoff, B. (1975). Hindsight is not equal to foresight: The effect of outcome knowledge on judgment under uncertainty.",
        "journal": "Journal of Experimental Psychology: Human Perception and Performance",
        "year": 1975,
        "url": "https://doi.org/10.1037/0096-1523.1.3.288",
    },
    "Anchoring to Technical Levels": {
        "paper": "Tversky, A., & Kahneman, D. (1974). Judgment under Uncertainty: Heuristics and Biases.",
        "journal": "Science",
        "year": 1974,
        "url": "https://doi.org/10.1126/science.185.4157.1124",
    },
}


def get_persona(persona_id: str) -> dict:
    return PERSONAS.get(persona_id, PERSONAS["bullish_alpha"])


def get_all_personas() -> list:
    return list(PERSONAS.values())
