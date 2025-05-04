import pandas as pd
import numpy as np
from sklearn.linear_model import LinearRegression
# Try to import m-patternpy, but don't fail if it's not available
try:
    import m_patternpy as mpp
    MPP_AVAILABLE = True
except ImportError:
    MPP_AVAILABLE = False
    print("m-patternpy package not available, using built-in pattern recognition")

def detect_candlestick_patterns(df):
    """
    Detect candlestick patterns in the dataframe
    
    Parameters:
    df (pandas.DataFrame): DataFrame with OHLCV data
    
    Returns:
    pandas.DataFrame: DataFrame with pattern columns
    """
    # Create a copy to avoid modifying the original
    df_patterns = df.copy()
    
    # Calculate shadows (wicks) using pandas operations directly
    # Keep everything as pandas Series to maintain index alignment
    # Fix: Ensure we're working with Series, not DataFrames
    max_price = df_patterns[['Open', 'Close']].max(axis=1)
    min_price = df_patterns[['Open', 'Close']].min(axis=1)
    
    # Now these operations will work correctly with pandas Series
    df_patterns['upper_shadow'] = df_patterns['High'] - max_price
    df_patterns['lower_shadow'] = min_price - df_patterns['Low']
    df_patterns['body'] = abs(df_patterns['Close'] - df_patterns['Open'])
    
    # Initialize pattern columns
    pattern_columns = ['doji', 'hammer', 'shooting_star', 'engulfing_bullish', 
                       'engulfing_bearish', 'morning_star', 'evening_star']
    
    for col in pattern_columns:
        df_patterns[col] = False
    
    # Try using m-patternpy for candlestick pattern detection if available
    try:
        # Check if the package has candlestick pattern detection
        if hasattr(mpp, 'detect_candlesticks'):
            candlestick_patterns = mpp.detect_candlesticks(df)
            # Merge the detected patterns with our dataframe
            for pattern in pattern_columns:
                if pattern in candlestick_patterns.columns:
                    df_patterns[pattern] = candlestick_patterns[pattern]
            return df_patterns
    except (ImportError, AttributeError) as e:
        print(f"Using fallback candlestick detection: {e}")
    
    # Fallback to our original implementation if m-patternpy doesn't work
    # Detect Doji (very small body compared to shadows)
    df_patterns['doji'] = df_patterns['body'] <= 0.1 * (df_patterns['High'] - df_patterns['Low'])
    
    # Detect Hammer (small body at the top, long lower shadow, small upper shadow)
    hammer_condition = (
        (df_patterns['lower_shadow'] >= 2 * df_patterns['body']) & 
        (df_patterns['upper_shadow'] <= 0.5 * df_patterns['body']) &
        (df_patterns['body'] > 0)
    )
    df_patterns['hammer'] = hammer_condition
    
    # Detect Shooting Star (small body at the bottom, long upper shadow, small lower shadow)
    shooting_star_condition = (
        (df_patterns['upper_shadow'] >= 2 * df_patterns['body']) & 
        (df_patterns['lower_shadow'] <= 0.5 * df_patterns['body']) &
        (df_patterns['body'] > 0)
    )
    df_patterns['shooting_star'] = shooting_star_condition
    
    # Detect Bullish Engulfing (current candle's body engulfs previous candle's body)
    for i in range(1, len(df_patterns)):
        if (df_patterns['Close'].iloc[i] > df_patterns['Open'].iloc[i] and  # Current candle is bullish
            df_patterns['Open'].iloc[i-1] > df_patterns['Close'].iloc[i-1] and  # Previous candle is bearish
            df_patterns['Open'].iloc[i] <= df_patterns['Close'].iloc[i-1] and  # Current open <= previous close
            df_patterns['Close'].iloc[i] >= df_patterns['Open'].iloc[i-1]):  # Current close >= previous open
            df_patterns['engulfing_bullish'].iloc[i] = True
    
    # Detect Bearish Engulfing (current candle's body engulfs previous candle's body)
    for i in range(1, len(df_patterns)):
        if (df_patterns['Close'].iloc[i] < df_patterns['Open'].iloc[i] and  # Current candle is bearish
            df_patterns['Open'].iloc[i-1] < df_patterns['Close'].iloc[i-1] and  # Previous candle is bullish
            df_patterns['Open'].iloc[i] >= df_patterns['Close'].iloc[i-1] and  # Current open >= previous close
            df_patterns['Close'].iloc[i] <= df_patterns['Open'].iloc[i-1]):  # Current close <= previous open
            df_patterns['engulfing_bearish'].iloc[i] = True
    
    # Detect Morning Star (bearish trend, small middle candle, bullish third candle)
    for i in range(2, len(df_patterns)):
        if (df_patterns['Close'].iloc[i-2] < df_patterns['Open'].iloc[i-2] and  # First candle is bearish
            abs(df_patterns['Close'].iloc[i-1] - df_patterns['Open'].iloc[i-1]) < 0.3 * df_patterns['body'].iloc[i-2] and  # Second candle has small body
            df_patterns['Close'].iloc[i] > df_patterns['Open'].iloc[i] and  # Third candle is bullish
            df_patterns['Close'].iloc[i] > (df_patterns['Open'].iloc[i-2] + df_patterns['Close'].iloc[i-2]) / 2):  # Third candle closes above midpoint of first
            df_patterns['morning_star'].iloc[i] = True
    
    # Detect Evening Star (bullish trend, small middle candle, bearish third candle)
    for i in range(2, len(df_patterns)):
        if (df_patterns['Close'].iloc[i-2] > df_patterns['Open'].iloc[i-2] and  # First candle is bullish
            abs(df_patterns['Close'].iloc[i-1] - df_patterns['Open'].iloc[i-1]) < 0.3 * df_patterns['body'].iloc[i-2] and  # Second candle has small body
            df_patterns['Close'].iloc[i] < df_patterns['Open'].iloc[i] and  # Third candle is bearish
            df_patterns['Close'].iloc[i] < (df_patterns['Open'].iloc[i-2] + df_patterns['Close'].iloc[i-2]) / 2):  # Third candle closes below midpoint of first
            df_patterns['evening_star'].iloc[i] = True
    
    return df_patterns

