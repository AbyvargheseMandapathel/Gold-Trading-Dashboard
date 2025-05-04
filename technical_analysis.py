"""
Technical Analysis Module
This module combines functionality from indicators, pattern recognition, and signal generation
to provide a unified interface for technical analysis of gold price data.
"""

# Import functions from other modules
from indicators import add_indicators as add_all_indicators
from indicators import calculate_support_resistance
from pattern_recognition import (
    detect_candlestick_patterns, 
    detect_chart_patterns
)
from signal_generator import generate_signals as generate_trading_signals

def add_indicators(df):
    """
    Add all technical indicators to the dataframe
    
    Parameters:
    df (pandas.DataFrame): DataFrame with OHLCV data
    
    Returns:
    pandas.DataFrame: DataFrame with added indicators
    """
    # Use the add_indicators function from indicators.py
    return add_all_indicators(df)

def identify_support_resistance(df):
    """
    Identify support and resistance levels
    
    Parameters:
    df (pandas.DataFrame): DataFrame with OHLCV data
    
    Returns:
    tuple: (support_levels, resistance_levels)
    """
    # This would typically use more complex algorithms
    # For now, we'll use a simple approach based on recent highs and lows
    
    # Find local minima for support
    support_levels = []
    for i in range(2, len(df) - 2):
        # Check if this point is a local minimum
        if (df['Low'].iloc[i] < df['Low'].iloc[i-1]).item() and \
           (df['Low'].iloc[i] < df['Low'].iloc[i-2]).item() and \
           (df['Low'].iloc[i] < df['Low'].iloc[i+1]).item() and \
           (df['Low'].iloc[i] < df['Low'].iloc[i+2]).item():
            support_levels.append(df['Low'].iloc[i].item())  # Extract the scalar value
    
    # Find local maxima for resistance
    resistance_levels = []
    for i in range(2, len(df) - 2):
        # Check if this point is a local maximum
        if (df['High'].iloc[i] > df['High'].iloc[i-1]).item() and \
           (df['High'].iloc[i] > df['High'].iloc[i-2]).item() and \
           (df['High'].iloc[i] > df['High'].iloc[i+1]).item() and \
           (df['High'].iloc[i] > df['High'].iloc[i+2]).item():
            resistance_levels.append(df['High'].iloc[i].item())  # Extract the scalar value
    
    # Keep only the most recent levels (last 5)
    support_levels = sorted(support_levels)[-5:] if support_levels else []
    resistance_levels = sorted(resistance_levels)[-5:] if resistance_levels else []
    
    return support_levels, resistance_levels

def identify_candlestick_patterns(df):
    """
    Identify candlestick patterns
    
    Parameters:
    df (pandas.DataFrame): DataFrame with OHLCV data
    
    Returns:
    dict: Dictionary of patterns and their locations
    """
    # Use the detect_candlestick_patterns function from pattern_recognition.py
    patterns_df = detect_candlestick_patterns(df)
    
    # Convert to dictionary format for dashboard
    patterns = {}
    pattern_columns = ['doji', 'hammer', 'shooting_star', 'engulfing_bullish', 
                       'engulfing_bearish', 'morning_star', 'evening_star']
    
    for pattern in pattern_columns:
        if pattern in patterns_df.columns:
            indices = patterns_df.index[patterns_df[pattern]].tolist()
            if indices:
                patterns[pattern] = indices
    
    return patterns

def identify_chart_patterns(df):
    """
    Identify chart patterns
    
    Parameters:
    df (pandas.DataFrame): DataFrame with OHLCV data
    
    Returns:
    dict: Dictionary of patterns and their locations
    """
    # Use the detect_chart_patterns function from pattern_recognition.py
    patterns_df = detect_chart_patterns(df)
    
    # Convert to dictionary format for dashboard
    patterns = {}
    pattern_columns = ['double_top', 'double_bottom', 'head_and_shoulders', 
                       'inverse_head_and_shoulders']
    
    for pattern in pattern_columns:
        if pattern in patterns_df.columns:
            indices = patterns_df.index[patterns_df[pattern]].tolist()
            if indices:
                patterns[pattern] = indices
    
    return patterns

def identify_patterns(df):
    """
    Identify both candlestick and chart patterns
    
    Parameters:
    df (pandas.DataFrame): DataFrame with OHLCV data
    
    Returns:
    dict: Dictionary of patterns and their locations
    """
    try:
        # Combine candlestick and chart patterns
        candlestick_patterns = identify_candlestick_patterns(df)
        chart_patterns = identify_chart_patterns(df)
        
        # Merge the dictionaries
        all_patterns = {**candlestick_patterns, **chart_patterns}
        
        return all_patterns
    except Exception as e:
        print(f"Error identifying patterns: {e}")
        return {}  # Return empty dict on error

def generate_signals(df):
    """
    Generate trading signals based on technical indicators and patterns
    
    Parameters:
    df (pandas.DataFrame): DataFrame with OHLCV data and indicators
    
    Returns:
    pandas.DataFrame: DataFrame with added signal columns
    """
    # Use the generate_signals function from signal_generator.py
    return generate_trading_signals(df)