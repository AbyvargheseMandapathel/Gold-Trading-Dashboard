import pandas as pd
import numpy as np

def generate_signals(df):
    """
    Generate trading signals based on technical indicators
    
    Parameters:
    df (pandas.DataFrame): DataFrame with technical indicators
    
    Returns:
    pandas.DataFrame: DataFrame with added signal columns
    """
    # Create a copy to avoid modifying the original
    df_signals = df.copy()
    
    # Make sure all columns have the same index
    df_signals = df_signals.apply(lambda x: pd.Series(x.values, index=df_signals.index))
    
    # Initialize signal column (0 = no signal, 1 = buy, -1 = sell)
    df_signals['signal'] = 0
    
    # Initialize signal columns with zeros
    signal_columns = ['signal_rsi', 'signal_macd', 'signal_bb', 'signal_ma']
    for col in signal_columns:
        df_signals[col] = 0
    
    # Generate signals based on RSI
    df_signals.loc[df_signals['RSI'] < 30, 'signal_rsi'] = 1  # Oversold - Buy signal
    df_signals.loc[df_signals['RSI'] > 70, 'signal_rsi'] = -1  # Overbought - Sell signal
    
    # Generate signals based on MACD
    try:
        df_signals.loc[(df_signals['MACD'] > df_signals['MACD_Signal']) & 
                      (df_signals['MACD'].shift(1) <= df_signals['MACD_Signal'].shift(1)), 'signal_macd'] = 1  # MACD crosses above signal line - Buy
        df_signals.loc[(df_signals['MACD'] < df_signals['MACD_Signal']) & 
                      (df_signals['MACD'].shift(1) >= df_signals['MACD_Signal'].shift(1)), 'signal_macd'] = -1  # MACD crosses below signal line - Sell
    except Exception as e:
        print(f"Error in MACD comparison: {e}")
    
    # Generate signals based on Bollinger Bands
    try:
        # First align the dataframes to ensure they have the same structure
        close_series = df_signals['Close']
        bb_lower = df_signals['BB_Lower']
        bb_upper = df_signals['BB_Upper']
        
        # Now perform the comparisons
        df_signals.loc[close_series < bb_lower, 'signal_bb'] = 1  # Price below lower band - Buy signal
        df_signals.loc[close_series > bb_upper, 'signal_bb'] = -1  # Price above upper band - Sell signal
    except Exception as e:
        print(f"Error in Bollinger Bands comparison: {e}")
        # Use a safer approach with loc instead of at
        for i in range(len(df_signals)):
            current_idx = df_signals.index[i]
            try:
                if pd.notna(df_signals.loc[current_idx, 'Close']) and pd.notna(df_signals.loc[current_idx, 'BB_Lower']):
                    if df_signals.loc[current_idx, 'Close'] < df_signals.loc[current_idx, 'BB_Lower']:
                        df_signals.loc[current_idx, 'signal_bb'] = 1
                
                if pd.notna(df_signals.loc[current_idx, 'Close']) and pd.notna(df_signals.loc[current_idx, 'BB_Upper']):
                    if df_signals.loc[current_idx, 'Close'] > df_signals.loc[current_idx, 'BB_Upper']:
                        df_signals.loc[current_idx, 'signal_bb'] = -1
            except Exception as inner_e:
                pass
                # print(f"Error processing index {current_idx}: {inner_e}")
    
    # Generate signals based on Moving Average crossovers
    try:
        df_signals.loc[(df_signals['SMA_20'] > df_signals['SMA_50']) & 
                      (df_signals['SMA_20'].shift(1) <= df_signals['SMA_50'].shift(1)), 'signal_ma'] = 1  # Short MA crosses above long MA - Buy
        df_signals.loc[(df_signals['SMA_20'] < df_signals['SMA_50']) & 
                      (df_signals['SMA_20'].shift(1) >= df_signals['SMA_50'].shift(1)), 'signal_ma'] = -1  # Short MA crosses below long MA - Sell
    except Exception as e:
        print(f"Error in Moving Average comparison: {e}")
        # Use a safer approach with loc instead of at
        for i in range(1, len(df_signals)):
            current_idx = df_signals.index[i]
            prev_idx = df_signals.index[i-1]
            
            try:
                if (pd.notna(df_signals.loc[current_idx, 'SMA_20']) and 
                    pd.notna(df_signals.loc[current_idx, 'SMA_50']) and
                    pd.notna(df_signals.loc[prev_idx, 'SMA_20']) and
                    pd.notna(df_signals.loc[prev_idx, 'SMA_50'])):
                    
                    if (df_signals.loc[current_idx, 'SMA_20'] > df_signals.loc[current_idx, 'SMA_50'] and 
                        df_signals.loc[prev_idx, 'SMA_20'] <= df_signals.loc[prev_idx, 'SMA_50']):
                        df_signals.loc[current_idx, 'signal_ma'] = 1
                        
                    if (df_signals.loc[current_idx, 'SMA_20'] < df_signals.loc[current_idx, 'SMA_50'] and 
                        df_signals.loc[prev_idx, 'SMA_20'] >= df_signals.loc[prev_idx, 'SMA_50']):
                        df_signals.loc[current_idx, 'signal_ma'] = -1
            except Exception as inner_e:
                print(f"Error processing indices {prev_idx} and {current_idx}: {inner_e}")
    
    # Fill NaN values with 0 (no signal)
    for col in signal_columns:
        if col in df_signals.columns:
            df_signals[col] = df_signals[col].fillna(0)
    
    # Calculate the combined signal
    df_signals['signal'] = df_signals[signal_columns].sum(axis=1)
    df_signals.loc[df_signals['signal'] > 0, 'signal'] = 1  # Positive sum becomes buy signal
    df_signals.loc[df_signals['signal'] < 0, 'signal'] = -1  # Negative sum becomes sell signal
    
    # Calculate signal strength (0-10 scale)
    df_signals['signal_strength'] = abs(df_signals[signal_columns].sum(axis=1)) / len(signal_columns) * 10
    df_signals['signal_strength'] = df_signals['signal_strength'].round().clip(1, 10)  # Clip to range 1-10
    
    # Add signal reason
    df_signals['signal_reason'] = ''
    
    # For buy signals
    buy_mask = df_signals['signal'] == 1
    df_signals.loc[buy_mask & (df_signals['signal_rsi'] > 0), 'signal_reason'] += 'RSI oversold; '
    df_signals.loc[buy_mask & (df_signals['signal_macd'] > 0), 'signal_reason'] += 'MACD bullish crossover; '
    df_signals.loc[buy_mask & (df_signals['signal_bb'] > 0), 'signal_reason'] += 'Price below lower BB; '
    df_signals.loc[buy_mask & (df_signals['signal_ma'] > 0), 'signal_reason'] += 'MA bullish crossover; '
    
    # For sell signals
    sell_mask = df_signals['signal'] == -1
    df_signals.loc[sell_mask & (df_signals['signal_rsi'] < 0), 'signal_reason'] += 'RSI overbought; '
    df_signals.loc[sell_mask & (df_signals['signal_macd'] < 0), 'signal_reason'] += 'MACD bearish crossover; '
    df_signals.loc[sell_mask & (df_signals['signal_bb'] < 0), 'signal_reason'] += 'Price above upper BB; '
    df_signals.loc[sell_mask & (df_signals['signal_ma'] < 0), 'signal_reason'] += 'MA bearish crossover; '
    
    # Remove trailing semicolon and space
    df_signals['signal_reason'] = df_signals['signal_reason'].str.rstrip('; ')
    
    return df_signals

if __name__ == "__main__":
    # Test the function
    from data_fetcher import fetch_gold_data
    from indicators import add_indicators
    from pattern_recognition import detect_candlestick_patterns, detect_chart_patterns
    
    data = fetch_gold_data(period="1mo")
    data_with_indicators = add_indicators(data)
    data_with_patterns = detect_candlestick_patterns(data_with_indicators)
    data_with_chart_patterns = detect_chart_patterns(data_with_patterns)
    data_with_signals = generate_signals(data_with_chart_patterns)
    
    # Count signals
    buy_signals = (data_with_signals['signal'] == 1).sum()
    sell_signals = (data_with_signals['signal'] == -1).sum()
    
    print(f"Buy signals: {buy_signals}")
    print(f"Sell signals: {sell_signals}")
    
    # Show the last few signals
    signal_data = data_with_signals[['Close', 'signal', 'signal_strength', 'signal_reason']].tail(10)
    print("\nRecent signals:")
    print(signal_data)