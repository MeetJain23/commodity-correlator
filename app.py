"""
The Streamlit web app — three views over the same data.
Run with: streamlit run app.py
"""

import streamlit as st
import plotly.graph_objects as go
from plotly.subplots import make_subplots

from universe import COMMODITIES, ALL_STOCKS, STOCKS
from data_fetcher import fetch_all_prices, fetch_returns
from analytics import (
    rolling_correlation,
    rank_stocks_by_commodity,
    rank_commodities_by_stock,
    regime_change_scan,
)

# --- Page setup ---
st.set_page_config(page_title="Commodity ↔ Stock Correlator", page_icon="📈", layout="wide")
st.title("📈 Commodity ↔ Stock Correlator (India)")
st.caption("Phase 1 of a bigger system. Built on free data from Yahoo Finance.")

# --- Sidebar: shared controls ---
st.sidebar.header("Settings")
window = st.sidebar.selectbox("Correlation window (days)", [30, 60, 90, 180], index=2)
period = st.sidebar.selectbox("Data history", ["2y", "5y", "10y"], index=1)
st.sidebar.markdown("---")
st.sidebar.caption("Correlations use *daily returns*, not raw prices. Window of 90d is the sweet spot for noise vs. responsiveness.")

# --- Load data ---
with st.spinner("Loading market data... (cached after first load)"):
    prices = fetch_all_prices(period)
    returns = fetch_returns(period)

st.sidebar.success(f"Loaded {len(prices)} trading days, {len(prices.columns)} tickers")

# --- Three tabs ---
tab1, tab2, tab3 = st.tabs(["🪙 By Commodity", "🏢 By Stock", "⚡ Regime Changes"])

# ===== TAB 1: Pick a commodity, see top stocks =====
with tab1:
    st.subheader("Which Indian stocks are currently most affected by a commodity?")

    col1, col2 = st.columns([1, 3])
    with col1:
        commodity_name = st.selectbox("Pick a commodity", list(COMMODITIES.keys()))
        commodity_ticker = COMMODITIES[commodity_name]
        top_n = st.slider("How many top stocks?", 5, 20, 10)

    ranked = rank_stocks_by_commodity(returns, commodity_ticker, window=window, top_n=top_n)

    with col2:
        st.markdown(f"**Top {top_n} stocks ranked by absolute correlation with {commodity_name}** (window = {window}d)")
        st.dataframe(ranked, width='stretch', hide_index=True)

    # Chart: pick the #1 stock and show its history with this commodity
    if len(ranked) > 0:
        top_ticker = ranked.iloc[0]["Ticker"]
        top_name = ranked.iloc[0]["Stock"]
        corr_series = rolling_correlation(returns, commodity_ticker, top_ticker, window).dropna()

        fig = make_subplots(
            rows=2, cols=1, shared_xaxes=True,
            vertical_spacing=0.08,
            subplot_titles=(f"{commodity_name} and {top_name} — Prices", f"Rolling {window}d Correlation"),
            specs=[[{"secondary_y": True}], [{"secondary_y": False}]],
            row_heights=[0.55, 0.45]
        )
        fig.add_trace(go.Scatter(x=prices.index, y=prices[commodity_ticker], name=commodity_name, line=dict(color="gold")), row=1, col=1)
        fig.add_trace(go.Scatter(x=prices.index, y=prices[top_ticker], name=top_name, line=dict(color="royalblue")), row=1, col=1, secondary_y=True)
        fig.add_trace(go.Scatter(x=corr_series.index, y=corr_series, name="Correlation", line=dict(color="crimson", width=2)), row=2, col=1)
        fig.add_hline(y=0, line_dash="dash", line_color="gray", row=2, col=1)
        fig.update_yaxes(range=[-1, 1], row=2, col=1)
        fig.update_layout(height=650, template="plotly_white", hovermode="x unified")
        st.plotly_chart(fig, width='stretch')

        # One-line interpretation
        corr_now = ranked.iloc[0]["Correlation Now"]
        corr_old = ranked.iloc[0]["Correlation 30d Ago"]
        direction = "strengthened" if corr_now > corr_old else "weakened"
        st.info(f"**Interpretation:** {top_name} shows {window}d correlation of **{corr_now}** with {commodity_name}. Has **{direction}** from {corr_old} a month ago.")

# ===== TAB 2: Pick a stock, see top commodities =====
with tab2:
    st.subheader("Which commodities are currently most affecting a stock?")

    # Build a sector-grouped selector
    options = []
    for sector_name, stocks in STOCKS.items():
        for ticker, name in stocks.items():
            options.append(f"{name} [{sector_name}]")
    selected = st.selectbox("Pick a stock", options)
    selected_name = selected.split(" [")[0]
    selected_ticker = next(t for t, n in ALL_STOCKS.items() if n == selected_name)

    ranked = rank_commodities_by_stock(returns, selected_ticker, window=window)
    st.dataframe(ranked, width='stretch', hide_index=True)

    if len(ranked) > 0:
        top_commodity_name = ranked.iloc[0]["Commodity"]
        top_commodity_ticker = COMMODITIES[top_commodity_name]
        corr_series = rolling_correlation(returns, top_commodity_ticker, selected_ticker, window).dropna()

        fig = make_subplots(
            rows=2, cols=1, shared_xaxes=True,
            vertical_spacing=0.08,
            subplot_titles=(f"{selected_name} and {top_commodity_name} — Prices", f"Rolling {window}d Correlation"),
            specs=[[{"secondary_y": True}], [{"secondary_y": False}]],
            row_heights=[0.55, 0.45]
        )
        fig.add_trace(go.Scatter(x=prices.index, y=prices[selected_ticker], name=selected_name, line=dict(color="royalblue")), row=1, col=1)
        fig.add_trace(go.Scatter(x=prices.index, y=prices[top_commodity_ticker], name=top_commodity_name, line=dict(color="gold")), row=1, col=1, secondary_y=True)
        fig.add_trace(go.Scatter(x=corr_series.index, y=corr_series, name="Correlation", line=dict(color="crimson", width=2)), row=2, col=1)
        fig.add_hline(y=0, line_dash="dash", line_color="gray", row=2, col=1)
        fig.update_yaxes(range=[-1, 1], row=2, col=1)
        fig.update_layout(height=650, template="plotly_white", hovermode="x unified")
        st.plotly_chart(fig, width='stretch')

# ===== TAB 3: Regime changes =====
with tab3:
    st.subheader("Stock–commodity pairs where correlation has shifted recently")
    st.caption("These are 'something has changed' signals — worth a human look. Large positive change = relationship strengthening; large negative = decoupling.")

    threshold = st.slider("Minimum |change| in correlation over last 30 days", 0.1, 0.8, 0.3, 0.05)

    with st.spinner("Scanning all pairs..."):
        flagged = regime_change_scan(returns, window=window, change_threshold=threshold)

    if len(flagged) == 0:
        st.warning("No pairs crossed the threshold. Try lowering it.")
    else:
        st.success(f"Found {len(flagged)} pairs with significant correlation shifts")
        st.dataframe(flagged, width='stretch', hide_index=True)