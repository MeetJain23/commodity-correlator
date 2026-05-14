"""
The math layer. Independent of Streamlit — could be unit-tested or
reused for the next modules (seasonality, pattern matching).
"""

import pandas as pd
from universe import COMMODITIES, ALL_STOCKS, STOCK_SECTOR

def rolling_correlation(returns: pd.DataFrame, ticker_a: str, ticker_b: str, window: int = 90) -> pd.Series:
    """Rolling correlation between two return series."""
    return returns[ticker_a].rolling(window=window).corr(returns[ticker_b])

def current_correlation(returns: pd.DataFrame, ticker_a: str, ticker_b: str, window: int = 90) -> float:
    """Just the most recent correlation value — a single number."""
    series = rolling_correlation(returns, ticker_a, ticker_b, window)
    return series.dropna().iloc[-1] if len(series.dropna()) > 0 else float("nan")

def rank_stocks_by_commodity(returns: pd.DataFrame, commodity_ticker: str, window: int = 90, top_n: int = 10) -> pd.DataFrame:
    """
    For a given commodity, rank all stocks by current correlation.
    Returns a sorted DataFrame with stock name, sector, correlation now,
    correlation 30 days ago, and the change (regime shift signal).
    """
    rows = []
    for stock_ticker, stock_name in ALL_STOCKS.items():
        corr_series = rolling_correlation(returns, commodity_ticker, stock_ticker, window).dropna()
        if len(corr_series) < 30:
            continue  # not enough data
        corr_now = corr_series.iloc[-1]
        corr_30_ago = corr_series.iloc[-30] if len(corr_series) >= 30 else float("nan")
        rows.append({
            "Stock": stock_name,
            "Ticker": stock_ticker,
            "Sector": STOCK_SECTOR[stock_ticker],
            "Correlation Now": round(corr_now, 3),
            "Correlation 30d Ago": round(corr_30_ago, 3),
            "Change": round(corr_now - corr_30_ago, 3),
        })
    df = pd.DataFrame(rows)
    df = df.sort_values("Correlation Now", key=abs, ascending=False)  # sort by ABSOLUTE strength
    return df.head(top_n).reset_index(drop=True)

def rank_commodities_by_stock(returns: pd.DataFrame, stock_ticker: str, window: int = 90) -> pd.DataFrame:
    """For a given stock, rank all commodities by how strongly they correlate."""
    rows = []
    for commodity_name, commodity_ticker in COMMODITIES.items():
        corr_series = rolling_correlation(returns, commodity_ticker, stock_ticker, window).dropna()
        if len(corr_series) < 30:
            continue
        corr_now = corr_series.iloc[-1]
        corr_30_ago = corr_series.iloc[-30]
        rows.append({
            "Commodity": commodity_name,
            "Correlation Now": round(corr_now, 3),
            "Correlation 30d Ago": round(corr_30_ago, 3),
            "Change": round(corr_now - corr_30_ago, 3),
        })
    df = pd.DataFrame(rows)
    return df.sort_values("Correlation Now", key=abs, ascending=False).reset_index(drop=True)

def regime_change_scan(returns: pd.DataFrame, window: int = 90, change_threshold: float = 0.3) -> pd.DataFrame:
    """
    Scan all stock-commodity pairs for big correlation shifts in the last 30 days.
    Returns pairs where |correlation_now - correlation_30_days_ago| > threshold.
    These are the 'something changed' signals — worth a human look.
    """
    rows = []
    for stock_ticker, stock_name in ALL_STOCKS.items():
        for commodity_name, commodity_ticker in COMMODITIES.items():
            corr_series = rolling_correlation(returns, commodity_ticker, stock_ticker, window).dropna()
            if len(corr_series) < 30:
                continue
            corr_now = corr_series.iloc[-1]
            corr_30_ago = corr_series.iloc[-30]
            change = corr_now - corr_30_ago
            if abs(change) >= change_threshold:
                rows.append({
                    "Stock": stock_name,
                    "Sector": STOCK_SECTOR[stock_ticker],
                    "Commodity": commodity_name,
                    "Correlation Now": round(corr_now, 3),
                    "Correlation 30d Ago": round(corr_30_ago, 3),
                    "Change": round(change, 3),
                    "Direction": "↑ Strengthening" if change > 0 else "↓ Weakening",
                })
    if not rows:
        return pd.DataFrame(columns=["Stock", "Sector", "Commodity", "Correlation Now", "Correlation 30d Ago", "Change", "Direction"])
    df = pd.DataFrame(rows)
    return df.sort_values("Change", key=abs, ascending=False).reset_index(drop=True)