import os
import logging
import asyncio
from telegram import Bot
from telegram.error import TelegramError

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class TelegramAlerts:
    """Class to send trading alerts via Telegram"""
    
    def __init__(self):
        """Initialize the Telegram bot with API token"""
        self.token = os.getenv("TELEGRAM_BOT_TOKEN", "")
        self.chat_id = os.getenv("TELEGRAM_CHAT_ID", "")
        self.enabled = bool(self.token and self.chat_id)
        
        if self.enabled:
            try:
                self.bot = Bot(token=self.token)
                logger.info("Telegram bot initialized successfully")
            except Exception as e:
                logger.error(f"Failed to initialize Telegram bot: {e}")
                self.enabled = False
        else:
            logger.warning("Telegram bot not configured. Set TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID environment variables.")
    
    async def send_message_async(self, message):
        """
        Send a message to the Telegram chat asynchronously
        
        Args:
            message (str): Message to send
            
        Returns:
            bool: True if sent successfully, False otherwise
        """
        if not self.enabled:
            logger.warning("Telegram bot not enabled, message not sent")
            return False
            
        try:
            await self.bot.send_message(
                chat_id=self.chat_id,
                text=message,
                parse_mode='Markdown'
            )
            return True
        except TelegramError as e:
            logger.error(f"Failed to send Telegram message: {e}")
            return False
    
    def send_message(self, message):
        """
        Send a message to the Telegram chat (synchronous wrapper)
        
        Args:
            message (str): Message to send
            
        Returns:
            bool: True if sent successfully, False otherwise
        """
        if not self.enabled:
            logger.warning("Telegram bot not enabled, message not sent")
            return False
            
        try:
            # Create a new event loop for the async call
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            result = loop.run_until_complete(self.send_message_async(message))
            loop.close()
            return result
        except Exception as e:
            logger.error(f"Error in send_message: {e}")
            return False
    
    def send_signal_alert(self, signal, price, symbol="XAUUSD"):
        """
        Send a trading signal alert
        
        Args:
            signal (dict): Signal information
            price (float): Current price
            symbol (str): Trading symbol
            
        Returns:
            bool: True if sent successfully, False otherwise
        """
        if not self.enabled:
            return False
            
        try:
            recommendation = signal.get('recommendation', 'Neutral')
            
            # Format the signals nicely
            signal_details = ""
            for s in signal.get('signals', []):
                signal_type = s.get('type', '').upper()
                reason = s.get('reason', '')
                signal_details += f"• {signal_type}: {reason}\n"
            
            message = f"*{symbol} SIGNAL ALERT*\n\n"
            message += f"*Recommendation:* {recommendation}\n"
            message += f"*Current Price:* ${price:.2f}\n\n"
            
            if signal_details:
                message += "*Signal Details:*\n"
                message += signal_details
            
            message += f"\n*Time:* {__import__('datetime').datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
            
            return self.send_message(message)
            
        except Exception as e:
            logger.error(f"Error sending signal alert: {e}")
            return False
