# Bitcoin Price Analysis EDA + Quant Trading Dashboard

## Quick Start (first time)

```bash
python run.py
```

The script will prompt you to create a virtual environment and install all dependencies, then launch the dashboard.

## Environment

- Virtual env at `.venv`. Activate: `.venv/Scripts/activate` (Windows) or `source .venv/bin/activate` (Unix)
- All dependencies in root `requirements.txt`. Install: `pip install -r requirements.txt`

## Project structure

```
run.py                     # Bootstrap launcher — creates venv, installs deps, launches dashboard
requirements.txt           # All dependencies (Bitcoin EDA + quant_tool) merged into one

src/                       # Bitcoin EDA notebooks helpers
  __init__.py
  data_processing.py
  visualization_utils.py

notebooks/                 # Bitcoin EDA notebooks (run in order 01→06)
  01_extracting_bitcoin_price_yfinance.ipynb
  02_eda_bitcoin_price.ipynb
  03_time_series_forecasting.ipynb
  04_reporting_insights.ipynb
  05_dashboard_.ipynb
  06_practical_aplications.ipynb

data/
  raw/bitcoin_historical_price_daily.csv
  enriched_data/Enriched_bitcoin_price_analysis.csv

quant_tool/                # Multi-Asset Quantitative Trading Engine
  config.py                # Settings, risk parameters, API keys
  scheduler.py             # Automated pipeline — backfill, hourly fetch, signals
  app.py                   # Streamlit dashboard (3 tabs: Dashboard, Simulator, Portfolio)

  database/
    db_handler.py           # SQLite schema, upserts, portfolio state
    data_quality.py         # Freshness, gap, and outlier detection

  fetchers/
    crypto_feed.py          # CCXT → Binance OHLCV with exponential backoff
    stock_feed.py           # yfinance + Finnhub with retry logic
    sentiment_feed.py       # RSS feedparser + NLTK VADER (keyword→symbol matching)

  analytics/
    indicators.py           # pandas-ta: RSI, EMA, ATR, Bollinger, MACD
    signals.py              # Composite rule engine (technicals + sentiment)
    backtester.py           # PaperTrader with 1% rule, ATR stops, friction
    regime.py               # Market regime detection (ADX, MA slope, ATR ratio)
    learning_calculator.py  # What-If calculator, risk sizing, asset guides
    asset_guides.py         # Per-symbol trading guides

  notifications/
    telegram.py             # Telegram bot alert dispatcher

sql/          # empty
reports/      # empty
```

## Workflow

1. **Notebooks must run in order** (01 → 06). `01` fetches data via yfinance; later notebooks depend on its output.
2. **src/ modules** are designed to be imported from notebooks. `data_processing.load_bitcoin_data()` resolves the project root relative to its own location (`..` from `src/`), so notebooks in any directory can import it.
3. **Dashboard**: `streamlit run quant_tool/app.py` (or `python run.py` for auto-setup)
4. **Scheduler** (background data pipeline): `python -m quant_tool.scheduler`

## Key dependencies

All listed in root `requirements.txt`: `ta`, `pmdarima`, `xgboost`, `pandas-ta`, `ccxt`, `streamlit`, `nltk`, `yfinance`, `plotly`, `feedparser`, `schedule`.

## quant_tool/ — Multi-Asset Quantitative Trading Engine

### Key design decisions

- **UTC-only** storage; local conversion only in Streamlit presentation layer.
- **Idempotent upserts** via `INSERT OR REPLACE` on composite PKs `(timestamp, symbol)`.
- **Exponential backoff** on all external API calls (CCXT, Finnhub, RSS, Telegram).
- **Logging** via Python `logging` module to both console and `logs/app.log`.
- **Risk rules**: 1% position sizing, ATR×1.5 stops, 1:2 min R:R, 3% daily loss circuit breaker, 10% max drawdown.
- **Friction**: 0.1% slippage + 0.1% commission per trade baked into `PaperTrader`.
- **No look-ahead bias**: indicators computed on sequential data; backtester executes at next available price.

## Agent Skills & Standard Workflows

### Skill 1: Adding a New Data Fetcher
When asked to integrate a new data source (e.g., an exchange or API):
1. **Create/Update Module:** Place the script inside `quant_tool/fetchers/`.
2. **Resiliency Required:** Implement exponential backoff retry logic and catch all request exceptions.
3. **Database Consistency:** Ensure all fetched timestamps are converted and stored strictly in **UTC**.
4. **Idempotency:** Use SQLite upsert patterns (`INSERT OR REPLACE` on composite primary keys of `timestamp + symbol`) to avoid duplicate records.
5. **Logging:** Log all API success/error metrics using Python's `logging` module to `logs/app.log`.

### Skill 2: Implementing Technical Indicators & Analytics
When adding new indicators or modifying analytics (`quant_tool/analytics/`):
1. **Library Standard:** Use `pandas-ta` or vectorized `pandas` operations. Never write custom slow loops for rolling calculations.
2. **Prevent Look-Ahead Bias:** Ensure calculations use sequential past data up to index $T$. Never let future values leak into historical rows.
3. **Stationarity Check:** If applying statistical models, ensure inputs are transformed (e.g., log-returns) rather than raw price series.

### Skill 3: Frontend UI / Streamlit Modifications
When updating `quant_tool/app.py`:
1. **Mobile Responsiveness:** Ensure layout blocks (`st.container`, `st.columns`) scale gracefully on mobile screens.
2. **Contextual Education:** Always keep the interactive asset-specific guides and risk-control calculators accessible next to the primary charts.
3. **No Business Logic in UI:** Keep all heavy calculation, database query, and simulation logic inside backend modules (`analytics/`, `database/`), importing clean data frames or results into `app.py`.

### Skill 4: Financial Risk & Backtester Guardrails
When modifying the paper trading simulator (`quant_tool/analytics/backtester.py`):
1. **Enforce Risk Rules:** Position sizing must strictly follow the **1% risk rule**, using dynamic ATR-based stop-losses ($\text{ATR} \times 1.5$).
2. **Friction Accounting:** Always deduct realistic execution overhead (0.1% slippage + 0.1% commission per round trip).
3. **Circuit Breakers:** Ensure daily loss checks (3% limit) and maximum drawdown limits (10%) are evaluated before any simulated trade execution.

### Running

1. **First time**: `python run.py` (creates venv, installs deps, prompts before installing, then launches)
2. **Subsequent runs**: `.venv/Scripts/activate` → `streamlit run quant_tool/app.py`
3. **Background scheduler**: `python -m quant_tool.scheduler` (hourly fetch + signal evaluation)
4. **Manual data seed**: `python -c "from quant_tool.fetchers.crypto_feed import fetch_all_crypto; fetch_all_crypto()"`
5. Copy `quant_tool/.env` → add your Finnhub/Telegram API keys to enable live features.

### Phase status

| Phase | Module | Status |
|-------|--------|--------|
| 1 & 2 | Database + Fetchers | Done |
| 3 | Analytics (indicators, signals) | Done |
| 4 & 5 | Streamlit UI + Telegram | Done |
| 6 | PaperTrader (backtester) | Done |
| 7 | Data quality + regime detection + scheduler + Portfolio tab | Done |

- No tests, linting, typechecking, or CI configuration.
