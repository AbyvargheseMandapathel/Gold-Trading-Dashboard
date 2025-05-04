import streamlit as st
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import time
# Import modules
from data_fetcher import fetch_gold_data_alpha_vantage as fetch_gold_data
from technical_analysis import add_indicators, generate_signals, identify_support_resistance, identify_patterns
from telegram_bot import TelegramNotifier
import talib

st.set_page_config(page_title="Gold Trading Dashboard", layout="wide")
st.title("📈 Live XAU/USD Trading Dashboard")

# Sidebar for settings
st.sidebar.header("Settings")

# Data settings
st.sidebar.subheader("Data Settings")
period = st.sidebar.selectbox(
    "Time Period",
    ["1d", "2d","5d","7d","1mo", "3mo", "6mo", "1y"],
    index=1
)

interval = st.sidebar.selectbox(
    "Interval",
    ["1m", "5m", "15m", "30m", "1h", "1d"],
    index=2
)

# Technical indicators settings
st.sidebar.subheader("Technical Indicators")
show_sma = st.sidebar.checkbox("Show SMA", value=True)
show_ema = st.sidebar.checkbox("Show EMA", value=True)
show_bollinger = st.sidebar.checkbox("Show Bollinger Bands", value=True)
show_support_resistance = st.sidebar.checkbox("Show Support/Resistance", value=True)
show_patterns = st.sidebar.checkbox("Show Patterns", value=True)

# Telegram Alerts
enable_telegram = st.sidebar.checkbox("Enable Telegram Alerts", value=False)
if enable_telegram:
    telegram_token = st.sidebar.text_input("Telegram Bot Token", type="password")
    chat_id = st.sidebar.text_input("Telegram Chat ID")
    if telegram_token and chat_id:
        notifier = TelegramNotifier(telegram_token, chat_id)
    else:
        st.sidebar.warning("Enter both Telegram Bot Token and Chat ID to enable alerts")
else:
    notifier = None

