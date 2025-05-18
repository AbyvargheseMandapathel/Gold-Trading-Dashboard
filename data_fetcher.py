import os
import pandas as pd
import requests
from datetime import datetime, timedelta
import time
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class TradingViewDataFetcher:
    def __init__(self):
        self.api_key = os.getenv("TRADERMADE_API_KEY", "demo")
        self.base_url = "https://marketdata.tradermade.com/api/v1"
        
    def get_live_data(self):
        """
        Fetch the latest XAU/USD data from TraderMade API
        """
        try:
            endpoint = f"{self.base_url}/live"
            params = {
                "currency": "XAUUSD",
                "api_key": self.api_key
            }
            
            response = requests.get(endpoint, params=params)
            response.raise_for_status()
            
            data = response.json()
            
            if 'quotes' in data and len(data['quotes']) > 0:
                quote = data['quotes'][0]
                return {
                    'symbol': quote.get('instrument', 'XAUUSD'),
                    'price': quote.get('mid', 0.0),
                    'bid': quote.get('bid', 0.0),
                    'ask': quote.get('ask', 0.0),
                    'timestamp': quote.get('updated', datetime.now().isoformat())
                }
            else:
                logger.warning("No quotes found in the response")
                return None
                
        except requests.exceptions.RequestException as e:
            logger.error(f"Error fetching live data: {e}")
            return None
    
    def get_historical_data(self, start_date=None, end_date=None, interval="hourly"):
        """
        Fetch historical data for XAU/USD from TraderMade API
        
        Args:
            start_date (str): Start date in format 'YYYY-MM-DD'
            end_date (str): End date in format 'YYYY-MM-DD'
            interval (str): Data interval - 'daily', 'hourly', etc.
            
        Returns:
            pandas.DataFrame: Historical data
        """
        
        if not start_date:
            start_date = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')
        if not end_date:
            end_date = datetime.now().strftime('%Y-%m-%d')
            
        try:
            endpoint = f"{self.base_url}/timeseries"
            params = {
                "currency": "XAUUSD",
                "api_key": self.api_key,
                "start_date": start_date,
                "end_date": end_date,
                "format": "records",
                "interval": interval
            }
            
            response = requests.get(endpoint, params=params)
            response.raise_for_status()
            
            data = response.json()
            
            if 'quotes' in data:
                df = pd.DataFrame(data['quotes'])
                
                # Format the dataframe for technical analysis
                if not df.empty:
                    df.rename(columns={
                        'close': 'close',
                        'high': 'high',
                        'low': 'low',
                        'open': 'open',
                        'date': 'timestamp'
                    }, inplace=True)
                    
                    # Ensure we have all required columns
                    for col in ['open', 'high', 'low', 'close']:
                        if col not in df.columns:
                            df[col] = 0.0
                    
                    # Convert timestamp to datetime
                    if 'timestamp' in df.columns:
                        df['timestamp'] = pd.to_datetime(df['timestamp'])
                        df.set_index('timestamp', inplace=True)
                    
                    return df
                
            return pd.DataFrame()
                
        except requests.exceptions.RequestException as e:
            logger.error(f"Error fetching historical data: {e}")
            return pd.DataFrame()
            
    def simulate_data(self):
        """
        In case of demo mode or API limits, simulate XAU/USD data
        Note: This should only be used for testing purposes
        """
        current_price = 1900 + (10 * (0.5 - (datetime.now().microsecond / 1000000)))
        
        return {
            'symbol': 'XAUUSD',
            'price': current_price,
            'bid': current_price - 0.1,
            'ask': current_price + 0.1,
            'timestamp': datetime.now().isoformat()
        }
