# Observations Log
## Project Status: Completed (May 2026)

This system is now in **maintenance mode**. Active development moves to a separate project building on different premises (macro overlay, international supply chains, fundamental drivers).

Final scope:
- 140+ NSE-listed stocks across 22 sectors
- 13 global commodities
- 90 hand-curated supply chain relationships
- 6 analytical modules + self-critiquing backtest engine
- Conservative methodology, honest negative finding on cascade signal

What this system is: a manual scanner for exploring correlation, seasonality, patterns, and supply chain dynamics in Indian markets.
What this system is not: a trading system. (Backtest finding documented below.)
A running record of findings from running the Commodity ↔ Stock Correlator on Indian markets.
Each entry: specific numbers, a hypothesis, and why it matters.

The point of this log is not to be right — it's to be specific and dated, so future-me
can come back and check whether the read of the data held up.

---

## May 2026 Scan

### 1. Gold and Silver Have Nearly Identical Top Indian Proxies

**Finding:** Top 5 Indian stocks correlated with Gold (90-day window) are: Hindalco (0.38), NALCO (0.34), Ambuja Cement (0.27), Tata Steel (0.26), Petronet LNG (0.24). Top 5 for Silver: Hindalco (0.37), NALCO (0.33), Ambuja Cement (0.24), Tata Steel (0.23), Britannia (-0.22). Four of the top five are identical despite gold and silver being meaningfully different commodities (silver has heavy industrial use; gold doesn't).

**Hypothesis:** Indian metals stocks are trading as a single "inflation hedge basket" rather than by specific metal exposure. When investors want precious metals exposure in India, they get an undifferentiated metals beta. Hindalco at the top of both lists is the giveaway — it's an aluminum/copper company with no direct precious metals exposure.

**Why it matters:** "Trading gold or silver via Indian stocks" is effectively the same trade. The system catches a market-structure inefficiency that wouldn't show up on a single-asset chart.

---

### 2. Asian Paints Crude Correlation Just Flipped

**Finding:** Asian Paints' 90-day correlation with crude oil went from -0.037 to -0.239 in 30 days (change of -0.20). Simultaneously, its correlation with steel went from +0.012 to +0.194 (change of +0.18, strengthening).

**Hypothesis:** For most of 2022-2025, Asian Paints' hedging program and pricing power neutralized the textbook crude-input-cost relationship. In the last 30 days, with crude at $140+ levels, the textbook relationship has reasserted itself — the hedges may be running off, or the magnitude exceeds what pricing can pass through.

**Why it matters:** Asian Paints has become structurally more commodity-sensitive in the last month. If crude stays elevated, this drag continues. If crude breaks down, snap-back potential. The regime change is the actionable signal, not the absolute correlation level.

---

### 3. Oil & Gas Sector Repricing Against Steel

**Finding:** Three different oil marketing companies showed near-identical correlation shifts with steel in the same 30-day window: BPCL +0.256, HPCL +0.256, Indian Oil +0.250 — all strengthening, all to the same magnitude.

**Hypothesis:** Three identical regime changes simultaneously is not coincidence — it's a systematic factor. Most likely the PSU re-rating narrative + infra capex story is bundling these stocks together. Oil PSUs are being repriced as "govt-spending plays" rather than pure oil-marketing companies.

**Why it matters:** This is what *sectoral re-pricing* looks like in data, in real time. The system catches it without anyone telling it where to look.

---

### 4. Capital Goods Decoupling From Commodities

**Finding:** Across the Capital Goods & Infra sector, 7+ stocks show simultaneous correlation declines with commodities over 30 days: Siemens (Sugar -0.27, Crude -0.22), Cummins (Crude -0.21), Thermax (Sugar -0.22), ABB (Sugar -0.18), KEC International (Crude -0.18), KPIL (Sugar -0.21). All weakening, all in 30 days.

**Hypothesis:** The whole sector is being driven by its own thematic factors right now — order book strength, govt capex narrative, defense/infra story — not by commodity input costs. A thematic narrative has taken over from the cost-of-inputs framing.

**Why it matters:** When an entire sector loses commodity sensitivity simultaneously, the story is no longer about fundamentals — it's about flows. That's worth knowing before placing trades in the sector.

---

### 5. Bharat Forge Trading as Cross-Sector Infra Basket

**Finding:** Bharat Forge's current 60-day peers (DTW distance, no sector filter): JSW Steel (2.04), KEI Industries (2.09), Bajaj Auto (2.11), Tata Steel (2.12), Kalpataru Projects (2.15), Polycab (2.23). Six stocks from four different sectors (Auto, Cables, Metals, Capital Goods) all tracing nearly identical normalized return paths.

**Hypothesis:** Bharat Forge isn't trading as an auto-component stock right now — it's trading as an India-infra-cycle exposure. A single underlying flow (likely FII / infra-thematic money) is driving the entire infra-related basket as one.

**Why it matters:** Sector-classification breaks down when thematic flows dominate. Cross-sector co-movement is a higher-signal observation than any single-sector ranking.

---

### 6. April Effect Is Statistically Validated in Auto and Oil & Gas

**Finding:** Auto sector in April: +5.59% average, 100% win rate, p-value 0.004 (statistically significant). Oil & Gas in April: +5.79% average, 100% win rate, p-value 0.007 (significant). Both based on 5 years of data. Auto extends into May (+5.0%, 83% win, p=0.02) and June (+3.56%, 100% win, p=0.05) — three consecutive significant months.

**Hypothesis:** Indian FY transitions, Budget-related capex visibility, Q4 results announcements, monsoon expectations — multiple structural drivers converge in April-June.

**Why it matters:** This is a *tradeable* seasonal pattern with statistical backing — not vibes, not "April feels good." The combination of high win rate + low p-value + multi-year sample is rare in seasonality.

---

### 7. IT & Tech February Crash

**Finding:** IT sector in February: -5.78% average return, 20% win rate over 5 years. Compared to November (+5.0%) and December (+3.9%), the swing is dramatic.

**Hypothesis:** IT companies announce annual wage hikes in their Q4 (Jan-March quarter). February is when wage-hike-margin-pressure stories hit forward guidance and analyst downgrades. The negative seasonality matches a fundamentals story — it's not just statistical noise.

**Why it matters:** Sector rotation in Indian markets has a *calendar component* that maps to actual corporate event cycles, not just vague "good months / bad months" intuition.

---

## Backtest Findings

### 8. Cascade Signal Has No Measurable Edge As Currently Designed

**Finding:** Across ~4000 trades in 7 backtest configurations (varied trigger sizes 3-7%, holding periods 5-20 days, directions up/down/both), the cascade signal consistently shows 36-40% win rate vs the sector portfolio benchmark, with average excess returns of -0.13pp to +0.09pp. All seven verdicts: **NEGATIVE — signal does not have edge as currently designed**.

**Hypotheses:**
1. **Lag weight may be inverted.** The signal favors suppliers that haven't moved yet when the customer rallies (high lag = high score). But unmoved suppliers may be unmoved for fundamental reasons, not because they're about to catch up. The lag factor might be picking *broken* suppliers, not *opportunity* suppliers.
2. **Supply chain mapping is too sparse.** 60 hand-curated edges across 73 stocks is partial coverage. Many cascade picks may be tangentially related at best.
3. **Supply chain doesn't transmit at 5-20 day horizons.** Customer earnings translate to supplier orders over quarters, not weeks. The premise may be economically correct but temporally wrong for short-horizon trading.

**Why it matters:** The system catches its own failure honestly, with conservative methodology (no look-ahead, transaction costs included, three benchmarks). A backtest engine that reports negative results is more trustworthy than one that always finds edge. The next step is testing each hypothesis — likely starting with inverted lag weight — but the honest baseline is documented here first.

---

*Last updated: 2026-05-25*