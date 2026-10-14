import os
import requests
from datetime import datetime

GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")

def get_robusta_data():
    try:
        # Sử dụng API trực tiếp của Yahoo Finance với Header giả lập trình duyệt để tránh bị chặn trên GitHub
        url = "https://query1.finance.yahoo.com/v8/finance/chart/RM=F?interval=1d&range=1mo"
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
        res = requests.get(url, headers=headers, timeout=10)
        data_json = res.json()
        
        result = data_json['chart']['result'][0]
        timestamps = result['timestamp']
        quote = result['indicators']['quote'][0]
        closes = quote['close']
        highs = quote['high']
        lows = quote['low']
        
        # Lọc bỏ các giá trị trống (None)
        valid_data = []
        for t, c, h, l in zip(timestamps, closes, highs, lows):
            if c is not None and h is not None and l is not None:
                valid_data.append((t, c, h, l))
                
        if len(valid_data) < 2:
            return None
            
        latest_price = valid_data[-1][1]
        prev_price = valid_data[-2][1]
        change_pct = ((latest_price - prev_price) / prev_price) * 100
        high_price = valid_data[-1][2]
        low_price = valid_data[-1][3]
        
        # Lấy lịch sử 5 phiên gần nhất
        history_str = ""
        for t, c, h, l in valid_data[-5:]:
            dt = datetime.fromtimestamp(t)
            history_str += f"- {dt.strftime('%d/%m')}: {c:.0f} USD\n"

        return {
            "latest": round(latest_price),
            "change_pct": round(change_pct, 2),
            "high": round(high_price),
            "low": round(low_price),
            "history": history_str
        }
    except Exception as e:
        print(f"Lỗi lấy giá: {e}")
        return None

def analyze_with_gemini(data):
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={GEMINI_API_KEY}"
    
    prompt = f"""
    Bạn là một chuyên gia phân tích thị trường cà phê Robusta. 
    Dữ liệu giá sàn London (RM=F) mới nhất:
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
        msg = f"📊 **BẢN TIN ROBUSTA LONDON (RM=F)**\n"
        msg += f"• Giá hiện tại: **{data['latest']} USD/tấn** ({data['change_pct']}%)\n"
        msg += f"• Biên độ: {data['low']} - {data['high']} USD\n\n"
        msg += f"🧠 **PHÂN TÍCH TỪ AI AGENT:**\n{analysis}"
        send_telegram(msg)
    else:
        send_telegram("⚠️ Không thể cập nhật dữ liệu giá Robusta hôm nay do lỗi kết nối dữ liệu.")
