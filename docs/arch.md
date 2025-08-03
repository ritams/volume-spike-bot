# 🏗️ Architecture & Execution Flow

Complete execution flow and logic breakdown for the Hyperliquid Volume Spike Detector Bot.

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
│hyperliquid_     │    │ volume_         │    │ alert_          │
│client.py        │    │ analyzer.py     │    │ system.py       │
│ API Client      │    │ Statistics      │    │ Notifications   │
└─────────────────┘    └─────────────────┘    └─────────────────┘
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
    └─ Print warning if Telegram not configured
    
    # Step 2: Initialize components
    self.client = HyperliquidClient()     # API client with rate limiting
    self.analyzer = VolumeAnalyzer()      # Volume statistics engine
    self.alerts = AlertSystem()           # Telegram/console alerts
    self.running = True                   # Control flag
    
    # Step 3: Setup signal handlers for graceful shutdown
    signal.signal(SIGINT, self._signal_handler)
    signal.signal(SIGTERM, self._signal_handler)
```

### **2. Main Monitoring Loop (`VolumeSpikeBot.run()`)**

```python
def run():
    """Main bot loop - runs indefinitely until stopped"""
    
    print("🚀 Bot Starting...")
    print(f"Config: σ≥{SIGMA_THRESHOLD}, Z≥{Z_SCORE_THRESHOLD}")
    
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
            ├─ Analyze each token for volume spikes
            ├─ Send alerts for tokens meeting thresholds
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

### **3. Single Monitoring Cycle (`VolumeSpikeBot.run_cycle()`)**

```python
def run_cycle():
    """Execute one complete monitoring cycle"""
    
    print(f"🔍 [{current_time}] Fetching token data...")
    
    # STEP 1: Get current market data
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
    
    # STEP 2: Filter tokens by criteria
    filtered_tokens = self._filter_tokens(tokens)
    │
    └─ Filter logic:
       ├─ Remove tokens with volume < $1000 (inactive/delisted)
       ├─ Remove tokens with price <= 0 (invalid data)
       └─ Return clean list for analysis
    
    print(f"📊 Analyzing {len(filtered_tokens)} tokens...")
    
    # STEP 3: Analyze each token for volume spikes
    alerts_sent = 0
    for token in filtered_tokens:
        if self._check_volume_spike(token):
            alerts_sent += 1
    
    # STEP 4: Print cycle summary
    if alerts_sent > 0:
        print(f"🚨 Sent {alerts_sent} volume spike alerts")
    else:
        print("✅ No significant volume spikes detected")
```

### **4. Volume Spike Detection (`VolumeSpikeBot._check_volume_spike()`)**

```python
def _check_volume_spike(token):
    """Core detection logic - the heart of the bot"""
    
    name = token['name']
    volume = token['volume_24h']
    
    # STEP 1: Update historical data
    self.analyzer.update_volume(name, volume)
    │
    └─ calls: VolumeAnalyzer.update_volume()
       │
       ├─ Add current volume to rolling window (deque)
       ├─ Window size = VOLUME_PERIODS (default: 20)
       ├─ Automatically drops oldest when full
       └─ Maintains separate history per token
    
    # STEP 2: Check if we have enough data for analysis
    if not self.analyzer.has_sufficient_data(name):
        return False  # Need at least 5 periods
    
    # STEP 3: Calculate statistics
    stats = self.analyzer.calculate_stats(name, volume)
    │
    └─ calls: VolumeAnalyzer.calculate_stats()
       │
       ├─ Get historical volumes (excluding current)
       ├─ Calculate: mean_volume = average of historical data
       ├─ Calculate: std_volume = standard deviation
       ├─ Calculate: sigma_dev = (current - mean) / std
       ├─ Calculate: z_score = same as sigma_dev
       ├─ Return None if std_volume == 0 (avoid division by zero)
       └─ Return {sigma_deviation, z_score, mean_volume, current_volume, periods_analyzed}
    
    if not stats:
        return False  # Skip if calculation failed
    
    # STEP 4: Check alert thresholds
    sigma_trigger = stats['sigma_deviation'] >= SIGMA_THRESHOLD  # Default: 2.0
    z_score_trigger = stats['z_score'] >= Z_SCORE_THRESHOLD      # Default: 2.0
    
    # STEP 5: Send alert if both conditions met
    if sigma_trigger and z_score_trigger:
        alert_data = {**token, **stats}  # Merge token + stats data
        self.alerts.send_alert(alert_data)
        │
        └─ calls: AlertSystem.send_alert()
           │
           ├─ Format message with token data
           ├─ Try Telegram if configured
           ├─ Fallback to console if Telegram fails
           └─ Return success/failure status
        
        return True  # Alert sent
    
    return False  # No alert needed
```

## 🔧 Component Deep Dive

### **HyperliquidClient (`hyperliquid_client.py`)**

