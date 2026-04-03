# StonxBuddy - The Deliberately Biased Stock Analyst

## Project Overview

**Project Name:** StonxBuddy  
**Type:** Hackathon AI/LLM Web Application  
**Core Functionality:** A satirical stock analysis agent that provides hilariously biased, overconfident analysis based on well-documented cognitive and behavioral biases found in retail and institutional investor discourse.  
**Target Users:** Hackathon participants, anyone interested in behavioral finance, entertainment/debugging use

---

## 48-Hour Plan

### Hour 0-4: Foundation
- [ ] Create project directory `/var/www/stonxbuddy`
- [ ] Initialize FastAPI project structure
- [ ] Set up virtual environment and dependencies
- [ ] Create `SPEC.md` (this file)
- [ ] Design 3 biased personas with academic backing

### Hour 4-12: Data Layer
- [ ] Build Yahoo Finance ingestion pipeline
- [ ] Create stock list (100 well-known equities)
- [ ] Cache historical price data
- [ ] Implement technical indicator calculations
- [ ] Store data in SQLite (hackathon simplicity)

### Hour 12-24: Core Logic
- [ ] Define behavioral bias framework with references
- [ ] Implement persona response generators
- [ ] Build LLM prompt templates for biased analysis
- [ ] Add hallucination engine ("met with CFO...")
- [ ] Create technical analysis bias injector

### Hour 24-36: API & Integration
- [ ] Build FastAPI endpoints
- [ ] Integrate with existing LLM infrastructure
- [ ] Create search functionality
- [ ] Add quick-action stock buttons

### Hour 36-48: Frontend & Polish
- [ ] Build responsive UI
- [ ] Implement persona selector
- [ ] Add stock search with autocomplete
- [ ] Style with bold, confident aesthetic
- [ ] Test and demo prep

---

## The 3 Personas

### 1. "Diamond Hands" Doug
**Style:** Ultra-bullish, sees moonshot in everything  
**Biases:**  
- **Confirmation Bias** - Only sees positive news
- **Availability Heuristic** - "Everyone I know is buying!"
- **Optimism Bias** - "This is a guaranteed 10x"
- **Sunk Cost Fallacy** - "I've held since $50, never selling"
**Catchphrase:** "To the moon, baby! 💎🙌"

### 2. "Doom Pumper" Debbie  
**Style:** Bearish catastrophe predictor  
**Biases:**  
- **Negativity Bias** -放大负面信息
- **Loss Aversion** - "It's going to crash any day now"
- **Anchoring** - "It was $150 once, now it's doomed"
- **Bandwagon Effect (Bear)** - "Everyone I know is selling"
**Catchphrase:** "I've seen this movie before. It ends badly."

### 3. "Smooth Brain" Steve  
**Style:** Clueless but ultra-confident  
**Biases:**  
- **Dunning-Kruger Effect** - Knows nothing, extremely confident
- **Overconfidence Bias** - "I'm basically a professional trader"
- **Herd Mentality** - "The Reddit crowd knows what's up"
- **Gambler's Fallacy** - "It's due for a rebound!"
**Catchphrase:** "Trust me, I've done the math. Actually, no math needed. It's obvious."

---

## Behavioral Bias Framework

### Cognitive Biases (Academic References)
| Bias | Definition | Stock Application |
|------|------------|------------------|
| Confirmation Bias | Seeking info that confirms existing beliefs | Only cites bullish articles for "buy" thesis |
| Anchoring | Over-relying on first piece of info | "It was $200 last year!" |
| Availability Heuristic | Recent events seem more likely | "TSLA recall = stock doomed" |
| Sunk Cost Fallacy | Continuing due to prior investment | "Held since IPO, can't sell now" |
| Overconfidence | Overestimating own abilities | "I have a feeling" as analysis |
| Loss Aversion | Losses hurt more than gains | "Better safe than sorry" = never buy |
| Bandwagon Effect | Doing what others do | "Everyone on Reddit says..." |
| Gambler's Fallacy | "Due for" after streak | "Up 5 days, gotta drop" |

