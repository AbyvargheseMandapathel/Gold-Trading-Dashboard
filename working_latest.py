import streamlit as st
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
import numpy as np
import yfinance as yf
import time
from datetime import datetime, timedelta
import pandas_ta as ta 

# Ensure lowercase 'nan' is used everywhere
nan = np.nan  # Just to be explicit about NaN usage

st.set_page_config(page_title="XAU/USD Dashboard", layout="wide")
st.title("📈 Live XAU/USD Trading Dashboard")

# Sidebar settings
st.sidebar.header("Settings")
period = st.sidebar.selectbox("Time Period", ["1d", "5d", "1mo", "3mo", "6mo", "1y"], index=2)
interval = st.sidebar.selectbox("Interval", ["1m", "5m", "15m", "30m", "1h", "1d"], index=4)

def fetch_gold_data(period="1d", interval="15m"):
    """Fetch live gold price data from Yahoo Finance with error handling"""
    try:
        ticker = "GC=F"
        data = yf.download(ticker, period=period, interval=interval, auto_adjust=False)
        
        if data.empty:
            print("No data returned from Yahoo Finance")
            return pd.DataFrame()
            
        data.reset_index(inplace=True)
        data['Datetime'] = pd.to_datetime(data['Datetime'])
        return data[['Datetime', 'Open', 'High', 'Low', 'Close', 'Volume']]
        
    except Exception as e:
        print(f"Error fetching data: {str(e)}")
        return pd.DataFrame()

def calculate_indicators(df):
    """Add technical indicators using pandas-ta [[2]]"""
    if len(df) < 20:
        return df
    
    # ✅ Use pandas-ta for efficient indicator calculations
    df.ta.sma(length=20, append=True)  # SMA 20
    df.ta.ema(length=50, append=True)  # EMA 50
    
    # 📈 Bollinger Bands [[2]]
    bbands = df.ta.bbands(length=20, std=2)
    if bbands is not None:
        df = pd.concat([df, bbands], axis=1)
    
    # 🔁 RSI [[2]]
    df.ta.rsi(length=14, append=True)
    
    # 📊 Pivot Points [[4]]
    df = calculate_pivot_points(df)
    
    # 🕯️ Candlestick Patterns [[7]]
    df.ta.cdl_pattern(name="all", append=True)  # Detect all patterns
    
    return df

def calculate_pivot_points(df):
    """Calculate classic pivot points [[4]]"""
    # Get daily pivot points from last complete day
    daily_data = df.resample('D', on='Datetime').agg({
        'Open': 'first',
        'High': 'max',
        'Low': 'min',
        'Close': 'last'
    }).dropna()
    
    if not daily_data.empty:
        last = daily_data.iloc[-1]
        pivot = (last.High + last.Low + last.Close) / 3
        r1 = 2 * pivot - last.Low
        s1 = 2 * pivot - last.High
        r2 = pivot + (last.High - last.Low)
        s2 = pivot - (last.High - last.Low)
        
        # Add as constant columns for visualization
        df['Pivot'] = pivot
        df['R1'] = r1
        df['S1'] = s1
        df['R2'] = r2
        df['S2'] = s2
        
    else:
        # Fallback to nan if no daily data
        df['Pivot'] = np.nan
        df['R1'] = np.nan
        df['S1'] = np.nan
        df['R2'] = np.nan
        df['S2'] = np.nan
        
    return df

def generate_signals(df):
    """Generate trading signals based on technical analysis"""
    df['Signal'] = 'HOLD'
    
    # Only generate signal if RSI_14 column exists
    if 'RSI_14' in df.columns:
        df.loc[df['RSI_14'] < 30, 'Signal'] = 'BUY'
        df.loc[df['RSI_14'] > 70, 'Signal'] = 'SELL'
    
    # Moving Average Crossover
    if 'SMA_20' in df.columns and 'EMA_50' in df.columns:
        df['MA_Signal'] = np.where(df['SMA_20'] > df['EMA_50'], 1, -1)
    else:
        df['MA_Signal'] = np.nan
    
    return df

