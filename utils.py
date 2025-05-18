import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import logging
from datetime import datetime, timedelta

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def format_price(price):
    """Format price value with appropriate decimal places"""
    try:
        return f"${price:.2f}"
    except:
        return "N/A"

def calculate_change(current, previous):
    """Calculate percentage change between two values"""
    try:
        change = (current - previous) / previous * 100
        return change
    except:
        return 0

def create_candlestick_chart(df, indicators=None, patterns=None, support_resistance=None):
    """
    Create an interactive candlestick chart with indicators
    
    Args:
        df (pd.DataFrame): Price data
        indicators (list): List of indicators to include
        patterns (dict): Chart patterns to highlight
        support_resistance (dict): Support and resistance levels
        
    Returns:
        plotly.graph_objects.Figure: Interactive chart figure
    """
    if df.empty:
        # Return empty figure with message
        fig = go.Figure()
        fig.add_annotation(
            text="No data available",
            xref="paper", yref="paper",
            x=0.5, y=0.5,
            showarrow=False
        )
        return fig
    
    # Create subplots: 1 for candlestick chart, 1 for indicators
    fig = make_subplots(
        rows=2, 
        cols=1, 
        shared_xaxes=True,
        vertical_spacing=0.05,
        subplot_titles=('XAU/USD Price', 'Indicators'),
        row_heights=[0.7, 0.3]
    )
    
    # Add candlestick chart
    fig.add_trace(
        go.Candlestick(
            x=df.index,
            open=df['open'],
            high=df['high'],
            low=df['low'],
            close=df['close'],
            name='XAU/USD'
        ),
        row=1, col=1
    )
    
    # Add moving averages if available
    if indicators:
        for indicator in indicators:
            if indicator.startswith('sma_') and indicator in df.columns:
                period = indicator.split('_')[1]
                fig.add_trace(
                    go.Scatter(
                        x=df.index,
                        y=df[indicator],
                        name=f'SMA {period}',
                        line=dict(width=1)
                    ),
                    row=1, col=1
                )
            elif indicator.startswith('ema_') and indicator in df.columns:
                period = indicator.split('_')[1]
                fig.add_trace(
                    go.Scatter(
                        x=df.index,
                        y=df[indicator],
                        name=f'EMA {period}',
                        line=dict(width=1)
                    ),
                    row=1, col=1
                )
    
    # Add Bollinger Bands if available
    if 'bb_upper' in df.columns and 'bb_middle' in df.columns and 'bb_lower' in df.columns:
        fig.add_trace(
            go.Scatter(
                x=df.index,
                y=df['bb_upper'],
                name='Upper BB',
                line=dict(width=1, dash='dot'),
                line_color='rgba(250, 0, 0, 0.5)'
            ),
            row=1, col=1
        )
        
        fig.add_trace(
            go.Scatter(
                x=df.index,
                y=df['bb_middle'],
                name='Middle BB',
                line=dict(width=1, dash='dot'),
                line_color='rgba(0, 0, 250, 0.5)'
            ),
            row=1, col=1
        )
        
        fig.add_trace(
            go.Scatter(
                x=df.index,
                y=df['bb_lower'],
                name='Lower BB',
                line=dict(width=1, dash='dot'),
                line_color='rgba(250, 0, 0, 0.5)',
                fill='tonexty',
                fillcolor='rgba(0, 250, 0, 0.05)'
            ),
            row=1, col=1
        )
    
    # Add RSI if available
    if 'rsi' in df.columns:
        fig.add_trace(
            go.Scatter(
                x=df.index,
                y=df['rsi'],
                name='RSI',
                line=dict(color='purple', width=1)
            ),
            row=2, col=1
        )
        
        # Add RSI overbought/oversold lines
        fig.add_shape(
            type="line",
            x0=df.index[0],
            y0=70,
            x1=df.index[-1],
            y1=70,
            line=dict(color="red", width=1, dash="dash"),
            row=2, col=1
        )
        
        fig.add_shape(
            type="line",
            x0=df.index[0],
            y0=30,
            x1=df.index[-1],
            y1=30,
            line=dict(color="green", width=1, dash="dash"),
            row=2, col=1
        )
    
    # Add support and resistance levels if available
    if support_resistance:
        # Add support levels
        for level in support_resistance.get('support', []):
            fig.add_shape(
                type="line",
                x0=df.index[0],
                y0=level,
                x1=df.index[-1],
                y1=level,
                line=dict(color="green", width=1, dash="dash"),
                row=1, col=1
            )
        
        # Add resistance levels
        for level in support_resistance.get('resistance', []):
            fig.add_shape(
                type="line",
                x0=df.index[0],
                y0=level,
                x1=df.index[-1],
                y1=level,
                line=dict(color="red", width=1, dash="dash"),
                row=1, col=1
            )
    
    # Highlight patterns if available
    if patterns:
        # Get the last few candles where the pattern was detected
        pattern_dates = df.index[-5:]  # Assuming the pattern is in the last 5 candles
        
        for pattern, direction in patterns.items():
            color = "rgba(0, 255, 0, 0.2)" if direction > 0 else "rgba(255, 0, 0, 0.2)"
            
            fig.add_shape(
                type="rect",
                x0=pattern_dates[0],
                y0=df['low'].iloc[-5:].min() * 0.999,
                x1=pattern_dates[-1],
                y1=df['high'].iloc[-5:].max() * 1.001,
                line=dict(width=0),
                fillcolor=color,
                row=1, col=1
            )
            
            # Add annotation for the pattern
            fig.add_annotation(
                x=pattern_dates[-1],
                y=df['high'].iloc[-5:].max() * 1.002,
                text=pattern,
                showarrow=False,
                row=1, col=1
            )
    
    # Update layout
    fig.update_layout(
        title='XAU/USD Price Chart',
        xaxis_title='Date',
        yaxis_title='Price (USD)',
        height=800,
        xaxis_rangeslider_visible=False,
        hovermode='x unified',
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1
        )
    )
    
    # Set y-axis for RSI
    if 'rsi' in df.columns:
        fig.update_yaxes(range=[0, 100], row=2, col=1, title_text='RSI')
    
    return fig

def create_period_options():
    """Create time period options for the dashboard"""
    now = datetime.now()
    
    return [
        {"label": "1 Day", "value": (now - timedelta(days=1)).strftime('%Y-%m-%d')},
        {"label": "1 Week", "value": (now - timedelta(weeks=1)).strftime('%Y-%m-%d')},
        {"label": "1 Month", "value": (now - timedelta(days=30)).strftime('%Y-%m-%d')},
        {"label": "3 Months", "value": (now - timedelta(days=90)).strftime('%Y-%m-%d')},
        {"label": "6 Months", "value": (now - timedelta(days=180)).strftime('%Y-%m-%d')},
        {"label": "1 Year", "value": (now - timedelta(days=365)).strftime('%Y-%m-%d')}
    ]

def create_interval_options():
    """Create interval options for the dashboard"""
    return [
        {"label": "1 Minute", "value": "1min"},
        {"label": "5 Minutes", "value": "5min"},
        {"label": "15 Minutes", "value": "15min"},
        {"label": "30 Minutes", "value": "30min"},
        {"label": "1 Hour", "value": "1hour"},
        {"label": "4 Hours", "value": "4hour"},
        {"label": "1 Day", "value": "daily"}
    ]