def detect_chart_patterns(df, window=20):
    """
    Detect chart patterns like head and shoulders, double tops, etc.
    
    Parameters:
    df (pandas.DataFrame): OHLCV dataframe
    window (int): Window size for pattern detection
    
    Returns:
    pandas.DataFrame: DataFrame with pattern columns
    """
    # Make a copy to avoid modifying the original
    df_patterns = df.copy()
    
    # Try using m-patternpy for chart pattern detection if available
    try:
        # Check if the package has chart pattern detection
        if hasattr(mpp, 'detect_patterns'):
            # Use m-patternpy to detect chart patterns
            chart_patterns = mpp.detect_patterns(df)
            
            # Initialize our pattern columns
            pattern_columns = ['double_top', 'double_bottom', 'head_and_shoulders', 
                              'inverse_head_and_shoulders', 'trend']
            
            for col in pattern_columns:
                if col != 'trend':
                    df_patterns[col] = False
                else:
                    df_patterns[col] = 'neutral'
            
            # Merge the detected patterns with our dataframe
            for pattern in pattern_columns:
                if pattern in chart_patterns.columns:
                    df_patterns[pattern] = chart_patterns[pattern]
            
            return df_patterns
    except (ImportError, AttributeError) as e:
        print(f"Using fallback chart pattern detection: {e}")
    
    # Fallback to our original implementation if m-patternpy doesn't work
    # Initialize pattern columns
    df_patterns['double_top'] = False
    df_patterns['double_bottom'] = False
    df_patterns['head_and_shoulders'] = False
    df_patterns['inverse_head_and_shoulders'] = False
    df_patterns['trend'] = 'neutral'  # Can be 'uptrend', 'downtrend', or 'neutral'
    
    # Detect trend using linear regression
    for i in range(window, len(df_patterns)):
        # Get the window of data
        window_data = df_patterns.iloc[i-window:i]
        
        # Prepare data for linear regression
        X = np.array(range(window)).reshape(-1, 1)
        y = window_data['Close'].values
        
        # Fit linear regression
        model = LinearRegression()
        model.fit(X, y)
        
        # Determine trend based on slope
        slope = model.coef_[0]
        if slope > 0.01 * np.mean(y) / window:  # Positive slope (uptrend)
            df_patterns.loc[df_patterns.index[i], 'trend'] = 'uptrend'
        elif slope < -0.01 * np.mean(y) / window:  # Negative slope (downtrend)
            df_patterns.loc[df_patterns.index[i], 'trend'] = 'downtrend'
        else:  # Flat slope (neutral)
            df_patterns.loc[df_patterns.index[i], 'trend'] = 'neutral'
    
    # Detect double tops and bottoms
    for i in range(2*window, len(df_patterns)):
        try:
            # Get the window of data
            window_data = df_patterns.iloc[i-2*window:i]
            
            # Find local maxima and minima
            local_maxima = []
            local_minima = []
            
            for j in range(1, len(window_data)-1):
                # Local maximum - use .item() to convert Series to scalar
                if (window_data['High'].iloc[j] > window_data['High'].iloc[j-1]).item() and \
                   (window_data['High'].iloc[j] > window_data['High'].iloc[j+1]).item():
                    local_maxima.append((j, window_data['High'].iloc[j].item()))
                
                # Local minimum - use .item() to convert Series to scalar
                if (window_data['Low'].iloc[j] < window_data['Low'].iloc[j-1]).item() and \
                   (window_data['Low'].iloc[j] < window_data['Low'].iloc[j+1]).item():
                    local_minima.append((j, window_data['Low'].iloc[j].item()))
            
            # Double top: two peaks of similar height with a trough in between
            if len(local_maxima) >= 2:
                for j in range(len(local_maxima)-1):
                    peak1_idx, peak1_val = local_maxima[j]
                    peak2_idx, peak2_val = local_maxima[j+1]
                    
                    # Check if peaks are of similar height (within 1%)
                    if abs(peak1_val - peak2_val) / peak1_val < 0.01 and peak2_idx - peak1_idx > window//4:
                        # Check if there's a trough in between
                        trough_exists = False
                        for k in range(len(local_minima)):
                            trough_idx, trough_val = local_minima[k]
                            if peak1_idx < trough_idx < peak2_idx and trough_val < min(peak1_val, peak2_val) * 0.98:
                                trough_exists = True
                                break
                        
                        if trough_exists:
                            df_patterns.loc[df_patterns.index[i], 'double_top'] = True
                            break
            
            # Double bottom: two troughs of similar depth with a peak in between
            if len(local_minima) >= 2:
                for j in range(len(local_minima)-1):
                    trough1_idx, trough1_val = local_minima[j]
                    trough2_idx, trough2_val = local_minima[j+1]
                    
                    # Check if troughs are of similar depth (within 1%)
                    if abs(trough1_val - trough2_val) / trough1_val < 0.01 and trough2_idx - trough1_idx > window//4:
                        # Check if there's a peak in between
                        peak_exists = False
                        for k in range(len(local_maxima)):
                            peak_idx, peak_val = local_maxima[k]
                            if trough1_idx < peak_idx < trough2_idx and peak_val > max(trough1_val, trough2_val) * 1.02:
                                peak_exists = True
                                break
                        
                        if peak_exists:
                            df_patterns.loc[df_patterns.index[i], 'double_bottom'] = True
                            break
        except Exception as e:
            # print(f"Error processing index {df_patterns.index[i]}: {e}")
            continue
    
    # Head and shoulders patterns are more complex and would require more sophisticated detection
    # This is a simplified version
    
    return df_patterns

