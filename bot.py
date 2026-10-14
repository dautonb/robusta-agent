import os
import requests
from bs4 import BeautifulSoup
import datetime
import random
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

# ==========================================
# 1. BỘ THU THẬP DỮ LIỆU ĐA NGUỒN (COLLECTOR)
# ==========================================
class CoffeeDataCollector:
    
    @staticmethod
    def get_daklak_weather():
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
        try:
            url = "https://query1.finance.yahoo.com/v8/finance/chart/RM=F?interval=1d&range=1d"
            res = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=8).json()
            meta = res['chart']['result'][0]['meta']
            price = meta.get('regularMarketPrice', 0)
            if price > 0:
                prev_close = meta.get('previousClose', price)
                change_pct = round(((price - prev_close) / prev_close) * 100, 2) if prev_close else 0.0
                return {"price": price, "change": change_pct}
        except Exception:
            pass
        return {"price": 3450, "change": 0.0}

    @staticmethod
    def get_vietnam_domestic_prices():
        try:
            url = "https://giacaphe.com/"
            headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
            res = requests.get(url, headers=headers, timeout=10)
            soup = BeautifulSoup(res.text, 'html.parser')
            for row in soup.find_all('tr'):
                cols = row.find_all('td')
                if len(cols) >= 2 and ("Đắk Lắk" in cols[0].text or "Đắc Lắc" in cols[0].text):
                    return cols[1].text.strip()
            return "98,500"
        except Exception:
            return "98,500"

# ==========================================
# 2. VẼ BIỂU ĐỒ TRADINGVIEW (DARK MODE + FALLBACK)
# ==========================================
def generate_tradingview_style_chart(current_price=3450):
    try:
        url = "https://query1.finance.yahoo.com/v8/finance/chart/RM=F?range=1mo&interval=1d"
        res = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=8).json()
        result = res['chart']['result'][0]
        timestamps = result['timestamp']
        closes = result['indicators']['quote'][0]['close']
        
        data = [(datetime.datetime.fromtimestamp(ts), c) for ts, c in zip(timestamps, closes) if c is not None]
        if not data:
            raise ValueError("Empty data")
        dates, prices = zip(*data)
    except Exception:
        base_date = datetime.datetime.now() - datetime.timedelta(days=30)
        dates = [base_date + datetime.timedelta(days=i) for i in range(31)]
        prices = [current_price]
        for _ in range(30):
            prices.append(prices[-1] + random.uniform(-15, 15))

    plt.style.use('dark_background')
    fig, ax = plt.subplots(figsize=(10, 5))
    
    ax.plot(dates, prices, color='#2962FF', linewidth=2.5, label='ICE Robusta')
    ax.fill_between(dates, prices, min(prices) * 0.99, color='#2962FF', alpha=0.15)
    
    ax.set_title('ICE LONDON ROBUSTA - XU HƯỚNG 30 NGÀY (TRADINGVIEW)', color='#d1d4dc', fontsize=11, fontweight='bold', pad=15)
    ax.grid(True, color='#2a2e39', linestyle='--', linewidth=0.5)
    ax.set_facecolor('#131722')
    fig.patch.set_facecolor('#131722')
    
    plt.xticks(rotation=20, color='#787b86', fontsize=8)
    plt.yticks(color='#787b86', fontsize=8)
    for spine in ax.spines.values():
        spine.set_color('#2a2e39')

    plt.tight_layout()
    chart_path = 'tradingview_chart.png'
    plt.savefig(chart_path, dpi=200, facecolor=fig.get_facecolor())
    plt.close()
    return chart_path

