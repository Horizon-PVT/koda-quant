import pandas as pd
import json
import os

CONFIG_FILE = "adaptive_config.json"

# =============================
# LOAD / SAVE CONFIG
# =============================
def load_config():
    try:
        with open(CONFIG_FILE, "r") as f:
            return json.load(f)
    except:
        return {
            "z_threshold": 2.5,
            "risk_multiplier": 1.0,
            "last_winrate": 0.0,
            "avg_pnl": 0.0,
            "total_trades": 0
        }

def save_config(config):
    with open(CONFIG_FILE, "w") as f:
        json.dump(config, f, indent=4)

# =============================
# MAIN ADAPTIVE FUNCTION
# =============================
def update_adaptive_rules(csv_file="trade_history.csv"):
    if not os.path.exists(csv_file):
        print("⚠️ No trade_history.csv found yet. Skipping adaptive update.")
        return load_config()
        
    df = pd.read_csv(csv_file)
    
    # P1 FIX: Validate CSV schema
    required_cols = ['pnl', 'z_ofi', 'spread', 'volatility', 'price', 'signal']
    missing = [c for c in required_cols if c not in df.columns]
    if missing:
        print(f"⚠️ CSV missing columns: {missing}. Skipping adaptive update.")
        return load_config()
    
    # P1 FIX: Filter out unsettled trades (PnL still 0.0 = not yet closed)
    df_settled = df[df['pnl'] != 0.0].copy()
    
    if len(df_settled) < 5:
        print(f"⚠️ Only {len(df_settled)} settled trades (need 5+). Skipping.")
        return load_config()
    
    # Use only last 50 settled trades (rolling window for faster adaptation)
    df_recent = df_settled.tail(50)
    
    # ===== BASIC METRICS =====
    total_trades = len(df_recent)
    winrate = (df_recent['pnl'] > 0).mean()
    avg_pnl = df_recent['pnl'].mean()
    
    # ===== LOAD CURRENT CONFIG =====
    config = load_config()
    z_threshold = config.get("z_threshold", 2.5)
    risk_multiplier = config.get("risk_multiplier", 1.0)
    
    # =============================
    # 1. ADAPT Z-SCORE THRESHOLD
    # =============================
    if winrate < 0.5:
        z_threshold += 0.2  # khó → trade ít lại
    elif winrate > 0.65:
        z_threshold -= 0.1  # market đẹp → mở rộng
        
    # Clamp
    z_threshold = max(2.0, min(z_threshold, 4.0))
    
    # =============================
    # 2. ADAPT POSITION SIZE
    # =============================
    if winrate < 0.5:
        risk_multiplier *= 0.8  # giảm size
    elif winrate > 0.65:
        risk_multiplier *= 1.1  # tăng nhẹ
        
    # Clamp
    risk_multiplier = max(0.5, min(risk_multiplier, 1.5))
    
    # =============================
    # SAVE NEW CONFIG
    # =============================
    new_config = {
        "z_threshold": round(z_threshold, 2),
        "risk_multiplier": round(risk_multiplier, 2),
        "last_winrate": round(winrate, 3),
        "avg_pnl": round(avg_pnl, 5),
        "total_trades": total_trades
    }
    
    save_config(new_config)
    print("\n🔥 ADAPTIVE ENGINE UPDATED CONFIG:")
    print(new_config)
    return new_config

if __name__ == "__main__":
    update_adaptive_rules()
