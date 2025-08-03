# 🏗️ Architecture & Execution Flow

Complete execution flow and logic breakdown for the **Hyperliquid Volume Spike + Momentum Detector Bot**.

## 📋 System Overview

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   main.py       │    │ config.py       │    │ .env file       │
│ VolumeSpikeBot  │───▶│ Config          │───▶│ Environment     │
│                 │    │ Validation      │    │ Variables       │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │
         ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│hyperliquid_     │    │ volume_         │    │ price_          │
│client.py        │    │ analyzer.py     │    │ analyzer.py     │
│ API Client      │    │ Volume Stats    │    │ EMA Momentum    │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         └───────────────────────┼───────────────────────┘
                                 ▼
                    ┌─────────────────┐
                    │ alert_          │
                    │ system.py       │
                    │ Notifications   │
                    └─────────────────┘
```

## 🚀 Complete Execution Flow

### **1. Bot Initialization (`main.py`)**

```python
def main():
    """Entry point - everything starts here"""
    try:
        bot = VolumeSpikeBot()  # Create bot instance
        bot.run()              # Start monitoring loop
    except KeyboardInterrupt:
        print("Shutting down...")
    except Exception as e:
        print(f"Fatal error: {e}")
        sys.exit(1)

class VolumeSpikeBot.__init__():
    """Initialize all components"""
    
    # Step 1: Load and validate configuration
    Config.validate()  
    │
    ├─ Load environment variables from .env
    ├─ Set defaults for missing values
    ├─ Validate thresholds > 0
    ├─ Validate EMA configuration
    └─ Print warning if Telegram not configured
    
    # Step 2: Initialize components
    self.client = HyperliquidClient()          # API client with rate limiting
    self.volume_analyzer = VolumeAnalyzer()    # Volume statistics engine
    self.price_analyzer = PriceAnalyzer()      # NEW: EMA momentum analyzer
    self.alerts = AlertSystem()                # Telegram/console alerts
    self.running = True                        # Control flag
    
    # Step 3: Setup signal handlers for graceful shutdown
    signal.signal(SIGINT, self._signal_handler)
    signal.signal(SIGTERM, self._signal_handler)
```

### **2. Main Monitoring Loop (`VolumeSpikeBot.run()`)**

```python
def run():
    """Main bot loop - runs indefinitely until stopped"""
    
    print("🚀 Volume Spike + Momentum Bot Starting...")
    print(f"Volume: σ≥{SIGMA_THRESHOLD}, Z≥{Z_SCORE_THRESHOLD}")
    print(f"Momentum: {EMA_PERIODS}-EMA, Price>EMA: {PRICE_ABOVE_EMA_REQUIRED}")
    
    cycle_count = 0
    
    while self.running:  # Main loop
        try:
            cycle_count += 1
            print(f"--- Cycle {cycle_count} ---")
            
            # CORE LOGIC: Run one monitoring cycle
            self.run_cycle()
            │
            ├─ Fetch token data from Hyperliquid API
            ├─ Filter tokens by volume/price criteria  
            ├─ TWO-STAGE ANALYSIS:
            │  ├─ Stage 1: Volume spike detection (fast)
            │  └─ Stage 2: Momentum confirmation (only for spikes)
            ├─ Send alerts for tokens meeting ALL thresholds
            └─ Print summary of cycle results
            
            # Wait for next cycle (15 minutes default)
            if self.running:
                wait_seconds = UPDATE_INTERVAL_MINUTES * 60
                
                # Sleep in 1-second chunks for responsive shutdown
                for _ in range(wait_seconds):
                    if not self.running:
                        break
                    time.sleep(1)
                        
        except Exception as e:
            print(f"Error in main loop: {e}")
            if self.running:
                print("Retrying in 30 seconds...")
                time.sleep(30)  # Brief pause before retry
    
    print("Bot shutdown complete")
