import logging
import sys
from datetime import datetime, timezone
from pathlib import Path

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

_root = Path(__file__).resolve().parent.parent
if str(_root) not in sys.path:
    sys.path.insert(0, str(_root))

from quant_tool.config import SYMBOLS, MIN_RISK_REWARD_RATIO
from quant_tool.database.db_handler import (
    init_db,
    load_market_data,
    load_sentiment,
    load_signals,
    load_paper_trades,
)
from quant_tool.analytics.indicators import compute_indicators
from quant_tool.analytics.signals import latest_sentiment
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
    page_title="Quant Trading",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

TIMEFRAME_LIMITS = {"1D": 48, "1W": 200, "1M": 750, "1Y": 1500, "ALL": 5000}

st.markdown("""
<style>
html,body,[class*="css"] {
    -webkit-font-smoothing:antialiased;
    -moz-osx-font-smoothing:grayscale;
    font-smooth:never;
}
.block-container { max-width:100%; padding:0.25rem 0.75rem !important; }

.metric-card {
    background:#161b22;
    border:1px solid #30363d;
    border-radius:4px;
    padding:0.35rem 0.65rem;
    display:flex;
    flex-direction:column;
    gap:1px;
}
.metric-card .label {
    font-size:0.55rem;
    color:#8b949e;
    text-transform:uppercase;
    letter-spacing:0.7px;
    font-weight:500;
    line-height:1;
}
.metric-card .value {
    font-size:0.95rem;
    font-weight:600;
    color:#e6edf3;
    line-height:1.2;
    font-variant-numeric:tabular-nums;
}
.metric-card .delta { font-size:0.65rem; font-weight:500; line-height:1; }
.metric-card .delta.pos { color:#3fb950; }
.metric-card .delta.neg { color:#f85149; }
.metric-card .delta.neu { color:#8b949e; }

.watchlist { width:100%; border-collapse:collapse; font-size:0.7rem; }
.watchlist th {
    text-align:left; padding:2px 5px;
    font-size:0.55rem; color:#8b949e;
    text-transform:uppercase; letter-spacing:0.7px;
    font-weight:500; border-bottom:1px solid #30363d;
}
.watchlist td { padding:3px 5px; border-bottom:1px solid #21262d; }
.watchlist tr:hover td { background:#1c2128; }
.watchlist .sym { font-weight:600; color:#e6edf3; }
.watchlist .prc { text-align:right; font-variant-numeric:tabular-nums; }
.watchlist .chg { text-align:right; font-weight:500; font-variant-numeric:tabular-nums; }
.watchlist .cls { text-align:center; font-size:0.55rem; }

div[data-testid="stMetric"] {
    background:#161b22;
    border:1px solid #30363d;
    border-radius:4px;
    padding:0.35rem 0.65rem;
}
div[data-testid="stMetric"] label {
    font-size:0.55rem !important;
    color:#8b949e !important;
    text-transform:uppercase;
    letter-spacing:0.7px;
}
div[data-testid="stMetric"] > div:first-child {
    color:#e6edf3 !important;
    font-weight:600 !important;
    font-variant-numeric:tabular-nums;
}

.section-title {
    font-size:0.6rem;
    color:#8b949e;
    text-transform:uppercase;
    letter-spacing:0.7px;
    font-weight:500;
    margin:0.4rem 0 0.2rem 0;
}

.mono, .watchlist .prc, .watchlist .chg,
.metric-card .value,
div[data-testid="stMetric"] > div:first-child {
    font-family: 'SF Mono','JetBrains Mono','Consolas','Cascadia Code','Fira Code',monospace;
}

.stTabs [data-baseweb="tab"] {
    font-size:0.7rem;
    text-transform:uppercase;
    letter-spacing:0.5px;
    padding:4px 10px;
}
.stTabs [data-baseweb="tab-list"] { gap:2px; }
.stAlert { font-size:0.75rem; }

div[data-testid="stHorizontalBlock"] { gap:0.25rem; }

.stRadio div[role="radiogroup"] {
    display:flex;
    flex-direction:row !important;
    gap:2px;
}
.stRadio div[role="radiogroup"] label {
    background:#21262d;
    border:1px solid #30363d;
    color:#8b949e;
    padding:1px 12px;
    border-radius:3px;
    font-size:0.7rem;
    font-weight:500;
    font-family: 'SF Mono','JetBrains Mono','Consolas','Fira Code',monospace;
    cursor:pointer;
    transition: all 0.15s ease;
}
.stRadio div[role="radiogroup"] label[aria-checked="true"] {
    background:#1f6feb;
    border-color:#1f6feb;
    color:#fff;
}
.stRadio div[role="radiogroup"] label input { display:none; }
.stRadio div[role="radiogroup"] label:hover:not([aria-checked="true"]) {
    border-color:#58a6ff;
    color:#58a6ff;
}

.stSidebar .stButton button {
    font-size:0.7rem;
    border-radius:3px;
    padding:2px 8px;
}
.stSidebar .stSelectbox label {
    font-size:0.6rem;
    color:#8b949e;
    text-transform:uppercase;
    letter-spacing:0.7px;
}
</style>
""", unsafe_allow_html=True)


