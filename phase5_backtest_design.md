# Phase 5: Backtest Engine — Design Document

## 1. What we're testing

The hypothesis is that the **cascade signal** generates trade ideas with measurable forward-return edge. Specifically:

> When a customer stock moves X% in N days, the top-scored supplier (per cascade composite score) outperforms the broader universe over the next K days.

If true, the system has a measurable, statistical edge.
If false, the system is honest but unprofitable as currently designed.
Either answer is valuable.

## 2. The four traps and how we handle them

### 2.1 Look-ahead bias
- We use only the supply chain edges we have today (necessary limitation — we don't have historical supply chain databases)
- We DO NOT re-tune cascade scoring weights based on backtest results (separate train/test sets)
- All signals at time T use ONLY data available at time T (no peeking at future returns)

### 2.2 Survivorship bias
- LIMITATION ACKNOWLEDGED: we test only on current universe (73 stocks)
- This biases results optimistically
- We will report this limitation explicitly in any output

### 2.3 Overfitting
- We use the SAME composite weights as the live cascade signal (0.30 SC weight, 0.30 correlation, 0.20 lag, etc.)
- We do NOT optimize weights during backtest
- We test only the existing signal as designed, not 50 variations

### 2.4 Transaction costs
- Conservative assumption: 0.3% per trade (combined brokerage + slippage + STT for Indian markets)
- Applied on both entry AND exit
- Total drag per trade: 0.6% — anything below this is not a real edge

## 3. Methodology

### 3.1 Universe
- 73 stocks (current ALL_STOCKS)
- 60 mapped supply chain edges
- 5 years of daily data
- Train period: 2021-01 to 2024-06 (~3.5 years)
- Test period: 2024-07 to 2026-05 (~2 years, out-of-sample)

### 3.2 Trigger definition
- A "customer move" = customer stock moves > X% in 5 trading days
- We test X = 3%, 5%, 7% to see how trigger strictness affects results
- Direction: we test BOTH directions (up moves expecting supplier follow-through, down moves expecting supplier weakness)

### 3.3 Trade rule
- When trigger fires, compute cascade score for all mapped suppliers
- Take TOP-1 ranked supplier
- "Enter" at next day's open (proxied by closing price + transaction cost)
- "Exit" after K days; we test K = 5, 10, 20

### 3.4 Comparison benchmarks
For each cascade trade, compare against:
- Random supplier from the mapped set (baseline)
- Equal-weight portfolio of all mapped suppliers (sector baseline)
- Nifty 50 return over same K days (market baseline)

The cascade signal must beat at least benchmark #1 to be considered "useful."

## 4. Outputs

### 4.1 Headline metrics
- Win rate (% of trades that beat the comparison benchmark)
- Average excess return per trade (cascade return minus benchmark)
- Sharpe-like ratio (excess return / std of excess returns)
- Number of trades in sample

### 4.2 Diagnostic views
- Win rate by customer sector (does cascade work better in some sectors?)
- Win rate by trigger magnitude (does it work better for bigger moves?)
- Win rate by holding period
- Distribution of forward returns (histogram, not just mean)

### 4.3 Honest verdict
At the end of the backtest output, a clear statement:
- "Signal has measurable edge: [conditions]"
- OR "Signal does not consistently beat benchmark; here's where it fails"
- OR "Inconclusive — too few trades / too high variance"

## 5. UI

New tab in app: **🧪 Backtest**

User selects:
- Trigger threshold (3%/5%/7%)
- Holding period (5d/10d/20d)
- Direction (Up moves / Down moves / Both)

System runs in ~10-20 seconds and shows:
- Summary metrics card (win rate, avg excess return, # trades, verdict)
- Equity curve chart (cumulative excess return over time)
- Distribution histogram of per-trade outcomes
- Top 10 actual trades that occurred (for sanity checking)

## 6. What this WON'T do (scope limits)

- Will NOT optimize cascade weights — that's a separate research project
- Will NOT test alternative signals (correlation-only, seasonality-only) — single signal in v1
- Will NOT account for liquidity constraints in small-cap suppliers
- Will NOT test long/short combinations
- Will NOT make trade recommendations — this is a diagnostic tool, not a trading system

## 7. Success criteria

The backtest module is "done" when:
1. Code runs without errors on the full universe
2. Output clearly states whether the cascade signal has edge
3. The four traps are visibly handled in the code (commented)
4. The "honest verdict" is computed automatically, not cherry-picked

Even if the verdict is "signal does not have edge" — the module is still successful. **Honest negative results are more valuable than fake positive ones.**

---

## 8. Post-build update (added after running the backtest)

The backtest ran across 7 configurations covering ~4000 trades. All seven verdicts: **NEGATIVE**. Win rate stayed consistently at 36-40% vs the sector portfolio benchmark, regardless of trigger size, holding period, or direction.

Specific hypotheses about why the signal failed (recorded in OBSERVATIONS.md):
1. The lag factor may be inverted — the signal favors suppliers that haven't moved when the customer rallies, but unmoved suppliers may be unmoved for fundamental reasons rather than being about to catch up.
2. Supply chain mapping is too sparse — 60 hand-curated edges across 73 stocks is partial coverage; many cascade picks may be tangentially related at best.
3. Supply chain doesn't transmit at 5-20 day horizons — the premise may be economically correct but temporally wrong for short-horizon trading.

The honest negative result is documented as the headline finding. Next iteration would test the inverted-lag hypothesis first, since it's the cheapest experiment.