```

### **3. Enhanced Monitoring Cycle (`VolumeSpikeBot.run_cycle()`)**

```python
def run_cycle():
    """Execute one complete monitoring cycle with two-stage filtering"""
    
    print(f"🔍 [{current_time}] Fetching token data...")
    
    # STEP 1: Get current market data (24h volume + prices)
    tokens = self.client.get_universe_and_volumes()
    │
    └─ calls: HyperliquidClient.get_universe_and_volumes()
       │
       ├─ POST https://api.hyperliquid.xyz/info
       ├─ Request: {"type": "metaAndAssetCtxs"}
       ├─ Parse universe (token names) + asset contexts (volumes, prices)
       ├─ Exclude BTC and ETH as specified
       ├─ Return list of {name, volume_24h, price} objects
       └─ Handle API failures gracefully
    
    if not tokens:
        print("❌ Failed to fetch token data")
        return  # Skip this cycle
    
    # STEP 2: Filter tokens by basic criteria
    filtered_tokens = self._filter_tokens(tokens)
    │
    └─ Filter logic:
       ├─ Remove tokens with volume < $1000 (inactive/delisted)
       ├─ Remove tokens with price <= 0 (invalid data)
       └─ Return clean list for analysis
    
    print(f"📊 Analyzing {len(filtered_tokens)} tokens (volume + momentum)...")
    
    # STEP 3: TWO-STAGE ANALYSIS for each token
    alerts_sent = 0
    start_time = time.time()
    
    for i, token in enumerate(filtered_tokens):
        try:
            if self._check_volume_and_momentum_spike(token):
                alerts_sent += 1
            
            # Progress indicator every 50 tokens
            if (i + 1) % 50 == 0:
                elapsed = time.time() - start_time
                print(f"📈 Processed {i + 1}/{len(filtered_tokens)} tokens")
                
        except Exception as e:
            print(f"⚠️  Error analyzing {token['name']}: {e}")
            continue  # Skip failed token, continue with others
    
    total_time = time.time() - start_time
    print(f"⏱️  Analysis complete: {total_time:.1f}s total")
    
    # STEP 4: Print cycle summary
    if alerts_sent > 0:
        print(f"🚨 Sent {alerts_sent} volume spike + momentum alerts")
    else:
        print("✅ No significant volume spikes with positive momentum detected")
```

### **4. Two-Stage Volume + Momentum Detection (`_check_volume_and_momentum_spike()`)**

```python
def _check_volume_and_momentum_spike(token):
    """Core detection logic - two-stage filtering for high-probability signals"""
    
    name = token['name']
    volume = token['volume_24h']
    
    # STAGE 1: VOLUME SPIKE DETECTION (Fast - uses existing data)
    self.volume_analyzer.update_volume(name, volume)
    
    # Skip if insufficient volume data
    if not self.volume_analyzer.has_sufficient_data(name):
        return False  # Need at least 5 periods
    
    # Calculate volume statistics
    volume_stats = self.volume_analyzer.calculate_stats(name, volume)
    if not volume_stats:
        return False
    
    # Check volume spike thresholds
    volume_spike = (volume_stats['sigma_deviation'] >= SIGMA_THRESHOLD and 
                   volume_stats['z_score'] >= Z_SCORE_THRESHOLD)
    
    if not volume_spike:
        return False  # No volume spike, skip expensive momentum check
    
    # STAGE 2: MOMENTUM CONFIRMATION (Slower - fetches 1h candles)
    print(f"📊 {name}: Volume spike detected, checking momentum...")
    
    # Fetch 1H candle data for EMA calculation
    candles = self.client.get_1h_candles(name, num_candles=EMA_PERIODS + 5)
    │
    └─ calls: HyperliquidClient.get_1h_candles()
       │
       ├─ POST https://api.hyperliquid.xyz/info
       ├─ Request: {"type": "candleSnapshot", "req": {...}}
       ├─ Calculate time range (21+ hours ago to now)
       ├─ Parse candle data {close, volume, timestamp, open, high, low}
       └─ Return chronologically sorted candles
    
    if not candles:
        print(f"⚠️  No candle data for {name}, skipping momentum analysis")
        return False
    
    # Update price history and calculate EMA
    self.price_analyzer.update_prices(name, candles)
    
    if not self.price_analyzer.has_sufficient_data(name):
        return False
    
    ema_stats = self.price_analyzer.calculate_ema(name)
    │
    └─ calls: PriceAnalyzer.calculate_ema()
       │
       ├─ Get price history from candles
       ├─ Choose EMA vs SMA based on data availability
       ├─ Calculate: ema_value, current_price, price_above_ema
       ├─ Calculate: ema_slope_up (3-period trend)
       └─ Return {current_price, ema_value, price_above_ema, ema_slope_up, method}
    
    if not ema_stats:
        return False
    
    # STAGE 2: Check momentum filters
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
    
    # ALERT: Both volume spike AND momentum confirmed
    alert_data = {
        **token,           # Original token data {name, volume_24h, price}
        **volume_stats,    # Volume spike statistics {sigma_deviation, z_score, ...}
        **ema_stats        # EMA momentum data {current_price, ema_value, price_above_ema, ...}
    }
    
    print(f"🎯 {name}: Volume spike + momentum confirmed! Conditions: {', '.join(momentum_conditions)}")
    self.alerts.send_alert(alert_data)
    return True