@st.cache_data(ttl=300)
def cached_market_data(symbol: str, limit: int = 500):
    return [dict(r) for r in load_market_data(symbol, limit)]


@st.cache_data(ttl=300)
def cached_indicators(symbol: str, lookback: int = 500):
    return compute_indicators(symbol, lookback)


@st.cache_data(ttl=120)
def cached_sentiment(symbol: str):
    return latest_sentiment(symbol)


@st.cache_data(ttl=120)
def cached_signals(symbol: str):
    return [dict(r) for r in load_signals(symbol, limit=20)]


@st.cache_data(ttl=60)
def cached_portfolio_summary():
    return PaperTrader().summary()


@st.cache_data(ttl=60)
def cached_paper_trades(status: str = "all"):
    return [dict(r) for r in load_paper_trades(status)]


@st.cache_data(ttl=300)
def cached_freshness(symbol: str):
    return freshness_status(symbol)


@st.cache_data(ttl=300)
def cached_regime(symbol: str):
    return detect_regime(symbol)


@st.cache_data(ttl=120)
def cached_watchlist_data():
    rows = []
    for asset_class, symbols in SYMBOLS.items():
        for sym in symbols:
            mrows = cached_market_data(sym, limit=2)
            price = None
            change_pct = None
            if len(mrows) >= 2:
                price = mrows[-1]["close"]
                prev = mrows[-2]["close"]
                change_pct = (price - prev) / prev * 100 if prev else 0
            elif len(mrows) == 1:
                price = mrows[-1]["close"]
                change_pct = 0.0
            age = cached_freshness(sym)
            rows.append({"symbol": sym, "class": asset_class, "price": price, "change_pct": change_pct, "freshness": age})
    return rows


def metric_card(label: str, value: str, delta: str | None = None, delta_dir: str | None = None) -> str:
    delta_html = ""
    if delta is not None:
        cls = {"up": "pos", "down": "neg", "neutral": "neu"}.get(delta_dir or "neutral", "neu")
        delta_html = f'<div class="delta {cls}">{delta}</div>'
    return f'<div class="metric-card"><div class="label">{label}</div><div class="value">{value}</div>{delta_html}</div>'


def format_volume(vol: float | None) -> str:
    if vol is None or vol <= 0:
        return "--"
    if vol >= 1_000_000_000:
        return f"${vol/1e9:.1f}B"
    if vol >= 1_000_000:
        return f"${vol/1e6:.1f}M"
    if vol >= 1_000:
        return f"${vol/1e3:.1f}K"
    return f"${vol:.0f}"


def _make_gl_trace(x, y, name: str, color: str, width: float = 1, dash: str | None = None, opacity: float = 1.0):
    return go.Scattergl(
        x=x, y=y,
        mode="lines",
        line=dict(width=width, color=color, dash=dash) if dash else dict(width=width, color=color),
        name=name,
        showlegend=False,
        opacity=opacity,
    )


