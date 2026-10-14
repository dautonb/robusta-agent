import os
import requests
from bs4 import BeautifulSoup
import datetime
import random
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

# ==========================================
# 1. THU THẬP DỮ LIỆU ĐA NGUỒN (THẾ GIỚI & BRAZIL)
# ==========================================
class CoffeeDataCollector:
    
    @staticmethod
    def get_daklak_weather():
        """Lấy thời tiết Buôn Ma Thuột"""
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
        """Lấy giá sàn London Robusta (ICE London - RM=F)"""
        try:
            url = "https://query1.finance.yahoo.com/v8/finance/chart/RM=F?interval=1d&range=1mo"
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
    def get_brazil_arabica():
        """Lấy giá sàn Arabica New York (ICE US - KC=F) đại diện nguồn cung Brazil"""
        try:
            url = "https://query1.finance.yahoo.com/v8/finance/chart/KC=F?interval=1d&range=1d"
            res = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=8).json()
            meta = res['chart']['result'][0]['meta']
            price_cents = meta.get('regularMarketPrice', 0) # Giá tính theo US Cent/lb
            if price_cents > 0:
                # Quy đổi từ Cent/lb sang USD/tấn (1 lb = 0.453592 kg, 1 tấn = 2204.62 lbs)
                price_usd_ton = round(price_cents * 22.0462, 1)
                prev_close = meta.get('previousClose', price_cents)
                change_pct = round(((price_cents - prev_close) / prev_close) * 100, 2) if prev_close else 0.0
                return {"price_cents": price_cents, "price_usd_ton": price_usd_ton, "change": change_pct}
        except Exception:
            pass
        return {"price_cents": 240.0, "price_usd_ton": 5291.0, "change": 0.0}

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
                    return cols[1].text.strip()
            return "98,500"
        except Exception:
            return "98,500"

# ==========================================
# 2. PHÂN TÍCH KỸ THUẬT (MA20 & RSI)
# ==========================================
def calculate_technical_indicators(prices):
    prices_arr = np.array(prices, dtype=float)
    
    ma20 = []
    for i in range(len(prices_arr)):
        if i < 19:
            ma20.append(np.mean(prices_arr[:i+1]))
        else:
            ma20.append(np.mean(prices_arr[i-19:i+1]))
            
    deltas = np.diff(prices_arr)
    seed = deltas[:14]
    up = seed[seed >= 0].sum() / 14
    down = -seed[seed < 0].sum() / 14
    rs = up / down if down != 0 else 0
    rsi = [100.0 - (100.0 / (1.0 + rs))]
    
    for delta in deltas[14:]:
        up = (up * 13 + (delta if delta > 0 else 0)) / 14
        down = (down * 13 + (-delta if delta < 0 else 0)) / 14
        rs = up / down if down != 0 else 0
        rsi.append(100.0 - (100.0 / (1.0 + rs)))
    
    rsi_full = [50.0] * 14 + rsi
    return ma20, rsi_full

