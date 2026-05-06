# KODA QUANT V8 - COMPLETE SYSTEM HANDOVER
> **Last Updated:** 2026-05-06 | **Status:** LIVE (Production) | **Author:** Antigravity AI + Human Operator

---

## 🏗️ Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                    KODA QUANT V8 ENGINE                      │
│                                                              │
│  ┌──────────────┐  ┌──────────────┐  ┌───────────────────┐  │
│  │  ai_brain.py │  │ Dashboard    │  │ Adaptive Engine   │  │
│  │  (CORE)      │  │ (Web UI)     │  │ (Self-Learning)   │  │
│  │              │  │              │  │                   │  │
│  │ • OFI Engine │  │ • index.html │  │ • adaptive_engine │  │
│  │ • Regime Det │  │ • app.js     │  │ • analyze_logs    │  │
│  │ • Execution  │  │ • style.css  │  │ • memory_reflect  │  │
│  │ • UserData WS│  │ • API proxy  │  │                   │  │
│  └──────┬───────┘  └──────┬───────┘  └─────────┬─────────┘  │
│         │                 │                     │            │
│  ┌──────▼─────────────────▼─────────────────────▼─────────┐  │
│  │              Binance Futures API                        │  │
│  │  • Market WS (100ms depth)  • User Data Stream         │  │
│  │  • REST (account/positions) • Order Execution           │  │
│  └────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

---

## 📁 File Structure & Purpose

| File | Purpose | Status |
|------|---------|--------|
| `ai_brain.py` | **Core engine.** WebSocket OFI scanner, signal detection, order execution, User Data Stream tracker, adaptive hook. Entry point: `python ai_brain.py` | ✅ LIVE |
| `start_dashboard.py` | **HTTP server + API proxy.** Serves dashboard UI and proxies `/api/portfolio` to Binance securely (HMAC-signed). Port 8001. | ✅ LIVE |
| `index.html` | Dashboard UI — Live Portfolio panel, Order Book DOM, AI Agent chat room, TradingView chart tab. | ✅ LIVE |
| `app.js` | Frontend JS — polls `/api/portfolio` every 3s, renders live balance/positions, WebSocket DOM feed, agent chat polling. | ✅ LIVE |
| `style.css` | Dark-theme quant dashboard styling with CSS custom properties. | ✅ LIVE |
| `adaptive_engine.py` | Self-learning module. Reads `trade_history.csv`, recalculates winrate, adjusts `z_threshold` and `risk_multiplier`. Outputs `adaptive_config.json`. | ✅ LIVE |
| `kronos_adapter.py` | Regime detection adapter (TREND/CHOP/NEUTRAL classification). | ✅ LIVE |
| `tradingagents_adapter.py` | Macro agent — background thread polling macro bias (BULL/BEAR/NEUTRAL) to filter signals. | ✅ LIVE |
| `risk_manager.py` | Portfolio risk manager — veto layer blocking trades during drawdown or consecutive losses. | ✅ LIVE |
| `memory_reflection.py` | End-of-day summary generator. Reads `trade_history.csv` → writes `trading_memory.md`. Run separately. | ✅ Ready |
| `analyze_logs.py` | Post-hoc statistical analysis. Run after collecting 50+ trades to find optimal Sniper Zones. | ✅ Ready |
| `trade_history.csv` | Live trade log with 10 columns: timestamp, z_ofi, spread, volatility, price, signal, tp_pct, sl_pct, strategy, pnl. | Auto-generated |
| `chat_logs.json` | Rolling 15-message agent chat log consumed by dashboard. | Auto-generated |
| `adaptive_config.json` | Current adaptive parameters (z_threshold, risk_multiplier, winrate). | Auto-generated |
| `macro_filter.json` | Current macro bias state from TradingAgents adapter. | Auto-generated |
| `.env` | API keys: `QWEN_API_KEY`, `BINANCE_API_KEY`, `BINANCE_SECRET_KEY`. **NEVER commit this.** | ✅ Configured |
| `requirements.txt` | Python dependencies: openai, pandas, python-dotenv, numpy, websockets. | ✅ Created |
| `setup.bat` | One-click install + launch script for Windows. | ✅ Created |
| `conversation_history.txt` | Full dev history from V1→V7 (238KB). | Reference only |

---

## 🔧 Engine Versions (Evolution History)