def plot_candlestick(df: pd.DataFrame) -> go.Figure:
    if df.empty:
        return go.Figure()

    fig = make_subplots(
        rows=3, cols=1,
        shared_xaxes=True,
        vertical_spacing=0.02,
        row_heights=[0.55, 0.25, 0.20],
    )

    fig.add_trace(
        go.Candlestick(
            x=df.index, open=df["open"], high=df["high"],
            low=df["low"], close=df["close"], name="",
            increasing_line_color="#3fb950", decreasing_line_color="#f85149",
            whiskerwidth=0.4,
        ),
        row=1, col=1,
    )

    if "ema_20" in df.columns:
        fig.add_trace(_make_gl_trace(df.index, df["ema_20"], "EMA 20", "#ffa726", 0.8), row=1, col=1)
    if "ema_50" in df.columns:
        fig.add_trace(_make_gl_trace(df.index, df["ema_50"], "EMA 50", "#ab47bc", 0.8), row=1, col=1)
    if "sma_200" in df.columns:
        fig.add_trace(_make_gl_trace(df.index, df["sma_200"], "SMA 200", "#ef5350", 0.8), row=1, col=1)
    if "bb_upper" in df.columns and "bb_lower" in df.columns:
        fig.add_trace(_make_gl_trace(df.index, df["bb_upper"], "BB Upper", "#888", 0.5, "dash", 0.6), row=1, col=1)
        fig.add_trace(_make_gl_trace(df.index, df["bb_lower"], "BB Lower", "#888", 0.5, "dash", 0.6), row=1, col=1)

    if "rsi" in df.columns:
        fig.add_trace(
            go.Scattergl(x=df.index, y=df["rsi"], mode="lines", line=dict(color="#7c4dff", width=0.8), name="RSI", showlegend=False),
            row=2, col=1,
        )
        fig.add_hline(y=70, line_dash="dash", line_color="#f85149", opacity=0.3, row=2, col=1)
        fig.add_hline(y=30, line_dash="dash", line_color="#3fb950", opacity=0.3, row=2, col=1)
        fig.update_yaxes(range=[0, 100], row=2, col=1)

    fig.add_trace(
        go.Bar(x=df.index, y=df["volume"], name="Volume", marker_color="#2962FF", opacity=0.5),
        row=3, col=1,
    )

    fig.update_layout(
        height=480,
        margin=dict(l=4, r=4, t=20, b=4),
        template="plotly_dark",
        showlegend=False,
        xaxis_rangeslider_visible=False,
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family="'SF Mono','JetBrains Mono','Consolas',monospace", size=9),
        hovermode="x unified",
        hoverlabel=dict(font_size=9, font_family="'SF Mono','JetBrains Mono','Consolas',monospace"),
    )
    fig.update_yaxes(title_text="", row=1, col=1, gridcolor="#21262d", zerolinecolor="#21262d", tickfont_size=8)
    fig.update_yaxes(title_text="", row=2, col=1, gridcolor="#21262d", zerolinecolor="#21262d", tickfont_size=8)
    fig.update_yaxes(title_text="", row=3, col=1, gridcolor="#21262d", zerolinecolor="#21262d", tickfont_size=8)
    fig.update_xaxes(gridcolor="#21262d", zerolinecolor="#21262d", tickfont_size=8)

    return fig


