"""
Pulls and caches price data.
Streamlit's @cache_data decorator means yfinance is called once per session;
subsequent calls return the cached result instantly.
"""

import yfinance as yf
import pandas as pd
import streamlit as st

from universe import COMMODITIES, ALL_STOCKS

@st.cache_data(ttl=60 * 60 * 6)  # cache for 6 hours
def fetch_all_prices(period: str = "5y") -> pd.DataFrame:
    """
    Pull closing prices for every commodity + every stock in our universe.
    Returns a single DataFrame: rows = dates, columns = tickers.
    """
    from universe import COMMODITIES, ALL_STOCKS, INTERNATIONAL
    all_tickers = list(COMMODITIES.values()) + list(ALL_STOCKS.keys()) + list(INTERNATIONAL.keys())

    raw = yf.download(
        all_tickers,
        period=period,
        interval="1d",
        auto_adjust=True,
        progress=False,
        group_by="ticker",     # cleaner column structure
    )

    # Extract just the 'Close' column for each ticker
    closes = pd.DataFrame({t: raw[t]["Close"] for t in all_tickers})

    # Forward-fill small gaps (Indian holidays vs US holidays cause misalignment)
    # but cap at 3 days so we don't paper over real data issues
    closes = closes.ffill(limit=3)
    closes = closes.dropna(how="all")

    return closes

@st.cache_data(ttl=60 * 60 * 6)
def fetch_returns(period: str = "5y") -> pd.DataFrame:
    """Daily percentage returns — what we actually correlate on."""
    prices = fetch_all_prices(period)
    return prices.pct_change().dropna(how="all")