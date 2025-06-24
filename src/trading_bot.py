import os
import pandas as pd
import requests
from alpaca.trading.client import TradingClient
from alpaca.trading.enums import OrderSide, TimeInForce, OrderType
from alpaca.trading.requests import MarketOrderRequest
from dotenv import load_dotenv
from candlestick_patterns import detect_candlestick_pattern

load_dotenv()

API_KEY = os.getenv("API_KEY")
API_SECRET = os.getenv("API_SECRET")
NEWSAPI_KEY = os.getenv("NEWSAPI_KEY")

client = TradingClient(API_KEY, API_SECRET, paper=True)

class MLTrader:
    def __init__(self, symbol="TSLA", cash_at_risk=0.5):
        self.symbol = symbol
        self.cash_at_risk = cash_at_risk
        self.client = client
        self.historical_data = pd.DataFrame()
        self.ma_period = 20
        self.cached_sentiment = None
        self.last_news_update = None
        self.price_data = []
        self.candles = []
        self.fetch_all_open_positions()

    def fetch_all_open_positions(self):
        try:
            positions = self.client.get_all_positions()
            print("[DEBUG] Offene Positionen laut Alpaca:")
            for pos in positions:
                print(f"  ➤ {pos.symbol}: {pos.qty} shares @ {pos.avg_entry_price}")
            return positions
        except Exception as e:
            print(f"[ERROR] Fehler beim Abrufen der Positionen: {e}")
            return []

    def get_cash(self):
        return float(self.client.get_account().cash)

    def get_price_trend_from_data(self):
        window_size = 20
        window = self.price_data[-window_size:]

        if len(window) < window_size:
            print("⚠️ Nicht genügend Preisdaten für Trendanalyse.")
            return None

        try:
            closes = [entry["close"] for entry in window if "close" in entry]
            if len(closes) < window_size:
                print("⚠️ Ungültige Daten im Trendfenster.")
                return None

            sma = sum(closes) / window_size
            last_price = closes[-1]
            trend = "up" if last_price > sma else "down"

            print(f"[Trend] SMA: {sma:.2f}, Letzter Preis: {last_price:.2f} ➜ Trend: {trend}")
            return trend

        except Exception as e:
            print(f"❌ Fehler bei Trendanalyse: {e}")
            return None

    def get_newsapi_headlines(self, query):
        url = (
            f"https://newsapi.org/v2/everything?q={query}&sortBy=publishedAt&language=en&pageSize=10&apiKey={NEWSAPI_KEY}"
        )
        response = requests.get(url)
        articles = response.json().get("articles", [])
        return [article["title"] for article in articles]

    def create_order(self, symbol, qty, side):
        return MarketOrderRequest(
            symbol=symbol,
            qty=int(qty),
            side=OrderSide.BUY if side == "buy" else OrderSide.SELL,
            type=OrderType.MARKET,
            time_in_force=TimeInForce.GTC,
        )

    def submit_order(self, order):
        self.client.submit_order(order)

    def get_position(self):
        try:
            return self.client.get_open_position(self.symbol)
        except:
            return None

    def get_candlestick_signal(self):
        if self.historical_data is None or len(self.historical_data) < 3:
            return "neutral"
        try:
            pattern = detect_candlestick_pattern(self.historical_data)
            print(f"[🕯️ Mustererkennung] Erkanntes Pattern: {pattern}")
            return pattern
        except Exception as e:
            print(f"[Fehler] Candle-Erkennung fehlgeschlagen: {e}")
            return "neutral"

    def make_decision(self, sentiment, trend, candle_signal):
        score = 0

        if trend == "up":
            score += 1
        elif trend == "down":
            score -= 1

        if candle_signal in ["bullish_engulfing", "hammer", "three_white_soldiers"]:
            score += 2
        elif candle_signal in ["bearish_engulfing", "shooting_star", "three_black_crows"]:
            score -= 2

        # Sentiment fließt nur leicht ein
        if sentiment == "positive":
            score += 0.5
        elif sentiment == "negative":
            score -= 0.5

        if score >= 2:
            return "buy"
        elif score <= -2:
            return "sell"
        else:
            return "hold"

    def calculate_risk_levels(self, entry_price, risk_pct=0.02, reward_pct=0.04):
        stop_loss = entry_price * (1 - risk_pct)
        take_profit = entry_price * (1 + reward_pct)
        return round(stop_loss, 2), round(take_profit, 2)
