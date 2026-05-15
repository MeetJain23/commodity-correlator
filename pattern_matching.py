"""
DTW-based chart pattern matching — v2 with sector filtering and richer output.
"""

import numpy as np
import pandas as pd
from dtaidistance import dtw

from universe import ALL_STOCKS, INTERNATIONAL, STOCK_SECTOR


def _normalize(series: np.ndarray) -> np.ndarray:
    s = np.asarray(series, dtype=float)
    s = s[~np.isnan(s)]
    if len(s) == 0 or s.std() == 0:
        return s
    return (s - s.mean()) / s.std()


def _pattern_from_prices(prices_series: pd.Series, end_date, window: int):
    end_idx = prices_series.index.get_indexer([end_date], method="pad")[0]
    if end_idx < window:
        return None
    window_prices = prices_series.iloc[end_idx - window + 1: end_idx + 1].values
    if np.isnan(window_prices).any():
        return None
    log_returns = np.diff(np.log(window_prices))
    cumulative = np.cumsum(log_returns)
    return _normalize(cumulative)


def _raw_pattern_path(prices_series: pd.Series, end_date, window: int):
    """
    Returns the actual normalized cumulative return path for plotting (not just for DTW).
    """
    return _pattern_from_prices(prices_series, end_date, window)


def _forward_path(prices_series: pd.Series, end_date, forward_days: int):
    """
    The forward `forward_days` of normalized cumulative returns AFTER end_date.
    Used to show 'what happened next' visually.
    """
    end_idx = prices_series.index.get_indexer([end_date], method="pad")[0]
    forward_end_idx = min(end_idx + forward_days, len(prices_series) - 1)
    if forward_end_idx <= end_idx:
        return None
    forward_prices = prices_series.iloc[end_idx: forward_end_idx + 1].values
    if np.isnan(forward_prices).any() or len(forward_prices) < 2:
        return None
    log_returns = np.diff(np.log(forward_prices))
    return np.cumsum(log_returns)


def find_historical_analogues(
    prices_df: pd.DataFrame,
    query_ticker: str,
    window: int = 60,
    top_n: int = 5,
    forward_days: int = 60,
    step_days: int = 10,
    same_sector_only: bool = True,
    max_distance: float = 3.0,
) -> tuple:
    """
    Returns (results_df, query_pattern, forward_paths_dict)
    forward_paths_dict maps row_index -> {'pattern': np.ndarray, 'forward': np.ndarray}
    so the app layer can plot each match.
    """
    query_prices = prices_df[query_ticker].dropna()
    if len(query_prices) < window + 1:
        return pd.DataFrame(), None, {}

    query_pattern = _pattern_from_prices(query_prices, query_prices.index[-1], window)
    if query_pattern is None:
        return pd.DataFrame(), None, {}

    # Decide which tickers to scan
    if same_sector_only and query_ticker in STOCK_SECTOR:
        query_sector = STOCK_SECTOR[query_ticker]
        scan_tickers = [t for t in prices_df.columns
                        if t in STOCK_SECTOR and STOCK_SECTOR[t] == query_sector]
    else:
        scan_tickers = [t for t in prices_df.columns
                        if t in ALL_STOCKS or t in INTERNATIONAL]

    candidates = []
    paths = {}
    counter = 0

    for ticker in scan_tickers:
        series = prices_df[ticker].dropna()
        if len(series) < window + forward_days + 30:
            continue

        for i in range(window, len(series) - forward_days, step_days):
            end_date = series.index[i]
            # Skip patterns that overlap the query's own recent window
            if ticker == query_ticker and i >= len(series) - window - forward_days:
                continue

            candidate_pattern = _pattern_from_prices(series, end_date, window)
            if candidate_pattern is None or len(candidate_pattern) != len(query_pattern):
                continue

            distance = dtw.distance(query_pattern, candidate_pattern)
            if distance > max_distance:
                continue

            forward_path = _forward_path(series, end_date, forward_days)
            if forward_path is None:
                continue

            forward_return = (np.exp(forward_path[-1]) - 1) * 100

            candidates.append({
                "Ticker": ticker,
                "Name": ALL_STOCKS.get(ticker) or INTERNATIONAL.get(ticker, ticker),
                "Sector": STOCK_SECTOR.get(ticker, "—"),
                "Pattern End Date": end_date.date(),
                "DTW Distance": round(distance, 3),
                f"Forward {forward_days}d Return %": round(forward_return, 2),
                "_pattern": candidate_pattern,
                "_forward": forward_path,
            })
            counter += 1

    if not candidates:
        return pd.DataFrame(), query_pattern, {}

    df = pd.DataFrame(candidates).sort_values("DTW Distance").head(top_n).reset_index(drop=True)
    # Extract the patterns/paths separately so the table is clean
    paths = {i: {"pattern": df.loc[i, "_pattern"], "forward": df.loc[i, "_forward"]}
             for i in df.index}
    display_df = df.drop(columns=["_pattern", "_forward"])
    return display_df, query_pattern, paths