def render_top_bar(df: pd.DataFrame, portfolio_summary: dict, regime_info: dict):
    if df.empty:
        cols = st.columns(6, gap="small")
        for col in cols:
            col.markdown(metric_card("--", "--"), unsafe_allow_html=True)
        return

    last = df.iloc[-1]
    price = last["close"]
    rsi = last.get("rsi", 50)
    ema_20 = last.get("ema_20", price)
    ema_50 = last.get("ema_50", price)

    trend_up = ema_20 > ema_50
    trend_label = "Bullish" if trend_up else "Bearish"

    regime_icons = {"trending_bull": "🟢", "trending_bear": "🔴", "ranging": "🟡", "high_volatility": "💥", "weak_trend": "🔵", "unknown": "⚪"}
    regime_str = f"{regime_icons.get(regime_info['regime'], '⚪')} {regime_info['regime'].replace('_', ' ').title()}"

    net_worth = portfolio_summary["equity"]
    cash = portfolio_summary["cash"]
    peak = portfolio_summary["peak_equity"]

    dd_val = peak - net_worth
    net_delta = f"-${dd_val:.0f}" if dd_val > 0 else "ATH"
    net_dir = "neutral" if dd_val == 0 else "down"

    price_delta_pct = ((price - df.iloc[-2]["close"]) / df.iloc[-2]["close"] * 100) if len(df) >= 2 else 0
    price_delta = f"{price_delta_pct:+.2f}%"
    price_dir = "up" if price_delta_pct >= 0 else "down"

    vol_24h = df["volume"].tail(24).sum()
    vol_fmt = format_volume(vol_24h)

    rsi_color = "#f85149" if rsi > 70 else "#3fb950" if rsi < 30 else "#e6edf3"

    roi_pct = ((price - df.iloc[0]["close"]) / df.iloc[0]["close"] * 100) if len(df) >= 2 else 0
    roi_delta = f"{roi_pct:+.2f}%"
    roi_dir = "up" if roi_pct >= 0 else "down"

    cash_pct = cash / net_worth * 100 if net_worth > 0 else 0

    cols = st.columns(6, gap="small")
    with cols[0]:
        st.markdown(metric_card("Net Worth", f"${net_worth:,.0f}", net_delta, net_dir), unsafe_allow_html=True)
    with cols[1]:
        st.markdown(metric_card("Price", f"${price:,.2f}", price_delta, price_dir), unsafe_allow_html=True)
    with cols[2]:
        st.markdown(metric_card("Volume 24h", vol_fmt), unsafe_allow_html=True)
    with cols[3]:
        st.markdown(
            f'<div class="metric-card"><div class="label">RSI (14)</div>'
            f'<div class="value" style="color:{rsi_color}">{rsi:.1f}</div>'
            f'<div class="delta neu">{regime_str}</div></div>',
            unsafe_allow_html=True,
        )
    with cols[4]:
        st.markdown(metric_card("ROI", roi_delta, trend_label, "up" if trend_up else "down"), unsafe_allow_html=True)
    with cols[5]:
        st.markdown(metric_card("Cash Reserve", f"${cash:,.0f}", f"{cash_pct:.0f}% of NW", "neutral"), unsafe_allow_html=True)


def render_watchlist() -> str:
    data = cached_watchlist_data()
    age_dots = {"fresh": "🟢", "aging": "🟡", "stale": "🔴", "no_data": "⚪"}

    rows_html = ""
    for d in data:
        if d["price"] is None:
            rows_html += (
                f'<tr><td class="sym">{d["symbol"]}</td>'
                f'<td class="prc" colspan="2" style="color:#8b949e">—</td>'
                f'<td class="cls">{age_dots.get(d["freshness"], "⚪")}</td></tr>'
            )
            continue
        chg = d["change_pct"] or 0
        chg_cls = "pos" if chg >= 0 else "neg"
        chg_sign = "+" if chg >= 0 else ""
        rows_html += (
            f'<tr>'
            f'<td class="sym">{d["symbol"]}</td>'
            f'<td class="prc">${d["price"]:,.2f}</td>'
            f'<td class="chg {chg_cls}">{chg_sign}{chg:.2f}%</td>'
            f'<td class="cls">{age_dots.get(d["freshness"], "⚪")}</td>'
            f'</tr>'
        )

    return f"""
    <div style="background:#161b22;border:1px solid #30363d;border-radius:4px;padding:0.4rem;overflow-y:auto">
        <div style="font-size:0.55rem;color:#8b949e;text-transform:uppercase;letter-spacing:0.7px;font-weight:500;margin-bottom:3px">Watchlist</div>
        <table class="watchlist">
            <tr><th>Symbol</th><th style="text-align:right">Price</th><th style="text-align:right">Chg%</th><th style="text-align:center">Age</th></tr>
            {rows_html}
        </table>
    </div>
    """


def render_guide_card(selected: str) -> str:
    guide = get_guide(selected)
    return (
        f'<div style="background:#161b22;border:1px solid #30363d;border-radius:4px;padding:0.4rem">'
        f'<div style="font-size:0.55rem;color:#8b949e;text-transform:uppercase;letter-spacing:0.7px;font-weight:500;margin-bottom:3px">'
        f'Guide — {selected}</div>'
        f'<div style="font-size:0.65rem;color:#e6edf3;line-height:1.5">'
        f'<b>Market:</b> {guide["market_type"]}<br>'
        f'<b>Style:</b> {guide["best_style"]}<br>'
        f'<b>Entry:</b> {guide["entry_rule"]}<br>'
        f'<b>Exit:</b> {guide["exit_rule"]}<br>'
        f'<b>Risk:</b> {guide["risk_rule"]}</div></div>'
    )


