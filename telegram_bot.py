import telegram

class TelegramNotifier:
    def __init__(self, token, chat_id):
        """
        Initialize the Telegram bot notifier.
        
        Args:
            token (str): Your Telegram bot's API token
            chat_id (str): The chat ID where messages will be sent
        """
        self.token = token
        self.chat_id = chat_id
        try:
            self.bot = telegram.Bot(token=self.token)
            self._test_connection()
        except Exception as e:
            raise ConnectionError(f"Failed to initialize Telegram bot: {e}")

    def _test_connection(self):
        """Test if the bot can communicate with Telegram"""
        try:
            self.bot.get_me()
            print("✅ Telegram bot connected successfully")
        except Exception as e:
            raise ConnectionError(f"Telegram bot connection failed: {e}")

    def send_signal(self, signal_type, price, indicators):
        """
        Send a formatted trading signal to Telegram
        
        Args:
            signal_type (str): 'BUY', 'SELL', or 'HOLD'
            price (float): Current gold price
            indicators (dict): Technical indicators like RSI, MACD, etc.
        """
        try:
            emoji = "🟢" if signal_type == "BUY" else "🔴" if signal_type == "SELL" else "🟠"
            message = f"""
{emoji} <b>{signal_type} Signal for XAU/USD</b>
💰 Price: ${price:.2f}

📊 Indicators:
RSI: {indicators['RSI']:.2f}
MACD: {indicators['MACD']:.2f}
Signal Line: {indicators['MACD_Signal']:.2f}
SMA 20: ${indicators['SMA_20']:.2f}
SMA 50: ${indicators['SMA_50']:.2f}
Strength: {indicators['Signal_Strength']:.2f}
            """
            self.bot.send_message(chat_id=self.chat_id, text=message, parse_mode='HTML')
            print(f"📩 Telegram signal sent: {signal_type}")
        except Exception as e:
            print(f"❌ Failed to send Telegram message: {e}")