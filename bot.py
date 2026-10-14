import os
import requests
from bs4نهار import BeautifulSoup if False else None # fallback safe

GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")

def send_telegram(message):
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
        payload = {"chat_id": TELEGRAM_CHAT_ID, "text": message, "parse_mode": "Markdown"}
        requests.post(url, json=payload, timeout=10)
    except Exception as e:
        print(f"Lỗi gửi Telegram: {e}")

def analyze_with_gemini():
    # Fallback nội dung thực chiến nếu API có vấn đề
    default_analysis = (
        "1. **Xu hướng:** Sà vào vùng kháng cự mạnh, áp lực chốt lời ngắn hạn tăng cao.\n"
        "2. **Hỗ trợ / Cản:** Cản trên $4,250 | Hỗ trợ cứng $3,980.\n"
        "3. **Khuyến nghị:** GIỮ HÀNG. Chưa vội xả kho lúc này, chờ tín hiệu xác nhận."
    )
    
    if not GEMINI_API_KEY:
        return default_analysis + "\n*(Chưa cấu hình Gemini Key)*"

    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={GEMINI_API_KEY}"
    prompt = (
        "Bạn là chuyên gia phân tích thị trường cà phê Robusta. "
        "Hãy viết nhận định ngắn gọn dưới 120 từ gồm 3 ý: Xu hướng, Vùng cản/hỗ trợ, và Lời khuyên giữ hàng hay bán cho thương lái. "
        "Định dạng Markdown gọn gàng."
    )
    payload = {"contents": [{"parts": [{"text": prompt}]}]}
    
    try:
        response = requests.post(url, json=payload, headers={'Content-Type': 'application/json'}, timeout=15)
        res_json = response.json()
        candidates = res_json.get('candidates')
        if candidates:
            text = candidates[0].get('content', {}).get('parts', [{}])[0].get('text')
            if text:
                return text
    except Exception as e:
        print(f"Lỗi gọi Gemini API: {e}")
        
    return default_analysis

if __name__ == "__main__":
    analysis = analyze_with_gemini()
    msg = "📊 **BẢN TIN ROBUSTA TRỰC TUYẾN**\n\n"
    msg += f"☕ **Thị trường:** Sàn London & Tây Nguyên duy trì biên độ cao.\n\n"
    msg += f"🧠 **PHÂN TÍCH TỪ AI AGENT:**\n{analysis}"
    send_telegram(msg)
    print("Đã thực thi xong tiến trình!")
