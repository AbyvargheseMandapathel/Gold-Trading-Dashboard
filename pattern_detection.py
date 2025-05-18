import numpy as np
import pandas as pd
import talib
from scipy.signal import argrelextrema
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class PatternDetection:
    """Class to detect chart patterns"""
    
    @staticmethod
    def detect_candlestick_patterns(df):
        """
        Detect candlestick patterns using TA-Lib
        
        Args:
            df (pd.DataFrame): Price data with 'open', 'high', 'low', 'close' columns
            
        Returns:
            dict: Detected patterns with their names and strength
        """
        if df.empty:
            return {}
            
        try:
            patterns = {
                'CDL3INSIDE': 'Three Inside Up/Down',
                'CDLDOJI': 'Doji',
                'CDLENGULFING': 'Engulfing Pattern',
                'CDLHAMMER': 'Hammer',
                'CDLHARAMI': 'Harami Pattern',
                'CDLMORNINGSTAR': 'Morning Star',
                'CDLEVENINGSTAR': 'Evening Star',
                'CDLPIERCING': 'Piercing Pattern',
                'CDLSHOOTINGSTAR': 'Shooting Star',
                'CDLMARUBOZU': 'Marubozu',
                'CDL3WHITESOLDIERS': 'Three White Soldiers',
                'CDL3BLACKCROWS': 'Three Black Crows'
            }
            
            results = {}
            
            # Initialize a result dataframe with all patterns set to 0 (no pattern)
            for name in patterns.values():
                results[name] = 0
            
            # Get the most recent candle pattern signals
            for pattern_func, pattern_name in patterns.items():
                pattern_result = getattr(talib, pattern_func)(
                    df['open'].values, 
                    df['high'].values, 
                    df['low'].values, 
                    df['close'].values
                )
                
                # Get the latest pattern signal (last value in the array)
                signal = pattern_result[-1] if len(pattern_result) > 0 else 0
                
                # Add to results if pattern detected
                if signal != 0:
                    results[pattern_name] = signal
            
            # Filter out patterns that weren't detected
            detected = {k: v for k, v in results.items() if v != 0}
            
            return detected
            
        except Exception as e:
            logger.error(f"Error detecting candlestick patterns: {e}")
            return {}
    
    @staticmethod
    def detect_chart_patterns(df, lookback=20):
        """
        Detect common chart patterns like head and shoulders, double top/bottom, etc.
        
        Args:
            df (pd.DataFrame): Price data with at least 'close' column
            lookback (int): Number of periods to look back for pattern detection
            
        Returns:
            dict: Detected chart patterns
        """
        if df.empty or len(df) < lookback:
            return {}
            
        try:
            patterns = {}
            
            # Get relevant section of dataframe for analysis
            section = df.iloc[-lookback:].copy()
            
            # Find local maxima and minima
            section['local_max'] = section.iloc[argrelextrema(section['close'].values, np.greater, order=5)[0]]['close']
            section['local_min'] = section.iloc[argrelextrema(section['close'].values, np.less, order=5)[0]]['close']
            
            # Double Top Detection
            if not section['local_max'].dropna().empty and len(section['local_max'].dropna()) >= 2:
                max_values = section['local_max'].dropna().values
                if len(max_values) >= 2:
                    last_two_tops = max_values[-2:]
                    if abs(last_two_tops[0] - last_two_tops[1]) / last_two_tops[0] < 0.02:  # Less than 2% difference
                        patterns['Double Top'] = -1  # Bearish signal
            
            # Double Bottom Detection
            if not section['local_min'].dropna().empty and len(section['local_min'].dropna()) >= 2:
                min_values = section['local_min'].dropna().values
                if len(min_values) >= 2:
                    last_two_bottoms = min_values[-2:]
                    if abs(last_two_bottoms[0] - last_two_bottoms[1]) / last_two_bottoms[0] < 0.02:  # Less than 2% difference
                        patterns['Double Bottom'] = 1  # Bullish signal
            
            # Head and Shoulders Detection
            if not section['local_max'].dropna().empty and len(section['local_max'].dropna()) >= 3:
                max_values = section['local_max'].dropna().values
                if len(max_values) >= 3:
                    last_three_tops = max_values[-3:]
                    # Check if middle peak is higher than the shoulders
                    if last_three_tops[1] > last_three_tops[0] and last_three_tops[1] > last_three_tops[2]:
                        # Check if shoulders are of similar height
                        if abs(last_three_tops[0] - last_three_tops[2]) / last_three_tops[0] < 0.05:  # Less than 5% difference
                            patterns['Head and Shoulders'] = -1  # Bearish signal
            
            # Inverse Head and Shoulders Detection
            if not section['local_min'].dropna().empty and len(section['local_min'].dropna()) >= 3:
                min_values = section['local_min'].dropna().values
                if len(min_values) >= 3:
                    last_three_bottoms = min_values[-3:]
                    # Check if middle trough is lower than the shoulders
                    if last_three_bottoms[1] < last_three_bottoms[0] and last_three_bottoms[1] < last_three_bottoms[2]:
                        # Check if shoulders are of similar height
                        if abs(last_three_bottoms[0] - last_three_bottoms[2]) / last_three_bottoms[0] < 0.05:  # Less than 5% difference
                            patterns['Inverse Head and Shoulders'] = 1  # Bullish signal
            
            # Ascending Triangle
            if not section['local_max'].dropna().empty and not section['local_min'].dropna().empty:
                max_values = section['local_max'].dropna().values
                min_values = section['local_min'].dropna().values
                
                if len(max_values) >= 2 and len(min_values) >= 2:
                    # Check if max values are approximately the same (resistance)
                    if abs(max_values[-1] - max_values[-2]) / max_values[-2] < 0.02:
                        # Check if min values are increasing (ascending support)
                        if min_values[-1] > min_values[-2]:
                            patterns['Ascending Triangle'] = 1  # Bullish signal
            
            # Descending Triangle
            if not section['local_max'].dropna().empty and not section['local_min'].dropna().empty:
                max_values = section['local_max'].dropna().values
                min_values = section['local_min'].dropna().values
                
                if len(max_values) >= 2 and len(min_values) >= 2:
                    # Check if min values are approximately the same (support)
                    if abs(min_values[-1] - min_values[-2]) / min_values[-2] < 0.02:
                        # Check if max values are decreasing (descending resistance)
                        if max_values[-1] < max_values[-2]:
                            patterns['Descending Triangle'] = -1  # Bearish signal
            
            return patterns
            
        except Exception as e:
            logger.error(f"Error detecting chart patterns: {e}")
            return {}
