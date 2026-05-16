"""
Supply chain analytics:
  - validate relationships against historical price correlation
  - integrate supply chain + commodity correlation + seasonality
    into a single ranked "cascade signal"
"""

import pandas as pd
import numpy as np

from supply_chain import SUPPLY_CHAIN, get_suppliers_of, get_customers_of
from universe import ALL_STOCKS, STOCK_SECTOR
from analytics import rolling_correlation
from seasonality import seasonality_table


def validate_relationship(returns_df: pd.DataFrame, supplier: str, customer: str, window: int = 90) -> dict:
    """
    For a supposed supplier→customer link, compute:
      - current correlation of their daily returns
      - 1y average correlation
      - judgement: does the data support the claimed relationship?
    """
    if supplier not in returns_df.columns or customer not in returns_df.columns:
        return {"valid_data": False}

    corr_series = rolling_correlation(returns_df, supplier, customer, window=window).dropna()
    if len(corr_series) < 30:
        return {"valid_data": False}

    corr_now = corr_series.iloc[-1]
    corr_1y_avg = corr_series.tail(252).mean() if len(corr_series) >= 252 else corr_series.mean()

    # Judgement logic
    if corr_now > 0.5:
        verdict = "Strong ✓"
    elif corr_now > 0.3:
        verdict = "Moderate"
    elif corr_now > 0.1:
        verdict = "Weak"
    else:
        verdict = "No detectable link"

    return {
        "valid_data": True,
        "corr_now": round(corr_now, 3),
        "corr_1y_avg": round(corr_1y_avg, 3),
        "verdict": verdict,
    }


def suppliers_table_with_validation(returns_df: pd.DataFrame, customer_ticker: str, window: int = 90) -> pd.DataFrame:
    """For a given customer, list its known suppliers with validated correlations."""
    suppliers = get_suppliers_of(customer_ticker)
    if not suppliers:
        return pd.DataFrame()

    rows = []
    for s in suppliers:
        validation = validate_relationship(returns_df, s["Ticker"], customer_ticker, window)
        rows.append({
            "Supplier": ALL_STOCKS.get(s["Ticker"], s["Ticker"]),
            "Ticker": s["Ticker"],
            "Sector": STOCK_SECTOR.get(s["Ticker"], "—"),
            "Supply Chain Weight": s["Weight"],
            "Correlation Now": validation.get("corr_now", "—"),
            "1y Avg Correlation": validation.get("corr_1y_avg", "—"),
            "Verdict": validation.get("verdict", "No data"),
            "Note": s["Note"],
        })
    df = pd.DataFrame(rows)
    return df.sort_values("Supply Chain Weight", ascending=False).reset_index(drop=True)


def customers_table_with_validation(returns_df: pd.DataFrame, supplier_ticker: str, window: int = 90) -> pd.DataFrame:
    """For a given supplier, list its known customers with validated correlations."""
    customers = get_customers_of(supplier_ticker)
    if not customers:
        return pd.DataFrame()

    rows = []
    for c in customers:
        validation = validate_relationship(returns_df, supplier_ticker, c["Ticker"], window)
        rows.append({
            "Customer": ALL_STOCKS.get(c["Ticker"], c["Ticker"]),
            "Ticker": c["Ticker"],
            "Sector": STOCK_SECTOR.get(c["Ticker"], "—"),
            "Revenue Dependence": c["Weight"],
            "Correlation Now": validation.get("corr_now", "—"),
            "1y Avg Correlation": validation.get("corr_1y_avg", "—"),
            "Verdict": validation.get("verdict", "No data"),
            "Note": c["Note"],
        })
    df = pd.DataFrame(rows)
    return df.sort_values("Revenue Dependence", ascending=False).reset_index(drop=True)


def cascade_signal(returns_df: pd.DataFrame, prices_df: pd.DataFrame, customer_ticker: str, window: int = 90) -> pd.DataFrame:
    """
    THE INTEGRATED SIGNAL.

    Given a customer stock that recently moved, find its suppliers and rank them by a composite score:
      - Supply chain weight (how dependent supplier is on customer)
      - Validated correlation (does the link actually show up in data?)
      - Current-month seasonality (is this historically a good month for supplier?)
      - Recent relative momentum (has supplier already moved, or is it lagging?)

    A supplier that scores high on ALL of these is the strongest candidate.
    """
    suppliers = get_suppliers_of(customer_ticker)
    if not suppliers:
        return pd.DataFrame()

    # How did the customer move recently? (5d, 20d)
    customer_5d_return = (prices_df[customer_ticker].iloc[-1] / prices_df[customer_ticker].iloc[-5] - 1) * 100
    customer_20d_return = (prices_df[customer_ticker].iloc[-1] / prices_df[customer_ticker].iloc[-20] - 1) * 100

    current_month = pd.Timestamp.today().month
    rows = []

    for s in suppliers:
        st_ticker = s["Ticker"]
        weight = s["Weight"]

        if st_ticker not in returns_df.columns:
            continue

        # Validate the link
        validation = validate_relationship(returns_df, st_ticker, customer_ticker, window)
        corr_now = validation.get("corr_now", 0)
        if not validation["valid_data"]:
            corr_now = 0

        # Supplier's recent move
        supplier_5d_return = (prices_df[st_ticker].iloc[-1] / prices_df[st_ticker].iloc[-5] - 1) * 100
        supplier_20d_return = (prices_df[st_ticker].iloc[-1] / prices_df[st_ticker].iloc[-20] - 1) * 100

        # Relative momentum: has supplier MOVED yet relative to customer?
        # If customer ran +8% in 5d but supplier only ran +1%, supplier is LAGGING — potential catch-up trade
        lag_5d = customer_5d_return - supplier_5d_return

        # Current-month seasonality
        season_table = seasonality_table(returns_df[st_ticker])
        if not season_table.empty:
            current_month_row = season_table[season_table["Month_Num"] == current_month]
            if not current_month_row.empty:
                season_return = current_month_row["Avg Return %"].values[0]
                season_winrate = current_month_row["Win Rate %"].values[0]
            else:
                season_return, season_winrate = 0, 50
        else:
            season_return, season_winrate = 0, 50

        # Composite score: normalize each factor to 0-1, weight them, sum
        # weights chosen so each factor matters but none dominates
        score = (
            0.30 * min(weight, 1.0) +               # supply chain dependence
            0.30 * max(0, corr_now) +               # validated correlation (only positive)
            0.20 * max(0, lag_5d / 10) +            # lag signal (capped)
            0.10 * max(0, season_return / 5) +      # seasonality
            0.10 * max(0, (season_winrate - 50) / 50)  # season win-rate above 50%
        )

        rows.append({
            "Supplier": ALL_STOCKS.get(st_ticker, st_ticker),
            "Ticker": st_ticker,
            "SC Weight": round(weight, 2),
            "Corr Now": round(corr_now, 2),
            "Customer 5d %": round(customer_5d_return, 1),
            "Supplier 5d %": round(supplier_5d_return, 1),
            "Lag (5d)": round(lag_5d, 1),
            "Season Month %": round(season_return, 1),
            "Season Win %": round(season_winrate, 0),
            "Score": round(score, 3),
        })

    df = pd.DataFrame(rows)
    if df.empty:
        return df
    return df.sort_values("Score", ascending=False).reset_index(drop=True)