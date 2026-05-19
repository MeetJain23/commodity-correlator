"""
The Streamlit web app — three views over the same data.
Run with: streamlit run app.py
"""

import streamlit as st
import plotly.graph_objects as go
import numpy as np
from plotly.subplots import make_subplots
from seasonality import seasonality_table, sector_seasonality_table, sector_month_heatmap_data, MONTH_NAMES
from pattern_matching import (
    find_historical_analogues,
    find_current_peers,
    find_international_leader_matches,
)
from backtest import run_backtest
from universe import INTERNATIONAL
from universe import COMMODITIES, ALL_STOCKS, STOCKS , STOCK_SECTOR
from data_fetcher import fetch_all_prices, fetch_returns
from analytics import (
    rolling_correlation,
    rank_stocks_by_commodity,
    rank_commodities_by_stock,
    regime_change_scan,
)
from supply_chain import SUPPLY_CHAIN, get_suppliers_of, get_customers_of, all_tickers_in_graph
from supply_chain_analytics import (
    suppliers_table_with_validation,
    customers_table_with_validation,
    cascade_signal,
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
tab1, tab2, tab3, tab4, tab5, tab6, tab7 = st.tabs(["🪙 By Commodity", "🏢 By Stock", "⚡ Regime Changes", "📅 Seasonality", "🔍 Pattern Match", "🔗 Supply Chain","🧪 Backtest"])

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

    # Let the user pick which stock to deep-dive on
    if len(ranked) > 0:
        st.markdown("---")
        st.markdown("### Deep dive — pick any stock from the table above")

        chart_options = [f"{row['Stock']} (corr={row['Correlation Now']})"
                         for _, row in ranked.iterrows()]
        selected_chart = st.selectbox("Chart this stock vs the commodity:",
                                       chart_options, key="tab1_chart_pick")
        chart_idx = chart_options.index(selected_chart)

        chart_ticker = ranked.iloc[chart_idx]["Ticker"]
        chart_name = ranked.iloc[chart_idx]["Stock"]
        corr_series = rolling_correlation(returns, commodity_ticker, chart_ticker, window).dropna()

        fig = make_subplots(
            rows=2, cols=1, shared_xaxes=True,
            vertical_spacing=0.08,
            subplot_titles=(f"{commodity_name} and {chart_name} — Prices", f"Rolling {window}d Correlation"),
            specs=[[{"secondary_y": True}], [{"secondary_y": False}]],
            row_heights=[0.55, 0.45]
        )
        fig.add_trace(go.Scatter(x=prices.index, y=prices[commodity_ticker], name=commodity_name, line=dict(color="gold")), row=1, col=1)
        fig.add_trace(go.Scatter(x=prices.index, y=prices[chart_ticker], name=chart_name, line=dict(color="royalblue")), row=1, col=1, secondary_y=True)
        fig.add_trace(go.Scatter(x=corr_series.index, y=corr_series, name="Correlation", line=dict(color="crimson", width=2)), row=2, col=1)
        fig.add_hline(y=0, line_dash="dash", line_color="gray", row=2, col=1)
        fig.update_yaxes(range=[-1, 1], row=2, col=1)
        fig.update_layout(height=650, template="plotly_white", hovermode="x unified")
        st.plotly_chart(fig, width='stretch')

        # Interpretation based on selected stock
        corr_now = ranked.iloc[chart_idx]["Correlation Now"]
        corr_old = ranked.iloc[chart_idx]["Correlation 30d Ago"]
        direction = "strengthened" if corr_now > corr_old else "weakened"
        st.info(f"**{chart_name}** shows {window}d correlation of **{corr_now}** with {commodity_name}. "
                f"Has **{direction}** from {corr_old} a month ago.")
        

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

    if ranked is None or len(ranked) == 0:
        st.warning(f"No data available for {selected_name}. The ticker may have failed to download.")
    else:
        st.dataframe(ranked, width='stretch', hide_index=True)
        st.markdown("---")
        st.markdown("### Deep dive — pick any commodity from the table above")
        # ... rest of the chart code (indented under else)

        chart_options = [f"{row['Commodity']} (corr={row['Correlation Now']})"
                         for _, row in ranked.iterrows()]
        selected_chart = st.selectbox("Chart this commodity vs the stock:",
                                       chart_options, key="tab2_chart_pick")
        chart_idx = chart_options.index(selected_chart)

        chart_commodity_name = ranked.iloc[chart_idx]["Commodity"]
        chart_commodity_ticker = COMMODITIES[chart_commodity_name]
        corr_series = rolling_correlation(returns, chart_commodity_ticker, selected_ticker, window).dropna()

        fig = make_subplots(
            rows=2, cols=1, shared_xaxes=True,
            vertical_spacing=0.08,
            subplot_titles=(f"{selected_name} and {chart_commodity_name} — Prices", f"Rolling {window}d Correlation"),
            specs=[[{"secondary_y": True}], [{"secondary_y": False}]],
            row_heights=[0.55, 0.45]
        )
        fig.add_trace(go.Scatter(x=prices.index, y=prices[selected_ticker], name=selected_name, line=dict(color="royalblue")), row=1, col=1)
        fig.add_trace(go.Scatter(x=prices.index, y=prices[chart_commodity_ticker], name=chart_commodity_name, line=dict(color="gold")), row=1, col=1, secondary_y=True)
        fig.add_trace(go.Scatter(x=corr_series.index, y=corr_series, name="Correlation", line=dict(color="crimson", width=2)), row=2, col=1)
        fig.add_hline(y=0, line_dash="dash", line_color="gray", row=2, col=1)
        fig.update_yaxes(range=[-1, 1], row=2, col=1)
        fig.update_layout(height=650, template="plotly_white", hovermode="x unified")
        st.plotly_chart(fig, width='stretch')

        corr_now = ranked.iloc[chart_idx]["Correlation Now"]
        corr_old = ranked.iloc[chart_idx]["Correlation 30d Ago"]
        direction = "strengthened" if corr_now > corr_old else "weakened"
        st.info(f"**{selected_name}** shows {window}d correlation of **{corr_now}** with {chart_commodity_name}. "
                f"Has **{direction}** from {corr_old} a month ago.")

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

# ===== TAB 4: Seasonality =====
with tab4:
    st.subheader("Historical monthly patterns")
    st.caption("Based on the last few years of daily data. Significance marked when p < 0.10 (i.e. the pattern is unlikely to be pure noise).")

    sub1, sub2, sub3 = st.tabs(["By Stock", "By Sector", "Sector × Month Heatmap"])

    # --- Sub-tab: By stock ---
    with sub1:
        options = [f"{name} [{STOCK_SECTOR[ticker]}]" for ticker, name in ALL_STOCKS.items()]
        selected = st.selectbox("Pick a stock", options, key="season_stock")
        selected_name = selected.split(" [")[0]
        selected_ticker = next(t for t, n in ALL_STOCKS.items() if n == selected_name)

        table = seasonality_table(returns[selected_ticker])

        if table.empty:
            st.warning("Not enough data for this stock.")
        else:
            col1, col2 = st.columns([1, 1])
            with col1:
                st.dataframe(table.drop(columns=["Month_Num"]), width='stretch', hide_index=True)

            with col2:
                fig = go.Figure()
                colors = ["green" if v > 0 else "crimson" for v in table["Avg Return %"]]
                fig.add_trace(go.Bar(x=table["Month"], y=table["Avg Return %"], marker_color=colors,
                                     text=[f"{v:.1f}%" for v in table["Avg Return %"]], textposition="outside"))
                fig.add_hline(y=0, line_color="gray")
                fig.update_layout(
                    title=f"{selected_name} — Average Return by Month",
                    yaxis_title="Avg Return %",
                    template="plotly_white",
                    height=400
                )
                st.plotly_chart(fig, width='stretch')

            # Highlight best/worst months
            best = table.loc[table["Avg Return %"].idxmax()]
            worst = table.loc[table["Avg Return %"].idxmin()]
            st.info(f"**Best historical month:** {best['Month']} (avg {best['Avg Return %']}%, win rate {best['Win Rate %']}%, {best['Years of Data']} years of data)")
            st.warning(f"**Worst historical month:** {worst['Month']} (avg {worst['Avg Return %']}%, win rate {worst['Win Rate %']}%)")

    # --- Sub-tab: By sector ---
    with sub2:
        sector_choice = st.selectbox("Pick a sector", list(STOCKS.keys()), key="season_sector")
        sector_table = sector_seasonality_table(returns, sector_choice)

        if sector_table.empty:
            st.warning("Not enough data for this sector.")
        else:
            col1, col2 = st.columns([1, 1])
            with col1:
                st.dataframe(sector_table.drop(columns=["Month_Num"]), width='stretch', hide_index=True)
            with col2:
                fig = go.Figure()
                colors = ["green" if v > 0 else "crimson" for v in sector_table["Avg Return %"]]
                fig.add_trace(go.Bar(x=sector_table["Month"], y=sector_table["Avg Return %"], marker_color=colors,
                                     text=[f"{v:.1f}%" for v in sector_table["Avg Return %"]], textposition="outside"))
                fig.add_hline(y=0, line_color="gray")
                fig.update_layout(
                    title=f"{sector_choice} — Sector Avg Return by Month (equal-weighted)",
                    yaxis_title="Avg Return %",
                    template="plotly_white",
                    height=400
                )
                st.plotly_chart(fig, width='stretch')

    # --- Sub-tab: Heatmap ---
    with sub3:
        st.markdown("**The big picture:** which sector tends to perform when?")
        heatmap_df = sector_month_heatmap_data(returns)

        if heatmap_df.empty:
            st.warning("Not enough data to build the heatmap.")
        else:
            fig = go.Figure(data=go.Heatmap(
                z=heatmap_df.values,
                x=heatmap_df.columns,
                y=heatmap_df.index,
                colorscale="RdYlGn",
                zmid=0,
                text=heatmap_df.round(1).values,
                texttemplate="%{text}%",
                colorbar=dict(title="Avg Return %"),
            ))
            fig.update_layout(
                title="Sector × Month — Average Historical Return",
                template="plotly_white",
                height=500,
                xaxis_title="Month",
                yaxis_title="Sector",
            )
            st.plotly_chart(fig, width='stretch')

            st.caption("Green = historically positive month for that sector. Red = historically negative. Look for diagonal patterns and stand-out cells.")

           # ===== TAB 5: Pattern Matching =====
with tab5:
    st.subheader("Chart pattern matching using Dynamic Time Warping (DTW)")
    st.caption(
        "DTW compares chart shapes regardless of speed. Sector filtering keeps matches relevant. "
        "Always read the forward-return spread — tight clusters = signal, wide spreads = noise."
    )

    pm_sub1, pm_sub2, pm_sub3 = st.tabs(
        ["Historical Analogues", "Current Peers", "International Leader Scan"]
    )

    # ============== HISTORICAL ANALOGUES ==============
    with pm_sub1:
        c1, c2, c3, c4 = st.columns([2, 1, 1, 1])
        with c1:
            options = list(ALL_STOCKS.values())
            choice = st.selectbox("Stock", options, key="pm_hist_stock")
            chosen_ticker = next(t for t, n in ALL_STOCKS.items() if n == choice)
        with c2:
            pattern_window = st.selectbox("Pattern (days)", [30, 60, 90, 120], index=1, key="pm_hist_win")
        with c3:
            forward_horizon = st.selectbox("Forward (days)", [30, 60, 90], index=1, key="pm_hist_fwd")
        with c4:
            sector_only = st.checkbox("Same sector only", value=True, key="pm_hist_sector",
                                       help="Limits matches to the query stock's sector. Recommended ON — cross-sector matches are usually noise.")

        # Query stock's recent performance card
        query_series = prices[chosen_ticker].dropna()
        recent_ret = (query_series.iloc[-1] / query_series.iloc[-pattern_window] - 1) * 100
        st.markdown(
            f"**Query:** {choice} — last {pattern_window} days: "
            f"<span style='color:{'#22c55e' if recent_ret >= 0 else '#ef4444'};font-weight:600'>{recent_ret:+.1f}%</span>",
            unsafe_allow_html=True,
        )

        with st.spinner("Scanning history..."):
            results, query_pat, paths = find_historical_analogues(
                prices, chosen_ticker,
                window=pattern_window, top_n=5,
                forward_days=forward_horizon, step_days=10,
                same_sector_only=sector_only,
            )

        if results.empty:
            st.warning(
                "No close historical matches found. Try: (a) turning off 'Same sector only', "
                "(b) shorter pattern window, or (c) different stock. "
                "An empty result is informative — means this stock's current shape is unusual."
            )
        else:
            # Summary header
            fwd_col = f"Forward {forward_horizon}d Return %"
            avg_fwd = results[fwd_col].mean()
            win_rate = (results[fwd_col] > 0).sum() / len(results) * 100
            spread = results[fwd_col].max() - results[fwd_col].min()

            summary_color = "#22c55e" if avg_fwd > 0 else "#ef4444"
            spread_signal = "tight cluster ✓" if spread < 15 else "wide spread — noisy" if spread > 30 else "moderate spread"

            st.markdown(f"""
            <div style='background:#1e293b;padding:14px 18px;border-radius:8px;margin:12px 0;border-left:4px solid {summary_color}'>
              <div style='display:flex;gap:30px;flex-wrap:wrap'>
                <div><div style='color:#94a3b8;font-size:12px'>AVG FORWARD RETURN</div>
                     <div style='color:{summary_color};font-size:22px;font-weight:700'>{avg_fwd:+.1f}%</div></div>
                <div><div style='color:#94a3b8;font-size:12px'>WIN RATE</div>
                     <div style='color:#e2e8f0;font-size:22px;font-weight:700'>{win_rate:.0f}%</div></div>
                <div><div style='color:#94a3b8;font-size:12px'>SPREAD</div>
                     <div style='color:#e2e8f0;font-size:22px;font-weight:700'>{spread:.1f}pp</div>
                     <div style='color:#94a3b8;font-size:11px'>{spread_signal}</div></div>
                <div><div style='color:#94a3b8;font-size:12px'>SAMPLE SIZE</div>
                     <div style='color:#e2e8f0;font-size:22px;font-weight:700'>{len(results)}</div></div>
              </div>
            </div>
            """, unsafe_allow_html=True)

            st.dataframe(results, width='stretch', hide_index=True)

            # Per-match charts — the visual proof
            st.markdown("### Visual comparison: query pattern vs each historical match")
            st.caption("Left half of each chart = the matched historical pattern. Right half = what happened next.")

            for idx, row in results.iterrows():
                pattern = paths[idx]["pattern"]
                forward = paths[idx]["forward"]
                fwd_ret = row[fwd_col]
                color = "#22c55e" if fwd_ret >= 0 else "#ef4444"

                fig = go.Figure()
                # Query pattern (the present)
                fig.add_trace(go.Scatter(
                    y=query_pat, mode="lines", name=f"Now: {choice}",
                    line=dict(color="#60a5fa", width=2.5)
                ))
                # Historical pattern (the past)
                fig.add_trace(go.Scatter(
                    y=pattern, mode="lines", name=f"Then: {row['Name']} ({row['Pattern End Date']})",
                    line=dict(color="#cbd5e1", width=2, dash="dot")
                ))
                # What happened next, shifted to start where the pattern ends
                forward_x = list(range(len(pattern) - 1, len(pattern) - 1 + len(forward)))
                fig.add_trace(go.Scatter(
                    x=forward_x, y=pattern[-1] + forward, mode="lines",
                    name=f"Forward {forward_horizon}d ({fwd_ret:+.1f}%)",
                    line=dict(color=color, width=2.5)
                ))
                fig.update_layout(
                    height=280,
                    margin=dict(l=10, r=10, t=40, b=10),
                    title=dict(
                        text=f"<b>{row['Name']}</b> · {row['Pattern End Date']} · DTW {row['DTW Distance']} · "
                             f"<span style='color:{color}'>{fwd_ret:+.1f}%</span>",
                        font=dict(size=14)
                    ),
                    template="plotly_dark",
                    showlegend=True,
                    legend=dict(orientation="h", y=-0.15),
                    yaxis_title="Normalized return path",
                    xaxis_title="Days",
                )
                st.plotly_chart(fig, width='stretch')

            st.info(
                "**How to read this:** each grey dotted line is a past chart that looked like the blue (now) line. "
                "The green/red line is what happened next in that past case. If most green/red lines move the same way, "
                "it's a real signal. If they're all over the place, the pattern isn't predictive — move on."
            )

    # ============== CURRENT PEERS ==============
    with pm_sub2:
        c1, c2, c3 = st.columns([2, 1, 1])
        with c1:
            choice = st.selectbox("Stock", list(ALL_STOCKS.values()), key="pm_peer_stock")
            chosen_ticker = next(t for t, n in ALL_STOCKS.items() if n == choice)
        with c2:
            peer_window = st.selectbox("Window (days)", [30, 60, 90], index=1, key="pm_peer_win")
        with c3:
            peer_sector_only = st.checkbox("Same sector only", value=False, key="pm_peer_sector",
                                            help="OFF by default — peer scan often reveals cross-sector co-movement.")

        results, query_pat, peer_pats = find_current_peers(
            prices, chosen_ticker, window=peer_window, top_n=8, same_sector_only=peer_sector_only,
        )

        if results.empty:
            st.warning("No close peers under current threshold.")
        else:
            st.dataframe(results, width='stretch', hide_index=True)

            st.markdown("### Visual overlay: query vs current peers")
            fig = go.Figure()
            fig.add_trace(go.Scatter(
                y=query_pat, mode="lines", name=f"{choice} (you)",
                line=dict(color="#60a5fa", width=3)
            ))
            peer_colors = ["#fbbf24", "#a78bfa", "#34d399", "#f87171", "#fb923c", "#22d3ee", "#e879f9", "#fcd34d"]
            for idx, row in results.iterrows():
                fig.add_trace(go.Scatter(
                    y=peer_pats[idx], mode="lines",
                    name=f"{row['Name']} (d={row['DTW Distance']})",
                    line=dict(color=peer_colors[idx % len(peer_colors)], width=1.5, dash="dot"),
                    opacity=0.7,
                ))
            fig.update_layout(
                height=420, template="plotly_dark",
                title=f"Stocks moving like {choice} — last {peer_window} days",
                yaxis_title="Normalized return path",
                xaxis_title="Days",
                legend=dict(orientation="h", y=-0.2),
                margin=dict(l=10, r=10, t=50, b=10),
            )
            st.plotly_chart(fig, width='stretch')
            st.caption("Solid blue = your stock. Dotted lines = stocks moving similarly right now. Useful for spotting laggards/leaders within a co-moving group.")

    # ============== INTERNATIONAL LEADER SCAN ==============
    with pm_sub3:
        st.markdown(
            "**Premise:** international stocks sometimes lead Indian peers. "
            "We take an international ticker's pattern from `lead_days` ago and find Indian stocks "
            "whose *current* pattern matches it."
        )

        c1, c2, c3 = st.columns(3)
        with c1:
            intl_choice = st.selectbox("International ticker", list(INTERNATIONAL.values()), key="pm_intl_stock")
            intl_ticker = next(t for t, n in INTERNATIONAL.items() if n == intl_choice)
        with c2:
            lead = st.selectbox("Lead days", [15, 30, 45, 60], index=1, key="pm_intl_lead")
        with c3:
            intl_window = st.selectbox("Pattern (days)", [30, 60, 90], index=1, key="pm_intl_win")

        results, intl_pat, intl_fwd, peer_pats = find_international_leader_matches(
            prices, intl_ticker, lead_days=lead, window=intl_window, top_n=8,
        )

        if results.empty:
            st.warning("No close matches.")
        else:
            # How did the international stock itself move after the pattern?
            intl_return = (np.exp(intl_fwd[-1]) - 1) * 100 if intl_fwd is not None else 0
            color = "#22c55e" if intl_return >= 0 else "#ef4444"

            st.markdown(
                f"**{intl_choice}** moved "
                f"<span style='color:{color};font-weight:700'>{intl_return:+.1f}%</span> "
                f"in the {lead} days after its reference pattern.",
                unsafe_allow_html=True,
            )

            st.dataframe(results, width='stretch', hide_index=True)

            st.markdown(f"### How {intl_choice}'s past pattern + its forward move compares to today's Indian matches")
            fig = go.Figure()
            # International past pattern
            fig.add_trace(go.Scatter(
                y=intl_pat, mode="lines", name=f"{intl_choice} (then)",
                line=dict(color="#cbd5e1", width=2, dash="dot")
            ))
            # International forward (what happened after)
            forward_x = list(range(len(intl_pat) - 1, len(intl_pat) - 1 + len(intl_fwd)))
            fig.add_trace(go.Scatter(
                x=forward_x, y=intl_pat[-1] + intl_fwd, mode="lines",
                name=f"{intl_choice} (forward {lead}d)",
                line=dict(color=color, width=3)
            ))
            # Top Indian matches as faint overlays
            peer_colors = ["#fbbf24", "#a78bfa", "#34d399", "#f87171", "#fb923c"]
            for idx in list(results.index)[:5]:
                row = results.loc[idx]
                fig.add_trace(go.Scatter(
                    y=peer_pats[idx], mode="lines",
                    name=f"{row['Name']} (now, d={row['DTW Distance']})",
                    line=dict(color=peer_colors[idx % len(peer_colors)], width=1.5),
                    opacity=0.6,
                ))
            fig.update_layout(
                height=450, template="plotly_dark",
                yaxis_title="Normalized return path",
                xaxis_title="Days",
                legend=dict(orientation="h", y=-0.2),
                margin=dict(l=10, r=10, t=30, b=10),
            )
            st.plotly_chart(fig, width='stretch')

            st.info(
                f"**Interpretation:** if the pattern holds, the Indian matches above might track {intl_choice}'s "
                f"forward move ({intl_return:+.1f}%) over the next {lead} days. "
                f"⚠️ This is a hypothesis, not a forecast — different macro, different flows."
            )
# ===== TAB 6: Supply Chain =====
with tab6:
    st.subheader("Supply chain mapping & cascade signals")
    st.caption(
        "Causal relationships between Indian stocks. Curated by hand from annual reports — "
        "partial coverage, ~60 relationships across major sectors. "
        "Every supposed link is validated against actual price correlation in the data."
    )

    graph_tickers = all_tickers_in_graph()
    graph_stocks = {t: ALL_STOCKS[t] for t in graph_tickers if t in ALL_STOCKS}

    sc_sub1, sc_sub2, sc_sub3 = st.tabs(
        ["Find Suppliers", "Find Customers", "⚡ Cascade Signal"]
    )

    # ============ SUB 1: Find Suppliers ============
    with sc_sub1:
        st.markdown("**Pick a customer — see who supplies them, and whether the price data confirms the link.**")

        customers_in_graph = sorted([(t, n) for t, n in graph_stocks.items() if get_suppliers_of(t)],
                                     key=lambda x: x[1])
        if not customers_in_graph:
            st.warning("No customers in the graph yet.")
        else:
            options = [n for _, n in customers_in_graph]
            choice = st.selectbox("Customer", options, key="sc_customer")
            customer_ticker = next(t for t, n in customers_in_graph if n == choice)

            df = suppliers_table_with_validation(returns, customer_ticker, window=window)
            if df.empty:
                st.warning("No suppliers mapped yet for this stock.")
            else:
                st.dataframe(df, width='stretch', hide_index=True)
                st.caption(
                    "**How to read this:** Supply Chain Weight = how dependent the supplier is on this customer. "
                    "Correlation Now = whether their stock returns actually move together in current data. "
                    "Strong supply chain link + strong correlation = clean signal. "
                    "Strong supply chain link + weak correlation = relationship exists on paper but isn't priced together (could be opportunity OR could mean the link is overstated)."
                )

    # ============ SUB 2: Find Customers ============
    with sc_sub2:
        st.markdown("**Pick a supplier — see who buys from them, and validate the link.**")

        suppliers_in_graph = sorted([(t, n) for t, n in graph_stocks.items() if get_customers_of(t)],
                                     key=lambda x: x[1])
        if not suppliers_in_graph:
            st.warning("No suppliers in the graph yet.")
        else:
            options = [n for _, n in suppliers_in_graph]
            choice = st.selectbox("Supplier", options, key="sc_supplier")
            supplier_ticker = next(t for t, n in suppliers_in_graph if n == choice)

            df = customers_table_with_validation(returns, supplier_ticker, window=window)
            if df.empty:
                st.warning("No customers mapped for this supplier.")
            else:
                st.dataframe(df, width='stretch', hide_index=True)

    # ============ SUB 3: CASCADE SIGNAL ============
    with sc_sub3:
        st.markdown("### The integrated signal — Phase 4 payoff")
        st.markdown(
            "**Scenario:** A major company just moved. Which of its suppliers should you watch? "
            "This view scores suppliers using four independent signals:"
        )
        st.markdown(
            "- **Supply chain weight** — how revenue-dependent the supplier is on this customer\n"
            "- **Validated correlation** — do their stock returns actually move together?\n"
            "- **Lag** — has the supplier already moved, or is it still lagging the customer's move (catch-up potential)?\n"
            "- **Seasonality** — is this historically a good month for the supplier?"
        )

        customers_in_graph = sorted([(t, n) for t, n in graph_stocks.items() if get_suppliers_of(t)],
                                     key=lambda x: x[1])
        options = [n for _, n in customers_in_graph]
        choice = st.selectbox("Pick the customer that just moved", options, key="sc_cascade")
        customer_ticker = next(t for t, n in customers_in_graph if n == choice)

        cascade_df = cascade_signal(returns, prices, customer_ticker, window=window)
        if cascade_df.empty:
            st.warning("No suppliers mapped for this customer yet.")
        else:
            # Highlight the customer's own recent move
            customer_5d = cascade_df.iloc[0]["Customer 5d %"] if len(cascade_df) > 0 else 0
            move_color = "#22c55e" if customer_5d >= 0 else "#ef4444"
            st.markdown(
                f"**{choice}** moved <span style='color:{move_color};font-weight:700'>{customer_5d:+.1f}%</span> "
                f"in the last 5 days. Suppliers ranked by composite cascade score below:",
                unsafe_allow_html=True,
            )

            st.dataframe(cascade_df, width='stretch', hide_index=True)

            # Top pick highlight
            top = cascade_df.iloc[0]
            st.success(
                f"**Top cascade pick: {top['Supplier']}** — Score {top['Score']}. "
                f"Supply chain weight {top['SC Weight']}, correlation {top['Corr Now']}, "
                f"already moved {top['Supplier 5d %']:+.1f}% (lag vs customer = {top['Lag (5d)']:+.1f}pp), "
                f"historical avg return this month = {top['Season Month %']:+.1f}%."
            )

            st.caption(
                "⚠️ **Reality check:** This is a *ranked list of candidates worth investigating*, not a buy signal. "
                "Multi-factor scoring reduces noise but cannot create certainty. "
                "Position sizing and risk management are where money is actually made or lost."
            )
# ===== TAB 7: Backtest =====
with tab7:
    st.subheader("Backtest: does the cascade signal actually predict forward returns?")
    st.caption(
        "Tests the cascade signal against three benchmarks across historical trigger events. "
        "Conservative methodology: no look-ahead bias, transaction costs included, honest verdict."
    )

    with st.expander("ℹ️ How this backtest is built (read this once)"):
        st.markdown("""
        **What we're testing:** when a customer stock moves significantly, does the cascade signal's
        top-ranked supplier outperform alternatives over the next N days?

        **Three benchmarks:**
        - **Random supplier** — picks one supplier at random from the mapped set
        - **Sector portfolio** — equal-weight return of ALL mapped suppliers
        - **Universe average** — average return across all 73 stocks

        **Bias controls built in:**
        - *No look-ahead:* cascade signal at time T uses only data available at time T
        - *Transaction costs:* 0.3% per side (0.6% round-trip) applied to every cascade trade
        - *Survivorship bias acknowledged:* we test only on the current universe (limitation)
        - *No overfitting:* cascade weights are fixed, not tuned to backtest results

        **Honest verdict:** the system computes a verdict automatically from the numbers,
        with thresholds set upfront. Negative verdicts are reported as clearly as positive ones.
        """)

    c1, c2, c3 = st.columns(3)
    with c1:
        trigger_pct = st.selectbox("Trigger: customer move %", [3.0, 5.0, 7.0], index=1)
    with c2:
        holding_days = st.selectbox("Holding period (days)", [5, 10, 20], index=1)
    with c3:
        direction = st.selectbox("Direction", ["up", "down", "both"], index=0)

    if st.button("▶ Run backtest", type="primary"):
        with st.spinner("Running backtest... (typically 20-40 seconds)"):
            result = run_backtest(
                returns, prices,
                trigger_pct=trigger_pct,
                holding_days=holding_days,
                direction=direction,
                correlation_window=window,
            )

        if result["status"] == "insufficient_events":
            st.warning(result["message"])
        elif result["status"] == "no_valid_trades":
            st.warning(f"Found {result['n_events']} triggers but no valid trades could be computed.")
        else:
            # Verdict banner
            v_color_map = {"success": "success", "info": "info", "warning": "warning", "error": "error"}
            getattr(st, v_color_map[result["verdict_color"]])(f"**Verdict:** {result['verdict']}")

            # Metrics row
            m = result["metrics"]
            mc1, mc2, mc3, mc4 = st.columns(4)
            mc1.metric("Trades", result["n_trades"])
            mc2.metric("Avg Excess vs Portfolio", f"{m['avg_excess_vs_portfolio']:+.2f}pp")
            mc3.metric("Win Rate vs Portfolio", f"{m['win_rate_vs_portfolio']:.0f}%")
            mc4.metric("Sharpe-like", f"{m['sharpe_like']:.2f}")

            st.markdown("---")
            st.markdown("### Equity curve — cumulative excess return over time")
            st.caption("Each trade contributes its excess return vs the sector portfolio. "
                       "Upward trend = signal has cumulative edge. Flat or downward = no edge.")

            equity_fig = go.Figure()
            equity_fig.add_trace(go.Scatter(
                x=result["trades"]["Date"],
                y=result["trades"]["Cumulative Excess %"],
                mode="lines+markers",
                line=dict(color="#22c55e" if m['avg_excess_vs_portfolio'] > 0 else "#ef4444", width=2),
                fill="tozeroy",
                fillcolor="rgba(34,197,94,0.1)" if m['avg_excess_vs_portfolio'] > 0 else "rgba(239,68,68,0.1)",
            ))
            equity_fig.add_hline(y=0, line_dash="dash", line_color="gray")
            equity_fig.update_layout(
                height=350, template="plotly_white",
                yaxis_title="Cumulative excess return (pp)",
                xaxis_title="Trade date",
                margin=dict(l=10, r=10, t=20, b=10),
            )
            st.plotly_chart(equity_fig, width='stretch')

            st.markdown("### Distribution of per-trade outcomes")
            st.caption("Where the trades actually landed. A tight distribution centered above 0 = real edge. "
                       "Wide distribution centered near 0 = noise.")

            hist_fig = go.Figure(data=[go.Histogram(
                x=result["trades"]["Excess vs Portfolio"],
                nbinsx=20,
                marker_color="#60a5fa",
            )])
            hist_fig.add_vline(x=0, line_dash="dash", line_color="gray")
            hist_fig.add_vline(x=m['avg_excess_vs_portfolio'], line_color="#ef4444", line_width=2,
                                annotation_text=f"Mean: {m['avg_excess_vs_portfolio']:+.1f}pp")
            hist_fig.update_layout(
                height=300, template="plotly_white",
                xaxis_title="Excess return vs portfolio (pp)",
                yaxis_title="Number of trades",
                margin=dict(l=10, r=10, t=30, b=10),
            )
            st.plotly_chart(hist_fig, width='stretch')

            st.markdown("### Breakdown by customer sector")
            st.caption("Does the signal work better in some sectors than others?")
            st.dataframe(result["by_sector"], width='stretch', hide_index=True)

            st.markdown("### All trades (audit trail)")
            st.caption("Every individual trade the backtest executed. Sanity-check: do these dates and stocks make sense?")
            st.dataframe(result["trades"], width='stretch', hide_index=True)