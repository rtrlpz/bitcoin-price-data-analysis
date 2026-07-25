import logging
import math
from datetime import datetime, timezone

import numpy as np

from quant_tool.config import RISK_PER_TRADE, MIN_RISK_REWARD_RATIO
from quant_tool.database.db_handler import load_market_data

logger = logging.getLogger("quant_tool.learning_calc")

ANNUAL_RETURNS = {
    "bitcoin": {"conservative": 0.10, "balanced": 0.18, "aggressive": 0.30},
    "stocks": {"conservative": 0.07, "balanced": 0.10, "aggressive": 0.15},
    "forex": {"conservative": 0.03, "balanced": 0.06, "aggressive": 0.10},
}

DAILY_VOLATILITY = {
    "bitcoin": {"conservative": 0.015, "balanced": 0.025, "aggressive": 0.040},
    "stocks": {"conservative": 0.008, "balanced": 0.012, "aggressive": 0.020},
    "forex": {"conservative": 0.003, "balanced": 0.005, "aggressive": 0.008},
}

SYMBOL_MAP = {
    "bitcoin": "BTC/USDT",
    "ethereum": "ETH/USDT",
    "stocks": "AAPL",
    "forex": "EURUSD=X",
}


def _resolve_symbol(asset_class: str) -> str:
    return SYMBOL_MAP.get(asset_class, "BTC/USDT")


def _real_volatility(symbol: str, lookback: int = 200) -> dict:
    rows = load_market_data(symbol, limit=lookback)
    if len(rows) < 10:
        return {"atr": None, "daily_std": None}

    try:
        closes = [r["close"] for r in rows]
        returns = [(closes[i] - closes[i - 1]) / closes[i - 1] for i in range(1, len(closes))]
        daily_std = float(np.std(returns)) if returns else None

        highs = [r["high"] for r in rows]
        lows = [r["low"] for r in rows]
        tr_range = [
            max(
                highs[i] - lows[i],
                abs(highs[i] - closes[i - 1]),
                abs(lows[i] - closes[i - 1]),
            )
            for i in range(1, len(rows))
        ]
        atr = float(np.mean(tr_range[-14:])) if len(tr_range) >= 14 else None
    except Exception as exc:
        logger.warning("Volatility computation failed for %s: %s", symbol, exc)
        return {"atr": None, "daily_std": None}

    return {"atr": atr, "daily_std": daily_std, "current_price": closes[-1]}


def project_growth(investment: float, asset_class: str, risk_level: str, years: float) -> dict:
    risk_level = risk_level.lower()
    asset_class = asset_class.lower()
    annual_return = ANNUAL_RETURNS.get(asset_class, {}).get(risk_level, 0.10)

    vol_key = DAILY_VOLATILITY.get(asset_class, {}).get(risk_level, 0.01)
    annual_vol = vol_key * math.sqrt(252)

    yearly = []
    running = investment
    for y in range(1, int(years) + 1):
        running = running * (1 + annual_return)
        yearly.append({"year": y, "value": round(running, 2), "gain": round(running - investment, 2)})

    final_value = investment * (1 + annual_return) ** years
    total_return_pct = ((final_value - investment) / investment) * 100

    worst_case = investment * (1 + annual_return - annual_vol) ** years
    best_case = investment * (1 + annual_return + annual_vol) ** years

    return {
        "investment": round(investment, 2),
        "asset_class": asset_class,
        "risk_level": risk_level,
        "annual_return": annual_return,
        "years": years,
        "final_value": round(final_value, 2),
        "final_value_range": (round(max(0, worst_case), 2), round(best_case, 2)),
        "total_return_pct": round(total_return_pct, 2),
        "yearly": yearly,
    }


def estimate_time_for_target(asset_class: str, risk_level: str, target_pct: float) -> dict:
    asset_class = asset_class.lower()
    risk_level = risk_level.lower()
    symbol = _resolve_symbol(asset_class)

    vol = _real_volatility(symbol)
    daily_move = vol.get("daily_std")

    if daily_move is None or daily_move <= 0:
        daily_move = DAILY_VOLATILITY.get(asset_class, {}).get(risk_level, 0.01)

    target_abs = abs(target_pct) / 100.0
    if daily_move <= 0:
        return {"days_lower": None, "days_upper": None, "daily_move": None}

    days_estimate = target_abs / daily_move
    days_lower = max(1, int(days_estimate * 0.7))
    days_upper = max(1, int(days_estimate * 1.3))

    return {
        "days_lower": days_lower,
        "days_upper": days_upper,
        "daily_move_pct": round(daily_move * 100, 2),
        "target_pct": target_pct,
        "current_price": vol.get("current_price"),
    }


def risk_calculator(
    entry_price: float,
    investment: float,
    asset_class: str,
    side: str = "buy",
    stop_loss: float | None = None,
) -> dict:
    max_loss = investment * RISK_PER_TRADE

    if stop_loss is None or stop_loss <= 0:
        symbol = _resolve_symbol(asset_class)
        vol = _real_volatility(symbol)
        atr = vol.get("atr")
        current_price = vol.get("current_price") or entry_price
        if atr and atr > 0:
            stop_distance = 1.5 * atr
            if side == "buy":
                stop_loss = current_price - stop_distance
            else:
                stop_loss = current_price + stop_distance
        else:
            daily_vol = DAILY_VOLATILITY.get(asset_class.lower(), {}).get("balanced", 0.012)
            if side == "buy":
                stop_loss = current_price * (1 - 2 * daily_vol)
            else:
                stop_loss = current_price * (1 + 2 * daily_vol)

    if side == "buy":
        stop_loss = min(stop_loss, entry_price * 0.95) if stop_loss > entry_price else stop_loss
    else:
        stop_loss = max(stop_loss, entry_price * 1.05) if stop_loss < entry_price else stop_loss

    stop_loss = max(0.01, stop_loss)

    risk_per_share = abs(entry_price - stop_loss)
    if risk_per_share <= 0:
        risk_per_share = entry_price * 0.02

    position_size = max_loss / risk_per_share
    cost = position_size * entry_price
    if cost > investment:
        position_size = investment / entry_price
        cost = investment

    if side == "buy":
        take_profit = entry_price + 2 * (entry_price - stop_loss) if entry_price > stop_loss else entry_price * 1.05
    else:
        take_profit = entry_price - 2 * (stop_loss - entry_price) if stop_loss > entry_price else entry_price * 0.95

    if side == "buy":
        risk_dist = entry_price - stop_loss if entry_price > stop_loss else 0
        reward_dist = take_profit - entry_price if take_profit > entry_price else 0
    else:
        risk_dist = stop_loss - entry_price if stop_loss > entry_price else 0
        reward_dist = entry_price - take_profit if entry_price > take_profit else 0

    rr_ratio = round(reward_dist / risk_dist, 2) if risk_dist > 0 else 0
    rr_passes = rr_ratio >= MIN_RISK_REWARD_RATIO

    allocation_pct = round(cost / max(investment, 1) * 100, 1)

    return {
        "entry_price": round(entry_price, 4),
        "stop_loss": round(stop_loss, 4),
        "take_profit": round(take_profit, 4),
        "max_loss_allowed": round(max_loss, 2),
        "position_size_units": round(position_size, 4),
        "position_size_cost": round(cost, 2),
        "risk_per_share": round(risk_per_share, 4),
        "risk_reward_ratio": rr_ratio,
        "rr_passes": rr_passes,
        "allocation_pct": allocation_pct,
    }