```

## 🔧 Component Deep Dive

### **HyperliquidClient (`hyperliquid_client.py`)** - Enhanced

```python
class HyperliquidClient:
    """Handles all Hyperliquid API communication"""
    
    def get_universe_and_volumes():
        """Get all token data (existing method)"""
        # Returns: [{"name": "SOL", "volume_24h": 123456, "price": 43.2}, ...]
    
    def get_1h_candles(coin, num_candles=25):  # NEW METHOD
        """Get 1H candle data for EMA calculation"""
        
        # Calculate time range
        end_time = int(time.time() * 1000)
        start_time = end_time - (num_candles * 60 * 60 * 1000)
        
        # Call candleSnapshot endpoint
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
        
        # Parse and return candle data
        candles = []
        for candle in data:
            candles.append({
                "close": float(candle["c"]),
                "volume": float(candle["v"]),
                "timestamp": int(candle["t"]),
                "open": float(candle["o"]),
                "high": float(candle["h"]),
                "low": float(candle["l"])
            })
        
        return sorted(candles, key=lambda x: x['timestamp'])
```

### **PriceAnalyzer (`price_analyzer.py`)** - NEW COMPONENT

```python
class PriceAnalyzer:
    """EMA momentum analysis engine"""
    
    def __init__(ema_periods=21):
        self.ema_periods = ema_periods
        self.price_history = defaultdict(lambda: deque(maxlen=ema_periods + 5))
        self.ema_history = defaultdict(lambda: deque(maxlen=5))  # For slope
    
    def update_prices(token, candles):
        """Update price history with candle data"""
        sorted_candles = sorted(candles, key=lambda x: x['timestamp'])
        
        self.price_history[token].clear()
        for candle in sorted_candles:
            self.price_history[token].append(candle['close'])
    
    def calculate_ema(token):
        """Calculate EMA with SMA fallback"""
        prices = list(self.price_history[token])
        current_price = prices[-1]
        
        # Choose calculation method based on data availability
        if len(prices) >= self.ema_periods:
            ema_value = self._calculate_ema_21(prices)  # True EMA
            method = "EMA"
        else:
            ema_value = np.mean(prices)  # SMA fallback
            method = "SMA"
        
        # Store EMA for slope calculation
        self.ema_history[token].append(ema_value)
        
        return {
            "current_price": current_price,
            "ema_value": ema_value,
            "price_above_ema": current_price > ema_value,
            "ema_slope_up": self._is_ema_sloping_up(token),
            "method": method,
            "periods_used": len(prices)
        }
    
    def _calculate_ema_21(prices):
        """Calculate true 21-period EMA"""
        alpha = 2 / (21 + 1)  # 0.0909
        
        # Initialize with SMA of first 21 periods
        ema = np.mean(prices[:21])
        
        # Apply EMA formula to remaining periods
        for price in prices[21:]:
            ema = alpha * price + (1 - alpha) * ema
        
        return ema
    
    def _is_ema_sloping_up(token):
        """Check if EMA is trending upward"""
        ema_values = list(self.ema_history[token])
        
        if len(ema_values) < 3:
            return None  # Insufficient data
        
        # Check if strictly increasing over last 3 periods
        return ema_values[-3] < ema_values[-2] < ema_values[-1]