def dashboard_tab():
    if "timeframe" not in st.session_state:
        st.session_state.timeframe = "1W"

    all_symbols = []
    for asset_class, symbols in SYMBOLS.items():
        for sym in symbols:
            all_symbols.append({"symbol": sym, "class": asset_class})

    if "selected_symbol" not in st.session_state:
        st.session_state.selected_symbol = all_symbols[0]["symbol"]

    selected = st.session_state.selected_symbol
    limit = TIMEFRAME_LIMITS[st.session_state.timeframe]

    df = cached_indicators(selected, lookback=max(limit, 100))
    portfolio_summary = cached_portfolio_summary()
    regime_info = cached_regime(selected)
    sentiment = cached_sentiment(selected)
    signals = cached_signals(selected)
    data_age = cached_freshness(selected)

    render_top_bar(df, portfolio_summary, regime_info)

    watch_col, chart_col = st.columns([1.05, 4.95], gap="small")

    with watch_col:
        st.markdown(render_watchlist(), unsafe_allow_html=True)
        st.markdown("<div style='height:4px'></div>", unsafe_allow_html=True)
        st.markdown(render_guide_card(selected), unsafe_allow_html=True)

    with chart_col:
        tf_cols = st.columns([1, 5], gap="small")
        with tf_cols[0]:
            st.markdown(f"<div style='font-size:0.7rem;color:#8b949e;padding-top:3px'>{selected}</div>", unsafe_allow_html=True)
        with tf_cols[1]:
            tf = st.radio(
                "timeframe",
                ["1D", "1W", "1M", "1Y", "ALL"],
                horizontal=True,
                label_visibility="collapsed",
                index=["1D", "1W", "1M", "1Y", "ALL"].index(st.session_state.timeframe),
                key="tf_radio",
            )
            if tf != st.session_state.timeframe:
                st.session_state.timeframe = tf
                st.rerun()

        if df.empty:
            st.info("No indicator data available. Fetch data from the sidebar.")
        else:
            config = {"displayModeBar": False, "responsive": True, "scrollZoom": False}
            fig = plot_candlestick(df)
            st.plotly_chart(fig, use_container_width=True, config=config)

            sig_col, sent_col = st.columns(2, gap="small")
            with sig_col:
                st.markdown("<div class='section-title'>Signals</div>", unsafe_allow_html=True)
                if signals:
                    emoji_map = {
                        "STRONG_BUY": "🟢", "BUY_WATCH": "👀", "STRONG_SELL": "🔴",
                        "SELL_WATCH": "⚠️", "BULLISH_CROSS": "📈", "BEARISH_CROSS": "📉",
                        "BOUNCE_WATCH": "💫", "BREAKDOWN_WATCH": "💥", "UPTREND": "⬆️", "DOWNTREND": "⬇️",
                    }
                    for sig in signals[:6]:
                        emoji = emoji_map.get(sig["signal_type"], "📊")
                        st.markdown(
                            f'<div style="background:#161b22;border:1px solid #30363d;border-radius:3px;'
                            f'padding:2px 7px;margin:1px 0;font-size:0.7rem">'
                            f'{emoji} <b>{sig["signal_type"]}</b><br>'
                            f'<span style="color:#8b949e">{sig["indicator_trigger"][:80]}</span></div>',
                            unsafe_allow_html=True,
                        )
                else:
                    st.markdown("<div style='color:#8b949e;font-size:0.7rem'>No active signals</div>", unsafe_allow_html=True)

            with sent_col:
                st.markdown('<div class="section-title">Sentiment</div>', unsafe_allow_html=True)
                sent_rows = load_sentiment(selected, limit=5)
                if sent_rows:
                    for s in sent_rows[:5]:
                        c = "#3fb950" if s["sentiment_score"] > 0 else "#f85149"
                        st.markdown(
                            f'<div style="background:#161b22;border:1px solid #30363d;border-radius:3px;'
                            f'padding:2px 7px;margin:1px 0;font-size:0.7rem">'
                            f'{s["headline"][:65]}... '
                            f'<b style="color:{c}">{s["sentiment_score"]:+.2f}</b></div>',
                            unsafe_allow_html=True,
                        )
                else:
                    st.markdown("<div style='color:#8b949e;font-size:0.7rem'>No sentiment data</div>", unsafe_allow_html=True)

        age_emoji = {"fresh": "🟢", "aging": "🟡", "stale": "🔴", "no_data": "⚪"}
        st.caption(f"⏰ {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S')} UTC · Data: {age_emoji.get(data_age, '⚪')} {data_age.replace('_', ' ').title()}")


