"""
The math layer. Independent of Streamlit — could be unit-tested or
reused for the next modules (seasonality, pattern matching).

All ranking functions are defensive: they skip tickers missing from the
returns DataFrame (failed downloads) and always return a DataFrame,
never None.
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
    Skips tickers not present in the returns DataFrame (e.g. failed downloads).
    """
    if commodity_ticker not in returns.columns:
        return pd.DataFrame()

    rows = []
    for stock_ticker, stock_name in ALL_STOCKS.items():
        if stock_ticker not in returns.columns:
            continue  # ticker failed to download — skip silently
        corr_series = rolling_correlation(returns, commodity_ticker, stock_ticker, window).dropna()
        if len(corr_series) < 30:
            continue
        corr_now = corr_series.iloc[-1]
        corr_30_ago = corr_series.iloc[-30]
        rows.append({
            "Stock": stock_name,
            "Ticker": stock_ticker,
            "Sector": STOCK_SECTOR[stock_ticker],
            "Correlation Now": round(corr_now, 3),
            "Correlation 30d Ago": round(corr_30_ago, 3),
            "Change": round(corr_now - corr_30_ago, 3),
        })
    if not rows:
        return pd.DataFrame()
    df = pd.DataFrame(rows)
    df = df.sort_values("Correlation Now", key=abs, ascending=False)
    return df.head(top_n).reset_index(drop=True)


def rank_commodities_by_stock(returns: pd.DataFrame, stock_ticker: str, window: int = 90) -> pd.DataFrame:
    """
    For a given stock, rank commodities by current correlation.
    Skips commodities not present in the returns DataFrame.
    """
    if stock_ticker not in returns.columns:
        return pd.DataFrame()

    rows = []
    for commodity_name, commodity_ticker in COMMODITIES.items():
        if commodity_ticker not in returns.columns:
            continue
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
    if not rows:
        return pd.DataFrame()
    df = pd.DataFrame(rows)
    return df.sort_values("Correlation Now", key=abs, ascending=False).reset_index(drop=True)


def regime_change_scan(returns: pd.DataFrame, window: int = 90, change_threshold: float = 0.3) -> pd.DataFrame:
    """
    Scan all stock-commodity pairs for big correlation shifts in the last 30 days.
    Returns pairs where |correlation_now - correlation_30_days_ago| > threshold.
    """
    rows = []
    # Pre-filter: only scan tickers with enough data
    valid_stocks = {t: name for t, name in ALL_STOCKS.items()
                    if t in returns.columns and returns[t].dropna().shape[0] >= window + 30}

    for stock_ticker, stock_name in valid_stocks.items():
        for commodity_name, commodity_ticker in COMMODITIES.items():
            if commodity_ticker not in returns.columns:
                continue
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