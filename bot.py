import os
import requests
from bs4 import BeautifulSoup

GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")

def get_robusta_data():
    try:
        # Cào trực tiếp từ giacaphe.com - trang chuyên về giá cà phê nội địa và London
        url = "https://giacaphe.com/"
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
        res = requests.get(url, headers=headers, timeout=15)
        soup = BeautifulSoup(res.text, 'html.parser')
        
        # Gom toàn bộ nội dung văn bản chứa thông tin giá trên trang chủ
        main_content = ""
        for p in soup.select('table, .box-content, p, div'):
            t = p.get_text(strip=True)
            if "London" in t or "Đắk Lắk" in t or "giá cà phê" in t.lower():
                main_content += t + "\n"
                
        return {
            "raw_text": main_content[:4000] # Truyền nội dung thô để AI tự phân tích
        }
    except Exception as e:
        print(f"Lỗi lấy giá: {e}")
        return None

def analyze_with_gemini(data):
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={GEMINI_API_KEY}"
    
    prompt = f"""
    Bạn là một chuyên gia phân tích thị trường cà phê Robusta. 
    Dưới đây là dữ liệu mới nhất được cào từ trang giacaphe.com:
    {data['raw_text']}

    Hãy đọc dữ liệu trên, tự động tìm mức giá sàn London và giá cà phê nội địa Đắk Lắk mới nhất, sau đó đưa ra bản phân tích ngắn gọn (dưới 150 từ) gồm 3 phần:
    1. Giá Robusta London & Giá nội địa mới nhất tìm được.
    2. Nhận định xu hướng ngắn hạn.
    3. Khuyên người thu mua nên GIỮ HÀNG hay CHỐT LỜI TỪNG PHẦN.
    Định dạng Markdown gọn gàng để gửi qua tin nhắn Telegram.
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
    if data and data['raw_text']:
        analysis = analyze_with_gemini(data)
        msg = f"📊 **BẢN TIN THỊ TRƯỜNG CAFE**\n\n"
        msg += f"🧠 **PHÂN TÍCH TỪ AI AGENT:**\n{analysis}"
        send_telegram(msg)
    else:
        send_telegram("⚠️ Không thể cập nhật dữ liệu giá Robusta hôm nay do lỗi kết nối nguồn tin.")
