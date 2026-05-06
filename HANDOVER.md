# KODA QUANT HFT - BÀN GIAO DỰ ÁN (HANDOVER)

## Trạng thái Hệ thống (V8 - Active)
Dự án đã được nâng cấp từ một Chatbot Agent thô sơ lên thành hệ thống **Prop Firm HFT (High-Frequency Trading) Engine**, hoàn thành 100% các lõi quan trọng nhất:

1. **V4 OFI Engine:** Sử dụng Order Flow Imbalance đa tầng (5 levels) quét qua WebSocket 100ms.
2. **V5 Sniper Mode:** Chỉ bắn lệnh khi Z-Score > 2.5. Sử dụng thuật toán Kelly Position Sizing và Dynamic TP/SL (dựa trên Spread & Volatility).
3. **V6 Adaptive Learning:** Lõi `adaptive_engine.py` cho phép hệ thống tự động co giãn Z-Score Threshold và Khối lượng lệnh dựa trên Winrate của những lệnh gần nhất.
4. **V6 Data Pipeline:** Hệ thống tự động ghi nhật ký vào `trade_history.csv` gồm 10 cột chuẩn Quant để chuẩn bị cho Data Mining.
5. **V7 Regime Detection:** Tự động đo độ giật giá (Micro-Volatility) để nhận diện xu hướng (TREND) hoặc thị trường đi ngang (CHOP), từ đó khóa các chiến thuật không phù hợp.

## Các File Quan Trọng:
*   `ai_brain.py`: Bộ não trung tâm chạy luồng WebSocket và Execution.
*   `adaptive_engine.py`: Module tự tiến hóa, sinh ra file `adaptive_config.json`.
*   `analyze_logs.py`: Script dùng để chạy thống kê sau này khi đã thu thập đủ Data (do chuyên gia AI bên ngoài cấp).
*   `trade_history.csv`: Nơi chứa dòng tiền thực.
*   `index.html` & `app.js`: Giao diện Dashboard hiển thị thông số và Logs trực tiếp (Đọc từ `chat_logs.json`).
*   `conversation_history.txt`: Toàn bộ đoạn chat chi tiết giải thích quá trình xây dựng từ V1 -> V7.

## Nhiệm vụ Tiếp theo (Khi Sếp mở máy lên tại nơi công tác):
1. Treo máy chạy `python ai_brain.py` trong 1-2 ngày để lấy ít nhất 50-100 lệnh vào `trade_history.csv`.
2. Chạy `python analyze_logs.py` để tìm ra **Sniper Zone** (Vùng in tiền).
3. Nếu muốn lên **V8**, cần xây dựng tính năng "Lắng nghe Binance User Data Stream" để lấy PnL (Lãi/Lỗ) Realtime, phục vụ cho **Bayesian Winrate Update**.

---
> [!NOTE]
> Ghi chú cho AI kế nhiệm: Đọc `conversation_history.txt` và file này để bắt nhịp ngay lập tức. Sếp đang dùng tư duy của một Quỹ Giao Dịch Chuyên Nghiệp. Không được tư vấn lệch hướng sang các chỉ báo tĩnh (Candlesticks, RSI, MACD).


## V8 Update (2026-05-05)
- Dashboard đã kéo dữ liệu thị trường thật từ Binance REST `ticker/24hr` (BTC last price + 24h change) để giám sát thời gian thực ngay trên top-nav.
- DOM vẫn lấy real-time WebSocket 100ms từ Binance như các bản trước.


## Cách mở Dashboard local
1. Chạy `python start_dashboard.py` (hoặc `npm start`, hoặc double-click `start_dashboard.bat` trên Windows).
2. Mở trình duyệt: `http://localhost:8000/index.html`.
3. Nếu cổng 8000 bận, server sẽ tự nhảy sang cổng kế tiếp (vd: 8001) và in link mới trong terminal.


## TradingAgents Integration Roadmap (Implemented)
- Sprint A (Macro Filter): thêm `tradingagents_adapter.py` chạy nền, xuất bias BULL/BEAR/NEUTRAL và gate tín hiệu ngược bias trong `ai_brain.py`.
- Sprint B (Risk Veto): thêm `risk_manager.py` với lớp `PortfolioRiskManager` để chặn lệnh khi drawdown cao hoặc thua liên tiếp.
- Sprint C (Memory Reflection): thêm `memory_reflection.py` để tổng kết cuối ngày từ `trade_history.csv` sang `trading_memory.md`.
