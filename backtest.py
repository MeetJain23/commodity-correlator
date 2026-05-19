"""
Phase 5: Backtest engine for the cascade signal.

This module validates whether the cascade signal generates trade ideas with
measurable forward-return edge. It is DELIBERATELY conservative:

  - No look-ahead bias (signals at time T use only data available at time T)
  - Transaction costs applied to every trade (0.3% per side = 0.6% round trip)
  - Compared against benchmarks, not against zero
  - Honest about sample size and statistical power
  - Reports negative results as clearly as positive ones

A backtest that lies politely is worse than no backtest at all.
"""

import pandas as pd
import numpy as np
from typing import Optional

from supply_chain import get_suppliers_of
from universe import ALL_STOCKS, STOCK_SECTOR
from supply_chain_analytics import cascade_signal


# Transaction cost assumption — conservative for Indian retail markets
# Includes: brokerage, STT, exchange charges, GST, slippage estimate
TRANSACTION_COST = 0.003  # 0.3% per side, applied at entry AND exit


def _safe_return(prices: pd.Series, start_idx: int, end_idx: int) -> Optional[float]:
    """Return % change between two indices, with safety checks."""
    if start_idx < 0 or end_idx >= len(prices):
        return None
    p_start = prices.iloc[start_idx]
    p_end = prices.iloc[end_idx]
    if pd.isna(p_start) or pd.isna(p_end) or p_start <= 0:
        return None
    return (p_end / p_start - 1) * 100


def _cascade_at_time(
    returns_history: pd.DataFrame,
    prices_history: pd.DataFrame,
    customer_ticker: str,
    as_of_idx: int,
    window: int = 90,
) -> Optional[pd.DataFrame]:
    """
    Recompute the cascade signal AS IF we were at as_of_idx, using only
    data available up to that point. This is the look-ahead bias guard.
    """
    # Slice data to only what was visible at as_of_idx
    returns_visible = returns_history.iloc[:as_of_idx + 1]
    prices_visible = prices_history.iloc[:as_of_idx + 1]

    if len(returns_visible) < window + 30:
        return None
    if customer_ticker not in returns_visible.columns:
        return None

    # Use the existing cascade_signal function with the truncated data
    # NOTE: cascade_signal uses pd.Timestamp.today() for seasonality month —
    # for backtest correctness, we'd ideally pass the as_of_date through.
    # For v1, we accept this small imperfection (seasonality is the smallest weight).
    cascade_df = cascade_signal(returns_visible, prices_visible, customer_ticker, window=window)
    return cascade_df


def find_trigger_events(
    prices: pd.DataFrame,
    customers_with_suppliers: list,
    trigger_pct: float = 5.0,
    trigger_window_days: int = 5,
    direction: str = "up",
    min_idx: int = 100,  # don't trigger in the first ~100 days (need history for cascade)
) -> list:
    """
    Scan history for events where a customer stock moved by trigger_pct
    in trigger_window_days. Returns a list of (customer_ticker, trigger_idx) tuples.

    Each customer is "rate-limited" — once a trigger fires, we wait
    trigger_window_days before allowing another trigger on the same customer.
    This prevents over-counting during prolonged trending moves.
    """
    events = []

    for customer in customers_with_suppliers:
        if customer not in prices.columns:
            continue
        series = prices[customer].dropna()
        if len(series) < min_idx + trigger_window_days:
            continue

        last_trigger_idx = -trigger_window_days - 1  # initialize so first trigger is allowed
        for i in range(min_idx, len(series) - 1):
            if i - last_trigger_idx <= trigger_window_days:
                continue  # rate-limit

            window_return = _safe_return(series, i - trigger_window_days, i)
            if window_return is None:
                continue

            triggered = False
            if direction == "up" and window_return >= trigger_pct:
                triggered = True
            elif direction == "down" and window_return <= -trigger_pct:
                triggered = True
            elif direction == "both" and abs(window_return) >= trigger_pct:
                triggered = True

            if triggered:
                # Map back to the index in the full prices DataFrame
                full_idx = prices.index.get_loc(series.index[i])
                events.append((customer, full_idx, window_return))
                last_trigger_idx = i

    return events


