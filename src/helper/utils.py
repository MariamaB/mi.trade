from alpaca.data.historical import StockHistoricalDataClient
from alpaca.data.requests import StockBarsRequest
from alpaca.data.timeframe import TimeFrame
from dotenv import load_dotenv
import os
import pandas as pd
import pytz

load_dotenv()
API_KEY = os.getenv("API_KEY")
API_SECRET = os.getenv("API_SECRET")

data_client = StockHistoricalDataClient(API_KEY, API_SECRET)

def load_alpaca_data(symbol, start_date, end_date):
    request_params = StockBarsRequest(
        symbol_or_symbols=symbol,
        timeframe=TimeFrame.Day,
        start=start_date,
        end=end_date,
    )
    bars = data_client.get_stock_bars(request_params).df
    if not bars.empty:
        bars = bars.reset_index()
        bars = bars[bars['symbol'] == symbol]
        return pd.DataFrame({
            'date': bars['timestamp'],
            'open': bars['open'],
            'high': bars['high'],
            'low': bars['low'],
            'close': bars['close'],
            'volume': bars['volume']
        })
    return pd.DataFrame()

def convert_to_german_time(us_open_time, us_close_time):
    # Umwandlung und Rückgabe in deutsche Zeit (Berlin)
    return f"{us_open_time.astimezone(pytz.timezone('Europe/Berlin')).strftime('%d:%m:%Y %H:%M')}-{us_close_time.astimezone(pytz.timezone('Europe/Berlin')).strftime('%H:%M')}"