# ==========================================
# 3. PHÂN TÍCH CHIẾN LƯỢC DEEPSEEK AI
# ==========================================
def analyze_market_with_deepseek(market_data):
    api_key = os.environ.get("DEEPSEEK_API_KEY")
    if not api_key:
        return "⚠️ Lỗi: Chưa cấu hình DEEPSEEK_API_KEY"

    prompt = f"""
    Bạn là Giám đốc Lượng hóa Rủi ro và Chiến lược Thương mại cho kho cà phê Robusta (100–500 tấn) tại Đắk Lắk.
    
    [DỮ LIỆU THỜI THỰC]
    - Sàn London (ICE): {market_data['london']['price']} USD/tấn (Biến động: {market_data['london']['change']}%)
    - Giá xô Đắk Lắk: {market_data['domestic']} VNĐ/kg
    - Thời tiết Buôn Ma Thuột: {market_data['weather']['temp']}°C, Độ ẩm {market_data['weather']['humidity']}%, Mưa {market_data['weather']['rain']}mm
    
    Hãy lập BẢN LỆNH GIAO DỊCH CHUYÊN NGHIỆP nhưng BÌNH DÂN HÓA THUẬT NGỮ theo đúng cấu trúc sau:

    🎯 **1. ĐỌC BÀI THỊ TRƯỜNG (Không dùng từ viết tắt/tiếng Anh)**
    - Thế giới (Sàn London): [Nêu giá, xu hướng dòng tiền và ý nghĩa con số này]
    - Trong nước (Đắk Lắk): [Tâm lý mua/bán của đại lý và nông dân, tình trạng nguồn cung]
    - Chất lượng & Thời tiết: [Cảnh báo độ ẩm, nguy cơ mốc/sương mai nếu giữ kho lâu]

    💼 **2. KẾ HOẠCH BÁN HÀNG & DÒNG TIỀN (Cho kho 100 - 500 tấn)**
    - **BÁN TIỀN TƯƠI (Spot)**: [Tỷ lệ %] — [Nêu rõ lý do và mức giá cần chốt]
    - **CHỐT GIÁ TRƯỚC (Forward/Giao xa)**: [Tỷ lệ %] — [Mức giá mục tiêu và điều kiện ký hợp đồng]
    - **DỰ PHÒNG KHO (Giữ lại)**: [Tỷ lệ %] — [Mục đích giữ để làm gì]

    🛡️ **3. VẠCH ĐỎ AN TOÀN (Kỷ luật quản trị rủi ro)**
    - **Điểm xả hàng cắt lỗ**: [Giá xô rơi xuống mức nào thì bắt buộc phải xả sạch để bảo toàn vốn]
    - **Điểm chốt lời ngắt đọt**: [Giá London/Nội địa chạm mức nào thì chốt nấc tiếp theo]
    
    📌 **4. LỆNH ĐIỀU HÀNH 1 DÒNG**
    [Viết một câu hành động dứt khoát nhất cho chủ kho]
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
# 4. GỬI BÁO CÁO QUA TELEGRAM
# ==========================================
def send_telegram_report(photo_path, report_text):
    bot_token = os.environ.get("TELEGRAM_BOT_TOKEN")
    chat_id = os.environ.get("TELEGRAM_CHAT_ID")
    
    if not bot_token or not chat_id:
        print("⚠️ Chưa cấu hình Token hoặc Chat ID")
        return

    if photo_path and os.path.exists(photo_path):
        url_photo = f"https://api.telegram.org/bot{bot_token}/sendPhoto"
        with open(photo_path, 'rb') as photo:
            payload = {'chat_id': chat_id, 'caption': "📉 **BIỂU ĐỒ XU HƯỚNG SÀN LONDON (30 NGÀY)**", 'parse_mode': 'Markdown'}
            files = {'photo': photo}
            requests.post(url_photo, data=payload, files=files, timeout=20)

    url_msg = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    payload = {
        'chat_id': chat_id, 
        'text': f"📊 **BÁO CÁO CHIẾN LƯỢC ROBUSTA DAK LAK**\n\n{report_text}", 
        'parse_mode': 'Markdown'
    }
    requests.post(url_msg, json=payload, timeout=10)

# ==========================================
# MAIN EXECUTION
# ==========================================
if __name__ == "__main__":
    print("🔄 Đang thu thập dữ liệu...")
    london_data = CoffeeDataCollector.get_london_robusta()
    domestic_price = CoffeeDataCollector.get_vietnam_domestic_prices()
    weather_data = CoffeeDataCollector.get_daklak_weather()
    
    market_data = {
        "london": london_data,
        "domestic": domestic_price,
        "weather": weather_data
    }
    
    print("📈 Đang vẽ biểu đồ TradingView...")
    chart_file = generate_tradingview_style_chart(london_data['price'])
    
    print("🤖 Đang phân tích chiến lược...")
    analysis = analyze_market_with_deepseek(market_data)
    
    print("🚀 Đang gửi báo cáo về Telegram...")
    send_telegram_report(chart_file, analysis)
    print("✅ Hoàn tất!")
