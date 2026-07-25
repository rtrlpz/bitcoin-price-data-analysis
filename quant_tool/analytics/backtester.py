import logging
from datetime import datetime, timezone

from quant_tool.config import (
    INITIAL_CAPITAL,
    RISK_PER_TRADE,
    MAX_DAILY_LOSS_PCT,
    MAX_DRAWDOWN_PCT,
    MIN_RISK_REWARD_RATIO,
    SLIPPAGE_PCT,
    COMMISSION_PCT,
    ATR_STOP_MULTIPLE,
)
from quant_tool.database.db_handler import (
    get_portfolio_value,
    set_portfolio_value,
    load_market_data,
    insert_paper_trade,
    update_paper_trade,
    load_paper_trades,
)
from quant_tool.analytics.indicators import compute_indicators

logger = logging.getLogger("quant_tool.backtester")


class PaperTrader:
    def __init__(self):
        self.cash = get_portfolio_value("cash") or INITIAL_CAPITAL
        self.equity_peak = get_portfolio_value("equity_peak") or INITIAL_CAPITAL

    def _sync_state(self):
        self.cash = get_portfolio_value("cash") or INITIAL_CAPITAL
        self.equity_peak = get_portfolio_value("equity_peak") or INITIAL_CAPITAL

    def _persist(self):
        set_portfolio_value("cash", self.cash)
        set_portfolio_value("equity_peak", self.equity_peak)

    def current_equity(self) -> float:
        open_trades = load_paper_trades(status="open")
        unrealized = 0.0
        for t in open_trades:
            rows = load_market_data(t["symbol"], limit=1)
            if rows:
                last_price = rows[-1]["close"]
                if t["side"] == "buy":
                    unrealized += (last_price - t["entry_price"]) * t["quantity"]
                else:
                    unrealized += (t["entry_price"] - last_price) * t["quantity"]
        return self.cash + unrealized

    def daily_pnl_pct(self) -> float:
        equity = self.current_equity()
        return (equity - self.equity_peak) / self.equity_peak

    def circuit_check(self) -> str | None:
        daily_pnl = self.daily_pnl_pct()
        if daily_pnl <= -MAX_DAILY_LOSS_PCT:
            logger.critical("Daily loss limit hit: %.2f%% (threshold: %.1f%%)", daily_pnl * 100, MAX_DAILY_LOSS_PCT * 100)
            return "daily_loss_limit"

        equity = self.current_equity()
        dd = (self.equity_peak - equity) / self.equity_peak
        if dd >= MAX_DRAWDOWN_PCT:
            logger.critical("Max drawdown hit: %.2f%% (threshold: %.1f%%)", dd * 100, MAX_DRAWDOWN_PCT * 100)
            return "max_drawdown"

        return None

    def calculate_position_size(self, symbol: str, entry_price: float, stop_loss: float) -> float:
        risk_per_share = abs(entry_price - stop_loss)
        if risk_per_share <= 0:
            logger.warning("Stop loss equals entry price for %s — cannot size position", symbol)
            return 0.0

        max_risk = self.cash * RISK_PER_TRADE
        shares = max_risk / risk_per_share
        cost = shares * entry_price
        if cost > self.cash:
            shares = self.cash / entry_price
        return round(shares, 4)

    def _apply_friction(self, price: float) -> tuple[float, float]:
        slippage = price * SLIPPAGE_PCT
        buy_price = price + slippage
        sell_price = price - slippage
        return buy_price, sell_price

    def _commission(self, value: float) -> float:
        return value * COMMISSION_PCT

    def open_trade(self, symbol: str, side: str, signal: dict):
        circuit = self.circuit_check()
        if circuit:
            logger.warning("Circuit breaker active (%s) — trade for %s blocked", circuit, symbol)
            return

        df = compute_indicators(symbol, lookback=100)
        if df.empty:
            logger.warning("No indicators for %s — cannot open trade", symbol)
            return

        last = df.iloc[-1]
        entry_price = float(last["close"])
        atr = float(last.get("atr", 0))

        if atr <= 0:
            logger.warning("ATR is zero for %s — using fixed 2% stop", symbol)
            stop_loss = entry_price * 0.98 if side == "buy" else entry_price * 1.02
        else:
            stop_distance = ATR_STOP_MULTIPLE * atr
            stop_loss = entry_price - stop_distance if side == "buy" else entry_price + stop_distance

        take_profit = entry_price + 2 * (entry_price - stop_loss) if side == "buy" else entry_price - 2 * (stop_loss - entry_price)

        if side == "buy":
            risk = entry_price - stop_loss
            reward = take_profit - entry_price
        else:
            risk = stop_loss - entry_price
            reward = entry_price - take_profit

        if risk <= 0 or (reward / risk) < MIN_RISK_REWARD_RATIO:
            logger.info("Signal for %s rejected — R:R=%.2f (min %.1f)", symbol, reward / risk if risk > 0 else 0, MIN_RISK_REWARD_RATIO)
            return

        quantity = self.calculate_position_size(symbol, entry_price, stop_loss)
        if quantity <= 0:
            logger.info("Position size zero for %s — skipping", symbol)
            return

        buy_price, _ = self._apply_friction(entry_price)
        cost = quantity * buy_price
        fee = self._commission(cost)
        total_cost = cost + fee

        if total_cost > self.cash:
            quantity = self.cash / buy_price
            cost = quantity * buy_price
            fee = self._commission(cost)
            total_cost = cost + fee

        self.cash -= total_cost
        self._persist()

        trade = {
            "timestamp": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S"),
            "symbol": symbol,
            "side": side,
            "quantity": round(quantity, 4),
            "entry_price": round(buy_price, 4),
            "stop_loss": round(stop_loss, 4),
            "take_profit": round(take_profit, 4),
            "fees": round(fee, 4),
            "pnl": 0.0,
            "pnl_pct": 0.0,
            "exit_price": 0.0,
            "status": "open",
        }
        insert_paper_trade(trade)
        logger.info("Opened %s %s %.4f units at %.2f (SL=%.2f TP=%.2f)", side.upper(), symbol, quantity, buy_price, stop_loss, take_profit)

    def close_trade(self, trade: dict, exit_price: float):
        side = trade["side"]
        quantity = trade["quantity"]
        entry = trade["entry_price"]

        _, sell_price = self._apply_friction(exit_price)
        exit_value = quantity * sell_price
        fee = self._commission(exit_value)

        if side == "buy":
            pnl = exit_value - (quantity * entry) - fee - trade["fees"]
        else:
            pnl = (quantity * entry) - exit_value - fee - trade["fees"]

        pnl_pct = pnl / (quantity * entry) if quantity * entry > 0 else 0.0

        self.cash += exit_value - fee
        self._persist()

        update_paper_trade(trade["id"], {
            "exit_price": round(sell_price, 4),
            "pnl": round(pnl, 4),
            "pnl_pct": round(pnl_pct, 6),
            "fees": round(trade["fees"] + fee, 4),
            "status": "closed",
        })

        direction = "LONG" if side == "buy" else "SHORT"
        logger.info("Closed %s %s PnL=%.2f (%.2f%%)", direction, trade["symbol"], pnl, pnl_pct * 100)

    def check_stops_and_targets(self):
        circuit = self.circuit_check()
        if circuit:
            logger.warning("Circuit breaker active (%s) — stopping trade monitoring", circuit)
            return

        open_trades = load_paper_trades(status="open")
        for trade in open_trades:
            rows = load_market_data(trade["symbol"], limit=1)
            if not rows:
                continue
            last_price = rows[-1]["close"]

            if trade["side"] == "buy":
                if last_price <= trade["stop_loss"]:
                    self.close_trade(trade, trade["stop_loss"])
                elif last_price >= trade["take_profit"]:
                    self.close_trade(trade, trade["take_profit"])
            else:
                if last_price >= trade["stop_loss"]:
                    self.close_trade(trade, trade["stop_loss"])
                elif last_price <= trade["take_profit"]:
                    self.close_trade(trade, trade["take_profit"])

    def update_equity_peak(self):
        equity = self.current_equity()
        if equity > self.equity_peak:
            self.equity_peak = equity
            self._persist()

    def summary(self) -> dict:
        self._sync_state()
        trades = load_paper_trades(status="closed")
        open_trades = load_paper_trades(status="open")
        equity = self.current_equity()
        dd = (self.equity_peak - equity) / self.equity_peak if self.equity_peak > 0 else 0.0

        wins = [t for t in trades if t["pnl"] > 0]
        losses = [t for t in trades if t["pnl"] < 0]
        total_wins = sum(t["pnl"] for t in wins)
        total_losses = abs(sum(t["pnl"] for t in losses)) if losses else 1
        profit_factor = total_wins / total_losses if total_losses > 0 else float("inf")

        return {
            "total_trades": len(trades),
            "open_positions": len(open_trades),
            "win_rate": len(wins) / len(trades) * 100 if trades else 0.0,
            "profit_factor": round(profit_factor, 2),
            "equity": round(equity, 2),
            "cash": round(self.cash, 2),
            "drawdown_pct": round(dd * 100, 2),
            "peak_equity": round(self.equity_peak, 2),
        }
