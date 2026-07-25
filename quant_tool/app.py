import logging
from datetime import datetime, timezone

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

from quant_tool.config import SYMBOLS, MIN_RISK_REWARD_RATIO
from quant_tool.database.db_handler import (
    init_db,
    load_market_data,
    load_sentiment,
    load_signals,
    load_paper_trades,
)
from quant_tool.analytics.indicators import compute_indicators
from quant_tool.analytics.signals import evaluate_signals, latest_sentiment
from quant_tool.analytics.learning_calculator import (
    project_growth,
    estimate_time_for_target,
    risk_calculator,
)
from quant_tool.analytics.asset_guides import get_guide, TRADING_GUIDES
from quant_tool.analytics.regime import detect_regime
from quant_tool.analytics.backtester import PaperTrader
from quant_tool.database.data_quality import freshness_status
from quant_tool.fetchers.crypto_feed import fetch_all_crypto
from quant_tool.fetchers.stock_feed import fetch_all_stocks_and_forex
from quant_tool.fetchers.sentiment_feed import fetch_all_sentiment

logger = logging.getLogger("quant_tool.dashboard")

st.set_page_config(
    page_title="Quant Trading Dashboard",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="collapsed",
)

st.markdown(
    """
<style>
.block-container { max-width: 100%; padding: 1rem 1rem; }
.kpi-card {
    background: #1e1e2e;
    border-radius: 12px;
    padding: 1rem;
    text-align: center;
    box-shadow: 0 2px 8px rgba(0,0,0,0.3);
}
.kpi-card .label { font-size: 0.75rem; color: #888; text-transform: uppercase; letter-spacing: 0.5px; }
.kpi-card .value { font-size: 1.4rem; font-weight: 700; margin-top: 2px; }
.guide-card {
    background: #1a1a2e;
    border-radius: 8px; padding: 10px;
    margin: 4px 0; height: 100%;
}
.guide-label {
    font-size: 0.7rem; color: #888; text-transform: uppercase; letter-spacing: 0.5px;
}
.guide-val {
    font-size: 0.85rem; display: block; margin-top: 2px;
}
@media (max-width: 768px) {
    .kpi-card .value { font-size: 1rem; }
    .guide-val { font-size: 0.8rem; }
}
</style>
""",
    unsafe_allow_html=True,
)


@st.cache_data(ttl=300)
def cached_market_data(symbol: str, limit: int = 500):
    return load_market_data(symbol, limit)


@st.cache_data(ttl=300)
def cached_indicators(symbol: str, lookback: int = 500):
    return compute_indicators(symbol, lookback)


@st.cache_data(ttl=120)
def cached_sentiment(symbol: str):
    return latest_sentiment(symbol)


@st.cache_data(ttl=120)
def cached_signals(symbol: str):
    return load_signals(symbol, limit=20)


@st.cache_data(ttl=60)
def cached_portfolio_summary():
    return PaperTrader().summary()


@st.cache_data(ttl=60)
def cached_paper_trades(status: str = "all"):
    return load_paper_trades(status)


@st.cache_data(ttl=300)
def cached_freshness(symbol: str):
    return freshness_status(symbol)


@st.cache_data(ttl=300)
def cached_regime(symbol: str):
    return detect_regime(symbol)


def kpi_card(label: str, value: str, color: str = "#fff"):
    return f"""
    <div class="kpi-card">
        <div class="label">{label}</div>
        <div class="value" style="color:{color}">{value}</div>
    </div>
    """