def simulator_tab():
    st.markdown("<div class='section-title' style='font-size:0.75rem'>Beginner Guide & Profit Simulator</div>", unsafe_allow_html=True)

    with st.expander("📐 What-If Profit Calculator", expanded=True):
        col_inp, col_out = st.columns([1, 1])
        with col_inp:
            invest_amount = st.number_input("Investment ($)", min_value=10, max_value=100_000, value=100, step=10)
            asset_choice = st.selectbox("Asset Class", ["bitcoin", "stocks", "forex"], format_func=lambda x: x.capitalize())
            risk_choice = st.selectbox("Risk Level", ["conservative", "balanced", "aggressive"], format_func=lambda x: x.capitalize())
            time_horizon = st.slider("Time Horizon (Years)", min_value=1, max_value=30, value=5)

        with col_out:
            proj = project_growth(invest_amount, asset_choice, risk_choice, time_horizon)
            mc = st.columns(2)
            dd = (proj["final_value"] - proj["investment"]) / proj["investment"] * 100
            mc[0].metric("Final Value", f"${proj['final_value']:,.0f}")
            mc[0].metric("Total Return", f"{proj['total_return_pct']:+.2f}%", delta=f"{dd:+.1f}%")
            mc[1].metric("Annual Return", f"{proj['annual_return']*100:.1f}%")
            mc[1].metric("Time Horizon", f"{proj['years']}y")
            worst, best = proj['final_value_range']
            mc[1].metric("Range", f"${worst:,.0f} – ${best:,.0f}")

            target_pct = 5.0
            time_est = estimate_time_for_target(asset_choice, risk_choice, target_pct)
            if time_est["days_lower"]:
                mc[1].metric(f"Time for {target_pct:+.0f}% Move", f"~{time_est['days_lower']}–{time_est['days_upper']}d")

            years_arr = [y["year"] for y in proj["yearly"]]
            values_arr = [y["value"] for y in proj["yearly"]]
            fig_proj = go.Figure()
            fig_proj.add_trace(go.Bar(x=years_arr, y=values_arr, marker_color="#2962FF", name="Portfolio Value"))
            fig_proj.add_hline(y=proj["investment"], line_dash="dash", line_color="#8b949e", annotation_text="Initial Investment")
            fig_proj.update_layout(
                height=200, margin=dict(l=10, r=10, t=10, b=10),
                template="plotly_dark", showlegend=False,
                paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
            )
            st.plotly_chart(fig_proj, use_container_width=True, config={"displayModeBar": False})

    with st.expander("⚠️ Risk Controller & Position Sizing", expanded=False):
        col_rin, col_rout = st.columns([1, 1])
        with col_rin:
            risk_entry = st.number_input("Entry Price ($)", min_value=0.01, max_value=500_000.0, value=60_000.0, step=100.0)
            risk_invest = st.number_input("Total Investment ($)", min_value=10, max_value=100_000, value=500, step=10)
            risk_asset = st.selectbox("Asset Class", ["bitcoin", "stocks", "forex"], format_func=lambda x: x.capitalize(), key="risk_asset")
            risk_stop = st.number_input("Stop-Loss (0=auto)", min_value=0.0, max_value=500_000.0, value=0.0, step=10.0)
            risk_side = st.selectbox("Direction", ["buy", "sell"], format_func=lambda x: "Long (Buy)" if x == "buy" else "Short (Sell)", key="risk_side")

        with col_rout:
            rc = risk_calculator(
                risk_entry, risk_invest, risk_asset,
                side=risk_side,
                stop_loss=risk_stop if risk_stop > 0 else None,
            )
            mc2 = st.columns(2)
            mc2[0].metric("Max Loss (1% Rule)", f"${rc['max_loss_allowed']:.2f}")
            mc2[0].metric("Stop-Loss", f"${rc['stop_loss']:.2f}")
            mc2[0].metric("Take-Profit", f"${rc['take_profit']:.2f}")
            mc2[1].metric("Position Size", f"{rc['position_size_units']:.4f} units")
            mc2[1].metric("Cost at Entry", f"${rc['position_size_cost']:.2f}")
            rr_color = "normal"
            if rc["rr_passes"]:
                rr_delta = "✅ Pass"
            else:
                rr_delta = f"❌ Min {MIN_RISK_REWARD_RATIO}:1"
                rr_color = "inverse"
            mc2[1].metric("Risk:Reward", f"{rc['risk_reward_ratio']:.2f}", delta=rr_delta, delta_color=rr_color)
            alc = rc["allocation_pct"]
            mc2[1].metric("Allocation", f"{alc}% of investment")

            if not rc["rr_passes"]:
                st.warning(f"R:R ratio ({rc['risk_reward_ratio']:.2f}) is below {MIN_RISK_REWARD_RATIO}:1. Widen TP or tighten SL.")
            if alc > 100:
                st.warning(f"Position cost (${rc['position_size_cost']:.2f}) exceeds investment. Reduce size.")
            st.info(f"**1% Rule:** Risking ${rc['max_loss_allowed']:.2f} (1% of ${risk_invest:.2f})")

    with st.expander("📖 Asset Trading Guides", expanded=False):
        guide_keys = list(TRADING_GUIDES.keys())
        gcols = st.columns(3)
        for idx, key in enumerate(guide_keys):
            g = TRADING_GUIDES[key]
            with gcols[idx]:
                st.markdown(
                    f"<div style='background:#161b22;border:1px solid #30363d;border-radius:4px;padding:0.6rem;height:100%'>"
                    f"<h3 style='margin:0 0 2px 0;font-size:0.9rem'>{g['icon']} {g['title']}</h3>"
                    f"<p style='color:#8b949e;font-size:0.7rem'><b>Style:</b> {g['style']}</p>"
                    f"<p style='font-size:0.7rem'>{g['description']}</p></div>",
                    unsafe_allow_html=True,
                )
                with st.expander("📥 Entry"):
                    st.markdown(g["entry"])
                with st.expander("📤 Take Profit"):
                    st.markdown(g["exit_take_profit"])
                with st.expander("🛑 Stop-Loss"):
                    st.markdown(g["exit_stop_loss"])
                    st.markdown(f"**Loss Control:** {g['loss_control']}")
                with st.expander("💡 Tips"):
                    for tip in g["tips"]:
                        st.markdown(f"- {tip}")


