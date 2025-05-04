import streamlit as st
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import time
# Import our modules
from data_fetcher import fetch_gold_data_alpha_vantage as fetch_gold_data
from technical_analysis import add_indicators, identify_support_resistance, identify_patterns, generate_signals
from telegram_bot import TelegramNotifier

st.set_page_config(
    page_title="Gold Trading Dashboard",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Sidebar for settings
st.sidebar.title("Settings")
# Data settings
st.sidebar.subheader("Data Settings")
period = st.sidebar.selectbox(
    "Time Period",
    options=["1d", "5d", "1mo", "3mo", "6mo", "1y"],
    index=2
)
interval = st.sidebar.selectbox(
    "Interval",
    options=["1m", "5m", "15m", "30m", "1h", "1d"],
    index=4
)
# Technical indicators settings
st.sidebar.subheader("Technical Indicators")
show_sma = st.sidebar.checkbox("Show SMA", value=True)
show_ema = st.sidebar.checkbox("Show EMA", value=True)
show_bollinger = st.sidebar.checkbox("Show Bollinger Bands", value=True)
show_support_resistance = st.sidebar.checkbox("Show Support/Resistance", value=True)
show_patterns = st.sidebar.checkbox("Show Patterns", value=True)
# Telegram settings
st.sidebar.subheader("Telegram Notifications")
enable_telegram = st.sidebar.checkbox("Enable Telegram Alerts", value=False)
if enable_telegram:
    telegram_token = st.sidebar.text_input("Telegram Bot Token", type="password")
    telegram_chat_id = st.sidebar.text_input("Telegram Chat ID")
    if telegram_token and telegram_chat_id:
        notifier = TelegramNotifier(token=telegram_token, chat_id=telegram_chat_id)
    else:
        st.sidebar.warning("Please enter both Telegram Bot Token and Chat ID to enable notifications")
        enable_telegram = False

# Main dashboard
st.title("Gold Trading Dashboard")

def create_dashboard():
    # Fetch data
    with st.spinner("Fetching latest gold data..."):
        df = fetch_gold_data(period=period, interval=interval)
    if df.empty:
        st.error("Failed to fetch data. Please check your internet connection and try again.")
        return
    
    # Add technical indicators
    with st.spinner("Calculating technical indicators..."):
        df = add_indicators(df)
        df = generate_signals(df)
    
    # Identify support and resistance levels
    if show_support_resistance:
        support_levels, resistance_levels = identify_support_resistance(df)
    
    # Identify patterns
    if show_patterns:
        patterns = identify_patterns(df)
    
    # Create main chart
    fig = make_subplots(
        rows=3,
        cols=1,
        shared_xaxes=True,
        vertical_spacing=0.05,
        row_heights=[0.6, 0.2, 0.2],
        subplot_titles=("XAU/USD Price", "Volume", "RSI")
    )
    
    # Add candlestick chart
    fig.add_trace(
        go.Candlestick(
            x=df['Datetime'],
            open=df['Open'],
            high=df['High'],
            low=df['Low'],
            close=df['Close'],
            name="XAU/USD"
        ),
        row=1, col=1
    )
    
    # Add moving averages
    if show_sma:
        fig.add_trace(
            go.Scatter(
                x=df['Datetime'],
                y=df['SMA_20'],
                name="SMA 20",
                line=dict(color='blue', width=1),
                visible='legendonly'  # Initially hidden in legend
            ),
            row=1, col=1
        )
        fig.add_trace(
            go.Scatter(
                x=df['Datetime'],
                y=df['SMA_50'],
                name="SMA 50",
                line=dict(color='orange', width=1),
                visible='legendonly'
            ),
            row=1, col=1
        )
        fig.add_trace(
            go.Scatter(
                x=df['Datetime'],
                y=df['SMA_200'],
                name="SMA 200",
                line=dict(color='purple', width=1),
                visible='legendonly'
            ),
            row=1, col=1
        )
    
    if show_ema:
        fig.add_trace(
            go.Scatter(
                x=df['Datetime'],
                y=df['EMA_20'],
                name="EMA 20",
                line=dict(color='green', width=1),
                visible='legendonly'
            ),
            row=1, col=1
        )
    
    # Add Bollinger Bands
    if show_bollinger:
        fig.add_trace(
            go.Scatter(
                x=df['Datetime'],
                y=df['BB_Upper'],
                name="BB Upper",
                line=dict(color='rgba(250, 0, 0, 0.5)', width=1),
                visible='legendonly'
            ),
            row=1, col=1
        )
        fig.add_trace(
            go.Scatter(
                x=df['Datetime'],
                y=df['BB_Middle'],
                name="BB Middle",
                line=dict(color='rgba(0, 0, 250, 0.5)', width=1),
                visible='legendonly'
            ),
            row=1, col=1
        )
        fig.add_trace(
            go.Scatter(
                x=df['Datetime'],
                y=df['BB_Lower'],
                name="BB Lower",
                line=dict(color='rgba(0, 250, 0, 0.5)', width=1),
                visible='legendonly'
            ),
            row=1, col=1
        )
    
    # Add volume chart
    fig.add_trace(
        go.Bar(
            x=df['Datetime'],
            y=df['Volume'],
            name="Volume",
            marker_color='rgba(0, 0, 250, 0.5)',
            visible='legendonly'
        ),
        row=2, col=1
    )
    
    # Add RSI
    fig.add_trace(
        go.Scatter(
            x=df['Datetime'],
            y=df['RSI'],
            name="RSI",
            line=dict(color='purple', width=1),
            visible='legendonly'
        ),
        row=3, col=1
    )
    
    # Add RSI overbought/oversold lines
    fig.add_shape(
        type="line",
        x0=df['Datetime'].iloc[0],
        y0=70,
        x1=df['Datetime'].iloc[-1],
        y1=70,
        line=dict(color="red", width=1, dash="dash"),
        row=3, col=1
    )
    fig.add_shape(
        type="line",
        x0=df['Datetime'].iloc[0],
        y0=30,
        x1=df['Datetime'].iloc[-1],
        y1=30,
        line=dict(color="green", width=1, dash="dash"),
        row=3, col=1
    )
    
    # Add support and resistance levels
    if show_support_resistance:
        for level in support_levels:
            fig.add_shape(
                type="line",
                x0=df['Datetime'].iloc[0],
                y0=level,
                x1=df['Datetime'].iloc[-1],
                y1=level,
                line=dict(color="green", width=1, dash="dash"),
                row=1, col=1
            )
        for level in resistance_levels:
            fig.add_shape(
                type="line",
                x0=df['Datetime'].iloc[0],
                y0=level,
                x1=df['Datetime'].iloc[-1],
                y1=level,
                line=dict(color="red", width=1, dash="dash"),
                row=1, col=1
            )
    
    # Add patterns
    if show_patterns and patterns:
        for pattern_name, indices in patterns.items():
            for idx in indices:
                fig.add_annotation(
                    x=df.loc[idx, 'Datetime'],
                    y=df.loc[idx, 'High'] + 5,  # Offset above the candle
                    text=pattern_name,
                    showarrow=True,
                    arrowhead=1,
                    row=1, col=1
                )
    
    # Update layout
    fig.update_layout(
        height=800,
        title_text="XAU/USD Trading Chart",
        xaxis_rangeslider_visible=False,
        template="plotly_dark",
        updatemenus=[
            dict(
                buttons=list([
                    dict(
                        label="All Indicators",
                        method="update",
                        args=[{"visible": [True] * len(fig.data)}]
                    ),
                    dict(
                        label="Candles Only",
                        method="update",
                        args=[{"visible": [True] + [False] * (len(fig.data) - 1)}]
                    ),
                    dict(
                        label="SMA & EMA",
                        method="update",
                        args=[{"visible": [True] + [trace.name.startswith(("SMA", "EMA")) for trace in fig.data[1:]]}]
                    ),
                    dict(
                        label="Bollinger Bands",
                        method="update",
                        args=[{"visible": [True] + [trace.name.startswith("BB") for trace in fig.data[1:]]}]
                    ),
                    dict(
                        label="Volume",
                        method="update",
                        args=[{"visible": [True] + [trace.name == "Volume" for trace in fig.data[1:]]}]
                    ),
                    dict(
                        label="RSI",
                        method="update",
                        args=[{"visible": [True] + [trace.name == "RSI" for trace in fig.data[1:]]}]
                    )
                ]),
                direction="down",
                pad={"r": 10, "t": 10},
                showactive=True,
                x=0.1,
                xanchor="left",
                y=1.1,
                yanchor="top"
            )
        ]
    )
    
    # Display the chart
    st.plotly_chart(fig, use_container_width=True)
    
    # Display current signals
    st.subheader("Current Trading Signals")
    # Get the latest signal
    latest_signal = df.iloc[-1]
    # Check if latest_signal has a 'Signal' key, if not, create it based on other signals
    if 'Signal' not in latest_signal:
        # Determine signal based on other columns that do exist
        if 'signal_combined' in latest_signal:
            if latest_signal['signal_combined'] > 0:
                latest_signal['Signal'] = 'BUY'
            elif latest_signal['signal_combined'] < 0:
                latest_signal['Signal'] = 'SELL'
            else:
                latest_signal['Signal'] = 'HOLD'
        else:
            # Default if we can't determine
            latest_signal['Signal'] = 'HOLD'
    signal_color = "green" if latest_signal['Signal'] == "BUY" else "red" if latest_signal['Signal'] == "SELL" else "gray"
    st.markdown(f"<h1 style='text-align: center; color: {signal_color};'>{latest_signal['Signal']}</h1>", unsafe_allow_html=True)
    st.markdown(f"<h3 style='text-align: center;'>Signal Strength: {latest_signal['Signal_Strength']:.2f}</h3>", unsafe_allow_html=True)
    
    # Display recent signals history
    st.subheader("Recent Signals History")
    signals_df = df[['Datetime', 'Close', 'Signal', 'Signal_Strength', 'RSI', 'MACD']].tail(10)
    signals_df = signals_df.rename(columns={'Datetime': 'Time', 'Close': 'Price'})
    st.dataframe(signals_df)
    
    # Auto-refresh
    st.write(f"Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

# Run the dashboard
if __name__ == "__main__":
    create_dashboard()
    # Auto-refresh every 60 seconds
    refresh_rate = 60  # seconds
    time.sleep(refresh_rate)
    st.experimental_rerun()