def plot_candlestick(symbol: str, df: pd.DataFrame):
    if df.empty:
        return go.Figure()

    fig = make_subplots(
        rows=3, cols=1,
        shared_xaxes=True,
        vertical_spacing=0.04,
        row_heights=[0.55, 0.25, 0.20],
        subplot_titles=(f"{symbol} — Price", "RSI", "Volume"),
    )

    fig.add_trace(
        go.Candlestick(
            x=df.index,
            open=df["open"],
            high=df["high"],
            low=df["low"],
            close=df["close"],
            name="OHLC",
        ),
        row=1, col=1,
    )

    if "ema_20" in df.columns:
        fig.add_trace(
            go.Scatter(x=df.index, y=df["ema_20"], line=dict(width=1, color="#ffa726"), name="EMA 20"),
            row=1, col=1,
        )
    if "ema_50" in df.columns:
        fig.add_trace(
            go.Scatter(x=df.index, y=df["ema_50"], line=dict(width=1, color="#ab47bc"), name="EMA 50"),
            row=1, col=1,
        )
    if "sma_200" in df.columns:
        fig.add_trace(
            go.Scatter(x=df.index, y=df["sma_200"], line=dict(width=1, color="#ef5350"), name="SMA 200"),
            row=1, col=1,
        )
    if "bb_upper" in df.columns and "bb_lower" in df.columns:
        fig.add_trace(
            go.Scatter(x=df.index, y=df["bb_upper"], line=dict(width=0.5, color="#888", dash="dash"), name="BB Upper"),
            row=1, col=1,
        )
        fig.add_trace(
            go.Scatter(x=df.index, y=df["bb_lower"], line=dict(width=0.5, color="#888", dash="dash"), name="BB Lower"),
            row=1, col=1,
        )

    if "rsi" in df.columns:
        fig.add_trace(
            go.Scatter(x=df.index, y=df["rsi"], line=dict(color="#7c4dff"), name="RSI"),
            row=2, col=1,
        )
        fig.add_hline(y=70, line_dash="dash", line_color="red", row=2, col=1)
        fig.add_hline(y=30, line_dash="dash", line_color="green", row=2, col=1)
        fig.update_yaxes(range=[0, 100], row=2, col=1)

    fig.add_trace(
        go.Bar(x=df.index, y=df["volume"], name="Volume", marker_color="#42a5f5"),
        row=3, col=1,
    )

    fig.update_layout(
        height=550,
        margin=dict(l=10, r=10, t=40, b=10),
        template="plotly_dark",
        showlegend=False,
        xaxis_rangeslider_visible=False,
    )
    fig.update_yaxes(title_text="Price", row=1, col=1)
    fig.update_yaxes(title_text="RSI", row=2, col=1)
    fig.update_yaxes(title_text="Volume", row=3, col=1)

    return fig


