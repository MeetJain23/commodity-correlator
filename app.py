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
from universe import INTERNATIONAL
from universe import COMMODITIES, ALL_STOCKS, STOCKS , STOCK_SECTOR
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
tab1, tab2, tab3, tab4, tab5 = st.tabs(["🪙 By Commodity", "🏢 By Stock", "⚡ Regime Changes", "📅 Seasonality", "🔍 Pattern Match"])

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
    st.dataframe(ranked, width='stretch', hide_index=True)

    if len(ranked) > 0:
        st.markdown("---")
        st.markdown("### Deep dive — pick any commodity from the table above")

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