def find_current_peers(
    prices_df: pd.DataFrame,
    query_ticker: str,
    window: int = 60,
    top_n: int = 10,
    same_sector_only: bool = False,
    max_distance: float = 3.0,
) -> tuple:
    """Returns (results_df, query_pattern, peer_patterns_dict)"""
    query_prices = prices_df[query_ticker].dropna()
    if len(query_prices) < window + 1:
        return pd.DataFrame(), None, {}

    query_pattern = _pattern_from_prices(query_prices, query_prices.index[-1], window)
    if query_pattern is None:
        return pd.DataFrame(), None, {}

    if same_sector_only and query_ticker in STOCK_SECTOR:
        query_sector = STOCK_SECTOR[query_ticker]
        scan_tickers = [t for t in ALL_STOCKS
                        if t != query_ticker and STOCK_SECTOR.get(t) == query_sector]
    else:
        scan_tickers = [t for t in ALL_STOCKS if t != query_ticker]

    rows = []
    patterns = {}

    for ticker in scan_tickers:
        if ticker not in prices_df.columns:
            continue
        series = prices_df[ticker].dropna()
        if len(series) < window + 1:
            continue

        candidate_pattern = _pattern_from_prices(series, series.index[-1], window)
        if candidate_pattern is None or len(candidate_pattern) != len(query_pattern):
            continue

        distance = dtw.distance(query_pattern, candidate_pattern)
        if distance > max_distance:
            continue

        recent_return = (series.iloc[-1] / series.iloc[-window] - 1) * 100

        rows.append({
            "Ticker": ticker,
            "Name": ALL_STOCKS[ticker],
            "Sector": STOCK_SECTOR.get(ticker, "—"),
            "DTW Distance": round(distance, 3),
            f"Recent {window}d Return %": round(recent_return, 2),
            "_pattern": candidate_pattern,
        })

    if not rows:
        return pd.DataFrame(), query_pattern, {}

    df = pd.DataFrame(rows).sort_values("DTW Distance").head(top_n).reset_index(drop=True)
    patterns = {i: df.loc[i, "_pattern"] for i in df.index}
    return df.drop(columns=["_pattern"]), query_pattern, patterns


def find_international_leader_matches(
    prices_df: pd.DataFrame,
    international_ticker: str,
    lead_days: int = 30,
    window: int = 60,
    top_n: int = 10,
    max_distance: float = 3.0,
) -> tuple:
    """Returns (results_df, intl_pattern, intl_forward, peer_patterns_dict)"""
    if international_ticker not in prices_df.columns:
        return pd.DataFrame(), None, None, {}

    intl_series = prices_df[international_ticker].dropna()
    if len(intl_series) < window + lead_days + 1:
        return pd.DataFrame(), None, None, {}

    intl_end_date = intl_series.index[-lead_days]
    intl_pattern = _pattern_from_prices(intl_series, intl_end_date, window)
    if intl_pattern is None:
        return pd.DataFrame(), None, None, {}

    intl_forward = _forward_path(intl_series, intl_end_date, lead_days)
    intl_subsequent_return = (intl_series.iloc[-1] / intl_series.iloc[-lead_days] - 1) * 100

    rows = []
    patterns = {}

    for ticker in ALL_STOCKS:
        if ticker not in prices_df.columns:
            continue
        series = prices_df[ticker].dropna()
        if len(series) < window + 1:
            continue

        current_pattern = _pattern_from_prices(series, series.index[-1], window)
        if current_pattern is None or len(current_pattern) != len(intl_pattern):
            continue

        distance = dtw.distance(intl_pattern, current_pattern)
        if distance > max_distance:
            continue

        rows.append({
            "Ticker": ticker,
            "Name": ALL_STOCKS[ticker],
            "Sector": STOCK_SECTOR.get(ticker, "—"),
            "DTW Distance": round(distance, 3),
            f"If pattern holds, suggested {lead_days}d move %": round(intl_subsequent_return, 2),
            "_pattern": current_pattern,
        })

    if not rows:
        return pd.DataFrame(), intl_pattern, intl_forward, {}

    df = pd.DataFrame(rows).sort_values("DTW Distance").head(top_n).reset_index(drop=True)
    patterns = {i: df.loc[i, "_pattern"] for i in df.index}
    return df.drop(columns=["_pattern"]), intl_pattern, intl_forward, patterns