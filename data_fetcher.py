import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta

def fetch_gold_data_alpha_vantage(period="1mo", interval="1h"):
    """
    Fetch live gold price data (GC=F) from Yahoo Finance using dynamic date ranges.
    """
    try:
        ticker = "GC=F"  # Gold Futures

        print(f"\n📊 Fetching data with period='{period}', interval='{interval}'")

        # Fetch data with period/interval
        data = yf.download(ticker, period=period, interval=interval, auto_adjust=False)

        if data.empty:
            print("❌ No data retrieved from Yahoo Finance.")
            return pd.DataFrame()

        # Reset index to convert DatetimeIndex to a column
        data.reset_index(inplace=True)

        # Flatten MultiIndex columns
        if isinstance(data.columns, pd.MultiIndex):
            new_columns = []
            for col in data.columns:
                if isinstance(col, tuple):
                    valid_levels = [level for level in col if level not in ['', ticker]]
                    new_columns.append(valid_levels[0] if valid_levels else col)
                else:
                    new_columns.append(col)
            data.columns = new_columns

        # Rename datetime column
        if 'Datetime' in data.columns:
            data.rename(columns={'Datetime': 'datetime'}, inplace=True)
        elif 'Date' in data.columns:
            data.rename(columns={'Date': 'datetime'}, inplace=True)
        else:
            raise ValueError("Missing datetime column after resetting index")

        # Lowercase column names
        data.columns = [col.lower() for col in data.columns]

        # Final validation
        required_columns = ['datetime', 'open', 'high', 'low', 'close', 'volume']
        missing_cols = [col for col in required_columns if col not in data.columns]
        if missing_cols:
            raise KeyError(f"Missing columns: {missing_cols}")

        data['datetime'] = pd.to_datetime(data['datetime'])

        print(f"✅ Fetched {len(data)} rows from {data['datetime'].min()} to {data['datetime'].max()}")

        return data[required_columns]

    except Exception as e:
        print(f"❌ Error fetching data: {e}")
        return pd.DataFrame()