def create_chart(df):
    """Create interactive price chart with indicators"""
    fig = make_subplots(
        rows=3, cols=1, shared_xaxes=True,
        row_heights=[0.6, 0.2, 0.2],
        subplot_titles=("Price", "Volume", "RSI")
    )
    
    # Candlesticks
    fig.add_trace(go.Candlestick(
        x=df['Datetime'],
        open=df['Open'], high=df['High'], 
        low=df['Low'], close=df['Close'],
        name="Candlesticks"
    ))
    
    # ✅ pandas-ta indicators
    if 'SMA_20' in df.columns:
        fig.add_trace(go.Scatter(
            x=df['Datetime'], y=df['SMA_20'], 
            name="SMA 20", line=dict(color='blue')
        ))
        
    if 'EMA_50' in df.columns:
        fig.add_trace(go.Scatter(
            x=df['Datetime'], y=df['EMA_50'], 
            name="EMA 50", line=dict(color='green')
        ))
    
    # 📈 Bollinger Bands from pandas-ta [[2]]
    if 'BBU_20_2.0' in df.columns:
        fig.add_trace(go.Scatter(
            x=df['Datetime'], y=df['BBU_20_2.0'], 
            name="BB Upper", line=dict(color='red', dash='dot')
        ))
        fig.add_trace(go.Scatter(
            x=df['Datetime'], y=df['BBL_20_2.0'], 
            name="BB Lower", line=dict(color='green', dash='dot')
        ))
    
    # 📊 Pivot Points [[4]]
    for level, color in [('Pivot', 'purple'), ('R1', 'red'), ('S1', 'green'), ('R2', 'darkred'), ('S2', 'darkgreen')]:
        if level in df.columns:
            fig.add_shape(
                type="line",
                x0=df['Datetime'].iloc[0],
                y0=df[level].iloc[-1],
                x1=df['Datetime'].iloc[-1],
                y1=df[level].iloc[-1],
                line=dict(color=color, width=1, dash="dash"),
                row=1, col=1
            )
    
    # 🕯️ Candlestick Patterns [[7]]
    pattern_columns = [col for col in df.columns if col.startswith('CDL')]
    for pattern in pattern_columns:
        if pattern in df.columns and df[pattern].iloc[-1] != 0:  # Pattern detected
            fig.add_annotation(
                x=df['Datetime'].iloc[-1],
                y=df['High'].iloc[-1] + 5,
                text=pattern,
                showarrow=True,
                arrowhead=1
            )
    
    # Volume
    fig.add_trace(go.Bar(
        x=df['Datetime'], y=df['Volume'],
        name="Volume"
    ), row=2, col=1)
    
    # RSI
    if 'RSI_14' in df.columns:
        fig.add_trace(go.Scatter(
            x=df['Datetime'], y=df['RSI_14'],
            name="RSI", line=dict(color='purple')
        ), row=3, col=1)
    
    # RSI Overbought/Oversold
    fig.add_hline(y=70, row=3, col=1, line_dash="dash", line_color="red")
    fig.add_hline(y=30, row=3, col=1, line_dash="dash", line_color="green")
    
    fig.update_layout(height=800, template="plotly_dark")
    return fig

def get_fallback_data():
    """Generate dummy data for testing"""
    dates = [datetime.now() - timedelta(hours=i) for i in range(30)]
    return pd.DataFrame({
        'Datetime': dates,
        'Open': np.random.uniform(2300, 2350, 30),
        'High': np.random.uniform(2300, 2350, 30),
        'Low': np.random.uniform(2300, 2350, 30),
        'Close': np.random.uniform(2300, 2350, 30),
        'Volume': np.random.randint(10000, 100000, 30)
    })

def main():
    # Skip weekends
    if datetime.today().weekday() >= 5:
        st.warning("Market data is not available on weekends.")
        df = get_fallback_data()
    else:
        # Try fetching data up to 3 times
        df = pd.DataFrame()
        for attempt in range(3):
            with st.spinner(f"Loading data... (Attempt {attempt+1}/3)"):
                df = fetch_gold_data(period=period, interval=interval)
                if not df.empty:
                    break
                time.sleep(5)
    
    if df.empty or df['Close'].isnull().all():
        st.warning("Using fallback data (no valid market data found)")
        df = get_fallback_data()
    
    # Calculate indicators
    df = calculate_indicators(df)
    df = generate_signals(df)
    
    # Show Chart
    st.subheader("Live XAU/USD Chart")
    chart = create_chart(df)
    st.plotly_chart(chart, use_container_width=True)
    
    # Current Signal
    latest = df.iloc[-1]
    signal_color = "green" if latest['Signal'] == 'BUY' else "red" if latest['Signal'] == 'SELL' else "gray"
    st.markdown(f"<h2 style='color:{signal_color}'>{latest['Signal']}</h2>", unsafe_allow_html=True)
    
    # Technical Summary
    col1, col2, col3 = st.columns(3)
    col1.metric("Current Price", f"${latest['Close']:.2f}")
    if 'RSI_14' in df.columns:
        col2.metric("RSI (14)", f"{latest['RSI_14']:.1f}")
    if 'SMA_20' in df.columns:
        col3.metric("20 SMA", f"${latest['SMA_20']:.2f}")
    
    # 📊 Pattern Detection Results [[7]]
    pattern_columns = [col for col in df.columns if col.startswith('CDL')]
    patterns_found = []
    for pattern in pattern_columns:
        if pattern in df.columns and df[pattern].iloc[-1] != 0:  # Pattern detected
            patterns_found.append(pattern.replace('CDL_', ''))
    
    if patterns_found:
        st.info(f"Detected Patterns: {', '.join(patterns_found)}")
    
    # 📈 Pivot Levels
    st.subheader("Pivot Points")
    col1, col2, col3 = st.columns(3)
    col4, col5 = st.columns(2)
    
    if 'Pivot' in df.columns:
        col1.metric("Pivot", f"${latest['Pivot']:.2f}")
        col2.metric("Resistance 1", f"${latest['R1']:.2f}")
        col3.metric("Support 1", f"${latest['S1']:.2f}")
        col4.metric("Resistance 2", f"${latest['R2']:.2f}")
        col5.metric("Support 2", f"${latest['S2']:.2f}")

if __name__ == "__main__":
    while True:
        main()
        st.info(f"Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        time.sleep(60)
        st.experimental_rerun()