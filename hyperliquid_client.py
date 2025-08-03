import requests
import time
from typing import Dict, List, Optional

class HyperliquidClient:
    BASE_URL = "https://api.hyperliquid.xyz"
    RATE_LIMIT_DELAY = 0.05  # 50ms between requests to stay under 1200/min
    
    def __init__(self):
        self.session = requests.Session()
        self.last_request_time = 0
    
    def _rate_limit(self):
        """Ensure rate limiting compliance"""
        elapsed = time.time() - self.last_request_time
        if elapsed < self.RATE_LIMIT_DELAY:
            time.sleep(self.RATE_LIMIT_DELAY - elapsed)
        self.last_request_time = time.time()
    
    def _post(self, endpoint: str, data: dict, retries: int = 1) -> Optional[dict]:
        """Make POST request with rate limiting and retry logic"""
        self._rate_limit()
        
        for attempt in range(retries + 1):
            try:
                response = self.session.post(f"{self.BASE_URL}/{endpoint}", json=data, timeout=10)
                response.raise_for_status()
                return response.json()
            except Exception as e:
                if attempt == retries:
                    print(f"❌ API request failed after {retries + 1} attempts: {e}")
                    return None
                time.sleep(1)  # Brief pause before retry
    
    def get_universe_and_volumes(self) -> Optional[List[Dict]]:
        """Get token universe with volume data"""
        data = self._post("info", {"type": "metaAndAssetCtxs"})
        if not data or len(data) != 2:
            return None
        
        universe, asset_contexts = data
        tokens = []
        
        for i, token_info in enumerate(universe.get("universe", [])):
            if i >= len(asset_contexts):
                continue
            
            name = token_info.get("name")
            if not name or name in ["BTC", "ETH"]:  # Exclude BTC/ETH as specified
                continue
            
            asset_ctx = asset_contexts[i]
            volume_24h = float(asset_ctx.get("dayNtlVlm", 0))
            price = float(asset_ctx.get("markPx", 0))
            
            tokens.append({
                "name": name,
                "volume_24h": volume_24h,
                "price": price
            })
        
        return tokens
    
    def get_1h_candles(self, coin: str, num_candles: int = 25) -> Optional[List[Dict]]:
        """Get 1H candle data for EMA calculation
        
        Args:
            coin: Token symbol (e.g., "SOL")
            num_candles: Number of recent 1H candles to fetch (default: 25 for 21 EMA + buffer)
        
        Returns:
            List of candle dictionaries with {close, volume, timestamp} or None if failed
        """
        # Calculate time range (num_candles hours ago to now)
        end_time = int(time.time() * 1000)  # Current time in ms
        start_time = end_time - (num_candles * 60 * 60 * 1000)  # num_candles hours ago
        
        request_data = {
            "type": "candleSnapshot",
            "req": {
                "coin": coin,
                "interval": "1h",
                "startTime": start_time,
                "endTime": end_time
            }
        }
        
        data = self._post("info", request_data)
        if not data:
            return None
        
        # Parse candle data
        candles = []
        for candle in data:
            try:
                candles.append({
                    "close": float(candle["c"]),
                    "volume": float(candle["v"]),
                    "timestamp": int(candle["t"]),
                    "open": float(candle["o"]),
                    "high": float(candle["h"]),
                    "low": float(candle["l"])
                })
            except (KeyError, ValueError, TypeError):
                continue  # Skip malformed candles
        
        return candles if candles else None 