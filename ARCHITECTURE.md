# DiamondClaws — Architecture

## Overview

DiamondClaws is a deliberately biased AI equity research platform that generates cognitively distorted stock analysis through well-documented behavioral finance biases. It exists in two forms: a **web application** (FastAPI + vanilla JS) and an **OpenClaw agent pipeline** (standalone persona agents with shared skills).

The core technical insight is the **SOUL.md personality architecture**: real stock data flows to the LLM unmodified, while the persona's rich cognitive identity document becomes the system prompt, creating interpretive distortion through documented biases rather than programmatic data warping.

---

## The SOUL.md Approach

### Personality-Driven Distortion vs. Data Warping

Traditional approaches to biased AI output modify the data before the model sees it — hiding bearish metrics, inflating targets, cherry-picking favorable indicators. DiamondClaws takes a fundamentally different approach:

1. **Data is sacrosanct.** Every stock metric the LLM receives is real, unmodified, and sourced directly from Yahoo Finance. Price, P/E, revenue growth, short interest — all accurate.

2. **Personality creates distortion.** Each persona has a ~1500-word SOUL.md document that defines their cognitive identity: who they are, what they believe, how they interpret data, and which cognitive biases shape their worldview. This document becomes the LLM's system prompt.

3. **The LLM does the biasing.** Given accurate data and a biased personality, the model naturally exhibits the documented cognitive distortions — anchoring to historical prices, overweighting recent momentum, confirmation-biasing toward bullish signals — without any programmatic intervention.

This architecture is more faithful to how cognitive biases actually work in human analysts: the data is the same for everyone, but each analyst's cognitive framework causes them to interpret it differently.

### Why This Matters

- **Academically grounded:** Every bias is mapped to a specific peer-reviewed paper (see Academic Grounding below). The distortions are not arbitrary — they are documented psychological phenomena.
- **Technically auditable:** Because the data is unmodified, a judge or reviewer can compare the raw data against the analysis and observe exactly how the persona's biases distorted interpretation.
- **Educationally valuable:** Users learn to recognize cognitive biases by seeing them in action against real data they can verify.

---

## Data Flow

```
                                    ┌──────────────────────┐
                                    │     SOUL.md          │
                                    │  (system prompt)     │
                                    │                      │
                                    │  Identity            │
                                    │  Philosophy          │
                                    │  Cognitive Biases    │
                                    │  Analytical Framework│
                                    │  Output Format       │
                                    └──────────┬───────────┘
                                               │
  ┌─────────┐    ┌──────────┐    ┌─────────────▼──────────────┐    ┌─────────────┐
  │ yfinance │───▶│ Stock DB │───▶│     OpenRouter LLM         │───▶│  Analysis   │
  │  (live)  │    │ (SQLite) │    │   (Gemini 2.0 Flash)       │    │  Response   │
  └─────────┘    └──────────┘    │                             │    └─────────────┘
                                 │  system: SOUL.md persona    │
                                 │  user:   unmodified data    │
                                 └─────────────────────────────┘
```

1. **Ingestion:** yfinance fetches live fundamentals, price history, and news headlines
2. **Caching:** SQLite stores stock data with 4-hour staleness window and lazy-refresh on access
3. **Persona Loading:** `load_soul()` reads the persona's SOUL.md from `souls/` directory
4. **LLM Call:** SOUL.md is sent as `{"role": "system"}`, stock data as `{"role": "user"}`
5. **Post-processing:** Extract BUY/SELL/HOLD recommendation, attach bias citations and hallucination templates

---

## Dual-Version Architecture

### Web Version (FastAPI)

The primary user-facing application. Serves a browser UI and REST API.

```
diamondclaws/
├── main.py                    # FastAPI app with CORS, static files
├── api/routes.py              # REST endpoints (/api/analyze, /api/stocks/*, /api/personas)
├── data/personas.py           # Persona dicts, BIAS_REFERENCES, load_soul()
├── tools/analysis.py          # call_llm() with system_prompt, generate_biased_analysis()
├── tools/yfinance_fetch.py    # Yahoo Finance data fetcher
├── models/database.py         # SQLAlchemy ORM, stock table, CRUD
├── models/schemas.py          # Pydantic request/response models
├── souls/                     # SOUL.md personality documents
│   ├── bullish_alpha.md
│   ├── value_contrarian.md
│   └── quant_momentum.md
└── web/index.html             # Frontend
```

