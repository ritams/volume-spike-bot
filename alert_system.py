import requests
from typing import Dict, Optional

class AlertSystem:
    def __init__(self, bot_token: Optional[str] = None, chat_id: Optional[str] = None):
        self.bot_token = bot_token
        self.chat_id = chat_id
        self.telegram_available = bool(bot_token and chat_id)
    
    def send_alert(self, token_data: Dict) -> bool:
        """Send volume spike alert with EMA momentum data"""
        message = self._format_message(token_data)
        
        if self.telegram_available:
            return self._send_telegram(message)
        else:
            self._print_console(message)
            return True
    
    def _format_message(self, data: Dict) -> str:
        """Format alert message with volume and momentum data"""
        # Volume data
        volume_section = (
            f"Volume: ${data['volume_24h']:,.0f}\n"
            f"Sigma Dev: {data['sigma_deviation']:.2f}\n"
            f"Z-Score: {data['z_score']:.2f}"
        )
        
        # Price and EMA data
        price_section = (
            f"Price: ${data['current_price']:.4f}\n"
            f"{data['method']}-21: ${data['ema_value']:.4f}"
        )
        
        # Momentum indicators
        price_vs_ema = "✅ Above EMA" if data['price_above_ema'] else "❌ Below EMA"
        
        if data['ema_slope_up'] is True:
            slope_indicator = "✅ EMA Rising"
        else:
            slope_indicator = "❓ EMA Slope Unknown/Flat/Down"
        
        return (
            f"🚨 VOLUME SPIKE + MOMENTUM DETECTED\n"
            f"Token: ${data['name']}\n"
            f"{volume_section}\n"
            f"{price_section}\n"
            f"Momentum: {price_vs_ema}\n"
            f"Trend: {slope_indicator}\n"
            f"Analysis: {data['periods_analyzed']} vol periods, {data['periods_used']} price periods"
        )
    
    def _send_telegram(self, message: str) -> bool:
        """Send message via Telegram"""
        try:
            url = f"https://api.telegram.org/bot{self.bot_token}/sendMessage"
            response = requests.post(url, json={"chat_id": self.chat_id, "text": message}, timeout=10)
            response.raise_for_status()
            return True
        except Exception as e:
            print(f"❌ Telegram send failed: {e}")
            self._print_console(message)  # Fallback to console
            return False
    
    def _print_console(self, message: str) -> None:
        """Print alert to console"""
        print(f"\n{message}\n" + "="*50) 