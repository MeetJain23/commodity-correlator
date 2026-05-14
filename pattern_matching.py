"""
DTW-based chart pattern matching.
The three core operations:
  1. find_historical_analogues — given a recent pattern, find similar past patterns
     across the universe and report what happened next.
  2. find_current_peers — find other stocks whose recent patterns match yours.
  3. find_international_leaders — find Indian stocks matching a global ticker's
     recent past (premise: global moves can lead Indian ones).
"""

import numpy as np
import pandas as pd
from dtaidistance import dtw
from typing import List, Tuple

from universe import ALL_STOCKS, INTERNATIONAL


def _normalize(series: np.ndarray) -> np.ndarray:
    """
    Z-score normalize a price/return series so DTW compares SHAPES, not levels.
    Without this, a stock at ₹100 and one at ₹5000 would never match
    even if their shapes are identical.
    """
    s = np.asarray(series, dtype=float)
    s = s[~np.isnan(s)]
    if len(s) == 0 or s.std() == 0:
        return s
    return (s - s.mean()) / s.std()


def _pattern_from_prices(prices_series: pd.Series, end_date, window: int) -> np.ndarray:
    """
    Extract a window of prices ending on end_date and convert to a normalized shape.
    We use cumulative log-returns so all patterns are scale-free.
    """
    end_idx = prices_series.index.get_indexer([end_date], method="pad")[0]
    if end_idx < window:
        return None
    window_prices = prices_series.iloc[end_idx - window + 1: end_idx + 1].values
    if np.isnan(window_prices).any():
        return None
    log_returns = np.diff(np.log(window_prices))
    cumulative = np.cumsum(log_returns)
    return _normalize(cumulative)


def find_historical_analogues(
    prices_df: pd.DataFrame,
    query_ticker: str,
    window: int = 60,
    top_n: int = 5,
    forward_days: int = 60,
    step_days: int = 10,
) -> pd.DataFrame:
    """
    Scan the entire universe's history for patterns similar to the query stock's
    last `window` days. For each match, also report the forward return.
    step_days: only check every Nth date in history to avoid scanning every single day
               (massive speedup, minimal accuracy loss).
    """
    query_prices = prices_df[query_ticker].dropna()
    if len(query_prices) < window + 1:
        return pd.DataFrame()

    query_pattern = _pattern_from_prices(query_prices, query_prices.index[-1], window)
    if query_pattern is None:
        return pd.DataFrame()

    candidates = []

    # Scan every ticker (including the query ticker itself — self-analogues are valid)
    all_tickers = [t for t in prices_df.columns if t in ALL_STOCKS or t in INTERNATIONAL]

    for ticker in all_tickers:
        series = prices_df[ticker].dropna()
        if len(series) < window + forward_days + 30:
            continue

        # Walk through history at step_days intervals
        # Stop forward_days before the end so we have data to evaluate forward returns
        for i in range(window, len(series) - forward_days, step_days):
            end_date = series.index[i]
            # Skip very recent dates for non-self-tickers to avoid overlap with the query window
            if ticker == query_ticker and i >= len(series) - window - forward_days:
                continue

            candidate_pattern = _pattern_from_prices(series, end_date, window)
            if candidate_pattern is None or len(candidate_pattern) != len(query_pattern):
                continue

            distance = dtw.distance(query_pattern, candidate_pattern)

            # Forward return: from end_date to forward_days later
            forward_end_idx = min(i + forward_days, len(series) - 1)
            forward_return = (series.iloc[forward_end_idx] / series.iloc[i] - 1) * 100

            candidates.append({
                "Ticker": ticker,
                "Name": ALL_STOCKS.get(ticker) or INTERNATIONAL.get(ticker, ticker),
                "Pattern End Date": end_date.date(),
                "DTW Distance": round(distance, 3),
                f"Forward {forward_days}d Return %": round(forward_return, 2),
            })

    if not candidates:
        return pd.DataFrame()

    df = pd.DataFrame(candidates).sort_values("DTW Distance").reset_index(drop=True)
    return df.head(top_n)


def find_current_peers(
    prices_df: pd.DataFrame,
    query_ticker: str,
    window: int = 60,
    top_n: int = 10,
) -> pd.DataFrame:
    """
    Find other stocks whose CURRENT (last `window` days) pattern matches the query's.
    No forward-return calculation here — these are concurrent peers, not historical analogues.
    """
    query_prices = prices_df[query_ticker].dropna()
    if len(query_prices) < window + 1:
        return pd.DataFrame()

    query_pattern = _pattern_from_prices(query_prices, query_prices.index[-1], window)
    if query_pattern is None:
        return pd.DataFrame()

    rows = []
    for ticker in ALL_STOCKS:
        if ticker == query_ticker or ticker not in prices_df.columns:
            continue
        series = prices_df[ticker].dropna()
        if len(series) < window + 1:
            continue

        candidate_pattern = _pattern_from_prices(series, series.index[-1], window)
        if candidate_pattern is None or len(candidate_pattern) != len(query_pattern):
            continue

        distance = dtw.distance(query_pattern, candidate_pattern)
        # Recent return for context
        recent_return = (series.iloc[-1] / series.iloc[-window] - 1) * 100

        rows.append({
            "Ticker": ticker,
            "Name": ALL_STOCKS[ticker],
            "DTW Distance": round(distance, 3),
            f"Recent {window}d Return %": round(recent_return, 2),
        })

    if not rows:
        return pd.DataFrame()
    return pd.DataFrame(rows).sort_values("DTW Distance").reset_index(drop=True).head(top_n)


def find_international_leader_matches(
    prices_df: pd.DataFrame,
    international_ticker: str,
    lead_days: int = 30,
    window: int = 60,
    top_n: int = 10,
) -> pd.DataFrame:
    """
    Premise: international names sometimes 'lead' Indian counterparts by ~30 days.
    Take an international ticker's pattern from `lead_days` ago, find Indian stocks
    whose CURRENT pattern matches that historical international pattern.
    Interpretation: the Indian stock may now be where the international one was a month ago.
    """
    if international_ticker not in prices_df.columns:
        return pd.DataFrame()

    intl_series = prices_df[international_ticker].dropna()
    if len(intl_series) < window + lead_days + 1:
        return pd.DataFrame()

    # International pattern from `lead_days` ago
    intl_end_date = intl_series.index[-lead_days]
    intl_pattern = _pattern_from_prices(intl_series, intl_end_date, window)
    if intl_pattern is None:
        return pd.DataFrame()

    # How the international stock moved AFTER this pattern (the "future" we're checking against)
    intl_subsequent_return = (intl_series.iloc[-1] / intl_series.iloc[-lead_days] - 1) * 100

    rows = []
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
        rows.append({
            "Ticker": ticker,
            "Name": ALL_STOCKS[ticker],
            "DTW Distance": round(distance, 3),
            f"If pattern holds, suggested {lead_days}d move %": round(intl_subsequent_return, 2),
        })

    if not rows:
        return pd.DataFrame()
    return pd.DataFrame(rows).sort_values("DTW Distance").reset_index(drop=True).head(top_n)