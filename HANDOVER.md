# KODA QUANT HFT - BÀN GIAO DỰ ÁN (HANDOVER)

## Trạng thái Hệ thống (V7)
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
