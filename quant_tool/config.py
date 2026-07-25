import os
import logging
from dotenv import load_dotenv

load_dotenv()

LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()
DB_PATH = os.path.join(os.path.dirname(__file__), "database", "market_data.db")

SYMBOLS = {
    "crypto": ["BTC/USDT", "ETH/USDT"],
    "stock": ["AAPL", "MSFT", "GOOGL", "AMZN"],
    "forex": ["EURUSD=X", "GBPUSD=X"],
}

TIMEFRAMES = {
    "crypto": "1h",
    "stock": "1d",
    "forex": "1d",
}

FETCH_INTERVAL_MINUTES = 60

INITIAL_CAPITAL = 10_000.0
RISK_PER_TRADE = 0.01
MAX_DAILY_LOSS_PCT = 0.03
MAX_DRAWDOWN_PCT = 0.10
MIN_RISK_REWARD_RATIO = 2.0
SLIPPAGE_PCT = 0.001
COMMISSION_PCT = 0.001
ATR_STOP_MULTIPLE = 1.5

FINNHUB_API_KEY = os.getenv("FINNHUB_API_KEY", "")
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "")

logging.basicConfig(
    level=getattr(logging, LOG_LEVEL, logging.INFO),
    format="%(asctime)s UTC | %(levelname)-8s | %(name)s:%(lineno)d | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(os.path.join(os.path.dirname(__file__), "logs", "app.log")),
    ],
)
logger = logging.getLogger("quant_tool")