def create_dashboard():
    # Weekend check
    today = datetime.today().weekday()
    if today >= 5:  # Saturday/Sunday
        st.warning("⚠️ Market is closed (Weekend). No live data available.")
        df = fetch_gold_data(period="5d", interval="1h")  # Fallback
    else:
        with st.spinner("Fetching latest gold data..."):
            df = fetch_gold_data(period=period, interval=interval)

    if df.empty:
        st.error("Failed to fetch data. Check internet connection.")
        return

    df = add_indicators(df)
    df = generate_signals(df)

    # Identify support/resistance and patterns
    support_levels, resistance_levels = identify_support_resistance(df)
    patterns = identify_patterns(df)

    # Create main chart
    fig = make_subplots(
        rows=3,
        cols=1,
        shared_xaxes=True,
        vertical_spacing=0.05,
        subplot_titles=("XAU/USD Price", "Volume", "RSI"),
        row_heights=[0.6, 0.2, 0.2]
    )

    # Add candlestick chart
    fig.add_trace(
        go.Candlestick(
            x=df['datetime'],
            open=df['open'],
            high=df['high'],
            low=df['low'],
            close=df['close'],
            name="XAU/USD"
        ),
        row=1, col=1
    )

    # Add moving averages
    if show_sma:
        if 'sma_20' in df.columns:
            fig.add_trace(
                go.Scatter(x=df['datetime'], y=df['sma_20'], name="SMA 20"),
                row=1, col=1
            )
        if 'sma_50' in df.columns:
            fig.add_trace(
                go.Scatter(x=df['datetime'], y=df['sma_50'], name="SMA 50"),
                row=1, col=1
            )

    if show_ema:
        if 'ema_20' in df.columns:
            fig.add_trace(
                go.Scatter(x=df['datetime'], y=df['ema_20'], name="EMA 20"),
                row=1, col=1
            )

    # Bollinger Bands
    if show_bollinger:
        if 'bb_upper' in df.columns and 'bb_lower' in df.columns:
            fig.add_trace(
                go.Scatter(x=df['datetime'], y=df['bb_upper'], name="BB Upper"),
                row=1, col=1
            )
            fig.add_trace(
                go.Scatter(x=df['datetime'], y=df['bb_lower'], name="BB Lower"),
                row=1, col=1
            )

    # Volume
    fig.add_trace(
        go.Bar(x=df['datetime'], y=df['volume'], name="Volume"),
        row=2, col=1
    )

    # RSI
    if 'rsi' in df.columns:
        fig.add_trace(
            go.Scatter(x=df['datetime'], y=df['rsi'], name="RSI"),
            row=3, col=1
        )
        fig.add_hline(y=70, row=3, col=1, line_dash="dash", line_color="red")
        fig.add_hline(y=30, row=3, col=1, line_dash="dash", line_color="green")

    # Support & Resistance
    for level in support_levels:
        fig.add_shape(
            type="line",
            x0=df['datetime'].iloc[0],
            y0=level,
            x1=df['datetime'].iloc[-1],
            y1=level,
            line=dict(color="green", dash="dash"),
            row=1, col=1
        )
    for level in resistance_levels:
        fig.add_shape(
            type="line",
            x0=df['datetime'].iloc[0],
            y0=level,
            x1=df['datetime'].iloc[-1],
            y1=level,
            line=dict(color="red", dash="dash"),
            row=1, col=1
        )

    # Candlestick Patterns
    for pattern_name, indices in patterns.items():
        for idx in indices:
            fig.add_annotation(
                x=df.loc[idx, 'datetime'],
                y=df.loc[idx, 'high'] + 5,
                text=pattern_name,
                showarrow=True,
                arrowhead=1,
                row=1, col=1
            )

    # Layout
    fig.update_layout(height=800, template="plotly_dark")
    st.plotly_chart(fig, use_container_width=True)

    # Display Latest Signal
    latest_signal = df.iloc[-1]
    st.subheader("Current Signal")
    signal_color = "green" if latest_signal['signal'] == 'BUY' else "red" if latest_signal['signal'] == 'SELL' else "gray"
    st.markdown(f"<h2 style='color:{signal_color}'>{latest_signal['signal']}</h2>", unsafe_allow_html=True)

    # Send Telegram Alert on Signal Change
    if enable_telegram and notifier:
        if 'signal' in df.columns and len(df) > 1:
            prev_signal = df.iloc[-2]['signal']
            curr_signal = latest_signal['signal']

            if prev_signal != curr_signal:
                indicators = {
                    'RSI': latest_signal.get('rsi', 0),
                    'MACD': latest_signal.get('macd', 0),
                    'Signal Line': latest_signal.get('macd_signal', 0),
                    'SMA_20': latest_signal.get('sma_20', 0),
                    'SMA_50': latest_signal.get('sma_50', 0),
                    'Signal_Strength': latest_signal.get('signal_strength', 0)
                }
                notifier.send_signal(curr_signal, latest_signal['close'], indicators)

    # Technical Summary
    col1, col2, col3 = st.columns(3)
    col1.metric("Price", f"${latest_signal['close']:.2f}")
    if 'rsi' in df.columns:
        col2.metric("RSI", f"{latest_signal['rsi']:.1f}")
    if 'sma_20' in df.columns:
        col3.metric("20 SMA", f"${latest_signal['sma_20']:.2f}")

    # Pattern Detection
    detected_patterns = list(patterns.keys())
    if detected_patterns:
        st.info(f"Detected Patterns: {', '.join(detected_patterns)}")

    # Signal History
    st.subheader("Recent Signals")
    signals_df = df[['datetime', 'close', 'signal', 'signal_strength', 'rsi', 'macd']].tail(10)
    signals_df = signals_df.rename(columns={'datetime': 'Time', 'close': 'Price'})
    st.dataframe(signals_df)

    # Auto-refresh
    st.write(f"Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    time.sleep(60)
    st.rerun()

if __name__ == "__main__":
    create_dashboard()