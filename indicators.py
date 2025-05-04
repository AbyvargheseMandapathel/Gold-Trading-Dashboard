import pandas as pd
import numpy as np
import ta

def add_indicators(df):
    """
    Add technical indicators to the dataframe
    
    Parameters:
    df (pandas.DataFrame): DataFrame with OHLCV data
    
    Returns:
    pandas.DataFrame: DataFrame with added indicators
    """
    # Create a copy to avoid modifying the original dataframe
    df_with_indicators = df.copy()
    
    # Extract raw numpy arrays for calculations
    close = df_with_indicators['Close'].values
    high = df_with_indicators['High'].values
    low = df_with_indicators['Low'].values
    
    # Ensure arrays are 1D
    if len(close.shape) > 1:
        close = close.flatten()
    if len(high.shape) > 1:
        high = high.flatten()
    if len(low.shape) > 1:
        low = low.flatten()
    
    # Calculate indicators manually or using ta library with explicit Series creation
    
    # Simple Moving Averages
    df_with_indicators['SMA_20'] = pd.Series(ta.trend.sma_indicator(pd.Series(close), window=20), index=df.index)
    df_with_indicators['SMA_50'] = pd.Series(ta.trend.sma_indicator(pd.Series(close), window=50), index=df.index)
    df_with_indicators['SMA_200'] = pd.Series(ta.trend.sma_indicator(pd.Series(close), window=200), index=df.index)
    
    # Exponential Moving Average
    df_with_indicators['EMA_20'] = pd.Series(ta.trend.ema_indicator(pd.Series(close), window=20), index=df.index)
    
    # Relative Strength Index
    df_with_indicators['RSI'] = pd.Series(ta.momentum.rsi(pd.Series(close), window=14), index=df.index)
    
    # MACD
    macd_series = pd.Series(close, index=df.index)
    macd = ta.trend.MACD(macd_series)
    df_with_indicators['MACD'] = macd.macd()
    df_with_indicators['MACD_Signal'] = macd.macd_signal()
    df_with_indicators['MACD_Hist'] = macd.macd_diff()
    
    # Bollinger Bands
    bollinger = ta.volatility.BollingerBands(pd.Series(close, index=df.index))
    df_with_indicators['BB_Upper'] = bollinger.bollinger_hband()
    df_with_indicators['BB_Middle'] = bollinger.bollinger_mavg()
    df_with_indicators['BB_Lower'] = bollinger.bollinger_lband()
    
    # Ensure all indicators have the same index
    for col in df_with_indicators.columns:
        if col not in df.columns:  # Only process indicator columns
            df_with_indicators[col] = pd.Series(df_with_indicators[col].values, index=df.index)
    
    # Average True Range
    high_series = pd.Series(high, index=df.index)
    low_series = pd.Series(low, index=df.index)
    close_series = pd.Series(close, index=df.index)
    df_with_indicators['ATR'] = ta.volatility.average_true_range(high_series, low_series, close_series)
    
    return df_with_indicators

def calculate_support_resistance(df, window=20):
    """
    Calculate support and resistance levels
    
    Parameters:
    df (pandas.DataFrame): OHLCV dataframe
    window (int): Window size for finding local minima/maxima
    
    Returns:
    tuple: (support_levels, resistance_levels)
    """
    # Make a copy to avoid modifying the original
    df_copy = df.copy()
    
    # Find local minima (support) and maxima (resistance)
    support_levels = []
    resistance_levels = []
    
    for i in range(window, len(df_copy) - window):
        # Check if this is a local minimum (support)
        if all(df_copy['Low'].iloc[i] <= df_copy['Low'].iloc[i-j] for j in range(1, window+1)) and \
           all(df_copy['Low'].iloc[i] <= df_copy['Low'].iloc[i+j] for j in range(1, window+1)):
            support_levels.append(df_copy['Low'].iloc[i])
        
        # Check if this is a local maximum (resistance)
        if all(df_copy['High'].iloc[i] >= df_copy['High'].iloc[i-j] for j in range(1, window+1)) and \
           all(df_copy['High'].iloc[i] >= df_copy['High'].iloc[i+j] for j in range(1, window+1)):
            resistance_levels.append(df_copy['High'].iloc[i])
    
    # Remove duplicates and sort
    support_levels = sorted(list(set([round(level, 2) for level in support_levels])))
    resistance_levels = sorted(list(set([round(level, 2) for level in resistance_levels])))
    
    return support_levels, resistance_levels

if __name__ == "__main__":
    # Test the functions
    from data_fetcher import fetch_gold_data
    
    data = fetch_gold_data()
    data_with_indicators = add_indicators(data)
    support, resistance = calculate_support_resistance(data)
    
    print("Data with indicators:")
    print(data_with_indicators.tail())
    print("\nSupport levels:", support)
    print("Resistance levels:", resistance)