# ==========================================
# 3. VẼ BIỂU ĐỒ 2 TẦNG TRADINGVIEW
# ==========================================
def generate_advanced_technical_chart(current_price=3450):
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
        prices = list(prices)
    except Exception:
        base_date = datetime.datetime.now() - datetime.timedelta(days=30)
        dates = [base_date + datetime.timedelta(days=i) for i in range(31)]
        prices = [current_price]
        for _ in range(30):
            prices.append(prices[-1] + random.uniform(-15, 15))

    ma20, rsi = calculate_technical_indicators(prices)

    plt.style.use('dark_background')
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 7), gridspec_kw={'height_ratios': [3, 1]}, sharex=True)
    fig.patch.set_facecolor('#131722')

    # Tầng 1: Giá & MA20
    ax1.set_facecolor('#131722')
    ax1.plot(dates, prices, color='#2962FF', linewidth=2, label='ICE Robusta')
    ax1.plot(dates, ma20, color='#FF9800', linewidth=1.5, linestyle='--', label='MA20')
    ax1.fill_between(dates, prices, min(prices) * 0.99, color='#2962FF', alpha=0.1)
    ax1.set_title('ICE LONDON ROBUSTA - XU HƯỚNG KỸ THUẬT (MA20 + RSI)', color='#d1d4dc', fontsize=11, fontweight='bold', pad=10)
    ax1.grid(True, color='#2a2e39', linestyle='--', linewidth=0.5)
    ax1.legend(loc='upper left', fontsize=8, facecolor='#1e222d', edgecolor='none')
    for spine in ax1.spines.values():
        spine.set_color('#2a2e39')

    # Tầng 2: RSI
    ax2.set_facecolor('#131722')
    ax2.plot(dates, rsi, color='#AB47BC', linewidth=1.5, label='RSI (14)')
    ax2.axhline(70, color='#ef5350', linestyle=':', alpha=0.7)
    ax2.axhline(30, color='#26a69a', linestyle=':', alpha=0.7)
    ax2.fill_between(dates, rsi, 70, where=(np.array(rsi) >= 70), color='#ef5350', alpha=0.2)
    ax2.fill_between(dates, rsi, 30, where=(np.array(rsi) <= 30), color='#26a69a', alpha=0.2)
    ax2.set_ylim(0, 100)
    ax2.grid(True, color='#2a2e39', linestyle='--', linewidth=0.5)
    ax2.legend(loc='upper left', fontsize=8, facecolor='#1e222d', edgecolor='none')
    for spine in ax2.spines.values():
        spine.set_color('#2a2e39')

    plt.xticks(rotation=15, color='#787b86', fontsize=8)
    plt.tight_layout()
    chart_path = 'advanced_technical_chart.png'
    plt.savefig(chart_path, dpi=200, facecolor=fig.get_facecolor())
    plt.close()
    return chart_path, prices[-1], ma20[-1], rsi[-1]

