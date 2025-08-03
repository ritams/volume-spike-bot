# 💼 Project Title: Hyperliquid Volume Spike + EMA Momentum Bot

## 📌 Objective

Monitor tokens on Hyperliquid with high trading activity (curated dynamically), detect **1-hour volume spikes** using Z-score, filter them using **EMA‑21-based momentum**, and send **Telegram alerts** when a high-probability breakout condition is met.

---

# 🧱 Architecture Overview

```
hypervolume_bot/
├── config/
│   └── .env.example            # Config template (tokens, thresholds)
├── data/
│   └── strict_list.json        # Auto-saved curated token list
├── core/
│   ├── strict_list.py          # Curate strict tokens
│   ├── fetch.py                # Fetch candles from Hyperliquid
│   ├── compute.py              # Z-score, EMA, EMA slope
│   ├── logic.py                # Alert condition check
│   ├── alert.py                # Telegram integration
│   └── config.py               # Load from .env and CLI
├── main.py                     # CLI entrypoint
├── requirements.txt
└── README.md
```

---

# 🧩 Core Functional Requirements

## ✅ 1. Strict List Curation

### Description:

Dynamically generate a list of reliable tokens from Hyperliquid using 24h volume.

### Logic:

* Endpoint:
  `POST https://api.hyperliquid.xyz/info`
  Request body: `{ "type": "metaAndAssetCtxs" }`

* Response contains:

  * `universe[i].name` → token symbol
  * `assetCtxs[i].dayNtlVlm` → 24h notional volume (string)

* Filter logic:

  * Exclude `"BTC"` and `"ETH"`
  * Keep tokens with `float(dayNtlVlm) >= 5_000_000`

### Output:

* Save result to `data/strict_list.json`

```json
["SOL", "ARB", "LINK", "TIA", "MATIC", "APT", "LDO"]
```

### Human Configuration:

* Volume threshold (default: `$5M`) configurable via `.env` or CLI

---

## ✅ 2. Candle Data Fetching

### Endpoint:

`POST https://api.hyperliquid.xyz/history/candles`

### Payload:

```json
{
  "coin": "SOL",
  "interval": "1h",
  "startTime": <timestamp_ms>,
  "endTime": <timestamp_ms>
}
```

### Logic:

* Fetch 21 1-hour candles per token
* Fields used: `close`, `volume`, `timestamp`
* Compute:

  * `volumes = [c['volume'] for c in candles]`
  * `closes = [c['close'] for c in candles]`

---

## ✅ 3. Statistical Analysis

### Z-Score (on volume):

```python
z = (volumes[-1] - mean(volumes[:-1])) / std(volumes[:-1])
```

### EMA-21 (on close prices):

Use standard exponential moving average (weights decreasing with age). Use pandas or compute manually:

```python
ema[t] = alpha * close[t] + (1 - alpha) * ema[t-1]
alpha = 2 / (N + 1), where N = 21
```

### EMA Slope Filter:

Optional. Passes only if:

```python
ema[-3] < ema[-2] < ema[-1]
```

---

## ✅ 4. Alert Conditions

### Required Conditions:

```python
z_score >= z_threshold AND
current_close > ema[-1]
```

### Optional Condition:

```python
ema[-3] < ema[-2] < ema[-1]   # slope filter (if enabled)
```

---

## ✅ 5. Price Change Calculation

* Use **Hyperliquid candle close prices** only
* Compute % change from:

  * `price_1h_ago = closes[-2]`
  * `price_now = closes[-1]`
  * `pct_change = (price_now - price_1h_ago) / price_1h_ago * 100`

Do same for 4h by sampling closes\[-5].

---

## ✅ 6. Alert Message + Telegram Integration

### Format:

```
🚨 VOLUME SPIKE DETECTED
Token: $SOL
Volume: $3.4M | Z: 2.34
Price: $43.20 > EMA(21): $41.80 ✅
Trend: EMA Slope Up ✅
Price Change: 1h +2.3%, 4h +6.5%
```

### Telegram Integration:

* Use standard Telegram Bot API:

```python
requests.post(f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage", data={
  "chat_id": CHAT_ID,
  "text": message
})
```

---

# ⚙️ 7. Runtime Configuration

## Environment Variables (.env)

```env
BOT_TOKEN=xxxxxxxxx
CHAT_ID=xxxxxxxxx
Z_THRESHOLD=2.0
VOLUME_THRESHOLD=5000000
SLOPE_FILTER=true
INTERVAL_MINUTES=15
```

## CLI Flags

All config values can be overridden via CLI:

```bash
python main.py --interval 15 --z-threshold 2.0 --slope-filter false
```

---

# 🔁 8. Scheduler Loop (main.py)

### Runtime Loop:

1. Load config from `.env` and CLI
2. Fetch current strict list (save JSON)
3. For each token:

   * Fetch 21 1h candles
   * Compute Z-score, EMA, slope
   * If alert conditions pass → send alert
4. Wait `INTERVAL_MINUTES` → repeat

---

# 🧪 9. Development Notes

### Dependencies:

```txt
requests
python-dotenv
pandas
numpy
```

### Runtime:

* Python 3.9+
* Works headlessly
* Logs errors and alerts to console

---

# 🧑‍💻 Human Interventions Required

| Step | What to Do                                       |
| ---- | ------------------------------------------------ |
| ✅    | Create Telegram bot via @BotFather               |
| ✅    | Store `BOT_TOKEN` and `CHAT_ID` in `.env`        |
| ✅    | Configure alert parameters in `.env` or CLI      |
| ✅    | Review strict list JSON if desired               |
| ⛔    | No Hyperliquid login, account, or API key needed |

---

