#!/usr/bin/env python3
"""
Hyperliquid Volume Spike Detector Bot
Monitors perpetual futures volume for abnormal spikes with EMA momentum filtering.
"""

import time
import signal
import sys
from datetime import datetime

from config import Config
from hyperliquid_client import HyperliquidClient
from volume_analyzer import VolumeAnalyzer
from price_analyzer import PriceAnalyzer
from alert_system import AlertSystem

class VolumeSpikeBot:
    def __init__(self):
        Config.validate()
        
        self.client = HyperliquidClient()
        self.volume_analyzer = VolumeAnalyzer(periods=Config.VOLUME_PERIODS)
        self.price_analyzer = PriceAnalyzer(ema_periods=Config.EMA_PERIODS)
        self.alerts = AlertSystem(Config.BOT_TOKEN, Config.CHAT_ID)
        self.running = True
        
        # Graceful shutdown handler
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
    
    def _signal_handler(self, signum, frame):
        """Handle shutdown signals gracefully"""
        print(f"\n📡 Received signal {signum}, shutting down gracefully...")
        self.running = False
    
    def _filter_tokens(self, tokens):
        """Filter tokens based on strict list, volume and price criteria"""
        filtered = []
        config = Config()
        strict_list = config.STRICT_LIST
        
        for token in tokens:
            # Apply strict list filter if enabled
            if Config.STRICT_LIST_ENABLED:
                if token['name'] not in strict_list:
                    continue  # Skip tokens not in strict list
            
            # Skip if volume is 0 or very low (likely delisted/inactive)
            if token['volume_24h'] < 1000:  # $1k minimum volume
                continue
            
            # Basic sanity checks
            if token['price'] <= 0:
                continue
                
            filtered.append(token)
        
        return filtered
    
    def _check_volume_and_momentum_spike(self, token):
        """Check if token has both volume spike and positive momentum"""
        name = token['name']
        volume = token['volume_24h']
        
        # STEP 1: Update volume history and check volume spike
        self.volume_analyzer.update_volume(name, volume)
        
        # Skip if insufficient volume data
        if not self.volume_analyzer.has_sufficient_data(name):
            return False
        
        # Calculate volume statistics
        volume_stats = self.volume_analyzer.calculate_stats(name, volume)
        if not volume_stats:
            return False
        
        # Check volume spike thresholds
        volume_spike = (volume_stats['sigma_deviation'] >= Config.SIGMA_THRESHOLD and 
                       volume_stats['z_score'] >= Config.Z_SCORE_THRESHOLD)
        
        if not volume_spike:
            return False  # No volume spike, skip momentum check
        
        # STEP 2: Get candle data and analyze price momentum
        candles = self.client.get_1h_candles(name, num_candles=Config.EMA_PERIODS + 5)
        if not candles:
            print(f"⚠️  No candle data for {name}, skipping momentum analysis")
            return False
        
        # Update price history and calculate EMA
        self.price_analyzer.update_prices(name, candles)
        
        if not self.price_analyzer.has_sufficient_data(name):
            return False
        
        ema_stats = self.price_analyzer.calculate_ema(name)
        if not ema_stats:
            return False
        
        # STEP 3: Check momentum filters
        momentum_conditions = []
        
        # Required: Price above EMA
        if Config.PRICE_ABOVE_EMA_REQUIRED:
            if not ema_stats['price_above_ema']:
                return False  # Price not above EMA, reject signal
            momentum_conditions.append("Price > EMA")
        
        # Optional: EMA slope filter
        if Config.EMA_SLOPE_FILTER_ENABLED:
            if ema_stats['ema_slope_up'] is False:  # Explicitly False (not None)
                return False  # EMA not sloping up, reject signal
            elif ema_stats['ema_slope_up'] is True:
                momentum_conditions.append("EMA Rising")
        
        # STEP 4: Send alert with combined data
        alert_data = {
            **token,           # Original token data
            **volume_stats,    # Volume spike statistics  
            **ema_stats        # EMA momentum data
        }
        
        print(f"🎯 {name}: Volume spike + momentum confirmed! Conditions: {', '.join(momentum_conditions)}")
        self.alerts.send_alert(alert_data)
        return True
    
    def run_cycle(self):
        """Run one monitoring cycle with volume and momentum analysis"""
        print(f"🔍 [{datetime.now().strftime('%H:%M:%S')}] Fetching token data...")
        
        # Get current token data
        tokens = self.client.get_universe_and_volumes()
        if not tokens:
            print("❌ Failed to fetch token data")
            return
        
        # Filter tokens (including strict list filter)
        filtered_tokens = self._filter_tokens(tokens)
        
        # Show filtering info
        config = Config()
        if Config.STRICT_LIST_ENABLED:
            strict_count = len(config.STRICT_LIST)
            print(f"📋 Strict list: {strict_count} tokens | Analyzing: {len(filtered_tokens)} tokens (volume + momentum)")
        else:
            print(f"📊 Analyzing {len(filtered_tokens)} tokens (volume + momentum)...")
        
        # Check each token for volume spikes AND momentum
        alerts_sent = 0
        start_time = time.time()
        
        for i, token in enumerate(filtered_tokens):
            try:
                if self._check_volume_and_momentum_spike(token):
                    alerts_sent += 1
                
                # Progress indicator every 25 tokens (adjusted for smaller lists)
                if (i + 1) % 25 == 0:
                    elapsed = time.time() - start_time
                    print(f"📈 Processed {i + 1}/{len(filtered_tokens)} tokens ({elapsed:.1f}s elapsed)")
                    
            except Exception as e:
                print(f"⚠️  Error analyzing {token['name']}: {e}")
                continue
        
        total_time = time.time() - start_time
        print(f"⏱️  Analysis complete: {total_time:.1f}s total")
        
        if alerts_sent > 0:
            print(f"🚨 Sent {alerts_sent} volume spike + momentum alerts")
        else:
            print("✅ No significant volume spikes with positive momentum detected")
    
    def run(self):
        """Main bot loop"""
        print("🚀 Hyperliquid Volume Spike + Momentum Bot Starting...")
        
        config = Config()
        config_summary = (
            f"⚙️  Volume: σ≥{Config.SIGMA_THRESHOLD}, Z≥{Config.Z_SCORE_THRESHOLD}, {Config.VOLUME_PERIODS} periods\n"
            f"📈 Momentum: {Config.EMA_PERIODS}-EMA, Price>EMA: {Config.PRICE_ABOVE_EMA_REQUIRED}, "
            f"Slope filter: {Config.EMA_SLOPE_FILTER_ENABLED}\n"
        )
        
        if Config.STRICT_LIST_ENABLED:
            strict_list = config.STRICT_LIST
            config_summary += f"📋 Strict list: {len(strict_list)} tokens enabled\n"
        else:
            config_summary += f"📊 Monitoring: All available tokens\n"
            
        config_summary += f"🔄 Interval: {Config.UPDATE_INTERVAL_MINUTES} minutes"
        print(config_summary)
        
        if not self.alerts.telegram_available:
            print("📱 Telegram not configured - alerts will print to console")
        
        cycle_count = 0
        
        while self.running:
            try:
                cycle_count += 1
                print(f"\n--- Cycle {cycle_count} ---")
                
                self.run_cycle()
                
                # Wait for next cycle
                if self.running:
                    wait_seconds = Config.UPDATE_INTERVAL_MINUTES * 60
                    print(f"⏳ Waiting {Config.UPDATE_INTERVAL_MINUTES} minutes until next cycle...")
                    
                    # Sleep in small chunks to allow for graceful shutdown
                    for _ in range(wait_seconds):
                        if not self.running:
                            break
                        time.sleep(1)
                        
            except Exception as e:
                print(f"❌ Error in main loop: {e}")
                if self.running:
                    print("🔄 Retrying in 30 seconds...")
                    time.sleep(30)
        
        print("👋 Bot shutdown complete")

def main():
    """Entry point"""
    try:
        bot = VolumeSpikeBot()
        bot.run()
    except KeyboardInterrupt:
        print("\n👋 Shutting down...")
    except Exception as e:
        print(f"💥 Fatal error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main() 