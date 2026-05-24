"""
Pulls and caches price data — optimized for larger universes (~150 stocks).

Changes from previous version:
  - Batches yfinance calls (50 tickers per batch with 1s sleeps) to avoid rate limits
  - Caches for 24 hours instead of 6
  - Reports failed tickers explicitly
  - Tolerates and skips any ticker that fails
"""

import time
import yfinance as yf
import pandas as pd
import streamlit as st

from universe import COMMODITIES, ALL_STOCKS, INTERNATIONAL


def _batch_download(tickers: list, period: str, batch_size: int = 50) -> pd.DataFrame:
    """Download tickers in batches to avoid Yahoo rate limits."""
    all_closes = {}
    failed = []

    for i in range(0, len(tickers), batch_size):
        batch = tickers[i:i + batch_size]
        try:
            raw = yf.download(
                batch,
                period=period,
                interval="1d",
                auto_adjust=True,
                progress=False,
                group_by="ticker",
                threads=True,
            )
            # Handle the multi-index columns
            for t in batch:
                try:
                    series = raw[t]["Close"]
                    if series.dropna().shape[0] > 0:
                        all_closes[t] = series
                    else:
                        failed.append(t)
                except (KeyError, TypeError):
                    failed.append(t)
        except Exception as e:
            print(f"[data_fetcher] Batch {i//batch_size + 1} error: {e}")
            failed.extend(batch)

        # Sleep between batches to be polite to Yahoo's servers
        if i + batch_size < len(tickers):
            time.sleep(1)

    if failed:
        print(f"[data_fetcher] Failed/empty tickers ({len(failed)}): {failed}")

    return pd.DataFrame(all_closes)


@st.cache_data(ttl=60 * 60 * 24)  # cache for 24 hours
def fetch_all_prices(period: str = "5y") -> pd.DataFrame:
    """
    Pull closing prices for every commodity + every stock + international tickers.
    """
    all_tickers = (
        list(COMMODITIES.values())
        + list(ALL_STOCKS.keys())
        + list(INTERNATIONAL.keys())
    )

    closes = _batch_download(all_tickers, period=period, batch_size=50)
    closes = closes.ffill(limit=3)
    closes = closes.dropna(how="all")
    return closes


@st.cache_data(ttl=60 * 60 * 24)
def fetch_returns(period: str = "5y") -> pd.DataFrame:
    """Daily percentage returns — what we correlate on."""
    prices = fetch_all_prices(period)
    return prices.pct_change().dropna(how="all")