import numpy as np
from typing import List, Dict, Optional
from collections import defaultdict, deque

class PriceAnalyzer:
    def __init__(self, ema_periods: int = 21):
        self.ema_periods = ema_periods
        self.price_history = defaultdict(lambda: deque(maxlen=ema_periods + 5))  # Extra buffer
        self.ema_history = defaultdict(lambda: deque(maxlen=5))  # Store last 5 EMA values for slope
    
    def update_prices(self, token: str, candles: List[Dict]) -> None:
        """Update price history with new candle data"""
        if not candles:
            return
        
        # Sort candles by timestamp to ensure chronological order
        sorted_candles = sorted(candles, key=lambda x: x['timestamp'])
        
        # Clear existing data and add all candles
        self.price_history[token].clear()
        for candle in sorted_candles:
            self.price_history[token].append(candle['close'])
    
    def calculate_ema(self, token: str) -> Optional[Dict]:
        """Calculate EMA and related metrics"""
        prices = list(self.price_history[token])
        
        if len(prices) < 5:  # Need minimum data
            return None
        
        current_price = prices[-1]
        
        # Calculate EMA or SMA based on available data
        if len(prices) >= self.ema_periods:
            # Use EMA calculation
            ema_value = self._calculate_ema_21(prices)
            method = "EMA"
        else:
            # Fallback to Simple Moving Average
            ema_value = np.mean(prices)
            method = "SMA"
        
        # Store EMA value for slope calculation
        self.ema_history[token].append(ema_value)
        
        # Calculate EMA slope if we have enough EMA history
        ema_slope_up = self._is_ema_sloping_up(token)
        
        return {
            "current_price": current_price,
            "ema_value": ema_value,
            "price_above_ema": current_price > ema_value,
            "ema_slope_up": ema_slope_up,
            "method": method,
            "periods_used": len(prices)
        }
    
    def _calculate_ema_21(self, prices: List[float]) -> float:
        """Calculate 21-period Exponential Moving Average"""
        if len(prices) < self.ema_periods:
            return np.mean(prices)  # Fallback to SMA
        
        # EMA formula: EMA[t] = α × Price[t] + (1-α) × EMA[t-1]
        alpha = 2 / (self.ema_periods + 1)  # 2/(21+1) = 0.0909
        
        # Initialize EMA with Simple Moving Average of first period
        ema = np.mean(prices[:self.ema_periods])
        
        # Calculate EMA for remaining periods
        for price in prices[self.ema_periods:]:
            ema = alpha * price + (1 - alpha) * ema
        
        return ema
    
    def _is_ema_sloping_up(self, token: str) -> Optional[bool]:
        """Check if EMA is sloping upward based on last 3 values"""
        ema_values = list(self.ema_history[token])
        
        if len(ema_values) < 3:
            return None  # Not enough data for slope calculation - unknown
        
        # Check if last 3 EMA values are strictly increasing
        is_upward = ema_values[-3] < ema_values[-2] < ema_values[-1]
        
        # Return True if upward, None if not upward (unknown)
        return True if is_upward else None
    
    def has_sufficient_data(self, token: str) -> bool:
        """Check if token has enough data for EMA analysis"""
        return len(self.price_history[token]) >= 5
    
    def get_analysis_summary(self, token: str) -> Optional[str]:
        """Get human-readable analysis summary"""
        if not self.has_sufficient_data(token):
            return "Insufficient data"
        
        ema_data = self.calculate_ema(token)
        if not ema_data:
            return "Calculation failed"
        
        price_status = "✅ Above" if ema_data['price_above_ema'] else "❌ Below"
        slope_status = "✅ Up" if ema_data['ema_slope_up'] is True else "❓ Unknown/Flat/Down"
        
        return f"Price {price_status} {ema_data['method']}-21 | Slope {slope_status} | Periods: {ema_data['periods_used']}" 