def portfolio_tab():
    st.markdown("<div class='section-title' style='font-size:0.75rem'>Paper Portfolio</div>", unsafe_allow_html=True)

    summary = cached_portfolio_summary()

    kpi_cols = st.columns(4, gap="small")
    eq_color = "normal" if summary["equity"] >= summary["peak_equity"] else "inverse"
    kpi_cols[0].metric("Equity", f"${summary['equity']:,.2f}", delta_color=eq_color)
    kpi_cols[1].metric("Cash", f"${summary['cash']:,.2f}")
    dd_delta = f"{summary['drawdown_pct']:.2f}%"
    dd_color = "inverse" if summary["drawdown_pct"] > 5 else "normal"
    kpi_cols[2].metric("Drawdown", dd_delta, delta_color=dd_color)
    kpi_cols[3].metric("Open Positions", str(summary["open_positions"]))

    kpi_cols2 = st.columns(4, gap="small")
    kpi_cols2[0].metric("Total Trades", str(summary["total_trades"]))
    wr_color = "normal" if summary["win_rate"] >= 50 else "inverse"
    kpi_cols2[1].metric("Win Rate", f"{summary['win_rate']:.1f}%", delta_color=wr_color)
    pf_val = summary["profit_factor"]
    pf_color = "normal" if pf_val >= 2 else "inverse" if pf_val < 1 else "off"
    kpi_cols2[2].metric("Profit Factor", str(pf_val), delta_color=pf_color)
    kpi_cols2[3].metric("Peak Equity", f"${summary['peak_equity']:,.2f}")

    open_trades = cached_paper_trades(status="open")
    if open_trades:
        st.markdown("<div class='section-title'>Open Positions</div>", unsafe_allow_html=True)
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
        st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True, height=160)
    else:
        st.info("No open positions")

    closed_trades = cached_paper_trades(status="closed")
    if closed_trades:
        st.markdown("<div class='section-title'>Trade History</div>", unsafe_allow_html=True)
        rows = []
        for t in closed_trades[:50]:
            dir_emoji = "🟢" if t["side"] == "buy" else "🔴"
            rows.append({
                "Symbol": t["symbol"],
                "Side": f"{dir_emoji} {t['side'].upper()}",
                "Entry": f"${t['entry_price']:.2f}",
                "Exit": f"${t['exit_price']:.2f}" if t["exit_price"] else "-",
                "PnL": f"${t['pnl']:+.2f}",
                "Return": f"{t['pnl_pct']*100:+.2f}%",
            })
        df_trades = pd.DataFrame(rows)

        def color_pnl(val):
            if isinstance(val, str) and val.startswith("$"):
                try:
                    num = float(val.replace("$", "").replace("+", ""))
                    return "color: #3fb950" if num >= 0 else "color: #f85149"
                except Exception:
                    pass
            return ""

        st.dataframe(
            df_trades.style.applymap(color_pnl, subset=["PnL", "Return"]),
            use_container_width=True,
            hide_index=True,
            height=min(45 * len(rows) + 30, 350),
        )

        eq_df = pd.DataFrame([dict(t) for t in closed_trades])
        eq_df = eq_df.sort_values("timestamp")
        eq_df["cumulative_pnl"] = eq_df["pnl"].cumsum() + summary["peak_equity"] - sum(t["pnl"] for t in closed_trades)

        fig_eq = go.Figure()
        fig_eq.add_trace(go.Scattergl(
            x=eq_df["timestamp"], y=eq_df["cumulative_pnl"],
            mode="lines+markers",
            name="Equity",
            line=dict(color="#2962FF", width=2),
            marker=dict(size=4, color="#2962FF"),
            fill="tozeroy",
            fillcolor="rgba(41, 98, 255, 0.1)",
        ))
        fig_eq.update_layout(
            height=220,
            margin=dict(l=10, r=10, t=20, b=10),
            template="plotly_dark",
            title="Equity Curve",
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            font=dict(family="'SF Mono','JetBrains Mono','Consolas',monospace", size=9),
            showlegend=False,
        )
        st.plotly_chart(fig_eq, use_container_width=True, config={"displayModeBar": False})
    else:
        st.info("No closed trades yet. Signals will auto-trade via the scheduler.")


