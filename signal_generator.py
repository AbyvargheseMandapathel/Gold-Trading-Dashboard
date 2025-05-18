import pandas as pd
import numpy as np
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class SignalGenerator:
    """Class to generate trading signals based on technical indicators and patterns"""
    
    def __init__(self, config=None):
        """
        Initialize signal generator with custom configuration
        
        Args:
            config (dict): Signal generation configuration
        """
        self.config = config or {
            # Default configuration for signal generation
            'rsi': {
                'oversold': 30,
                'overbought': 70
            },
            'sma': {
                'fast': 20,
                'slow': 50
            },
            'macd': {
                'signal_trigger': 0
            },
            'stochastic': {
                'oversold': 20,
                'overbought': 80
            },
            'bbands': {
                'lower_touch_percentage': 0.01,  # How close to lower band for a buy signal
                'upper_touch_percentage': 0.01   # How close to upper band for a sell signal
            }
        }
    
    def generate_signals(self, df, patterns=None, support_resistance=None):
        """
        Generate trading signals based on indicators and patterns
        
        Args:
            df (pd.DataFrame): Dataframe with price data and indicators
            patterns (dict): Detected chart patterns
            support_resistance (dict): Support and resistance levels
            
        Returns:
            dict: Dictionary of generated signals with strengths
        """
        if df.empty:
            return {'buy': 0, 'sell': 0, 'signals': []}
            
        try:
            # Get the latest row of data
            latest = df.iloc[-1]
            
            signals = []
            buy_strength = 0
            sell_strength = 0
            
            # RSI signals
            if 'rsi' in latest:
                if latest['rsi'] < self.config['rsi']['oversold']:
                    buy_strength += 1
                    signals.append({"type": "buy", "reason": f"RSI oversold at {latest['rsi']:.2f}"})
                elif latest['rsi'] > self.config['rsi']['overbought']:
                    sell_strength += 1
                    signals.append({"type": "sell", "reason": f"RSI overbought at {latest['rsi']:.2f}"})
            
            # SMA crossover
            fast_col = f"sma_{self.config['sma']['fast']}"
            slow_col = f"sma_{self.config['sma']['slow']}"
            
            if fast_col in df.columns and slow_col in df.columns and len(df) > 1:
                # Get current and previous values
                curr_fast, prev_fast = df[fast_col].iloc[-1], df[fast_col].iloc[-2]
                curr_slow, prev_slow = df[slow_col].iloc[-1], df[slow_col].iloc[-2]
                
                # Check for crossover
                if prev_fast < prev_slow and curr_fast > curr_slow:
                    buy_strength += 1.5  # Stronger signal
                    signals.append({"type": "buy", "reason": f"SMA crossover: {fast_col} crossed above {slow_col}"})
                elif prev_fast > prev_slow and curr_fast < curr_slow:
                    sell_strength += 1.5  # Stronger signal
                    signals.append({"type": "sell", "reason": f"SMA crossover: {fast_col} crossed below {slow_col}"})
            
            # MACD signals
            if 'macd' in latest and 'macd_signal' in latest:
                # MACD line crosses above signal line
                if len(df) > 1 and df['macd'].iloc[-2] < df['macd_signal'].iloc[-2] and latest['macd'] > latest['macd_signal']:
                    buy_strength += 1
                    signals.append({"type": "buy", "reason": "MACD crossed above signal line"})
                # MACD line crosses below signal line
                elif len(df) > 1 and df['macd'].iloc[-2] > df['macd_signal'].iloc[-2] and latest['macd'] < latest['macd_signal']:
                    sell_strength += 1
                    signals.append({"type": "sell", "reason": "MACD crossed below signal line"})
            
            # Bollinger Bands signals
            if 'bb_upper' in latest and 'bb_lower' in latest and 'close' in latest:
                # Price near lower band (potential buy)
                lower_distance = (latest['close'] - latest['bb_lower']) / latest['close']
                if abs(lower_distance) < self.config['bbands']['lower_touch_percentage']:
                    buy_strength += 0.5
                    signals.append({"type": "buy", "reason": "Price near lower Bollinger Band"})
                
                # Price near upper band (potential sell)
                upper_distance = (latest['bb_upper'] - latest['close']) / latest['close']
                if abs(upper_distance) < self.config['bbands']['upper_touch_percentage']:
                    sell_strength += 0.5
                    signals.append({"type": "sell", "reason": "Price near upper Bollinger Band"})
            
            # Stochastic signals
            if 'stoch_k' in latest and 'stoch_d' in latest:
                # Oversold zone
                if latest['stoch_k'] < self.config['stochastic']['oversold'] and latest['stoch_d'] < self.config['stochastic']['oversold']:
                    buy_strength += 0.5
                    signals.append({"type": "buy", "reason": "Stochastic in oversold territory"})
                # Overbought zone
                elif latest['stoch_k'] > self.config['stochastic']['overbought'] and latest['stoch_d'] > self.config['stochastic']['overbought']:
                    sell_strength += 0.5
                    signals.append({"type": "sell", "reason": "Stochastic in overbought territory"})
            
            # Add pattern signals if provided
            if patterns:
                for pattern, direction in patterns.items():
                    if direction > 0:  # Bullish pattern
                        buy_strength += 1
                        signals.append({"type": "buy", "reason": f"Bullish pattern detected: {pattern}"})
                    elif direction < 0:  # Bearish pattern
                        sell_strength += 1
                        signals.append({"type": "sell", "reason": f"Bearish pattern detected: {pattern}"})
            
            # Support/Resistance signals
            if support_resistance and 'close' in latest:
                current_price = latest['close']
                
                # Check proximity to support levels
                for level in support_resistance.get('support', []):
                    if 0 < (current_price - level) / current_price < 0.01:  # Within 1% above support
                        buy_strength += 0.5
                        signals.append({"type": "buy", "reason": f"Price near support level: {level:.2f}"})
                
                # Check proximity to resistance levels
                for level in support_resistance.get('resistance', []):
                    if 0 < (level - current_price) / current_price < 0.01:  # Within 1% below resistance
                        sell_strength += 0.5
                        signals.append({"type": "sell", "reason": f"Price near resistance level: {level:.2f}"})
            
            return {
                'buy': buy_strength,
                'sell': sell_strength,
                'signals': signals
            }
            
        except Exception as e:
            logger.error(f"Error generating signals: {e}")
            return {'buy': 0, 'sell': 0, 'signals': []}
    
    def get_signal_summary(self, signal_data):
        """
        Generate a summary of the signal data
        
        Args:
            signal_data (dict): Output from generate_signals
            
        Returns:
            dict: Signal summary with recommendation
        """
        try:
            buy_strength = signal_data.get('buy', 0)
            sell_strength = signal_data.get('sell', 0)
            signals = signal_data.get('signals', [])
            
            # Determine the recommendation
            if buy_strength > sell_strength and buy_strength >= 2:
                recommendation = "Strong Buy"
                color = "green"
            elif buy_strength > sell_strength:
                recommendation = "Buy"
                color = "lightgreen"
            elif sell_strength > buy_strength and sell_strength >= 2:
                recommendation = "Strong Sell"
                color = "red"
            elif sell_strength > buy_strength:
                recommendation = "Sell"
                color = "pink"
            else:
                recommendation = "Neutral"
                color = "gray"
            
            return {
                'recommendation': recommendation,
                'color': color,
                'buy_strength': buy_strength,
                'sell_strength': sell_strength,
                'signals': signals
            }
            
        except Exception as e:
            logger.error(f"Error generating signal summary: {e}")
            return {
                'recommendation': "Error",
                'color': "gray",
                'buy_strength': 0,
                'sell_strength': 0,
                'signals': []
            }
