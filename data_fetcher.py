import os
import pandas as pd
import requests
from datetime import datetime, timedelta
import time
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class TradingViewDataFetcher:

    def __init__(self):
        # self.api_key = os.getenv("TRADERMADE_API_KEY", "demo")
        self.api_key = "LGYrbRazgNCCc2RLJ7jD"
        self.base_url = "https://marketdata.tradermade.com/api/v1"

    def get_live_data(self):
        """
        Fetch the latest XAU/USD data from TraderMade API
        """
        try:
            endpoint = f"{self.base_url}/live"
            params = {"currency": "XAUUSD", "api_key": self.api_key}

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
                    'timestamp': quote.get('updated',
                                           datetime.now().isoformat())
                }
            else:
                logger.warning("No quotes found in the response")
                return None

        except requests.exceptions.RequestException as e:
            logger.error(f"Error fetching live data: {e}")
            return None

    def get_historical_data(self,
                            start_date=None,
                            end_date=None,
                            interval="hourly"):
        """
        Fetch historical data for XAU/USD from TraderMade API
        
        Args:
            start_date (str): Start date in format 'YYYY-MM-DD'
            end_date (str): End date in format 'YYYY-MM-DD'
            interval (str): Data interval - 'daily', 'hourly', or 'minute'
            
        Returns:
            pandas.DataFrame: Historical data
        """

        if not start_date:
            start_date = (datetime.now() -
                          timedelta(days=30)).strftime('%Y-%m-%d')
        if not end_date:
            end_date = datetime.now().strftime('%Y-%m-%d')

        # Validate interval parameter
        valid_intervals = ['daily', 'hourly', 'minute']
        if interval not in valid_intervals:
            logger.warning(f"Invalid interval: {interval}. Using 'hourly' instead.")
            interval = 'hourly'

        # Convert string dates to datetime objects for chunking
        start_dt = datetime.strptime(start_date, '%Y-%m-%d')
        end_dt = datetime.strptime(end_date, '%Y-%m-%d')
        
        # For minute data, limit to 5 days per request as per API limitation
        max_days_per_request = 5 if interval == 'minute' else 30
        
        # Initialize an empty DataFrame to store all results
        all_data = pd.DataFrame()
        
        # Process data in chunks to respect API limitations
        current_start = start_dt
        while current_start < end_dt:
            # Calculate end date for this chunk (either max_days_per_request days later or end_dt, whichever is earlier)
            current_end = min(current_start + timedelta(days=max_days_per_request), end_dt)
            
            # Format dates for API request
            chunk_start = current_start.strftime('%Y-%m-%d')
            chunk_end = current_end.strftime('%Y-%m-%d')
            
            try:
                endpoint = f"{self.base_url}/timeseries"
                params = {
                    "currency": "XAUUSD",
                    "api_key": self.api_key,
                    "start_date": chunk_start,
                    "end_date": chunk_end,
                    "format": "records",
                    "interval": interval
                }
                
                # Add period parameter only for minute data
                if interval == 'minute':
                    params["period"] = 30  # 30-minute intervals
                
                logger.info(f"Making API request to {endpoint} with params: {params}")
                response = requests.get(endpoint, params=params)
                
                # Log the full URL for debugging
                logger.info(f"Full URL: {response.url}")
                
                response.raise_for_status()
                
                data = response.json()
                
                if 'quotes' in data:
                    chunk_df = pd.DataFrame(data['quotes'])
                    
                    # Format the dataframe for technical analysis
                    if not chunk_df.empty:
                        chunk_df.rename(columns={
                            'close': 'close',
                            'high': 'high',
                            'low': 'low',
                            'open': 'open',
                            'date': 'timestamp'
                        }, inplace=True)
                        
                        # Ensure we have all required columns
                        for col in ['open', 'high', 'low', 'close']:
                            if col not in chunk_df.columns:
                                chunk_df[col] = 0.0
                        
                        # Convert timestamp to datetime
                        if 'timestamp' in chunk_df.columns:
                            chunk_df['timestamp'] = pd.to_datetime(chunk_df['timestamp'])
                            chunk_df.set_index('timestamp', inplace=True)
                        
                        # Append to our combined dataframe
                        all_data = pd.concat([all_data, chunk_df])
                
                # Add a small delay to avoid rate limiting
                time.sleep(0.5)
                
            except requests.exceptions.RequestException as e:
                logger.error(f"Error fetching historical data for period {chunk_start} to {chunk_end}: {e}")
                # Log the response content if available
                if hasattr(e, 'response') and e.response is not None:
                    error_content = e.response.text
                    logger.error(f"Response content: {error_content}")
                    
                    # Display error on screen
                    print(f"\n===== API ERROR =====")
                    print(f"Error fetching data for {chunk_start} to {chunk_end}")
                    print(f"Error details: {error_content}")
                    print("=====================\n")
            
            # Move to next chunk
            current_start = current_end + timedelta(days=1)
        
        # Sort the final dataframe by timestamp
        if not all_data.empty:
            all_data = all_data.sort_index()
            
        return all_data

    def simulate_data(self):
        """
        In case of demo mode or API limits, simulate XAU/USD data
        Note: This should only be used for testing purposes
        """
        current_price = 1900 + (10 * (0.5 -
                                      (datetime.now().microsecond / 1000000)))

        return {
            'symbol': 'XAUUSD',
            'price': current_price,
            'bid': current_price - 0.1,
            'ask': current_price + 0.1,
            'timestamp': datetime.now().isoformat()
        }
