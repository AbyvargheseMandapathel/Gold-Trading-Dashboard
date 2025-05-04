import pandas as pd
import numpy as np

def identify_support_resistance(df, window=20):
    """Identify support and resistance levels based on rolling min/max"""
    if df.empty or 'low' not in df.columns or 'high' not in df.columns:
        return [], []

    support = df['low'].rolling(window=window).min().iloc[-window:]
    resistance = df['high'].rolling(window=window).max().iloc[-window:]
    return support.values, resistance.values


def add_indicators(df):
    """Add technical indicators like SMA, EMA, RSI, MACD, Bollinger Bands"""
    if df.empty:
        return df

    # Moving Averages
    df['sma_20'] = df['close'].rolling(window=20).mean()
    df['sma_50'] = df['close'].rolling(window=50).mean()
    df['ema_20'] = df['close'].ewm(span=20, adjust=False).mean()

    # RSI
    delta = df['close'].diff()
    gain = delta.clip(lower=0).rolling(window=14).mean()
    loss = -delta.clip(upper=0).rolling(window=14).mean()
    rs = gain / loss
    df['rsi'] = 100 - (100 / (1 + rs))

    # MACD
    df['macd'] = df['close'].ewm(span=12, adjust=False).mean() - df['close'].ewm(span=26, adjust=False).mean()
    df['macd_signal'] = df['macd'].ewm(span=9, adjust=False).mean()

    # Bollinger Bands
    df['bb_middle'] = df['close'].rolling(window=20).mean()
    df['bb_upper'] = df['bb_middle'] + 2 * df['close'].rolling(window=20).std()
    df['bb_lower'] = df['bb_middle'] - 2 * df['close'].rolling(window=20).std()

    return df


def generate_signals(df):
    """Generate buy/sell signals based on technical indicators"""
    if df.empty:
        return df

    df['signal'] = 'HOLD'
    df['signal_strength'] = 0.0

    if 'rsi' in df.columns:
        df.loc[df['rsi'] < 30, 'signal'] = 'BUY'
        df.loc[df['rsi'] > 70, 'signal'] = 'SELL'

    if 'sma_20' in df.columns and 'sma_50' in df.columns:
        df['signal_strength'] += np.where(df['sma_20'] > df['sma_50'], 0.5, -0.5)

    if 'macd' in df.columns and 'macd_signal' in df.columns:
        df['signal_strength'] += np.where(df['macd'] > df['macd_signal'], 0.5, -0.5)

    return df


def identify_patterns(df):
    """Detect candlestick patterns using TA-Lib"""
    patterns = {}

    if len(df) < 14:
        return patterns

    try:
        hammer = talib.CDLHAMMER(df['open'], df['high'], df['low'], df['close'])
        engulfing = talib.CDLENGULFING(df['open'], df['high'], df['low'], df['close'])
        shooting_star = talib.CDLSHOOTINGSTAR(df['open'], df['high'], df['low'], df['close'])

        if (hammer != 0).any():
            patterns['Hammer'] = hammer[hammer != 0].index.tolist()
        if (engulfing != 0).any():
            patterns['Engulfing'] = engulfing[engulfing != 0].index.tolist()
        if (shooting_star != 0).any():
            patterns['Shooting Star'] = shooting_star[shooting_star != 0].index.tolist()

    except Exception as e:
        print("Pattern detection failed:", e)

    return patterns