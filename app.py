import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import time
from datetime import datetime, timedelta
import threading
import os

# Import custom modules
from data_fetcher import TradingViewDataFetcher
from technical_indicators import TechnicalIndicators
from pattern_detection import PatternDetection
from signal_generator import SignalGenerator
from telegram_bot import TelegramAlerts
import utils

# Configure page settings
st.set_page_config(
    page_title="XAU/USD Trading Dashboard",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize session state
if 'data' not in st.session_state:
    st.session_state.data = pd.DataFrame()
if 'last_update' not in st.session_state:
    st.session_state.last_update = None
if 'alert_sent' not in st.session_state:
    st.session_state.alert_sent = False
if 'signals' not in st.session_state:
    st.session_state.signals = None
if 'support_resistance' not in st.session_state:
    st.session_state.support_resistance = None

# Initialize the data fetcher
@st.cache_resource
def get_data_fetcher():
    return TradingViewDataFetcher()

# Initialize the telegram alerts
@st.cache_resource
def get_telegram_bot():
    return TelegramAlerts()

def fetch_live_data():
    """Fetch live gold price data"""
    data_fetcher = get_data_fetcher()
    live_data = data_fetcher.get_live_data()
    
    # Use simulated data if API fails
    if not live_data:
        live_data = data_fetcher.simulate_data()
    
    return live_data

def fetch_historical_data(start_date, end_date, interval):
    """Fetch historical gold price data"""
    data_fetcher = get_data_fetcher()
    df = data_fetcher.get_historical_data(
        start_date=start_date,
        end_date=end_date,
        interval=interval
    )
    
    return df

def analyze_data(data):
    """Perform technical analysis on data"""
    # Get indicator configuration from session state
    config = {
        'sma_periods': [
            st.session_state.get('sma_fast', 20),
            st.session_state.get('sma_slow', 50),
            200  # Always include 200 SMA
        ],
        'ema_periods': [
            st.session_state.get('ema_fast', 9),
            st.session_state.get('ema_slow', 21)
        ],
        'rsi_period': st.session_state.get('rsi_period', 14),
        'macd_fast': st.session_state.get('macd_fast', 12),
        'macd_slow': st.session_state.get('macd_slow', 26),
        'macd_signal': st.session_state.get('macd_signal', 9),
        'bbands_period': st.session_state.get('bbands_period', 20),
        'bbands_dev': st.session_state.get('bbands_dev', 2)
    }
    
    # Calculate technical indicators
    df_with_indicators = TechnicalIndicators.add_indicators(data, config)
    
    # Identify support and resistance levels
    support_resistance = TechnicalIndicators.identify_support_resistance(
        df_with_indicators, 
        window=st.session_state.get('sr_window', 10),
        threshold=st.session_state.get('sr_threshold', 0.02)
    )
    
    # Detect chart patterns
    candlestick_patterns = PatternDetection.detect_candlestick_patterns(df_with_indicators)
    chart_patterns = PatternDetection.detect_chart_patterns(
        df_with_indicators, 
        lookback=st.session_state.get('pattern_lookback', 20)
    )
    
    # Combine all patterns
    all_patterns = {**candlestick_patterns, **chart_patterns}
    
    # Generate trading signals
    signal_config = {
        'rsi': {
            'oversold': st.session_state.get('rsi_oversold', 30),
            'overbought': st.session_state.get('rsi_overbought', 70)
        },
        'sma': {
            'fast': st.session_state.get('sma_fast', 20),
            'slow': st.session_state.get('sma_slow', 50)
        },
        'macd': {
            'signal_trigger': 0
        },
        'stochastic': {
            'oversold': st.session_state.get('stoch_oversold', 20),
            'overbought': st.session_state.get('stoch_overbought', 80)
        },
        'bbands': {
            'lower_touch_percentage': 0.01,
            'upper_touch_percentage': 0.01
        }
    }
    
    signal_generator = SignalGenerator(signal_config)
    signals = signal_generator.generate_signals(
        df_with_indicators, 
        all_patterns, 
        support_resistance
    )
    
    signal_summary = signal_generator.get_signal_summary(signals)
    
    # Update session state
    st.session_state.data = df_with_indicators
    st.session_state.last_update = datetime.now()
    st.session_state.support_resistance = support_resistance
    st.session_state.signals = signal_summary
    
    # Send alerts if configured
    if st.session_state.get('enable_alerts', False) and not st.session_state.alert_sent:
        threshold = st.session_state.get('alert_threshold', 2)
        
        if (signal_summary['buy_strength'] >= threshold or signal_summary['sell_strength'] >= threshold):
            # Get current price
            current_price = df_with_indicators['close'].iloc[-1] if not df_with_indicators.empty else None
            
            # Send Telegram alert
            if current_price is not None:
                telegram_bot = get_telegram_bot()
                telegram_bot.send_signal_alert(signal_summary, current_price)
                
                # Set alert sent flag to avoid repeated alerts
                st.session_state.alert_sent = True
    
    return df_with_indicators, signal_summary, support_resistance, all_patterns

# Main dashboard layout
def main():
    st.title("🔱 XAU/USD Trading Dashboard")
    
    # Sidebar for configuration
    with st.sidebar:
        st.header("Dashboard Configuration")
        
        # Time period selector
        st.subheader("Data Settings")
        
        period_options = utils.create_period_options()
        selected_period = st.selectbox(
            "Select Time Period", 
            options=[p["value"] for p in period_options],
            format_func=lambda x: next((p["label"] for p in period_options if p["value"] == x), x),
            index=2  # Default to 1 Month
        )
        
        interval_options = utils.create_interval_options()
        selected_interval = st.selectbox(
            "Select Interval",
            options=[i["value"] for i in interval_options],
            format_func=lambda x: next((i["label"] for i in interval_options if i["value"] == x), x),
            index=4  # Default to 1 Hour
        )
        
        st.subheader("Indicators")
        
        # Moving Average settings
        col1, col2 = st.columns(2)
        with col1:
            st.session_state.sma_fast = st.number_input("SMA Fast", min_value=5, max_value=50, value=20)
            st.session_state.ema_fast = st.number_input("EMA Fast", min_value=3, max_value=30, value=9)
        with col2:
            st.session_state.sma_slow = st.number_input("SMA Slow", min_value=20, max_value=200, value=50)
            st.session_state.ema_slow = st.number_input("EMA Slow", min_value=10, max_value=50, value=21)
        
        # RSI settings
        col1, col2 = st.columns(2)
        with col1:
            st.session_state.rsi_period = st.number_input("RSI Period", min_value=7, max_value=30, value=14)
            st.session_state.rsi_oversold = st.number_input("RSI Oversold", min_value=10, max_value=40, value=30)
        with col2:
            st.session_state.macd_fast = st.number_input("MACD Fast", min_value=8, max_value=20, value=12)
            st.session_state.rsi_overbought = st.number_input("RSI Overbought", min_value=60, max_value=90, value=70)
        
        # MACD settings
        col1, col2 = st.columns(2)
        with col1:
            st.session_state.macd_slow = st.number_input("MACD Slow", min_value=15, max_value=35, value=26)
        with col2:
            st.session_state.macd_signal = st.number_input("MACD Signal", min_value=5, max_value=15, value=9)
        
        # Bollinger Bands settings
        col1, col2 = st.columns(2)
        with col1:
            st.session_state.bbands_period = st.number_input("BB Period", min_value=10, max_value=50, value=20)
        with col2:
            st.session_state.bbands_dev = st.number_input("BB StdDev", min_value=1.0, max_value=3.0, value=2.0, step=0.1)
        
        # Support/Resistance settings
        st.subheader("Support/Resistance")
        col1, col2 = st.columns(2)
        with col1:
            st.session_state.sr_window = st.number_input("S/R Window", min_value=5, max_value=20, value=10)
        with col2:
            st.session_state.sr_threshold = st.number_input("S/R Threshold", min_value=0.01, max_value=0.05, value=0.02, step=0.01)
        
        # Pattern recognition settings
        st.subheader("Pattern Recognition")
        st.session_state.pattern_lookback = st.number_input("Pattern Lookback", min_value=10, max_value=50, value=20)
        
        # Alert settings
        st.subheader("Alerts")
        st.session_state.enable_alerts = st.checkbox("Enable Telegram Alerts", value=False)
        
        if st.session_state.enable_alerts:
            st.session_state.alert_threshold = st.slider(
                "Alert Signal Strength Threshold", 
                min_value=1.0, 
                max_value=5.0, 
                value=2.0,
                step=0.5
            )
        
        # Auto-refresh setting
        st.subheader("Refresh Settings")
        auto_refresh = st.checkbox("Auto Refresh", value=True)
        
        if auto_refresh:
            refresh_interval = st.slider("Refresh Interval (seconds)", min_value=10, max_value=300, value=60)
        else:
            refresh_interval = None
        
        # Manual refresh button
        if st.button("Refresh Data"):
            st.session_state.alert_sent = False  # Reset alert flag
    
    # Main content area
    # Live price ticker
    ticker_container = st.container()
    
    # Charts container
    charts_container = st.container()
    
    # Signal and analysis container
    signal_container = st.container()
    
    # Data fetching and display
    def update_data():
        with st.spinner("Fetching data..."):
            # Get end date (today)
            end_date = datetime.now().strftime('%Y-%m-%d')
            
            # Get historical data
            df = fetch_historical_data(selected_period, end_date, selected_interval)
            
            if not df.empty:
                # Analyze data
                df_analyzed, signals, support_resistance, patterns = analyze_data(df)
                
                # Get live price data for ticker
                live_data = fetch_live_data()
                
                # Update ticker display
                with ticker_container:
                    col1, col2, col3, col4 = st.columns(4)
                    
                    with col1:
                        st.subheader("XAU/USD Live Price")
                        if live_data:
                            price = live_data.get('price', 'N/A')
                            if isinstance(price, (int, float)):
                                st.write(f"<h1 style='margin-bottom:0'>${price:.2f}</h1>", unsafe_allow_html=True)
                            else:
                                st.write(f"<h1 style='margin-bottom:0'>{price}</h1>", unsafe_allow_html=True)
                            
                            # Calculate price change if historical data is available
                            if not df_analyzed.empty:
                                prev_close = df_analyzed['close'].iloc[-2] if len(df_analyzed) > 1 else None
                                if prev_close and isinstance(price, (int, float)):
                                    change = utils.calculate_change(price, prev_close)
                                    change_color = "green" if change >= 0 else "red"
                                    st.write(f"<p style='color:{change_color}; margin-top:0'>{change:.2f}%</p>", unsafe_allow_html=True)
                    
                    with col2:
                        st.subheader("Trading Signal")
                        if signals:
                            rec = signals.get('recommendation', 'Neutral')
                            color = signals.get('color', 'gray')
                            st.write(f"<h1 style='color:{color}; margin-bottom:0'>{rec}</h1>", unsafe_allow_html=True)
                            
                            # Buy/Sell strength
                            buy = signals.get('buy_strength', 0)
                            sell = signals.get('sell_strength', 0)
                            st.write(f"<p style='margin-top:0'>Buy: {buy:.1f} | Sell: {sell:.1f}</p>", unsafe_allow_html=True)
                    
                    with col3:
                        st.subheader("Support Levels")
                        if support_resistance and 'support' in support_resistance:
                            for i, level in enumerate(support_resistance['support'][:3]):  # Show top 3
                                st.write(f"{i+1}. ${level:.2f}")
                        else:
                            st.write("No support levels detected")
                    
                    with col4:
                        st.subheader("Resistance Levels")
                        if support_resistance and 'resistance' in support_resistance:
                            for i, level in enumerate(support_resistance['resistance'][:3]):  # Show top 3
                                st.write(f"{i+1}. ${level:.2f}")
                        else:
                            st.write("No resistance levels detected")
                
                # Update charts
                with charts_container:
                    st.subheader("XAU/USD Chart Analysis")
                    
                    # Select indicators to display
                    indicators = [
                        f"sma_{st.session_state.sma_fast}",
                        f"sma_{st.session_state.sma_slow}",
                        f"ema_{st.session_state.ema_fast}",
                        f"ema_{st.session_state.ema_slow}"
                    ]
                    
                    # Create interactive chart
                    fig = utils.create_candlestick_chart(
                        df_analyzed, 
                        indicators=indicators,
                        patterns=patterns,
                        support_resistance=support_resistance
                    )
                    
                    st.plotly_chart(fig, use_container_width=True)
                
                # Update signal container
                with signal_container:
                    st.subheader("Trading Signals and Patterns")
                    
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.write("### Detected Signals")
                        if signals and 'signals' in signals:
                            for signal in signals['signals']:
                                signal_type = signal.get('type', '').upper()
                                reason = signal.get('reason', '')
                                
                                if signal_type == 'BUY':
                                    st.success(f"**{signal_type}:** {reason}")
                                elif signal_type == 'SELL':
                                    st.error(f"**{signal_type}:** {reason}")
                                else:
                                    st.info(f"**{signal_type}:** {reason}")
                        else:
                            st.write("No signals detected")
                    
                    with col2:
                        st.write("### Detected Patterns")
                        if patterns:
                            for pattern, direction in patterns.items():
                                if direction > 0:
                                    st.success(f"**Bullish Pattern:** {pattern}")
                                elif direction < 0:
                                    st.error(f"**Bearish Pattern:** {pattern}")
                                else:
                                    st.info(f"**Neutral Pattern:** {pattern}")
                        else:
                            st.write("No patterns detected")
                    
                    # Show last update time
                    if st.session_state.last_update:
                        st.caption(f"Last updated: {st.session_state.last_update.strftime('%Y-%m-%d %H:%M:%S')}")
            else:
                st.error("Failed to fetch data. Please check your API key or internet connection.")
    
    # Initial data load
    update_data()
    
    # Auto-refresh functionality
    if auto_refresh and refresh_interval:
        time.sleep(refresh_interval)
        st.session_state.alert_sent = False  # Reset alert flag
        st.rerun()

if __name__ == "__main__":
    main()
