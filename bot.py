import os
import requests
import yfinance as yf

GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")

def get_robusta_data():
    try:
        ticker = yf.Ticker("RC=F")
        df = ticker.history(period="1mo")
        if df.empty:
            return None
        
        latest_price = df['Close'].iloc[-1]
        prev_price = df['Close'].iloc[-2]
        change_pct = ((latest_price - prev_price) / prev_price) * 100
        high_price = df['High'].iloc[-1]
        low_price = df['Low'].iloc[-1]
        
        last_5_days = df['Close'].tail(5).to_dict()
        days_str = "\n".join([f"- {date.strftime('%d/%m')}: {price:.0f} USD" for date, price in last_5_days.items()])

        return {
            "latest": round(latest_price),
            "change_pct": round(change_pct, 2),
            "high": round(high_price),
            "low": round(low_price),
            "history": days_str
        }
    except Exception as e:
        print(f"Lỗi lấy giá: {e}")
        return None

def analyze_with_gemini(data):
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={GEMINI_API_KEY}"
    
    prompt = f"""
    Bạn là một chuyên gia phân tích thị trường cà phê Robusta. 
    Dữ liệu giá sàn London (RC=F) mới nhất:
    - Giá đóng cửa gần nhất: {data['latest']} USD/tấn
    - Biến động: {data['change_pct']}%
    - Thấp nhất / Cao nhất phiên: {data['low']} - {data['high']} USD/tấn
    - Lịch sử 5 phiên gần đây:
    {data['history']}

    Hãy đưa ra bản phân tích ngắn gọn (dưới 150 từ) gồm 3 phần:
    1. Nhận định xu hướng kỹ thuật (Tăng/Giảm/Đi ngang).
    2. Vùng cản / Hỗ trợ ngắn hạn.
    3. Khuyên người thu mua nên GIỮ HÀNG hay CHỐT LỜI TỪNG PHẦN.
    Định dạng Markdown gọn gàng để gửi qua tin nhắn.
    """

    payload = {"contents": [{"parts": [{"text": prompt}]}]}
    headers = {'Content-Type': 'application/json'}

    try:
        response = requests.post(url, json=payload, headers=headers)
        res_json = response.json()
        return res_json['candidates'][0]['content']['parts'][0]['text']
    except Exception as e:
        print(f"Lỗi gọi Gemini: {e}")
        return "Không thể lấy phân tích từ AI."

def send_telegram(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {"chat_id": TELEGRAM_CHAT_ID, "text": message, "parse_mode": "Markdown"}
    requests.post(url, json=payload)

if __name__ == "__main__":
    data = get_robusta_data()
    if data:
        analysis = analyze_with_gemini(data)
        msg = f"📊 **BẢN TIN ROBUSTA LONDON (RC=F)**\n"
        msg += f"• Giá hiện tại: **{data['latest']} USD/tấn** ({data['change_pct']}%)\n"
        msg += f"• Biên độ: {data['low']} - {data['high']} USD\n\n"
        msg += f"🧠 **PHÂN TÍCH TỪ AI AGENT:**\n{analysis}"
        send_telegram(msg)
    else:
        send_telegram("⚠️ Không thể cập nhật dữ liệu giá Robusta hôm nay.")