# ==========================================
# 4. PHÂN TÍCH CHIẾN LƯỢC TOÀN CẦU VỚI DEEPSEEK
# ==========================================
def analyze_market_with_deepseek(market_data, tech_indicators):
    api_key = os.environ.get("DEEPSEEK_API_KEY")
    if not api_key:
        return "⚠️ Lỗi: Chưa cấu hình DEEPSEEK_API_KEY"

    # Tính tỷ lệ chênh lệch Arabica / Robusta
    arabica_price_ton = market_data['arabica']['price_usd_ton']
    robusta_price_ton = market_data['london']['price']
    arbitrage_gap = arabica_price_ton - robusta_price_ton

    prompt = f"""
    Bạn là Giám đốc Lượng hóa Rủi ro và Chiến lược Thương mại cho kho cà phê Robusta (100–500 tấn) tại Đắk Lắk.
    
    [DỮ LIỆU THỊ TRƯỜNG THẾ GIỚI & TOÀN CẦU]
    - Sàn London (Robusta): {robusta_price_ton} USD/tấn (Biến động: {market_data['london']['change']}%)
    - Chỉ báo Kỹ thuật London: MA20 = {tech_indicators['ma20']:.1f} USD, RSI(14) = {tech_indicators['rsi']:.1f}
    - Sàn New York / Brazil (Arabica): {market_data['arabica']['price_cents']} US Cent/lb (Quy đổi: {arabica_price_ton} USD/tấn, Biến động: {market_data['arabica']['change']}%)
    - Chênh lệch Arabica vs Robusta: {arbitrage_gap:.1f} USD/tấn
    
    [DỮ LIỆU NỘI ĐỊA ĐẮK LẮK]
    - Giá xô Đắk Lắk: {market_data['domestic']} VNĐ/kg
    - Thời tiết Buôn Ma Thuột: {market_data['weather']['temp']}°C, Độ ẩm {market_data['weather']['humidity']}%, Mưa {market_data['weather']['rain']}mm
    
    Hãy lập BẢN LỆNH GIAO DỊCH CHUYÊN NGHIỆP, RÕ RÀNG, DỄ HIỂU theo cấu trúc sau:

    🌍 **1. THẾ TRẬN THỊ TRƯỜNG TOÀN CẦU**
    - **Nguồn cung Brazil (Arabica) & Tương quan Arabica/Robusta:** [Đánh giá giá Arabica Brazil ảnh hưởng gì đến nhu cầu Robusta Việt Nam. Chênh lệch giá làm các nhà rang xay chọn Robusta hay Arabica?]
    - **Sàn London (Kỹ thuật MA20, RSI):** [Giá Robusta đang khỏe hay yếu hơn đường MA20, dòng tiền có bị quá mua/quá bán không]
    - **Đắk Lắk & Kho bãi:** [Tâm lý nông dân găm/xả hàng và nguy cơ chất lượng kho]

    💼 **2. KẾ HOẠCH BÁN HÀNG & DÒNG TIỀN (Cho kho 100 - 500 tấn)**
    - **BÁN TIỀN TƯƠI (Spot):** [Tỷ lệ %] — [Mức giá chốt lời cụ thể]
    - **CHỐT GIÁ TRƯỚC (Forward):** [Tỷ lệ %] — [Mức giá mục tiêu và điều kiện ký hợp đồng]
    - **DỰ PHÒNG KHO:** [Tỷ lệ %] — [Mục đích giữ lại]

    🛡️ **3. VẠCH ĐỎ AN TOÀN (KỶ LUẬT CẮT LỖ & CHỐT LỜI)**
    - **Điểm cắt lỗ bắt buộc:** [Ngưỡng giá xô/London thủng mốc kỹ thuật nào thì xả gấp]
    - **Điểm chốt lời nấc tiếp theo:** [Mức giá mục tiêu khi dòng tiền bứt phá]
    
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
# 5. GỬI BÁO CÁO QUA TELEGRAM
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
            payload = {'chat_id': chat_id, 'caption': "🌐 **BIỂU ĐỒ KỸ THUẬT LONDON & THỊ TRƯỜNG TOÀN CẦU**", 'parse_mode': 'Markdown'}
            files = {'photo': photo}
            requests.post(url_photo, data=payload, files=files, timeout=20)

    url_msg = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    payload = {
        'chat_id': chat_id, 
        'text': f"📊 **BÁO CÁO CHIẾN LƯỢC ROBUSTA (TOÀN CẦU & ĐẮK LẮK)**\n\n{report_text}", 
        'parse_mode': 'Markdown'
    }
    requests.post(url_msg, json=payload, timeout=10)

# ==========================================
# MAIN EXECUTION
# ==========================================
if __name__ == "__main__":
    print("🔄 Đang thu thập dữ liệu toàn cầu (London, Brazil, Đắk Lắk)...")
    london_data = CoffeeDataCollector.get_london_robusta()
    brazil_data = CoffeeDataCollector.get_brazil_arabica()
    domestic_price = CoffeeDataCollector.get_vietnam_domestic_prices()
    weather_data = CoffeeDataCollector.get_daklak_weather()
    
    market_data = {
        "london": london_data,
        "arabica": brazil_data,
        "domestic": domestic_price,
        "weather": weather_data
    }
    
    print("📈 Đang tính toán kỹ thuật (MA20, RSI) và vẽ biểu đồ 2 tầng...")
    chart_file, current_p, ma20_val, rsi_val = generate_advanced_technical_chart(london_data['price'])
    
    tech_indicators = {
        "ma20": ma20_val,
        "rsi": rsi_val
    }
    
    print("🤖 Đang phân tích chiến lược cùng DeepSeek...")
    analysis = analyze_market_with_deepseek(market_data, tech_indicators)
    
    print("🚀 Đang gửi báo cáo về Telegram...")
    send_telegram_report(chart_file, analysis)
    print("✅ Hoàn tất!")
