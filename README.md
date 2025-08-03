# 🚨 Hyperliquid Volume Spike + Momentum Detector

Advanced Python bot that monitors Hyperliquid perpetual futures for **volume spikes combined with price momentum** - detecting high-probability explosive moves before they happen.

## 🎯 Features

- **Volume Spike Detection** - Statistical analysis using sigma deviation and Z-score
- **EMA Momentum Filtering** - Price above 21-EMA with optional slope confirmation  
- **Multi-Timeframe Analysis** - 24h volume + 1h price momentum confluence
- **Smart Filtering** - Only alerts when volume anomaly + bullish momentum align
- **Telegram alerts** with fallback to console output
- **Rate limiting** compliance with Hyperliquid API
- **Graceful error handling** and automatic retries
- **Minimal dependencies** and clean modular code

## 📋 Requirements

- Python 3.7+
- Internet connection
- Optional: Telegram bot token for alerts

## 🚀 Quick Start

1. **Create virtual environment**:
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure environment** (optional):
   ```bash
   cp .env.example .env
   # Edit .env with your settings
   ```

4. **Run the bot**:
   ```bash
   python main.py
   ```

5. **Stop the bot**:
   ```bash
   # Press Ctrl+C for graceful shutdown
   ```

## ⚙️ Configuration

Environment variables (all optional with sensible defaults):

| Variable | Default | Description |
|----------|---------|-------------|
| `BOT_TOKEN` | None | Telegram bot token (get from @BotFather) |
| `CHAT_ID` | None | Telegram chat ID for alerts |
| `SIGMA_THRESHOLD` | 2.0 | Minimum sigma deviation to trigger alert |
| `Z_SCORE_THRESHOLD` | 2.0 | Minimum Z-score to trigger alert |
| `UPDATE_INTERVAL_MINUTES` | 15 | Minutes between monitoring cycles |
| `VOLUME_PERIODS` | 20 | Number of historical periods for volume analysis |
| **`EMA_PERIODS`** | **21** | **EMA calculation period for momentum** |
| **`PRICE_ABOVE_EMA_REQUIRED`** | **true** | **Require price above EMA for alerts** |
| **`EMA_SLOPE_FILTER_ENABLED`** | **true** | **Optional EMA uptrend confirmation** |

## 📊 How It Works

### **Two-Stage Filtering System:**

**Stage 1: Volume Spike Detection**
1. Fetch 24h volume data for all tokens (excluding BTC/ETH)
2. Calculate sigma deviation and Z-score vs 20-period average
3. Identify tokens with abnormal volume (σ ≥ 2.0 AND Z ≥ 2.0)

**Stage 2: Momentum Confirmation** *(Only for volume spike tokens)*
4. Fetch 1h candle data for spike tokens
5. Calculate 21-period EMA on close prices
6. Confirm price above EMA (bullish momentum)
7. Optional: Verify EMA slope trending upward

**Alert Trigger:** `Volume Spike + Price > EMA + (Optional) EMA Rising`

## 🔧 Algorithm Details

### **Volume Analysis:**
- **Sigma Deviation**: `(current_volume - mean_volume) / std_volume`
- **Z-Score**: Same as sigma deviation in this implementation
- **Threshold**: Both σ ≥ 2.0 AND Z ≥ 2.0

### **Momentum Analysis:**
- **EMA Calculation**: `EMA[t] = α × Price[t] + (1-α) × EMA[t-1]` where `α = 2/(21+1)`
- **Price Filter**: `current_price > ema_21`
- **Slope Filter**: `ema[-3] < ema[-2] < ema[-1]` (strictly increasing)

### **Fallback Strategy:**
- **21+ periods**: Use proper EMA calculation
- **5-20 periods**: Use Simple Moving Average (SMA)
- **<5 periods**: Skip token (insufficient data)

## 🎯 Signal Quality

This approach creates **high-probability signals** by combining:

- **Statistical Volume Anomaly** - Unusual trading activity
- **Technical Price Momentum** - Price breaking above key moving average
- **Trend Confirmation** - Short-term uptrend established

**Result**: Much stronger signals than volume-only or price-only approaches!

## 🛡️ Safety Features

- **Two-stage filtering** - Efficient API usage (only fetch candles for volume spikes)
- **Rate limiting** with 50ms delays between API calls
- **Retry logic** for failed API requests
- **Graceful shutdown** on SIGINT/SIGTERM
- **Error handling** with automatic recovery per token
- **Configuration validation** on startup
- **Progress tracking** during analysis cycles

## 📱 Telegram Setup (Optional)

1. Create bot with @BotFather on Telegram
2. Get bot token and your chat ID
3. Set `BOT_TOKEN` and `CHAT_ID` in `.env` file

Without Telegram setup, alerts print to console.

## 🚨 Alert Format

```
🚨 VOLUME SPIKE + MOMENTUM DETECTED
Token: $SOL
Volume: $3,400,000
Sigma Dev: 2.34
Z-Score: 2.34
Price: $43.20
EMA-21: $41.80
Momentum: ✅ Above EMA
Trend: ✅ EMA Rising
Analysis: 19 vol periods, 23 price periods
```

## 🏃‍♂️ Running in Production

```bash
# Run with nohup (remember to activate venv first)
source venv/bin/activate
nohup python main.py > bot.log 2>&1 &

# Or use systemd, Docker, etc.
```

## 🔄 Development & Testing

```bash
# Activate virtual environment
source venv/bin/activate

# Run for testing (will output to console)
python main.py

# Monitor logs in another terminal
tail -f bot.log
```

## ⚡ Performance

- **~8-10 seconds per cycle** for 171 tokens
- **Stage 1**: Fast volume analysis (existing API data)  
- **Stage 2**: Only fetches 1h candles for tokens with volume spikes
- **Memory efficient** with rolling window storage
- **Rate limit compliant** - 1200 requests/minute max

## 📝 Notes

- **Virtual environment required** on macOS/externally managed Python environments
- **Minimum 5 periods** of data required before analysis begins
- **BTC and ETH excluded** as specified in requirements  
- **Two-stage filtering** optimizes API usage and performance
- **EMA vs SMA** - Automatically uses best method based on available data
- **First few cycles** will show "No spikes detected" while accumulating historical data
- **Volume spikes alone** may include bearish selling - momentum filter ensures bullish signals
- **High-probability signals** - Combines multiple timeframes and analysis methods

## 🎓 Trading Context

This bot is designed to catch the **early stages of explosive moves** by detecting:

1. **Unusual volume activity** (smart money moving)
2. **Price momentum confirmation** (breakout above key level)  
3. **Trend alignment** (short-term uptrend in place)

Perfect for identifying tokens before they make significant upward moves! 🚀 