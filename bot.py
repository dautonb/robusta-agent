import os
import requests
from bs4 import BeautifulSoup

# ==========================================
# 1. BỘ THU THẬP DỮ LIỆU ĐA NGUỒN (COLLECTOR)
# ==========================================
class CoffeeDataCollector:
    
    @staticmethod
    def get_daklak_weather():
        """Lấy dữ liệu thời tiết thực tế Buôn Ma Thuột qua Open-Meteo API"""
        try:
            url = "https://api.open-meteo.com/v1/forecast?latitude=12.67&longitude=108.03&current=temperature_2m,relative_humidity_2m,precipitation"
            res = requests.get(url, timeout=10).json()
            current = res.get('current', {})
            return {
                "temp": current.get('temperature_2m', 'N/A'),
                "humidity": current.get('relative_humidity_2m', 'N/A'),
                "rain": current.get('precipitation', 0)
            }
        except Exception:
            return {"temp": "N/A", "humidity": "N/A", "rain": 0}

    @staticmethod
    def get_london_robusta():
        """Lấy giá sàn ICE London (RM=F)"""
        try:
            url = "https://query1.finance.yahoo.com/v8/finance/chart/RM=F?interval=1d&range=1d"
            res = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=10).json()
            meta = res['chart']['result'][0]['meta']
            price = meta.get('regularMarketPrice', 0)
            prev_close = meta.get('previousClose', price)
            change_pct = round(((price - prev_close) / prev_close) * 100, 2) if prev_close else 0.0
            return {"price": price, "change": change_pct}
        except Exception:
            return {"price": 0, "change": 0.0}

    @staticmethod
    def get_vietnam_domestic_prices():
        """Cào giá xô nội địa Đắk Lắk"""
        try:
            url = "https://giacaphe.com/"
            headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
            res = requests.get(url, headers=headers, timeout=10)
            soup = BeautifulSoup(res.text, 'html.parser')
            
            for row in soup.find_all('tr'):
                cols = row.find_all('td')
                if len(cols) >= 2 and ("Đắk Lắk" in cols[0].text or "Đắc Lắc" in cols[0].text):
                    return cols[1].text.strip()
            return "Đang cập nhật"
        except Exception:
            return "Đang cập nhật"

# ==========================================
# 2. PHÂN TÍCH TỪ HỘI ĐỒNG AI (DEEPSEEK)
# ==========================================
def analyze_market_with_deepseek(market_data):
    api_key = os.environ.get("DEEPSEEK_API_KEY")
    if not api_key:
        return "⚠️ Lỗi: Chưa cấu hình DEEPSEEK_API_KEY"

    prompt = f"""
    Bạn là Hội đồng Chiến lược Giao dịch Cà phê Robusta quy mô 100-500 tấn tại Đắk Lắk.
    
    [DỮ LIỆU THỜI THỰC]
    - Sàn London (ICE): {market_data['london']['price']} USD/tấn (Biến động: {market_data['london']['change']}%)
    - Giá xô nội địa Đắk Lắk: {market_data['domestic']}
    - Thời tiết Buôn Ma Thuột: {market_data['weather']['temp']}°C, Độ ẩm {market_data['weather']['humidity']}%, Mưa {market_data['weather']['rain']}mm
    
    Yêu cầu xuất báo cáo theo định dạng Commercial Trading Plan (ngắn gọn, sắc bén):
    1. Xu hướng & Tâm lý
    2. Khuyến nghị Hành động (Tỷ lệ Spot vs Forward)
    3. Ngưỡng Rủi ro (Stop-Loss / Take-Profit)
    """

    # Sửa Content-Type chuẩn application/json
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": "deepseek-chat",
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.3
    }
    
    try:
        res = requests.post("https://api.deepseek.com/v1/chat/completions", json=payload, headers=headers, timeout=30)
        
        # Kiểm tra nếu HTTP status không phải 200 (ví dụ 500, 502, 401)
        if res.status_code != 200:
            return f"⚠️ Server DeepSeek phản hồi lỗi HTTP {res.status_code}: {res.text[:100]}"
            
        data = res.json()
        return data['choices'][0]['message']['content']
        
    except requests.exceptions.JSONDecodeError:
        return f"⚠️ Lỗi: API trả về dữ liệu không đúng chuẩn JSON (Mã trả về: {res.status_code})"
    except Exception as e:
        return f"⚠️ Lỗi kết nối DeepSeek: {str(e)}"

# ==========================================
# 3. GỬI BÁO CÁO QUA TELEGRAM
# ==========================================
def send_telegram_message(text):
    bot_token = os.environ.get("TELEGRAM_BOT_TOKEN")
    chat_id = os.environ.get("TELEGRAM_CHAT_ID")
    if not bot_token or not chat_id:
        print("⚠️ Chưa cấu hình TELEGRAM_BOT_TOKEN hoặc TELEGRAM_CHAT_ID")
        return

    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": text,
        "parse_mode": "Markdown"
    }
    requests.post(url, json=payload, timeout=10)

# ==========================================
# MAIN EXECUTION
# ==========================================
if __name__ == "__main__":
    # 1. Gom dữ liệu
    market_data = {
        "london": CoffeeDataCollector.get_london_robusta(),
        "domestic": CoffeeDataCollector.get_vietnam_domestic_prices(),
        "weather": CoffeeDataCollector.get_daklak_weather()
    }
    
    # 2. Phân tích
    report = analyze_market_with_deepseek(market_data)
    
    # 3. Bắn tin nhắn
    final_message = f"📊 **BÁO CÁO CHIẾN LƯỢC ROBUSTA DAK LAK**\n\n{report}"
    send_telegram_message(final_message)
    print("✅ Đã gửi báo cáo thành công!")
