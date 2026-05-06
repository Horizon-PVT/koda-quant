import pandas as pd
from pathlib import Path
from datetime import datetime, UTC


def generate_reflection(csv_file="trade_history.csv", out_file="trading_memory.md"):
    p = Path(csv_file)
    if not p.exists():
        Path(out_file).write_text("# Trading Memory\n\nNo trade history found.\n", encoding="utf-8")
        return

    df = pd.read_csv(p)
    if df.empty or "pnl" not in df.columns:
        Path(out_file).write_text("# Trading Memory\n\nTrade file empty or missing pnl column.\n", encoding="utf-8")
        return

    total = len(df)
    winrate = (df["pnl"] > 0).mean() * 100
    avg_pnl = df["pnl"].mean()
    gross = df["pnl"].sum()

    content = f"""# Trading Memory ({datetime.now(UTC).isoformat()})

- Total trades: {total}
- Winrate: {winrate:.2f}%
- Avg PnL: {avg_pnl:.5f}
- Net PnL: {gross:.5f}

## Reflection
- Nếu winrate < 50%: giảm risk_multiplier và tăng z_threshold.
- Nếu winrate > 65%: có thể mở rộng nhẹ risk_multiplier.
- Kiểm tra các khung giờ hoặc regime gây lỗ nhiều để chặn chiến thuật kém hiệu quả.
"""
    Path(out_file).write_text(content, encoding="utf-8")


if __name__ == "__main__":
    generate_reflection()