def main():
    init_db()

    with st.sidebar:
        st.markdown("<div style='font-size:0.85rem;font-weight:600;margin-bottom:0.4rem'>Quant Trading</div>", unsafe_allow_html=True)

        all_symbols = []
        for asset_class, symbols in SYMBOLS.items():
            for sym in symbols:
                all_symbols.append({"symbol": sym, "class": asset_class})

        sym_opts = [s["symbol"] for s in all_symbols]
        default_idx = sym_opts.index(st.session_state.get("selected_symbol", sym_opts[0])) if st.session_state.get("selected_symbol") in sym_opts else 0
        selected = st.selectbox("Asset", sym_opts, index=default_idx)
        if selected != st.session_state.get("selected_symbol"):
            st.session_state.selected_symbol = selected
            st.rerun()

        st.markdown("<hr style='margin:0.4rem 0;border-color:#30363d'>", unsafe_allow_html=True)
        st.markdown("<div style='font-size:0.6rem;color:#8b949e;text-transform:uppercase;letter-spacing:0.7px;font-weight:500'>Data Refresh</div>", unsafe_allow_html=True)

        for label, key, fetcher in [
            ("Crypto", "btn_crypto", fetch_all_crypto),
            ("Stocks/Forex", "btn_stocks", fetch_all_stocks_and_forex),
            ("Sentiment", "btn_sent", fetch_all_sentiment),
        ]:
            if st.button(f"🔄 {label}", use_container_width=True, key=key):
                with st.spinner(""):
                    n = fetcher()
                    st.cache_data.clear()
                    st.toast(f"Fetched {len(n)} {label.lower()} bars", icon="✅")

        st.markdown("<hr style='margin:0.4rem 0;border-color:#30363d'>", unsafe_allow_html=True)
        st.caption(f"⏰ {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S')} UTC")

    tab1, tab2, tab3 = st.tabs(["Dashboard", "Simulator", "Portfolio"])

    with tab1:
        dashboard_tab()
    with tab2:
        simulator_tab()
    with tab3:
        portfolio_tab()


if __name__ == "__main__":
    main()
