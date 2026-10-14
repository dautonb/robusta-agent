import os
import requests
from bs4 import BeautifulSoup
import matplotlib
matplotlib.use('Agg')  # Chế độ chạy ngầm không cần màn hình hiển thị
import matplotlib.pyplot as plt

# ==========================================
# 1. THU THẬP DỮ LIỆU ĐA NGUỒN (COLLECTOR)
# ==========================================
class CoffeeDataCollector:
    
    @staticmethod
    def get_daklak_weather():
        """Lấy thời tiết Buôn Ma Thuột qua Open-Meteo API"""
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
        """Lấy giá sàn London (RM=F)"""
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
        """Cào giá xô Đắk Lắk"""
        try:
            url = "https://giacaphe.com/"
            headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
            res = requests.get(url, headers=headers, timeout=10)
            soup = BeautifulSoup(res.text, 'html.parser')
            
            for row in soup.find_all('tr'):
                cols = row.find_all('td')
                if len(cols) >= 2 and ("Đắk Lắk" in cols[0].text or "Đắc Lắc" in cols[0].text):
                    # Trả về giá dạng chuỗi (ví dụ: "98,500")
                    return cols[1].text.strip()
            return "98,500"
        except Exception:
            return "98,500"

# ==========================================
# 2. VẼ BIỂU ĐỒ TRỰC QUAN (MATPLOTLIB)
# ==========================================
def generate_market_chart(london_price, domestic_price_str):
    """Tạo ảnh biểu đồ so sánh sóng giá London & Đắk Lắk"""
    try:
        # Chuyển đổi giá xô nội địa về dạng số (triệu VNĐ/tấn)
        clean_price = domestic_price_str.replace('.', '').replace(',', '').replace('đ', '').strip()
        domestic_num = float(clean_price) / 1000 if clean_price.isdigit() else 98.5

        fig, ax1 = plt.subplots(figsize=(8, 4.5))

        categories = [f'ICE London\n({london_price:,} USD/tấn)', f'Giá Xô Đắk Lắk\n({domestic_num:.1f} trđ/tấn)']
        values = [london_price, domestic_num]
        colors = ['#1a365d', '#2f855a']

        bars = ax1.bar(categories, values, color=colors, width=0.45)

        for bar in bars:
            yval = bar.get_height()
            ax1.text(bar.get_x() + bar.get_width()/2, yval + (yval * 0.02), 
                     f'{yval:,.1f}', ha='center', va='bottom', fontweight='bold', fontsize=11)

        plt.title('DỮ LIỆU THỊ TRƯỜNG CÀ PHÊ ROBUSTA THỜI THỰC', fontsize=13, fontweight='bold', pad=15)
        plt.tight_layout()
        
        chart_path = 'market_chart.png'
        plt.savefig(chart_path, dpi=200)
        plt.close()
        return chart_path
    except Exception as e:
        print(f"⚠️ Lỗi vẽ biểu đồ: {e}")
        return None

# ==========================================
# 3. PHÂN TÍCH TỪ DEEPSEEK AI
# ==========================================
def analyze_market_with_deepseek(market_data):
    api_key = os.environ.get("DEEPSEEK_API_KEY")
    if not api_key:
        return "⚠️ Lỗi: Chưa cấu hình DEEPSEEK_API_KEY"

    prompt = f"""
    Bạn là Hội đồng Chiến lược Giao dịch Cà phê Robusta quy mô 100-500 tấn tại Đắk Lắk.
    
    [DỮ LIỆU THỜI THỰC]
    - Sàn London (ICE): {market_data['london']['price']} USD/tấn (Biến động: {market_data['london']['change']}%)
    - Giá xô nội địa Đắk Lắk: {market_data['domestic']} VNĐ/kg
    - Thời tiết Buôn Ma Thuột: {market_data['weather']['temp']}°C, Độ ẩm {market_data['weather']['humidity']}%, Mưa {market_data['weather']['rain']}mm
    
    Yêu cầu xuất báo cáo theo định dạng Commercial Trading Plan (ngắn gọn, sắc bén):
    1. **Xu hướng & Tâm lý**: Sàn London + Tâm lý găm/xả hàng tại Đắk Lắk.
    2. **Khuyến nghị Hành động**: Tỷ lệ Spot vs Forward (Ví dụ: Chốt 30% Spot, Giữ 70% Forward).
    3. **Ngưỡng Rủi ro**: Vùng giá mục tiêu để chốt tiếp.
    """

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
        if res.status_code != 200:
            return f"⚠️ DeepSeek báo lỗi HTTP {res.status_code}: {res.text[:100]}"
            
        data = res.json()
        return data['choices'][0]['message']['content']
    except Exception as e:
        return f"⚠️ Lỗi kết nối DeepSeek: {str(e)}"

# ==========================================
# 4. GỬI ẢNH KÈM TEXT VỀ TELEGRAM
# ==========================================
def send_telegram_photo(photo_path, caption):
    bot_token = os.environ.get("TELEGRAM_BOT_TOKEN")
    chat_id = os.environ.get("TELEGRAM_CHAT_ID")
    
    if not bot_token or not chat_id:
        print("⚠️ Chưa cấu hình Token hoặc Chat ID")
        return

    # Nếu có ảnh biểu đồ -> Gửi sendPhoto kèm caption
    if photo_path and os.path.exists(photo_path):
        url = f"https://api.telegram.org/bot{bot_token}/sendPhoto"
        with open(photo_path, 'rb') as photo:
            # Telegram giới hạn caption tối đa 1024 ký tự
            short_caption = caption[:1020] if len(caption) > 1024 else caption
            payload = {'chat_id': chat_id, 'caption': short_caption, 'parse_mode': 'Markdown'}
            files = {'photo': photo}
            requests.post(url, data=payload, files=files, timeout=20)
    else:
        # Phương án dự phòng: Gửi tin nhắn text thường nếu vẽ ảnh lỗi
        url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
        payload = {'chat_id': chat_id, 'text': caption, 'parse_mode': 'Markdown'}
        requests.post(url, json=payload, timeout=10)

# ==========================================
# MAIN EXECUTION
# ==========================================
if __name__ == "__main__":
    print("🔄 Đang thu thập dữ liệu...")
    market_data = {
        "london": CoffeeDataCollector.get_london_robusta(),
        "domestic": CoffeeDataCollector.get_vietnam_domestic_prices(),
        "weather": CoffeeDataCollector.get_daklak_weather()
    }
    
    print("📊 Đang vẽ biểu đồ trực quan...")
    chart_file = generate_market_chart(market_data['london']['price'], market_data['domestic'])
    
    print("🤖 Đang phân tích chiến lược DeepSeek...")
    analysis = analyze_market_with_deepseek(market_data)
    
    final_caption = f"📊 **BÁO CÁO CHIẾN LƯỢC ROBUSTA DAK LAK**\n\n{analysis}"
    
    print("🚀 Đang gửi báo cáo về Telegram...")
    send_telegram_photo(chart_file, final_caption)
    print("✅ Hoàn tất!")
