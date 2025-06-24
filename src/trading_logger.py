import csv
from datetime import datetime
from pathlib import Path


LOG_FILE = Path("order_log.csv")


class TradeLogger:
    def __init__(self, log_file):
        self.remember_decision = ""
        self.log_file = log_file
        self.positions = {}  # Track open positions per symbol
        self._init_log_file()

    def _init_log_file(self):
        if not self.log_file.exists():
            with open(self.log_file, mode="w", newline="") as f:
                writer = csv.writer(f)
                writer.writerow([
                    "timestamp", "action", "symbol", "quantity", "price",
                    "sentiment", "trend", "invested_usd", "pnl_usd", "cash"
                ])

    def log_initial_positions(self, cash):
        for symbol, pos in self.positions.items():
            timestamp = datetime.utcnow().isoformat()
            writerow = [
                timestamp,
                "INITIAL-POSITION",
                symbol,
                pos["qty"],
                pos["price"],
                "",  # sentiment leer
                "",  # trend leer
                pos["invested"],
                "",  # kein PnL, da nichts geschlossen wurde
                cash
            ]
            with open(self.log_file, mode="a", newline="") as f:
                writer = csv.writer(f)
                writer.writerow(writerow)
            print(f"[Logger] Initiale Position geloggt für {symbol}: {writerow}")

    def log(self, action, symbol, qty, price, sentiment, trend, cash):
        timestamp = datetime.utcnow().isoformat()
        invested = 0
        pnl = ""

        if action in ("BUY", "SELL-OPEN"):
            invested = round(qty * price, 2)
            self.positions[symbol] = {"qty": qty, "price": price, "invested": invested}
            print(f"[📄 LOG] Neuer Trade: {action} | Investiert: ${invested}")
        elif action in ("SELL-CLOSE", "BUY-CLOSE"):
            entry = self.positions.get(symbol, {})
            invested = entry.get("invested", 0)
            pnl = round(qty * price - invested, 2) if action.startswith("SELL") else round(invested - qty * price, 2)
            print(f"[📄 LOG] Position geschlossen: {action} | PnL: ${pnl}")
            self.positions.pop(symbol, None)

        with open(self.log_file, mode="a", newline="") as f:
            writer = csv.writer(f)
            writer.writerow([
                timestamp, action, symbol, qty, price, sentiment, trend,
                invested, pnl, cash
            ])

    def generate_info_log(self, price, trend, candle_signal, sentiment, position, decision):

        if self.remember_decision != decision and decision is not None:
            self.remember_decision = decision
            print("\n========== 📊 INFO LOG ==========")

            # Preis und Trend
            print(f"💵 Preis: {price:.2f}")
            trend_symbol = "⬆️" if trend == "up" else "⬇️" if trend == "down" else "➖"
            print(f"📈 Trend: {trend_symbol} ({trend})")

            # Kerzenanalyse
            candle_emojis = {
                "hammer": "🔨",
                "shooting_star": "⭐",
                "bullish_engulfing": "🟩",
                "bearish_engulfing": "🟥",
                "neutral": "⚪"
            }
            candle_desc = candle_emojis.get(candle_signal, "❓")
            print(f"🕯️ Candle-Pattern: {candle_desc} ({candle_signal})")

            # Sentiment
            sentiment_symbol = "😊" if sentiment == "positive" else "😐" if sentiment == "neutral" else "☹️"
            print(f"📰 Sentiment: {sentiment_symbol} ({sentiment})")

            # Offene Position
            if position:
                qty = abs(float(position.qty))
                direction = "Long 📈" if float(position.qty) > 0 else "Short 📉"
                print(f"📌 Aktuelle Position: {qty} Stück ({direction})")
            else:
                print("📌 Aktuelle Position: ❌ Keine")

            # Entscheidung
            decision_symbols = {
                "buy": "🟢 KAUFEN",
                "sell": "🔴 VERKAUFEN",
                "hold": "🟡 HALTEN"
            }
            if decision is not None:
                symbol = decision_symbols.get(decision, decision.upper())
                print(f"🤖 Entscheidung: {symbol}")
            else:
                print("🤖 Entscheidung: ❓ (noch keine Entscheidung getroffen)")

            print("==================================\n")
