import pandas as pd
import numpy as np

# =============================
# LOAD DATA
# =============================
try:
    df = pd.read_csv("trade_history.csv")
    
    if df.empty or len(df) < 5:
        print("⚠️ Not enough data in trade_history.csv to analyze. Let the bot run for a while.")
        exit(0)
except FileNotFoundError:
    print("❌ trade_history.csv not found. Please run ai_brain.py first.")
    exit(1)

# Convert timestamp → datetime
df['timestamp'] = pd.to_datetime(df['timestamp'], unit='s')
df['hour'] = df['timestamp'].dt.hour

# Win / Loss
df['win'] = df['pnl'] > 0

# =============================
# BINNING
# =============================

# Z-score bins
df['z_bin'] = pd.cut(df['z_ofi'].abs(), bins=[0,2,2.5,3,4,10])

# Spread bins
df['spread_bin'] = pd.cut(df['spread'], bins=5)

# Hour bins (group 3h)
df['hour_bin'] = (df['hour'] // 3) * 3

# =============================
# ANALYSIS FUNCTION
# =============================

def analyze_group(group_cols):
    grouped = df.groupby(group_cols, observed=True).agg(
        trades=('pnl','count'),
        winrate=('win','mean'),
        avg_pnl=('pnl','mean')
    ).reset_index()

    # Filter: đủ số lệnh (Giảm xuống 5 để test tạm, sau này đổi thành 30)
    grouped = grouped[grouped['trades'] >= 5]

    # Score = winrate + profit bias
    grouped['score'] = grouped['winrate'] * grouped['avg_pnl']

    return grouped.sort_values(by='score', ascending=False)

# =============================
# FIND SNIPER ZONE
# =============================

result = analyze_group(['z_bin','spread_bin','hour_bin'])

top_zones = result.head(5)

print("\n🔥 TOP SNIPER ZONES:\n")
print(top_zones)

# =============================
# EXPORT RESULT
# =============================
if not top_zones.empty:
    top_zones.to_csv("sniper_zones.csv", index=False)
    print("\n✅ Saved to sniper_zones.csv")
else:
    print("\n⚠️ No optimal zones found yet. Need more data.")