| Version | Feature | Key Innovation |
|---------|---------|----------------|
| V1-V3 | Basic chatbot + candlestick signals | Prototype, no edge |
| V4 | Multi-level OFI Engine | 5-level order book imbalance via WebSocket 100ms |
| V5 | Sniper Mode | Z-Score > 2.5 filter, Kelly sizing, Dynamic TP/SL |
| V6 | Adaptive Learning | Auto-tune z_threshold & risk_multiplier from CSV winrate |
| V7 | Regime Detection | TREND/CHOP/NEUTRAL classification, strategy gating |
| **V8** | **Live Production** | **User Data Stream, real PnL tracking, API proxy dashboard, Macro filter, Risk veto, Self-learning loop** |

---

## 🧠 Signal Generation Pipeline

```
Raw Order Book (100ms) 
    → Multi-Level OFI (5 depths)
    → Exponential Decay Weighting (λ=0.8)
    → Z-Score Calculation
    → Regime Detection (TREND/CHOP/NEUTRAL)
    → Signal Filter:
        • Absorption: Z > 2.5 AND price flat → Counter-trade
        • Momentum: Z > 3.0 AND price moving → Trend-follow
    → Macro Gate (BULL blocks SELL, BEAR blocks BUY)
    → Risk Manager Veto (drawdown/consecutive loss check)
    → Dynamic TP/SL (spread-based + volatility-based hybrid)
    → Kelly Position Sizing (1% equity risk * adaptive multiplier)
    → Execution (Binance Futures Market Order)
    → User Data Stream catches fill → logs real PnL to CSV
    → Every 5 fills → Adaptive Engine recalculates and reloads config
```

---

## 🔑 Security & Credentials

- **API Key Permissions:** Read + Enable Futures ONLY (no Spot, no Withdrawal)
- **IP Whitelist:** Restricted to operator's IP on Binance side
- **Dashboard Proxy:** `start_dashboard.py` signs requests server-side — Secret Key never exposed to browser
- **`.gitignore`** excludes `.env` from version control

---

## 🚀 How to Run

### Quick Start (Windows)
```bash
# Option 1: One-click
double-click setup.bat

# Option 2: Manual
cd "C:\Users\ADMIN\.gemini\antigravity\scratch\multi-agent-high-frequency-trading-(hft)"
pip install -r requirements.txt
python start_dashboard.py    # Terminal 1 — Dashboard on :8001
python ai_brain.py           # Terminal 2 — HFT Engine
python memory_reflection.py  # Terminal 3 — (Optional) End-of-day summary
```

### Dashboard Access
- **Local:** `http://localhost:8001/index.html`
- **Features:** Live BTC price, Order Book DOM, AI Agent chat, Live Portfolio (balance + positions + PnL)

---

## ⚠️ Known Limitations & TODO

| Item | Status | Notes |
|------|--------|-------|
| Bot stops when PC shuts down | ❌ Pending | Solution: Deploy to VPS (Alibaba Cloud server ready at 47.250.174.44) |
| IP whitelist must match runtime IP | ⚠️ Manual | If deploying to VPS, update Binance API IP whitelist to VPS public IP |
| `trade_history.csv` PnL column | ⚠️ Partial | Real PnL filled via User Data Stream; older mock entries show 0.0 |
| Bayesian Winrate (full) | 🔮 Future | Current adaptive is rule-based. Full Bayesian requires more data |
| Heatmap 3D visualization | 🔮 Future | Planned for V9 after sufficient CSV data collected |
| Auto-retrain ML model | 🔮 Future | Need 500+ trades for statistical significance |

---

## 💰 Current Account Status (2026-05-06)
- **Binance Account:** Tom_Horizon
- **Futures Wallet:** ~75 USDT (pending transfer from Funding → USDⓈ-M)
- **Leverage:** 10x
- **Max Daily Drawdown:** 3% of equity
- **Max Trades/Day:** 10
- **Risk per Trade:** 1% of equity × adaptive multiplier

---

> [!NOTE]
> **For AI successors (Codex, etc.):** This system uses ORDER FLOW microstructure analysis, NOT traditional indicators (RSI, MACD, Bollinger). Do not suggest adding lagging indicators. The edge comes from reading raw order book pressure at 100ms resolution. Read `conversation_history.txt` for full architectural rationale from V1→V8.
