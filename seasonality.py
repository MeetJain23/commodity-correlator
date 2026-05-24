"""
Seasonality analysis: average monthly returns and win rates.
Reuses the returns DataFrame from data_fetcher.
"""

import pandas as pd
import numpy as np
from scipy import stats

from universe import ALL_STOCKS, STOCKS, STOCK_SECTOR

MONTH_NAMES = ["Jan", "Feb", "Mar", "Apr", "May", "Jun",
               "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]


def monthly_returns(daily_returns_series: pd.Series) -> pd.Series:
    """
    Compound daily returns into monthly returns.
    A 1% day followed by a 2% day is NOT 3% — it's (1.01 * 1.02) - 1 = 3.02%.
    The .prod() - 1 pattern is the right way to compound.
    """
    return (1 + daily_returns_series).resample("ME").prod() - 1


def seasonality_table(daily_returns_series: pd.Series) -> pd.DataFrame:
    """
    For one stock, return a 12-row table:
    month | avg_return | median_return | win_rate | num_years | t_stat | p_value | significant
    """
    monthly = monthly_returns(daily_returns_series).dropna()
    if len(monthly) < 24:  # need at least 2 years of data
        return pd.DataFrame()

    rows = []
    for month_num in range(1, 13):
        month_data = monthly[monthly.index.month == month_num]
        if len(month_data) < 2:
            continue

        avg = month_data.mean()
        median = month_data.median()
        win_rate = (month_data > 0).sum() / len(month_data)

        # One-sample t-test: is the mean different from 0?
        t_stat, p_value = stats.ttest_1samp(month_data, 0)

        rows.append({
            "Month": MONTH_NAMES[month_num - 1],
            "Month_Num": month_num,
            "Avg Return %": round(avg * 100, 2),
            "Median Return %": round(median * 100, 2),
            "Win Rate %": round(win_rate * 100, 1),
            "Years of Data": len(month_data),
            "t-stat": round(t_stat, 2),
            "p-value": round(p_value, 3),
            "Significant?": "✓" if p_value < 0.10 else "",  # 90% confidence — lenient bar
        })

    return pd.DataFrame(rows)


def sector_seasonality_table(returns_df: pd.DataFrame, sector_name: str) -> pd.DataFrame:
    """
    Average seasonality across all stocks in a sector.
    Equal-weighted: each stock contributes equally.
    Skips tickers not present in returns_df (failed downloads).
    """
    if sector_name not in STOCKS:
        return pd.DataFrame()

    # Filter to only tickers actually present in the returns DataFrame
    sector_tickers = [t for t in STOCKS[sector_name].keys() if t in returns_df.columns]
    if not sector_tickers:
        return pd.DataFrame()

    # Equal-weight daily returns across the sector's available stocks
    sector_returns = returns_df[sector_tickers].mean(axis=1)
    return seasonality_table(sector_returns)

def sector_month_heatmap_data(returns_df: pd.DataFrame) -> pd.DataFrame:
    """
    Build a sector × month matrix of average monthly returns.
    Used for the calendar heatmap visualization.
    """
    rows = {}
    for sector_name in STOCKS.keys():
        table = sector_seasonality_table(returns_df, sector_name)
        if len(table) == 12:
            rows[sector_name] = table.set_index("Month")["Avg Return %"]

    if not rows:
        return pd.DataFrame()

    df = pd.DataFrame(rows).T  # sectors as rows, months as columns
    df = df[MONTH_NAMES]  # ensure correct column order
    return df