### Technical Chart Biases
- **Head & Shoulders** = "Death pattern!" (often wrong)
- **Golden Cross** = "Moon soon!" (delayed indicator)
- **Support/Resistance** = "Guaranteed bounce!" (self-fulfilling sometimes)
- **Volume Spike** = "Institutional buying!" (could be anything)
- **Moving Average Alignment** = "Momentum building!" (lagging)

---

## Stock Data Requirements

### 100 Stocks to Ingest
**Tech Giants:** AAPL, MSFT, GOOGL, AMZN, META, NVDA, TSLA, AMD, INTC, CRM, ORCL, ADBE, NFLX, PYPL, SQ, HOOD, UBER, LYFT, SNAP, PLTR

**Finance:** JPM, BAC, GS, MS, C, WFC, AXP, V, MA, COF, SCHW, BLK, STT, SCHD, VOO, SPY, QQQ, DIA, IWM

**Healthcare:** JNJ, PFE, UNH, MRK, ABBV, LLY, TMO, AB, BMY, GILD, AMGN, VRTX, REGN, ISRG, DXCM

**Consumer:** WMT, TGT, COST, HD, LOW, NKE, SBUX, MCD, KO, PEP, PG, CL, EL, GIS, HSY

**Energy:** XOM, CVX, COP, SLB, OXY, EOG, MPC, VLO, PSX

**Industrial:** BA, CAT, DE, MMM, GE, HON, UPS, RTX, LMT

**Crypto-adjacent:** COIN, MSTR, MARA, RIOT

**Meme Stocks:** GME, AMC, BBBY, BB, NOK, PLTR

**Emerging:** PLTR, SNOW, CRWD, ZS, NET, DDOG, SQ, Pinterest, Roblox

---

## Technical Stack

- **Backend:** FastAPI (Python 3.11)
- **Data:** yfinance, SQLite
- **LLM:** OpenRouter (existing infrastructure)
- **Frontend:** Vanilla HTML/CSS/JS (hackathon speed)
- **Charts:** Lightweight-charts (TradingView)

---

## API Endpoints

```
GET  /api/stocks/search?q=nvda        # Search stocks
GET  /api/stocks/popular              # Quick action stocks
GET  /api/stocks/{ticker}             # Get stock data
POST /api/analyze                     # Get biased analysis
GET  /api/personas                    # List personas
```

---

## UI Design

### Homepage Layout
1. **Header:** "StonxBuddy - Your Biased Best Friend"
2. **Persona Selector:** 3 large cards with persona avatars
3. **Stock Search:** Prominent search bar with autocomplete
4. **Quick Actions:** Row of popular stock chips
5. **Analysis Panel:** Chat-style output with persona voice

### Visual Style
- Bold, meme-influenced aesthetic
- Confident color choices (green for bulls, red for bears)
- Comic-style typography
- Emoji integration

---

## Hallucination Examples

The personas should confidently make up stuff like:
- "I recently had dinner with Jensen Huang and he told me..."
- "My uncle who works at the SEC says..."
- "The insider buying activity is insane right now"
- "My model predicts 400% upside by Q4"
- "I know because I ran the numbers on my Bloomberg terminal"

All presented with 100% confidence and zero hedging.

---

## Acceptance Criteria

1. ✅ Project runs at `/var/www/stonxbuddy`
2. ✅ 100 stocks data ingested from Yahoo Finance
3. ✅ 3 distinct personas with different biases
4. ✅ Stock search works with autocomplete
5. ✅ Biased analysis generated on demand
6. ✅ Hallucinations included (marked clearly)
7. ✅ Academic references available on hover
8. ✅ Quick action buttons for top 20 stocks
9. ✅ Demoable in 48 hours
