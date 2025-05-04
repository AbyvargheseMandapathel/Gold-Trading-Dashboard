import yfinance as yf
import pandas as pd

def fetch_gold_data_alpha_vantage(period="1d", interval="15min"):
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
        print(f"Error fetching data: {e}")
        return pd.DataFrame()