```

### **Enhanced AlertSystem (`alert_system.py`)**

```python
def _format_message(data):
    """Format comprehensive alert with volume + momentum data"""
    
    # Volume section
    volume_section = (
        f"Volume: ${data['volume_24h']:,.0f}\n"
        f"Sigma Dev: {data['sigma_deviation']:.2f}\n"
        f"Z-Score: {data['z_score']:.2f}"
    )
    
    # Price & EMA section  
    price_section = (
        f"Price: ${data['current_price']:.4f}\n"
        f"{data['method']}-21: ${data['ema_value']:.4f}"
    )
    
    # Momentum indicators
    price_vs_ema = "✅ Above EMA" if data['price_above_ema'] else "❌ Below EMA"
    
    if data['ema_slope_up'] is not None:
        slope_indicator = "✅ EMA Rising" if data['ema_slope_up'] else "❌ EMA Falling"
    else:
        slope_indicator = "❓ EMA Slope Unknown"
    
    return (
        f"🚨 VOLUME SPIKE + MOMENTUM DETECTED\n"
        f"Token: ${data['name']}\n"
        f"{volume_section}\n"
        f"{price_section}\n"
        f"Momentum: {price_vs_ema}\n"
        f"Trend: {slope_indicator}\n"
        f"Analysis: {data['periods_analyzed']} vol periods, {data['periods_used']} price periods"
    )
```

## 🔄 Enhanced Data Flow Summary

```
1. STARTUP:
   main() → VolumeSpikeBot.__init__() → Config.validate() → Initialize analyzers

2. MONITORING LOOP:
   run() → run_cycle() → [REPEAT EVERY 15 MINUTES]

3. EACH CYCLE:
   run_cycle() → get_universe_and_volumes() → _filter_tokens() → [FOR EACH TOKEN]

4. TWO-STAGE ANALYSIS:
   _check_volume_and_momentum_spike() → 
   ├─ STAGE 1: volume_analyzer.calculate_stats() → [IF VOLUME SPIKE]
   └─ STAGE 2: get_1h_candles() → price_analyzer.calculate_ema() → [IF MOMENTUM] → send_alert()

5. ALERT DELIVERY:
   send_alert() → _format_message() → _send_telegram() OR _print_console()

6. ERROR HANDLING:
   [ANY STEP] → Exception → Log error → Continue with next token → [BACK TO LOOP]

7. SHUTDOWN:
   SIGINT/SIGTERM → _signal_handler() → self.running = False → Graceful exit
```

## 🧠 Key Decision Points

### **Volume Spike Thresholds:**
```python
# Both conditions must be true:
sigma_deviation >= 2.0  AND  z_score >= 2.0

# Minimum data requirement:
len(volume_history) >= 5 periods
```

### **Momentum Filters:**
```python
# Required filter:
current_price > ema_21

# Optional filter:
ema_slope_up == True  # ema[-3] < ema[-2] < ema[-1]
```

### **EMA Calculation Strategy:**
```python
# Data availability strategy:
if len(prices) >= 21:
    use_ema_calculation()      # True EMA
else:
    use_sma_fallback()         # Simple Moving Average
```

### **Two-Stage Performance Optimization:**
```python
# Stage 1: Fast volume check (existing data)
if volume_spike_detected():
    # Stage 2: Fetch candles only for spike tokens (slower)
    if momentum_confirmed():
        send_alert()  # High-probability signal
```

### **Rate Limiting Strategy:**
```python
# 50ms delay between API calls
# Estimated ~8-10 seconds per cycle for 171 tokens
# Stage 2 only runs for volume spike tokens (efficient)
RATE_LIMIT_DELAY = 0.05
```

## 🎯 Signal Quality Improvements

### **Before (Volume Only):**
```python
volume_spike → alert  # Could be bearish selling
```

### **After (Volume + Momentum):**
```python
volume_spike + price_above_ema + ema_rising → alert  # High-probability bullish breakout
```

This architecture creates **much stronger, higher-probability signals** by ensuring volume anomalies are combined with bullish price momentum - perfect for catching explosive upward moves! 🚀 