```python
class HyperliquidClient:
    """Handles all Hyperliquid API communication"""
    
    def __init__():
        self.session = requests.Session()  # Reuse connections
        self.last_request_time = 0         # Rate limiting tracker
    
    def _rate_limit():
        """Ensure 50ms between requests (1200/min max)"""
        elapsed = time.time() - self.last_request_time
        if elapsed < 0.05:  # 50ms
            time.sleep(0.05 - elapsed)
        self.last_request_time = time.time()
    
    def _post(endpoint, data, retries=1):
        """Make API request with retry logic"""
        self._rate_limit()  # Respect rate limits
        
        for attempt in range(retries + 1):
            try:
                response = session.post(url, json=data, timeout=10)
                response.raise_for_status()
                return response.json()
            except Exception as e:
                if attempt == retries:
                    print(f"API request failed: {e}")
                    return None
                time.sleep(1)  # Brief pause before retry
    
    def get_universe_and_volumes():
        """Get all token data from Hyperliquid"""
        
        # Call metaAndAssetCtxs endpoint
        data = self._post("info", {"type": "metaAndAssetCtxs"})
        
        if not data or len(data) != 2:
            return None
        
        universe, asset_contexts = data
        tokens = []
        
        # Parse each token
        for i, token_info in enumerate(universe["universe"]):
            name = token_info["name"]
            
            # Skip BTC/ETH as per requirements
            if name in ["BTC", "ETH"]:
                continue
            
            # Extract volume and price from asset context
            asset_ctx = asset_contexts[i]
            volume_24h = float(asset_ctx["dayNtlVlm"])
            price = float(asset_ctx["markPx"])
            
            tokens.append({
                "name": name,
                "volume_24h": volume_24h, 
                "price": price
            })
        
        return tokens
```

### **VolumeAnalyzer (`volume_analyzer.py`)**

```python
class VolumeAnalyzer:
    """Statistical analysis engine for volume data"""
    
    def __init__(periods=20):
        self.periods = periods
        # Rolling window storage per token
        self.volume_history = defaultdict(lambda: deque(maxlen=periods))
    
    def update_volume(token, volume):
        """Add new volume data point"""
        self.volume_history[token].append(volume)
        # Automatically drops oldest when maxlen reached
    
    def has_sufficient_data(token):
        """Check if we have enough data for meaningful analysis"""
        return len(self.volume_history[token]) >= 5
    
    def calculate_stats(token, current_volume):
        """Calculate sigma deviation and Z-score"""
        
        history = list(self.volume_history[token])
        
        # Use historical data excluding current for baseline
        if len(history) == self.periods:
            baseline_volumes = np.array(history[:-1])  # Exclude current
        else:
            baseline_volumes = np.array(history)       # Use all available
        
        if len(baseline_volumes) == 0:
            return None
        
        # Statistical calculations
        mean_volume = np.mean(baseline_volumes)
        std_volume = np.std(baseline_volumes)
        
        if std_volume == 0:  # Avoid division by zero
            return None
        
        # Core formulas
        sigma_dev = (current_volume - mean_volume) / std_volume
        z_score = sigma_dev  # Same calculation in this implementation
        
        return {
            "sigma_deviation": sigma_dev,
            "z_score": z_score,
            "mean_volume": mean_volume,
            "current_volume": current_volume,
            "periods_analyzed": len(baseline_volumes)
        }
```

### **AlertSystem (`alert_system.py`)**

```python
class AlertSystem:
    """Handles alert delivery via Telegram or console"""
    
    def __init__(bot_token=None, chat_id=None):
        self.bot_token = bot_token
        self.chat_id = chat_id
        self.telegram_available = bool(bot_token and chat_id)
    
    def send_alert(token_data):
        """Send volume spike alert"""
        
        # Format the alert message
        message = self._format_message(token_data)
        │
        └─ Format:
           🚨 VOLUME SPIKE DETECTED
           Token: $SOL
           Volume: $3,400,000
           Sigma Dev: 2.34
           Z-Score: 2.34
           Price: $43.20
           Analysis periods: 19
        
        # Try Telegram first, fallback to console
        if self.telegram_available:
            return self._send_telegram(message)
        else:
            self._print_console(message)
            return True
    
    def _send_telegram(message):
        """Send via Telegram Bot API"""
        try:
            url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
            payload = {"chat_id": chat_id, "text": message}
            response = requests.post(url, json=payload, timeout=10)
            response.raise_for_status()
            return True
        except Exception as e:
            print(f"Telegram send failed: {e}")
            self._print_console(message)  # Fallback
            return False
    
    def _print_console(message):
        """Print to console with formatting"""
        print(f"\n{message}\n" + "="*50)
```

## 🔄 Data Flow Summary

```
1. STARTUP:
   main() → VolumeSpikeBot.__init__() → Config.validate()

2. MONITORING LOOP:
   run() → run_cycle() → [REPEAT EVERY 15 MINUTES]

3. EACH CYCLE:
   run_cycle() → get_universe_and_volumes() → _filter_tokens() → [FOR EACH TOKEN]

4. PER TOKEN ANALYSIS:
   _check_volume_spike() → update_volume() → calculate_stats() → [IF SPIKE] → send_alert()

5. ALERT DELIVERY:
   send_alert() → _format_message() → _send_telegram() OR _print_console()

6. ERROR HANDLING:
   [ANY STEP] → Exception → Log error → Continue/Retry → [BACK TO LOOP]

7. SHUTDOWN:
   SIGINT/SIGTERM → _signal_handler() → self.running = False → Graceful exit
```

## 🧠 Key Decision Points

### **When to Send Alerts:**
```python
# Both conditions must be true:
sigma_deviation >= 2.0  AND  z_score >= 2.0

# Minimum data requirement:
len(volume_history) >= 5 periods
```

### **Rate Limiting Strategy:**
```python
# 50ms delay between API calls
# Max 1200 requests per minute = 1 request per 50ms
RATE_LIMIT_DELAY = 0.05
```

### **Error Recovery:**
```python
# API failures: Retry once, then skip cycle
# Main loop errors: Log and retry in 30 seconds  
# Graceful shutdown: Handle SIGINT/SIGTERM
```

### **Memory Management:**
```python
# Rolling window per token: maxlen=20 periods
# Automatic cleanup of old data
# No persistent storage (in-memory only)
```

This architecture ensures **reliable, efficient, and maintainable** volume spike detection with proper error handling and graceful degradation! 🚀 