def detect_support_resistance(df):
    """
    Detect support and resistance levels
    
    Parameters:
    df (pandas.DataFrame): OHLCV dataframe
    
    Returns:
    tuple: (support_levels, resistance_levels)
    """
    # Fallback to our existing implementation in technical_analysis.py
    from technical_analysis import identify_support_resistance
    return identify_support_resistance(df)

if __name__ == "__main__":
    # Test the functions
    from data_fetcher import fetch_gold_data
    
    data = fetch_gold_data(period="3mo")
    data_with_patterns = detect_candlestick_patterns(data)
    data_with_chart_patterns = detect_chart_patterns(data_with_patterns)
    
    # Test support/resistance detection
    support_levels, resistance_levels = detect_support_resistance(data)
    print(f"Support levels: {support_levels}")
    print(f"Resistance levels: {resistance_levels}")
    
    # Count patterns
    pattern_counts = {
        'Doji': data_with_chart_patterns['doji'].sum(),
        'Hammer': data_with_chart_patterns['hammer'].sum(),
        'Shooting Star': data_with_chart_patterns['shooting_star'].sum(),
        'Bullish Engulfing': data_with_chart_patterns['engulfing_bullish'].sum(),
        'Bearish Engulfing': data_with_chart_patterns['engulfing_bearish'].sum(),
        'Morning Star': data_with_chart_patterns['morning_star'].sum(),
        'Evening Star': data_with_chart_patterns['evening_star'].sum(),
        'Double Top': data_with_chart_patterns['double_top'].sum(),
        'Double Bottom': data_with_chart_patterns['double_bottom'].sum()
    }
    
    print("Pattern counts:")
    for pattern, count in pattern_counts.items():
        print(f"{pattern}: {count}")