**Key endpoint:** `POST /api/analyze` accepts `{ticker, persona_id}` and returns the full analysis response including biased interpretation, academic citations, confidence level, and hallucination templates.

### OpenClaw Version (Agent Pipeline)

Each persona is a standalone OpenClaw agent with its own model configuration and SOUL.md. A shared `diamond-analysis` skill provides the analysis pipeline.

```
~/.openclaw/
├── agents/
│   ├── diamond-bull/          # Bullish Alpha agent
│   │   ├── agent/models.json  # OpenRouter + Gemini 2.0 Flash
│   │   ├── agent/SOUL.md      # Bullish Alpha personality
│   │   └── sessions/
│   ├── diamond-value/         # Value Contrarian agent
│   │   └── ...
│   └── diamond-quant/         # Quant Momentum agent
│       └── ...
└── workspace/skills/
    └── diamond-analysis/
        ├── manifest.json      # Skill metadata and triggers
        ├── skill.md           # Usage documentation
        └── scripts/
            └── analyze.py     # Standalone CLI script
```

**Standalone usage:** `python analyze.py --ticker NVDA --persona bullish_alpha`

The OpenClaw version enables:
- Running personas through the managed agent pipeline with gateway routing
- Chaining analysis across personas for multi-perspective reports
- Integration with Telegram and other OpenClaw channels

---

## Academic Grounding

Each persona's cognitive biases are mapped to specific peer-reviewed papers:

### Bullish Alpha
| Bias | Paper | Year |
|------|-------|------|
| Confirmation Bias | Nickerson, R. S. — *Review of General Psychology* | 1998 |
| Optimism Bias | Weinstein, N. D. — *J. Personality and Social Psychology* | 1980 |
| Availability Heuristic | Tversky, A. & Kahneman, D. — *Cognitive Psychology* | 1973 |
| Representativeness Heuristic | Tversky, A. & Kahneman, D. — *Science* | 1974 |
| Illusion of Control | Langer, E. J. — *J. Personality and Social Psychology* | 1975 |

### Value Contrarian
| Bias | Paper | Year |
|------|-------|------|
| Sunk Cost Fallacy | Arkes, H. R. & Blumer, C. — *Org. Behavior and Human Decision Processes* | 1985 |
| Anchoring | Tversky, A. & Kahneman, D. — *Science* | 1974 |
| Gambler's Fallacy | Tversky, A. & Kahneman, D. — *Psychological Bulletin* | 1971 |
| Bandwagon Effect | Bikhchandani, S. et al. — *J. Political Economy* | 1992 |
| Confirmation Bias | Nickerson, R. S. — *Review of General Psychology* | 1998 |

### Quant Momentum
| Bias | Paper | Year |
|------|-------|------|
| Overconfidence Bias | Fischhoff, B. & Beyth-Marom, R. — *Psychological Review* | 1983 |
| Availability Heuristic | Tversky, A. & Kahneman, D. — *Cognitive Psychology* | 1973 |
| Clustering Illusion | Tversky, A. & Kahneman, D. — *Cognitive Psychology* | 1973 |
| Post-Prediction Rationalization | Fischhoff, B. — *J. Experimental Psychology: HPP* | 1975 |
| Anchoring to Technical Levels | Tversky, A. & Kahneman, D. — *Science* | 1974 |

---

## Tech Stack

| Component | Technology | Purpose |
|-----------|-----------|---------|
| Backend | FastAPI 0.109 + Uvicorn | Async HTTP server and REST API |
| ORM | SQLAlchemy 2.0 + SQLite | Stock data persistence with lazy-refresh |
| Data | yfinance 0.2.36 | Live stock fundamentals, price history, news |
| LLM | OpenRouter → Gemini 2.0 Flash | Analysis generation with system prompt support |
| Schemas | Pydantic 2.5 | Request/response validation |
| Frontend | Vanilla HTML/CSS/JS | Zero-dependency browser UI |
| Agent Pipeline | OpenClaw | Standalone persona agents with gateway routing |

---

## Backward Compatibility

The SOUL.md integration is designed with a graceful fallback:

- If `souls/{persona_id}.md` exists → used as LLM system prompt (personality-driven path)
- If the file is missing → falls back to the original inline prompt built from the persona dict

This means deleting the `souls/` directory reverts to the pre-SOUL.md behavior with zero code changes.
