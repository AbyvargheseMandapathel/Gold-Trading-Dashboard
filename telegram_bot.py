import telegram

class TelegramNotifier:
    def __init__(self, token, chat_id):
        self.bot = telegram.Bot(token=token)
        self.chat_id = chat_id

    def send_signal(self, signal_type, price, indicators):
        message = f"""
🚨 {signal_type} Signal for XAU/USD
💰 Price: ${price:.2f}

📊 Indicators:
RSI: {indicators['RSI']:.2f}
MACD: {indicators['MACD']:.2f}
Signal Line: {indicators['Signal Line']:.2f}
SMA 20: ${indicators['SMA_20']:.2f}
SMA 50: ${indicators['SMA_50']:.2f}
Strength: {indicators['Signal_Strength']:.2f}
        """
        self.bot.send_message(chat_id=self.chat_id, text=message)