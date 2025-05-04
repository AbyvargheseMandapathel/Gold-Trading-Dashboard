import pandas as pd
import numpy as np
import pandas_ta as ta

def add_indicators(df):
    """Add common technical indicators using pandas-ta"""
    
    # Ensure columns are not MultiIndex
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = ['_'.join(col).strip() for col in df.columns.values]
    
    # Add indicators
    df.ta.sma(length=20, append=True)   # Simple Moving Average 20
    df.ta.sma(length=50, append=True)  # Simple Moving Average 50
    df.ta.ema(length=20, append=True)  # Exponential Moving Average 20
    df.ta.rsi(length=14, append=True)  # RSI - Relative Strength Index
    df.ta.macd(append=True)            # MACD - Moving Average Convergence Divergence
    df.ta.bbands(length=20, std=2, append=True)  # Bollinger Bands
    
    return df

def identify_support_resistance(df, window=20):
    """Identify support and resistance levels based on rolling min/max"""
    support = df['Low'].rolling(window=window).min().iloc[-window:]
    resistance = df['High'].rolling(window=window).max().iloc[-window:]
    
    return support.values, resistance.values

def identify_patterns(df):
    """Detect candlestick patterns using pandas-ta"""
    patterns = {}
    
    # Hammer pattern
    hammer = df.ta.cdl_pattern(name="hammer").iloc[-50:]
    if (hammer != 0).any():
        patterns['Hammer'] = hammer[hammer != 0].index.tolist()
    
    # Shooting star
    shooting_star = df.ta.cdl_pattern(name="shootingstar").iloc[-50:]
    if (shooting_star != 0).any():
        patterns['Shooting Star'] = shooting_star[shooting_star != 0].index.tolist()
    
    # Engulfing
    engulfing = df.ta.cdl_pattern(name="engulfing").iloc[-50:]
    if (engulfing != 0).any():
        patterns['Engulfing'] = engulfing[engulfing != 0].index.tolist()

    return patterns

def generate_signals(df):
    """Generate buy/sell signals based on technical indicators"""
    df['Signal'] = 'HOLD'
    df['Signal_Strength'] = 0.0
    
    # RSI-based signal
    df.loc[df['RSI_14'] < 30, 'Signal'] = 'BUY'
    df.loc[df['RSI_14'] > 70, 'Signal'] = 'SELL'
    
    # MACD crossover signal
    df['MACD_diff'] = df['MACD_12_26_9'] - df['MACDs_12_26_9']
    df['Signal_Strength'] += np.where(df['MACD_diff'] > 0, 0.5, -0.5)
    
    # SMA trend signal
    df['SMA_20'] = df['Close'].rolling(window=20).mean()
    df['SMA_50'] = df['Close'].rolling(window=50).mean()
    df['Signal_Strength'] += np.where(df['SMA_20'] > df['SMA_50'], 0.5, -0.5)
    
    return df