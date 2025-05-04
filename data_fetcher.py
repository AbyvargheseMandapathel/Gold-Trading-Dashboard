import yfinance as yf
import pandas as pd

import yfinance as yf
import pandas as pd

def fetch_gold_data_alpha_vantage(period="5d", interval="1h"):
    """
    Fetch live gold price data (GC=F) from Yahoo Finance.
    """
    try:
        ticker = "GC=F"  # Gold Futures
        data = yf.download(ticker, period=period, interval=interval, auto_adjust=False)

        if data.empty:
            print("No data retrieved from Yahoo Finance.")
            return pd.DataFrame()

        # Reset index to convert DatetimeIndex to a column
        data.reset_index(inplace=True)

        # Flatten MultiIndex columns (critical fix)
        if isinstance(data.columns, pd.MultiIndex):
            # Join levels but discard empty or ticker-based suffixes
            new_columns = []
            for col in data.columns:
                # Keep only the first level (e.g., 'Close' from ('Close', 'GC=F'))
                if isinstance(col, tuple):
                    valid_levels = [level for level in col if level not in ['', ticker]]
                    new_columns.append(valid_levels[0] if valid_levels else col)
                else:
                    new_columns.append(col)
            data.columns = new_columns

        # Print columns for debugging
        print("Columns after reset:", data.columns.tolist())

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

        print(f"✅ Fetched {len(data)} rows of gold price data")
        return data[required_columns]

    except Exception as e:
        print(f"❌ Error fetching data: {e}")
        return pd.DataFrame()