def main():
    init_db()

    st.title("📊 Quant Trading Dashboard")

    tab1, tab2, tab3 = st.tabs(["📊 Dashboard", "🎓 Beginner Guide & Simulator", "📈 Portfolio"])

    with tab1:
        with st.expander("⚙️ Manual Data Refresh", expanded=False):
            col1, col2, col3 = st.columns(3)
            if col1.button("🔄 Fetch Crypto"):
                with st.spinner("Fetching crypto data..."):
                    rows = fetch_all_crypto()
                    st.success(f"Fetched {len(rows)} crypto bars")
                    st.cache_data.clear()

            if col2.button("🔄 Fetch Stocks/Forex"):
                with st.spinner("Fetching stock & forex data..."):
                    rows = fetch_all_stocks_and_forex()
                    st.success(f"Fetched {len(rows)} stock/forex bars")
                    st.cache_data.clear()

            if col3.button("🔄 Fetch Sentiment"):
                with st.spinner("Fetching sentiment data..."):
                    rows = fetch_all_sentiment()
                    st.success(f"Fetched {len(rows)} sentiment entries")
                    st.cache_data.clear()

        all_symbols = []
        for asset_class, symbols in SYMBOLS.items():
            for sym in symbols:
                all_symbols.append({"symbol": sym, "class": asset_class})

        selected = st.selectbox(
            "Select Asset",
            options=[s["symbol"] for s in all_symbols],
            format_func=lambda x: x,
        )

        rows = cached_market_data(selected, limit=500)
        df = cached_indicators(selected, lookback=500)
        sentiment = cached_sentiment(selected)
        signals = cached_signals(selected)

        guide = get_guide(selected)
        with st.expander(f"💡 How to Trade {selected}", expanded=True):
            c1, c2 = st.columns(2)
            c1.markdown(
                f"<div class='guide-card'><span class='guide-label'>Market</span>"
                f"<span class='guide-val'>{guide['market_type']}</span></div>"
                f"<div class='guide-card'><span class='guide-label'>Style</span>"
                f"<span class='guide-val'>{guide['best_style']}</span></div>",
                unsafe_allow_html=True,
            )
            c2.markdown(
                f"<div class='guide-card'><span class='guide-label'>Entry</span>"
                f"<span class='guide-val'>{guide['entry_rule']}</span></div>"
                f"<div class='guide-card'><span class='guide-label'>Exit</span>"
                f"<span class='guide-val'>{guide['exit_rule']}</span></div>",
                unsafe_allow_html=True,
            )
            st.markdown(
                f"<div class='guide-card'><span class='guide-label'>🛑 Risk</span>"
                f"<span class='guide-val'>{guide['risk_rule']}</span></div>",
                unsafe_allow_html=True,
            )

        if df.empty:
            st.info(f"No indicator data for {selected}. Use the refresh buttons above to fetch data.")
        else:
            last = df.iloc[-1]
            price = last["close"]
            rsi = last.get("rsi", 50)
            ema_20 = last.get("ema_20", price)
            ema_50 = last.get("ema_50", price)
            atr = last.get("atr", 0)

            trend = "🟢 Bullish" if (ema_20 > ema_50) else "🔴 Bearish"
            sentiment_label = "🟢 Greed" if sentiment > 0.3 else ("🔴 Fear" if sentiment < -0.3 else "⚪ Neutral")

            regime_info = cached_regime(selected)
            regime_emoji = {
                "trending_bull": "🟢", "trending_bear": "🔴",
                "ranging": "🟡", "high_volatility": "💥", "weak_trend": "🔵", "unknown": "⚪",
            }
            regime_label = regime_emoji.get(regime_info["regime"], "⚪") + " " + regime_info["regime"].replace("_", " ").title()

            data_age = cached_freshness(selected)
            age_emoji = {"fresh": "🟢", "aging": "🟡", "stale": "🔴", "no_data": "⚪"}
            age_label = f"{age_emoji.get(data_age, '⚪')} {data_age.replace('_', ' ').title()}"

            kpi_cols = st.columns([1, 1, 1, 1, 1])
            kpis = [
                ("Price", f"${price:.2f}"),
                ("Trend", trend),
                ("RSI (14)", f"{rsi:.1f}"),
                ("Regime", regime_label),
                ("Data Age", age_label),
            ]
            for col, (label, value) in zip(kpi_cols, kpis):
                col.markdown(kpi_card(label, value), unsafe_allow_html=True)

            col_chart, col_info = st.columns([3, 1])

            with col_chart:
                fig = plot_candlestick(selected, df)
                st.plotly_chart(fig, use_container_width=True)

            with col_info:
                st.subheader("📋 Active Signals")
                if signals:
                    for sig in signals[:10]:
                        emoji_map = {
                            "STRONG_BUY": "🟢", "BUY_WATCH": "👀", "STRONG_SELL": "🔴",
                            "SELL_WATCH": "⚠️", "BULLISH_CROSS": "📈", "BEARISH_CROSS": "📉",
                            "BOUNCE_WATCH": "💫", "BREAKDOWN_WATCH": "💥", "UPTREND": "⬆️", "DOWNTREND": "⬇️",
                        }
                        emoji = emoji_map.get(sig["signal_type"], "📊")
                        st.markdown(
                            f"<div style='background:#1e1e2e;border-radius:8px;padding:6px 10px;margin:4px 0'>"
                            f"<small>{emoji} <b>{sig['signal_type']}</b></small><br>"
                            f"<small style='color:#888'>{sig['indicator_trigger'][:80]}</small></div>",
                            unsafe_allow_html=True,
                        )
                else:
                    st.info("No active signals")

                st.subheader("📰 Recent Sentiment")
                sent_rows = load_sentiment(selected, limit=5)
                if sent_rows:
                    for s in sent_rows[:5]:
                        st.markdown(
                            f"<div style='font-size:0.85rem;padding:2px 0'>{s['headline'][:60]}... "
                            f"<b style='color:{'#4caf50' if s['sentiment_score']>0 else '#ef5350'}'>{s['sentiment_score']:+.2f}</b></div>",
                            unsafe_allow_html=True,
                        )
                else:
                    st.info("No sentiment data")

            st.caption(f"⏰ Last updated: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S')} UTC")

    with tab2:
        st.subheader("🎓 Beginner Guide & Profit Simulator")

        with st.expander("📐 What-If Profit Calculator", expanded=True):
            col_inp, col_out = st.columns([1, 1])
            with col_inp:
                invest_amount = st.number_input("Investment Amount ($)", min_value=10, max_value=100_000, value=100, step=10)
                asset_choice = st.selectbox("Asset Class", ["bitcoin", "stocks", "forex"], format_func=lambda x: x.capitalize())
                risk_choice = st.selectbox("Risk Level", ["conservative", "balanced", "aggressive"], format_func=lambda x: x.capitalize())
                time_horizon = st.slider("Time Horizon (Years)", min_value=1, max_value=30, value=5)

            with col_out:
                proj = project_growth(invest_amount, asset_choice, risk_choice, time_horizon)
                col_a, col_b = st.columns(2)

                dd = (proj["final_value"] - proj["investment"]) / proj["investment"] * 100
                color_dd = "#4caf50" if dd >= 0 else "#ef5350"

                col_a.markdown(kpi_card("Final Value", f"${proj['final_value']:,.2f}"), unsafe_allow_html=True)
                col_a.markdown(kpi_card("Total Return", f"{proj['total_return_pct']:+.2f}%", color_dd), unsafe_allow_html=True)
                col_b.markdown(kpi_card("Annual Return", f"{proj['annual_return']*100:.1f}%"), unsafe_allow_html=True)
                col_b.markdown(kpi_card("Years", f"{proj['years']}"), unsafe_allow_html=True)
                worst, best = proj['final_value_range']
                col_b.markdown(kpi_card("Range (Best–Worst)", f"${worst:,.0f} – ${best:,.0f}", "#ffa726"), unsafe_allow_html=True)

                target_pct = 5.0
                time_est = estimate_time_for_target(asset_choice, risk_choice, target_pct)
                if time_est["days_lower"]:
                    col_b.markdown(
                        kpi_card(
                            f"Time for {target_pct:+.0f}% Move",
                            f"~{time_est['days_lower']}–{time_est['days_upper']} trading days",
                            "#ffa726",
                        ),
                        unsafe_allow_html=True,
                    )

                years_arr = [y["year"] for y in proj["yearly"]]
                values_arr = [y["value"] for y in proj["yearly"]]
                fig_proj = go.Figure()
                fig_proj.add_trace(go.Bar(x=years_arr, y=values_arr, marker_color="#42a5f5", name="Portfolio Value"))
                fig_proj.add_hline(y=proj["investment"], line_dash="dash", line_color="#888", annotation_text="Initial Investment")
                fig_proj.update_layout(
                    height=250, margin=dict(l=10, r=10, t=10, b=10),
                    template="plotly_dark", title="Year-by-Year Growth",
                    xaxis_title="Year", yaxis_title="Value ($)",
                )
                st.plotly_chart(fig_proj, use_container_width=True)

        with st.expander("⚠️ Risk Controller & Position Sizing", expanded=False):
            col_rin, col_rout = st.columns([1, 1])
            with col_rin:
                risk_entry = st.number_input("Entry Price ($)", min_value=0.01, max_value=500_000.0, value=60_000.0, step=100.0)
                risk_invest = st.number_input("Total Investment ($)", min_value=10, max_value=100_000, value=500, step=10)
                risk_asset = st.selectbox(
                    "Asset Class for Risk Calc",
                    ["bitcoin", "stocks", "forex"],
                    format_func=lambda x: x.capitalize(),
                    key="risk_asset",
                )
                risk_stop = st.number_input(
                    "Stop-Loss Price (leave 0 for auto-calc)",
                    min_value=0.0, max_value=500_000.0, value=0.0, step=10.0,
                )
                risk_side = st.selectbox(
                    "Trade Direction",
                    ["buy", "sell"],
                    format_func=lambda x: "Long (Buy)" if x == "buy" else "Short (Sell)",
                    key="risk_side",
                )

            with col_rout:
                rc = risk_calculator(
                    risk_entry, risk_invest, risk_asset,
                    side=risk_side,
                    stop_loss=risk_stop if risk_stop > 0 else None,
                )
                ca, cb = st.columns(2)
                ca.markdown(kpi_card("Max Loss (1% Rule)", f"${rc['max_loss_allowed']:.2f}"), unsafe_allow_html=True)
                ca.markdown(kpi_card("Stop-Loss", f"${rc['stop_loss']:.2f}"), unsafe_allow_html=True)
                ca.markdown(kpi_card("Take-Profit Target", f"${rc['take_profit']:.2f}"), unsafe_allow_html=True)
                cb.markdown(kpi_card("Position Size", f"{rc['position_size_units']:.4f} units"), unsafe_allow_html=True)
                cb.markdown(kpi_card("Cost at Entry", f"${rc['position_size_cost']:.2f}"), unsafe_allow_html=True)
                rr_color = "#4caf50" if rc["rr_passes"] else "#ef5350"
                rr_label = f"{rc['risk_reward_ratio']:.2f} {'✅' if rc['rr_passes'] else '❌'} (min {MIN_RISK_REWARD_RATIO}:1)"
                cb.markdown(kpi_card("Risk:Reward Ratio", rr_label, rr_color), unsafe_allow_html=True)

                alc = rc["allocation_pct"]
                alc_color = "#ef5350" if alc > 90 else "#4caf50"
                alc_label = f"{alc}% {'⚠️' if alc > 90 else '✅'} of investment"
                cb.markdown(kpi_card("Allocation", alc_label, alc_color), unsafe_allow_html=True)

                if not rc["rr_passes"]:
                    st.warning(f"Your R:R ratio ({rc['risk_reward_ratio']:.2f}) is below the {MIN_RISK_REWARD_RATIO}:1 minimum. Consider widening your take-profit or tightening your stop-loss.")
                if alc > 100:
                    st.warning(f"⚠️ Position cost (${rc['position_size_cost']:.2f}) exceeds investment. Consider reducing position size.")
                st.info(f"📌 **1% Rule Applied:** Risking only ${rc['max_loss_allowed']:.2f} (1% of ${risk_invest:.2f})")

        with st.expander("📖 Asset Trading Guides", expanded=False):
            guide_keys = list(TRADING_GUIDES.keys())
            gcols = st.columns(3)
            for idx, key in enumerate(guide_keys):
                g = TRADING_GUIDES[key]
                with gcols[idx]:
                    st.markdown(
                        f"<div style='background:#1e1e2e;border-radius:12px;padding:1rem;height:100%'>"
                        f"<h3 style='margin:0 0 4px 0'>{g['icon']} {g['title']}</h3>"
                        f"<p style='color:#aaa;font-size:0.85rem'><b>Style:</b> {g['style']}</p>"
                        f"<p style='font-size:0.85rem'>{g['description']}</p>"
                        f"</div>",
                        unsafe_allow_html=True,
                    )
                    with st.expander("📥 Entry Strategy"):
                        st.markdown(g["entry"])
                    with st.expander("📤 When to Exit (Take Profit)"):
                        st.markdown(g["exit_take_profit"])
                    with st.expander("🛑 Stop-Loss & Loss Control"):
                        st.markdown(g["exit_stop_loss"])
                        st.markdown(f"**Loss Control:** {g['loss_control']}")
                    with st.expander("💡 Pro Tips"):
                        for tip in g["tips"]:
                            st.markdown(f"- {tip}")


    with tab3:
        st.subheader("📈 Paper Portfolio")

        summary = cached_portfolio_summary()

        kpi_cols = st.columns([1, 1, 1, 1])
        eq_color = "#4caf50" if summary["equity"] >= summary["peak_equity"] else "#ffa726"
        kpi_cols[0].markdown(kpi_card("Equity", f"${summary['equity']:,.2f}", eq_color), unsafe_allow_html=True)
        kpi_cols[1].markdown(kpi_card("Cash", f"${summary['cash']:,.2f}"), unsafe_allow_html=True)
        dd_color = "#ef5350" if summary["drawdown_pct"] > 5 else "#ffa726" if summary["drawdown_pct"] > 2 else "#4caf50"
        kpi_cols[2].markdown(kpi_card("Drawdown", f"{summary['drawdown_pct']:.2f}%", dd_color), unsafe_allow_html=True)
        kpi_cols[3].markdown(kpi_card("Open Positions", str(summary["open_positions"])), unsafe_allow_html=True)

        kpi_cols2 = st.columns([1, 1, 1, 1])
        kpi_cols2[0].markdown(kpi_card("Total Trades", str(summary["total_trades"])), unsafe_allow_html=True)
        wr_color = "#4caf50" if summary["win_rate"] >= 50 else "#ef5350"
        kpi_cols2[1].markdown(kpi_card("Win Rate", f"{summary['win_rate']:.1f}%", wr_color), unsafe_allow_html=True)
        pf_color = "#4caf50" if summary["profit_factor"] >= 2 else "#ffa726" if summary["profit_factor"] >= 1 else "#ef5350"
        kpi_cols2[2].markdown(kpi_card("Profit Factor", str(summary["profit_factor"]), pf_color), unsafe_allow_html=True)
        kpi_cols2[3].markdown(kpi_card("Peak Equity", f"${summary['peak_equity']:,.2f}"), unsafe_allow_html=True)

        # Open positions
        open_trades = cached_paper_trades(status="open")
        if open_trades:
            st.subheader("🔓 Open Positions")
            rows = []
            for t in open_trades:
                dir_emoji = "🟢" if t["side"] == "buy" else "🔴"
                rows.append({
                    "Symbol": t["symbol"],
                    "Side": f"{dir_emoji} {t['side'].upper()}",
                    "Qty": t["quantity"],
                    "Entry": f"${t['entry_price']:.2f}",
                    "Stop": f"${t['stop_loss']:.2f}",
                    "Target": f"${t['take_profit']:.2f}",
                })
            st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)
        else:
            st.info("No open positions")

        # Closed trades
        closed_trades = cached_paper_trades(status="closed")
        if closed_trades:
            st.subheader("📋 Trade History")
            rows = []
            for t in closed_trades[:50]:
                dir_emoji = "🟢" if t["side"] == "buy" else "🔴"
                pnl_color = "#4caf50" if t["pnl"] >= 0 else "#ef5350"
                rows.append({
                    "Symbol": t["symbol"],
                    "Side": f"{dir_emoji} {t['side'].upper()}",
                    "Entry": f"${t['entry_price']:.2f}",
                    "Exit": f"${t['exit_price']:.2f}" if t["exit_price"] else "-",
                    "PnL": f"<span style='color:{pnl_color}'>${t['pnl']:+.2f}</span>",
                    "Return": f"<span style='color:{pnl_color}'>{t['pnl_pct']*100:+.2f}%</span>",
                })
            st.markdown(
                pd.DataFrame(rows).to_html(escape=False, index=False),
                unsafe_allow_html=True,
            )

            # Equity curve from closed trades
            eq_df = pd.DataFrame([dict(t) for t in closed_trades])
            eq_df = eq_df.sort_values("timestamp")
            eq_df["cumulative_pnl"] = eq_df["pnl"].cumsum() + summary["peak_equity"] - sum(t["pnl"] for t in closed_trades)

            fig_eq = go.Figure()
            fig_eq.add_trace(go.Scatter(
                x=eq_df["timestamp"], y=eq_df["cumulative_pnl"],
                mode="lines+markers",
                name="Equity",
                line=dict(color="#42a5f5", width=2),
                fill="tozeroy",
                fillcolor="rgba(66, 165, 245, 0.15)",
            ))
            fig_eq.update_layout(
                height=300,
                margin=dict(l=10, r=10, t=10, b=10),
                template="plotly_dark",
                title="Equity Curve (Closed Trades)",
                xaxis_title="Date",
                yaxis_title="Equity ($)",
            )
            st.plotly_chart(fig_eq, use_container_width=True)
        else:
            st.info("No closed trades yet. Signals will auto-trade via the scheduler.")


if __name__ == "__main__":
    main()
