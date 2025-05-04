import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta

def fetch_gold_data(period="1mo", interval="1h"):
    """
    Fetch XAU/USD data from Yahoo Finance
    
    Parameters:
    period (str): Time period to fetch (1d, 5d, 1mo, 3mo, 6mo, 1y, 2y, 5y, 10y, ytd, max)
    interval (str): Data interval (1m, 2m, 5m, 15m, 30m, 60m, 90m, 1h, 1d, 5d, 1wk, 1mo, 3mo)
    
    Returns:
    pandas.DataFrame: OHLCV data for XAU/USD
    """
    try:
        # GC=F is the ticker for Gold Futures on Yahoo Finance
        data = yf.download("GC=F", period=period, interval=interval)
        
        # Clean the data
        data = data.dropna()
        
        # Add the index as a 'Datetime' column
        data['Datetime'] = data.index
        
        
        print(f"Successfully fetched {len(data)} rows of XAU/USD data")
        return data
    except Exception as e:
        print(f"Error fetching data: {e}")
        return pd.DataFrame()

if __name__ == "__main__":
    # Test the function
    data = fetch_gold_data()
    print(data.head())