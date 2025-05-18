import numpy as np
import pandas as pd
import talib
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class TechnicalIndicators:
    """Class to calculate technical indicators for market data"""
    
    @staticmethod
    def add_indicators(df, config=None):
        """
        Add technical indicators to the dataframe
        
        Args:
            df (pd.DataFrame): Price data with 'open', 'high', 'low', 'close' columns
            config (dict): Configuration for indicators (periods, etc.)
            
        Returns:
            pd.DataFrame: DataFrame with indicators added
        """
        if df.empty:
            return df
        
        # Use default config if none provided
        if config is None:
            config = {
                'sma_periods': [20, 50, 200],
                'ema_periods': [9, 21],
                'rsi_period': 14,
                'macd_fast': 12,
                'macd_slow': 26,
                'macd_signal': 9,
                'bbands_period': 20,
                'bbands_dev': 2
            }
            
        try:
            # Simple Moving Averages
            for period in config['sma_periods']:
                df[f'sma_{period}'] = talib.SMA(df['close'].values, timeperiod=period)
                
            # Exponential Moving Averages
            for period in config['ema_periods']:
                df[f'ema_{period}'] = talib.EMA(df['close'].values, timeperiod=period)
                
            # Relative Strength Index
            df['rsi'] = talib.RSI(df['close'].values, timeperiod=config['rsi_period'])
            
            # MACD
            macd, macd_signal, macd_hist = talib.MACD(
                df['close'].values,
                fastperiod=config['macd_fast'],
                slowperiod=config['macd_slow'],
                signalperiod=config['macd_signal']
            )
            df['macd'] = macd
            df['macd_signal'] = macd_signal
            df['macd_hist'] = macd_hist
            
            # Bollinger Bands
            upperband, middleband, lowerband = talib.BBANDS(
                df['close'].values,
                timeperiod=config['bbands_period'],
                nbdevup=config['bbands_dev'],
                nbdevdn=config['bbands_dev']
            )
            df['bb_upper'] = upperband
            df['bb_middle'] = middleband
            df['bb_lower'] = lowerband
            
            # Average True Range
            df['atr'] = talib.ATR(df['high'].values, df['low'].values, df['close'].values, timeperiod=14)
            
            # Stochastic Oscillator
            slowk, slowd = talib.STOCH(
                df['high'].values,
                df['low'].values,
                df['close'].values,
                fastk_period=14,
                slowk_period=3,
                slowk_matype=0,
                slowd_period=3,
                slowd_matype=0
            )
            df['stoch_k'] = slowk
            df['stoch_d'] = slowd
            
            return df
            
        except Exception as e:
            logger.error(f"Error calculating indicators: {e}")
            return df
    
    @staticmethod
    def identify_support_resistance(df, window=10, threshold=0.02):
        """
        Identify support and resistance levels
        
        Args:
            df (pd.DataFrame): Price data with at least 'high' and 'low' columns
            window (int): Window size for identifying swing highs/lows
            threshold (float): Price threshold for clustering levels (percentage)
            
        Returns:
            dict: Support and resistance levels
        """
        if df.empty:
            return {'support': [], 'resistance': []}
            
        try:
            # Find local swing highs and lows
            highs = []
            lows = []
            
            for i in range(window, len(df) - window):
                # Check if this is a swing high
                if all(df['high'].iloc[i] > df['high'].iloc[i-j] for j in range(1, window+1)) and \
                   all(df['high'].iloc[i] > df['high'].iloc[i+j] for j in range(1, window+1)):
                    highs.append(df['high'].iloc[i])
                
                # Check if this is a swing low
                if all(df['low'].iloc[i] < df['low'].iloc[i-j] for j in range(1, window+1)) and \
                   all(df['low'].iloc[i] < df['low'].iloc[i+j] for j in range(1, window+1)):
                    lows.append(df['low'].iloc[i])
            
            # Cluster levels that are close to each other
            def cluster_levels(levels, threshold_pct):
                if not levels:
                    return []
                    
                clustered = []
                levels.sort()
                
                current_cluster = [levels[0]]
                
                for level in levels[1:]:
                    # Check if the level is within threshold % of the average of current cluster
                    avg_cluster = sum(current_cluster) / len(current_cluster)
                    if (level - avg_cluster) / avg_cluster <= threshold_pct:
                        current_cluster.append(level)
                    else:
                        # Add the average of the current cluster to the result
                        clustered.append(sum(current_cluster) / len(current_cluster))
                        # Start a new cluster
                        current_cluster = [level]
                
                # Add the last cluster
                if current_cluster:
                    clustered.append(sum(current_cluster) / len(current_cluster))
                
                return clustered
            
            # Cluster the support and resistance levels
            clustered_lows = cluster_levels(lows, threshold)
            clustered_highs = cluster_levels(highs, threshold)
            
            return {
                'support': clustered_lows,
                'resistance': clustered_highs
            }
            
        except Exception as e:
            logger.error(f"Error identifying support/resistance: {e}")
            return {'support': [], 'resistance': []}
    
    @staticmethod
    def calculate_pivot_points(df):
        """
        Calculate pivot points (PP, S1, S2, R1, R2) based on the previous period
        
        Args:
            df (pd.DataFrame): Price data with 'high', 'low', 'close' columns
            
        Returns:
            dict: Pivot point values
        """
        if df.empty or len(df) < 1:
            return {
                'pivot': None,
                'r1': None, 'r2': None,
                's1': None, 's2': None
            }
            
        try:
            # Get previous period's data
            prev_high = df['high'].iloc[-1]
            prev_low = df['low'].iloc[-1]
            prev_close = df['close'].iloc[-1]
            
            # Calculate pivot point
            pivot = (prev_high + prev_low + prev_close) / 3
            
            # Calculate support and resistance levels
            r1 = (2 * pivot) - prev_low
            s1 = (2 * pivot) - prev_high
            r2 = pivot + (prev_high - prev_low)
            s2 = pivot - (prev_high - prev_low)
            
            return {
                'pivot': pivot,
                'r1': r1, 'r2': r2,
                's1': s1, 's2': s2
            }
            
        except Exception as e:
            logger.error(f"Error calculating pivot points: {e}")
            return {
                'pivot': None,
                'r1': None, 'r2': None,
                's1': None, 's2': None
            }
