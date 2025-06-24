
import asyncio
import os
from dotenv import load_dotenv
from datetime import datetime, timedelta
from pathlib import Path

import pandas as pd
from alpaca.data.historical import StockHistoricalDataClient
from alpaca.data.live import StockDataStream
from alpaca.data.requests import StockBarsRequest
from alpaca.data.timeframe import TimeFrame, TimeFrameUnit
from alpaca.trading.client import TradingClient

from news_watcher import NewsWatcher
from trading_bot import MLTrader
from trading_logger import TradeLogger

from helper.utils import convert_to_german_time

load_dotenv()

API_KEY = os.getenv("API_KEY")
API_SECRET = os.getenv("API_SECRET")
SYMBOL = "TSLA"

LOG_FILE = Path("order_log.csv")

client = TradingClient(API_KEY, API_SECRET, paper=True)
data_client = StockHistoricalDataClient(API_KEY, API_SECRET)
stream = StockDataStream(API_KEY, API_SECRET)


class LiveWebSocketBot:
    def __init__(self):
        self.trader = MLTrader(symbol=SYMBOL)
        self.news_watcher = NewsWatcher(self.trader)
        self.last_order_time = datetime.min
        self.order_cooldown = timedelta(seconds=30)
        self.logger = TradeLogger(LOG_FILE)
        self.log_existing_positions()

    def log_existing_positions(self):
        try:
            positions = self.trader.client.get_all_positions()
            if not positions:
                print("[INIT] No open positions found.")
            else:
                print("[INIT] Existing positions:")
                for p in positions:
                    print(f"  ➤ {p.symbol}: {p.qty} shares @ {p.avg_entry_price}")
                    if p.symbol == SYMBOL:
                        qty = float(p.qty)
                        direction = "LONG" if qty > 0 else "SHORT"
                        print(f"[INIT] Detected: {direction} position for {SYMBOL}")

                        # Log initial state
                        self.logger.log(
                            action=f"INIT-{direction}",
                            symbol=p.symbol,
                            qty=qty,
                            price=float(p.avg_entry_price),
                            sentiment="init",
                            trend="init",
                            cash=self.trader.get_cash()
                        )
        except Exception as e:
            print(f"[INIT] Error retrieving positions: {e}")

    def fetch_latest_bars(self, symbol="TSLA"):
        end = datetime.utcnow()
        start = end - timedelta(minutes=60)

        request_params = StockBarsRequest(
            symbol_or_symbols=symbol,
            timeframe=TimeFrame(amount=5, unit=TimeFrameUnit.Minute),
            start=start,
            end=end,
            feed='iex'
        )

        bars = data_client.get_stock_bars(request_params).df

        if isinstance(bars.index, pd.MultiIndex):
            bars = bars.reset_index()
        if isinstance(bars.columns, pd.MultiIndex):
            bars.columns = bars.columns.get_level_values(-1)
        if "symbol" in bars.columns:
            bars = bars[bars["symbol"] == symbol]

        bars = bars.sort_values("timestamp")
        self.trader.historical_data = bars
        return bars

    async def on_trade(self, data):
        print("=" * 40)
        print(f"[DEBUG] Trade Event erhalten: {data.symbol} @ {data.price}")
        print("=" * 40)
        price = data.price
        now = datetime.utcnow()
        print(f"[Live Trade] {data.symbol} @ {price}")

        self.fetch_latest_bars()
        trend = self.trader.get_price_trend_from_data()
        candle_signal = self.trader.get_candlestick_signal()
        probability, sentiment = self.trader.cached_sentiment or (0.5, "neutral")

        position = self.trader.get_position()
        position_qty = abs(float(position.qty)) if position else 0
        is_short = position and float(position.qty) < 0
        cash = round(self.trader.get_cash(), 2)

        # 👉 Ausgabe des strukturierten Info-Logs
        self.logger.generate_info_log(price, trend, candle_signal, sentiment, position, decision=None)

        decision = self.trader.make_decision(sentiment, trend, candle_signal)
        print(f"[Decision] → {decision.upper()}")

        # Aktualisiertes Log mit finaler Entscheidung
        self.logger.generate_info_log(price, trend, candle_signal, sentiment, position, decision)

        if now - self.last_order_time < self.order_cooldown:
            print("[INFO] Cooldown aktiv – kein Trade ausgeführt.")
            return

        if decision == "buy":
            if is_short:
                order = self.trader.create_order(SYMBOL, position_qty, "buy")
                self.trader.submit_order(order)
                self.last_order_time = now
                print(f"[ORDER] CLOSE SHORT {position_qty} shares @ {price}")
                self.logger.log("BUY-CLOSE", SYMBOL, position_qty, price, sentiment, trend, cash)
            elif position_qty == 0:
                quantity = int(self.trader.get_cash() // price)
                if quantity > 0:
                    order = self.trader.create_order(SYMBOL, quantity, "buy")
                    self.trader.submit_order(order)
                    self.last_order_time = now
                    print(f"[ORDER] BUY {quantity} shares @ {price}")
                    self.logger.log("BUY", SYMBOL, quantity, price, sentiment, trend, cash)
                else:
                    print("[INFO] Nicht genug Kapital zum Kauf.")

        elif decision == "sell":
            if not is_short and position_qty > 0:
                order = self.trader.create_order(SYMBOL, position_qty, "sell")
                self.trader.submit_order(order)
                self.last_order_time = now
                print(f"[ORDER] SELL {position_qty} shares @ {price}")
                self.logger.log("SELL-CLOSE", SYMBOL, position_qty, price, sentiment, trend, cash)
            elif position_qty == 0:
                quantity = int(self.trader.get_cash() // price)
                if quantity > 0:
                    order = self.trader.create_order(SYMBOL, quantity, "sell")
                    self.trader.submit_order(order)
                    self.last_order_time = now
                    print(f"[ORDER] OPEN SHORT {quantity} shares @ {price}")
                    self.logger.log("SELL-OPEN", SYMBOL, quantity, price, sentiment, trend, cash)
                else:
                    print("[INFO] Nicht genug Kapital für Short-Sell.")
            else:
                print("[WARNUNG] SELL-Signal aber keine logische Aktion möglich.")

    def check_market_status(self):
        is_open = False
        try:
            clock = self.trader.client.get_clock()
            is_open = clock.is_open
            if not is_open:
                print(f"🕒 [MARKET] The market is currently closed and will reopen at "
                      f"{convert_to_german_time(clock.next_open, clock.next_close)}")
            else:
                print("✅ [MARKET] The market is open.")
        except Exception as e:
            print(f"[ERROR] Could not retrieve market status: {e}")

        return is_open

    async def monitor_market_close(self):
        while True:
            try:
                clock = self.trader.client.get_clock()
                if not clock.is_open:
                    print(f"🔒 [MARKET] The market has closed. "
                          f"It will reopen at {convert_to_german_time(clock.next_open,clock.next_close)}. "
                          f"Shutting down bot.")
                    self.stop()
                    break
            except Exception as e:
                print(f"[ERROR] Market monitoring failed: {e}")
            await asyncio.sleep(60)  # alle 60 Sekunden prüfen

    async def start(self):
        market_open = self.check_market_status()
        asyncio.create_task(self.monitor_market_close())

        if market_open:
            print("[BOT] Starting NewsWatcher...")
            self.news_watcher.start()

            print("[BOT] Starting WebSocket stream...")
            stream.subscribe_trades(self.on_trade, SYMBOL)
            try:
                await stream._run_forever()
            except asyncio.exceptions.TimeoutError:
                print("[INFO] WebSocket Timeout beim Shutdown – ignoriert.")

    def stop(self):
        self.news_watcher.stop()
        self.news_watcher.join()


if __name__ == "__main__":
    bot = LiveWebSocketBot()
    try:
        asyncio.run(bot.start())
    except KeyboardInterrupt:
        print("\n[STOP] Stopping bot...")
        bot.stop()
