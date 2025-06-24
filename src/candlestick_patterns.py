import pandas as pd

def detect_candlestick_pattern(df: pd.DataFrame):
    """
    Erkennt grundlegende Candlestick-Muster anhand der letzten 3 Kerzen.
    Erwartet einen DataFrame mit mind. 3 Kerzen (open, high, low, close).
    Gibt das erkannte Muster zurück oder 'neutral'.
    """
    if len(df) < 3:
        return "neutral"

    c1, c2, c3 = df.iloc[-3], df.iloc[-2], df.iloc[-1]

    # Bullish Engulfing
    if c2['close'] < c2['open'] and c3['close'] > c3['open']:
        if c3['close'] > c2['open'] and c3['open'] < c2['close']:
            return "bullish_engulfing"

    # Bearish Engulfing
    if c2['close'] > c2['open'] and c3['close'] < c3['open']:
        if c3['open'] > c2['close'] and c3['close'] < c2['open']:
            return "bearish_engulfing"

    # Hammer
    body = abs(c3['close'] - c3['open'])
    lower_shadow = min(c3['open'], c3['close']) - c3['low']
    upper_shadow = c3['high'] - max(c3['open'], c3['close'])

    if lower_shadow > 2 * body and upper_shadow < body:
        return "hammer"

    # Shooting Star
    if upper_shadow > 2 * body and lower_shadow < body:
        return "shooting_star"

    # Morning Star (bullish reversal)
    if (c1['close'] < c1['open'] and
        abs(c2['close'] - c2['open']) < (c1['open'] - c1['close']) * 0.5 and
        c3['close'] > c3['open'] and
        c3['close'] > (c1['open'] + c1['close']) / 2):
        return "morning_star"

    return "neutral"