def evaluate_trade(
    prices: pd.DataFrame,
    supplier_ticker: str,
    entry_idx: int,
    holding_days: int,
) -> Optional[float]:
    """
    Compute the round-trip return of buying supplier at entry_idx and
    selling holding_days later. Includes transaction costs.
    """
    if supplier_ticker not in prices.columns:
        return None
    series = prices[supplier_ticker]
    if entry_idx >= len(series) - holding_days:
        return None  # not enough forward data

    raw_return = _safe_return(series, entry_idx, entry_idx + holding_days)
    if raw_return is None:
        return None

    # Apply transaction costs (entry + exit)
    net_return = raw_return - (TRANSACTION_COST * 2 * 100)  # in percentage points
    return net_return


def run_backtest(
    returns: pd.DataFrame,
    prices: pd.DataFrame,
    trigger_pct: float = 5.0,
    holding_days: int = 10,
    direction: str = "up",
    correlation_window: int = 90,
) -> dict:
    """
    Main backtest engine.

    For each customer trigger event:
      1. Compute cascade signal AT THAT POINT IN HISTORY (no look-ahead)
      2. Take top-ranked supplier from the cascade
      3. Compute forward return over holding_days
      4. Compare against benchmarks:
           - Random supplier from the mapped set
           - Equal-weight portfolio of all mapped suppliers
           - Universe-wide average return (market proxy)

    Returns a dict with metrics, trade list, and diagnostic breakdowns.
    """
    from supply_chain import SUPPLY_CHAIN

    # Build list of customers that have mapped suppliers
    customers_with_suppliers = list({c for _, c, _, _ in SUPPLY_CHAIN})

    print(f"[backtest] Finding trigger events: {direction} moves of {trigger_pct}% in 5 days")
    events = find_trigger_events(prices, customers_with_suppliers, trigger_pct=trigger_pct, direction=direction)
    print(f"[backtest] Found {len(events)} trigger events")

    if len(events) < 10:
        return {
            "status": "insufficient_events",
            "n_events": len(events),
            "message": f"Only {len(events)} trigger events found — too few for statistical inference.",
        }

    trades = []
    rng = np.random.default_rng(seed=42)  # reproducible randomness for benchmark

    for customer, trigger_idx, customer_move in events:
        # Compute cascade as if we were at trigger_idx (look-ahead guard)
        cascade_df = _cascade_at_time(returns, prices, customer, trigger_idx, window=correlation_window)
        if cascade_df is None or cascade_df.empty:
            continue

        # Take top-1 supplier per cascade score
        top_supplier = cascade_df.iloc[0]["Ticker"]

        # Evaluate that trade
        cascade_return = evaluate_trade(prices, top_supplier, trigger_idx, holding_days)
        if cascade_return is None:
            continue

        # Benchmark 1: random supplier from the same mapped set
        suppliers_for_customer = [s for s, c, _, _ in SUPPLY_CHAIN if c == customer]
        if not suppliers_for_customer:
            continue
        random_supplier = rng.choice(suppliers_for_customer)
        random_return = evaluate_trade(prices, random_supplier, trigger_idx, holding_days)

        # Benchmark 2: equal-weight portfolio of all mapped suppliers
        portfolio_returns = [evaluate_trade(prices, s, trigger_idx, holding_days)
                              for s in suppliers_for_customer]
        portfolio_returns = [r for r in portfolio_returns if r is not None]
        if not portfolio_returns:
            continue
        portfolio_return = np.mean(portfolio_returns)

        # Benchmark 3: universe-wide average (market proxy)
        all_returns = []
        for t in ALL_STOCKS:
            r = evaluate_trade(prices, t, trigger_idx, holding_days)
            if r is not None:
                all_returns.append(r)
        market_return = np.mean(all_returns) if all_returns else 0

        trades.append({
            "Date": prices.index[trigger_idx].date(),
            "Customer": ALL_STOCKS.get(customer, customer),
            "Customer Move %": round(customer_move, 1),
            "Top Supplier (Cascade)": ALL_STOCKS.get(top_supplier, top_supplier),
            "Cascade Return %": round(cascade_return, 2),
            "Random Supplier Return %": round(random_return, 2) if random_return is not None else None,
            "Portfolio Return %": round(portfolio_return, 2),
            "Market Return %": round(market_return, 2),
            "Excess vs Random": round(cascade_return - random_return, 2) if random_return is not None else None,
            "Excess vs Portfolio": round(cascade_return - portfolio_return, 2),
            "Excess vs Market": round(cascade_return - market_return, 2),
            "Customer Sector": STOCK_SECTOR.get(customer, "—"),
        })

    if not trades:
        return {"status": "no_valid_trades", "n_events": len(events)}

    trades_df = pd.DataFrame(trades)

    # Aggregate metrics
    n_trades = len(trades_df)
    avg_cascade = trades_df["Cascade Return %"].mean()
    avg_excess_random = trades_df["Excess vs Random"].dropna().mean()
    avg_excess_portfolio = trades_df["Excess vs Portfolio"].mean()
    avg_excess_market = trades_df["Excess vs Market"].mean()

    win_rate_vs_random = (trades_df["Excess vs Random"].dropna() > 0).sum() / len(trades_df["Excess vs Random"].dropna()) * 100
    win_rate_vs_portfolio = (trades_df["Excess vs Portfolio"] > 0).sum() / n_trades * 100
    win_rate_vs_market = (trades_df["Excess vs Market"] > 0).sum() / n_trades * 100

    # Sharpe-like: excess vs portfolio mean / std
    excess_std = trades_df["Excess vs Portfolio"].std()
    sharpe_like = avg_excess_portfolio / excess_std if excess_std > 0 else 0

    # Honest verdict
    verdict, verdict_color = _generate_verdict(
        n_trades, avg_excess_portfolio, win_rate_vs_portfolio, sharpe_like
    )

    # Diagnostic: by sector
    by_sector = trades_df.groupby("Customer Sector").agg({
        "Excess vs Portfolio": ["mean", "count"]
    }).round(2)
    by_sector.columns = ["Avg Excess %", "N Trades"]
    by_sector = by_sector.reset_index().sort_values("Avg Excess %", ascending=False)

    # Diagnostic: cumulative excess return (equity curve)
    trades_df_sorted = trades_df.sort_values("Date").reset_index(drop=True)
    trades_df_sorted["Cumulative Excess %"] = trades_df_sorted["Excess vs Portfolio"].cumsum()

    return {
        "status": "complete",
        "n_trades": n_trades,
        "n_events_scanned": len(events),
        "metrics": {
            "avg_cascade_return": round(avg_cascade, 2),
            "avg_excess_vs_random": round(avg_excess_random, 2),
            "avg_excess_vs_portfolio": round(avg_excess_portfolio, 2),
            "avg_excess_vs_market": round(avg_excess_market, 2),
            "win_rate_vs_random": round(win_rate_vs_random, 1),
            "win_rate_vs_portfolio": round(win_rate_vs_portfolio, 1),
            "win_rate_vs_market": round(win_rate_vs_market, 1),
            "sharpe_like": round(sharpe_like, 2),
            "excess_std": round(excess_std, 2),
        },
        "verdict": verdict,
        "verdict_color": verdict_color,
        "trades": trades_df_sorted,
        "by_sector": by_sector,
    }


