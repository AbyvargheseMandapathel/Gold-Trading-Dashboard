import yfinance as yf
import pandas as pd

def fetch_gold_data_alpha_vantage(period="7d", interval="1h"):
    """
    Fetch live gold price data from Yahoo Finance.
    """
    try:
        ticker = "GC=F"
        data = yf.download(ticker, period=period, interval=interval, auto_adjust=False)
        
        if data.empty:
            print("No data retrieved from Yahoo Finance.")
            return pd.DataFrame()

        # Reset index and rename columns to lowercase
        data.reset_index(inplace=True)
        data.columns = [col.lower() for col in data.columns]
        data.rename(columns={'date': 'datetime'}, inplace=True)

        # Return required columns
        return data[['datetime', 'open', 'high', 'low', 'close', 'volume']]
    
    except Exception as e:
        print(f"Error fetching data: {e}")
        return pd.DataFrame()