# KODA QUANT V8.5 — PRODUCTION HANDOVER
> **Status**: ✅ ALL SAFEGUARDS VERIFIED — APPROVED FOR PAPER TRADING PHASE A
> **Last Audit**: 2026-05-06 by Antigravity + Codex cross-review (5 rounds)
> **Repo**: https://github.com/Horizon-PVT/koda-quant

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────┐
│                    KODA QUANT V8.5                       │
├─────────────────────────────────────────────────────────┤
│  5 Async Tasks (asyncio.gather)                         │
│  ├── task1: Order Book WebSocket (100ms depth5)         │
│  ├── task2: ListenKey Keepalive (50min loop)            │
│  ├── task3: User Data Stream (PnL + ACCOUNT_UPDATE)     │
│  ├── task4: Position Sync REST (60s fallback)           │
│  └── task5: Daily Reset Loop (UTC 00:00)                │
├─────────────────────────────────────────────────────────┤
│  Signal Pipeline                                        │
│  OFI 5-Level → Decay → Z-Score → Regime → Signal       │
│  → Macro Filter → 5 Guards → Risk Manager → Execute    │
├─────────────────────────────────────────────────────────┤
│  Execution Pipeline                                     │
│  MARKET Entry (idempotent) → Slippage Check             │
│  → TP/SL Bracket Orders → Emergency Close if fail       │
├─────────────────────────────────────────────────────────┤
│  Self-Learning                                          │
│  Realized PnL → CSV → Adaptive Engine (every 5 trades)  │
│  → Adjust z_threshold + risk_multiplier                 │
└─────────────────────────────────────────────────────────┘
```

---

## Production Safeguards (Codex-Verified)

### 5 Pre-Trade Guards
| # | Guard | Threshold | Action |
|---|-------|-----------|--------|
| 1 | Spread Guard | > 0.12% | Skip trade |
| 2 | Max Open Positions | 1 | Skip trade |
| 3 | Daily Loss Circuit Breaker | -2.5% equity ($1.88) | Kill switch ON |
| 4 | Consecutive Loss Cooldown | 3 losses → 60min pause | Cooldown timer |
| 5 | Min R:R Ratio | < 1.2 | Skip trade |

### Execution Guards
| Guard | Description |
|-------|-------------|
| Order Validation | Check `orderId` in response before proceeding |
| Slippage Guard | If fill slippage > 0.08% → close immediately |
| avgPrice=0 Handling | Flag as UNKNOWN_FILL, skip slippage check |
| TP/SL Bracket | TAKE_PROFIT_MARKET + STOP_MARKET on Binance |
| Bracket Fail Safety | Both TP+SL fail → Emergency MARKET close |
| Order Idempotency | `newClientOrderId` prevents double-entry |
| Log Differentiation | [FILLED] vs [REJECTED] vs [BLOCKED] vs [FAILED] |

### Risk State Tracking
| State | Source |
|-------|--------|
| `equity` | Updated by User Data Stream (realized PnL) |
| `open_positions` | ACCOUNT_UPDATE event + REST sync every 60s |
| `daily_realized_loss` | Accumulated from negative PnL events |
| `consecutive_losses` | Incremented on loss, reset on win |
| `cooldown_until` | 15min after 1 loss, 60min after 2+ losses |

---

## Phase A Config (live_config.json)

| Parameter | Value |
|-----------|-------|
| Leverage | 5x |
| Risk/trade | 0.5% ($0.38) |
| Max margin/position | 20% equity ($15) |
| Max trades/day | 6 |
| Max consecutive losses | 3 |
| Daily loss stop | -2.5% ($1.88) |
| Spread guard | > 0.12% |
| Slippage guard | > 0.08% |
| Min R:R ratio | 1.2 |
| Max open positions | 1 |

### Phase Progression
- **Phase A** (Week 1): 5x, 0.5% risk — current
- **Phase B** (Week 2-3): 5x, 0.75% risk — requires 100 settled trades + 14 days no breach
- **Phase C**: 10x — requires 1 month stable log

---

## File Map

| File | Purpose |
|------|---------|
| `ai_brain.py` | Core engine: OFI, signals, execution, risk, WebSocket |
| `live_config.json` | Production thresholds (Phase A/B/C) |
| `adaptive_engine.py` | Self-learning z_threshold + risk_multiplier tuning |
| `adaptive_config.json` | Current adaptive parameters (auto-generated) |
| `tradingagents_adapter.py` | Macro bias adapter (Kronos + safe fallback) |
| `kronos_adapter.py` | Binance OHLCV macro regime detection |
| `risk_manager.py` | Portfolio-level risk evaluation |
| `start_dashboard.py` | Dashboard server (127.0.0.1, file blocking, API proxy) |
| `index.html` / `style.css` / `app.js` | Dashboard UI (XSS-safe, auto-reconnect) |
| `trade_history.csv` | Trade log (auto-generated) |
| `chat_logs.json` | Real-time agent communication log |
| `.env` | API keys (never committed) |

---

## Security

- Dashboard binds `127.0.0.1` only
- Sensitive files blocked from HTTP: `.env`, `trade_history.csv`, `adaptive_config.json`
- All chat rendering uses `textContent` (zero innerHTML for runtime data)
- API signing via HMAC-SHA256 server-side
- WebSocket exponential backoff (3s → 6s → 12s → cap 30s)

---

## Audit Trail (V8.1 → V8.5.1)

| Version | Changes | Reviewer |
|---------|---------|----------|
| V8.1 | TP/SL bracket orders, order validation, XSS fix, dashboard hardening | Antigravity |
| V8.2 | Exponential backoff, zero innerHTML, typed exceptions | Codex P2 |
| V8.3 | 5 guards, phased config, spread/RR/daily stop | Codex thresholds |
| V8.4 | ACCOUNT_UPDATE position sync + REST fallback | Codex critical bug |
| V8.5 | Slippage guard, daily reset UTC, order idempotency | Codex pre-live |
| V8.5.1 | avgPrice edge-case, log differentiation | Codex final notes |

---

## GO LIVE Checklist

- [ ] Paper trading 14+ days, 100+ settled trades
- [ ] Profit factor > 1.2, max drawdown < 5%
- [ ] Verify API key: Futures Only, no Withdraw, IP whitelisted
- [ ] Test kill switch + emergency close with dry-run
- [ ] Confirm TP/SL visible on Binance after entry
- [ ] Clock synced (NTP), WebSocket reconnect stable
- [ ] Telegram/Discord alerts for errors and risk breaches
- [ ] Start live with 0.25-0.5% risk, increase only after 1 week stable