def _generate_verdict(
    n_trades: int,
    avg_excess: float,
    win_rate: float,
    sharpe_like: float,
) -> tuple:
    """
    Generate an honest, automated verdict on the backtest result.
    No cherry-picking — the verdict follows directly from the numbers.
    """
    if n_trades < 20:
        return (
            f"INCONCLUSIVE — only {n_trades} trades. Too few for reliable inference. "
            f"Lower the trigger threshold or use 'both' direction to get more events.",
            "warning"
        )

    # Multi-criteria: need positive excess AND >50% win rate AND positive sharpe
    if avg_excess > 0.5 and win_rate > 55 and sharpe_like > 0.2:
        return (
            f"MEASURABLE EDGE — cascade signal beats sector portfolio by avg {avg_excess:+.1f}pp "
            f"with {win_rate:.0f}% win rate across {n_trades} trades. Worth further investigation.",
            "success"
        )
    elif avg_excess > 0 and win_rate > 50:
        return (
            f"WEAK POSITIVE — slight edge of {avg_excess:+.1f}pp avg, {win_rate:.0f}% win rate. "
            f"Not strong enough to act on alone, but consistent direction. "
            f"Would need larger sample to confirm.",
            "info"
        )
    elif abs(avg_excess) < 0.3 and 45 < win_rate < 55:
        return (
            f"NO EDGE DETECTED — cascade signal performs essentially the same as a sector portfolio. "
            f"Avg excess {avg_excess:+.1f}pp, win rate {win_rate:.0f}%. "
            f"The signal does not consistently outperform a naive alternative.",
            "warning"
        )
    else:
        return (
            f"NEGATIVE — cascade signal underperforms sector portfolio by {avg_excess:+.1f}pp "
            f"with {win_rate:.0f}% win rate. As currently designed, this signal does not have edge. "
            f"Either the scoring weights need rethinking, or the underlying premise is flawed.",
            "error"
        )