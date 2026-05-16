"""
Pulls and caches price data.
Streamlit's @cache_data decorator means yfinance is called once per session;
subsequent calls return the cached result instantly.
"""

import yfinance as yf
import pandas as pd
import streamlit as st

from universe import COMMODITIES, ALL_STOCKS, INTERNATIONAL

@st.cache_data(ttl=60 * 60 * 6)
def fetch_all_prices(period: str = "5y") -> pd.DataFrame:
    all_tickers = list(COMMODITIES.values()) + list(ALL_STOCKS.keys()) + list(INTERNATIONAL.keys())

    raw = yf.download(
        all_tickers,
        period=period,
        interval="1d",
        auto_adjust=True,
        progress=False,
        group_by="ticker",
    )

    # Build the closes DataFrame, skipping any ticker that failed
    closes_dict = {}
    failed = []
    for t in all_tickers:
        try:
            series = raw[t]["Close"]
            if series.dropna().shape[0] > 0:
                closes_dict[t] = series
            else:
                failed.append(t)
        except (KeyError, TypeError):
            failed.append(t)

    if failed:
        print(f"[data_fetcher] Failed/empty tickers: {failed}")

    closes = pd.DataFrame(closes_dict)
    closes = closes.ffill(limit=3)
    closes = closes.dropna(how="all")
    return closes

    # Forward-fill small gaps (Indian holidays vs US holidays cause misalignment)
    # but cap at 3 days so we don't paper over real data issues

@st.cache_data(ttl=60 * 60 * 6)
def fetch_returns(period: str = "5y") -> pd.DataFrame:
    """Daily percentage returns — what we actually correlate on."""
    prices = fetch_all_prices(period)
    return prices.pct_change().dropna(how="all")