import numpy as np
from typing import List, Dict, Optional
from collections import defaultdict, deque

class VolumeAnalyzer:
    def __init__(self, periods: int = 20):
        self.periods = periods
        self.volume_history = defaultdict(lambda: deque(maxlen=periods))
    
    def update_volume(self, token: str, volume: float) -> None:
        """Update volume history for a token"""
        self.volume_history[token].append(volume)
    
    def calculate_stats(self, token: str, current_volume: float) -> Optional[Dict]:
        """Calculate sigma deviation and Z-score for current volume"""
        history = list(self.volume_history[token])
        
        # Need at least 5 periods for meaningful statistics
        if len(history) < 5:
            return None
        
        # Use historical data (excluding current) for baseline
        baseline_volumes = np.array(history[:-1] if len(history) == self.periods else history)
        
        if len(baseline_volumes) == 0:
            return None
        
        mean_volume = np.mean(baseline_volumes)
        std_volume = np.std(baseline_volumes)
        
        # Avoid division by zero
        if std_volume == 0:
            return None
        
        # Sigma deviation: how many standard deviations above mean
        sigma_dev = (current_volume - mean_volume) / std_volume
        
        # Z-score: standardized score (same calculation in this case)
        z_score = sigma_dev
        
        return {
            "sigma_deviation": sigma_dev,
            "z_score": z_score,
            "mean_volume": mean_volume,
            "current_volume": current_volume,
            "periods_analyzed": len(baseline_volumes)
        }
    
    def has_sufficient_data(self, token: str) -> bool:
        """Check if token has enough data for analysis"""
        return len(self.volume_history[token]) >= 5 