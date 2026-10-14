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
# 1. THU THẬP DỮ LIỆU ĐA NGUỒN
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
        try:
            url = "https://query1.finance.yahoo.com/v8/finance/chart/KC=F?interval=1d&range=1d"
            res = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=8).json()
            meta = res['chart']['result'][0]['meta']
            price_cents = meta.get('regularMarketPrice', 0)
            if price_cents > 0:
                price_usd_ton = round(price_cents * 22.0462, 1)
                prev_close = meta.get('previousClose', price_cents)
                change_pct = round(((price_cents - prev_close) / prev_close) * 100, 2) if prev_close else 0.0
                return {"price_cents": price_cents, "price_usd_ton": price_usd_ton, "change": change_pct}
        except Exception:
            pass
        return {"price_cents": 240.0, "price_usd_ton": 5291.0, "change": 0.0}

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
# 2. PHÂN TÍCH KỸ THUẬT & VẼ BIỂU ĐỒ 2 TẦNG
# ==========================================
def calculate_technical_indicators(prices):
    prices_arr = np.array(prices, dtype=float)
    ma20 = [np.mean(prices_arr[:i+1]) if i < 19 else np.mean(prices_arr[i-19:i+1]) for i in range(len(prices_arr))]
    
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
    
    return ma20, [50.0] * 14 + rsi

def generate_technical_chart(current_price=3450):
    try:
        url = "https://query1.finance.yahoo.com/v8/finance/chart/RM=F?range=1mo&interval=1d"
        res = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=8).json()
        result = res['chart']['result'][0]
        timestamps, closes = result['timestamp'], result['indicators']['quote'][0]['close']
        data = [(datetime.datetime.fromtimestamp(ts), c) for ts, c in zip(timestamps, closes) if c is not None]
        dates, prices = zip(*data)
        prices = list(prices)
    except Exception:
        base_date = datetime.datetime.now() - datetime.timedelta(days=30)
        dates = [base_date + datetime.timedelta(days=i) for i in range(31)]
        prices = [current_price + random.uniform(-15, 15) for _ in range(31)]

    ma20, rsi = calculate_technical_indicators(prices)

    plt.style.use('dark_background')
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 7), gridspec_kw={'height_ratios': [3, 1]}, sharex=True)
    fig.patch.set_facecolor('#131722')

    ax1.set_facecolor('#131722')
    ax1.plot(dates, prices, color='#2962FF', linewidth=2, label='ICE Robusta')
    ax1.plot(dates, ma20, color='#FF9800', linewidth=1.5, linestyle='--', label='MA20')
    ax1.set_title('ICE LONDON ROBUSTA - XU HƯỚNG KỸ THUẬT (MA20 + RSI)', color='#d1d4dc', fontsize=11, fontweight='bold', pad=10)
    ax1.grid(True, color='#2a2e39', linestyle='--', linewidth=0.5)
    ax1.legend(loc='upper left', fontsize=8, facecolor='#1e222d', edgecolor='none')

    ax2.set_facecolor('#131722')
    ax2.plot(dates, rsi, color='#AB47BC', linewidth=1.5, label='RSI (14)')
    ax2.axhline(70, color='#ef5350', linestyle=':', alpha=0.7)
    ax2.axhline(30, color='#26a69a', linestyle=':', alpha=0.7)
    ax2.set_ylim(0, 100)
    ax2.grid(True, color='#2a2e39', linestyle='--', linewidth=0.5)
    ax2.legend(loc='upper left', fontsize=8, facecolor='#1e222d', edgecolor='none')

    plt.xticks(rotation=15, color='#787b86', fontsize=8)
    plt.tight_layout()
    chart_path = 'advanced_technical_chart.png'
    plt.savefig(chart_path, dpi=200, facecolor=fig.get_facecolor())
    plt.close()
    return chart_path, prices[-1], ma20[-1], rsi[-1]

# ==========================================
# 3. HÀM GỌI API (DEEPSEEK NATIVE + OPENROUTER FREE)
# ==========================================
def call_deepseek_native(prompt):
    api_key = os.environ.get("DEEPSEEK_API_KEY")
    if not api_key:
        return "⚠️ Lỗi: Chưa cấu hình DEEPSEEK_API_KEY"

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
            return f"⚠️ DeepSeek API lỗi {res.status_code}: {res.text[:100]}"
        return res.json()['choices'][0]['message']['content']
    except Exception as e:
        return f"⚠️ Lỗi kết nối DeepSeek: {str(e)}"

def call_openrouter_free(model_name, prompt):
    api_key = os.environ.get("OPENROUTER_API_KEY")
    if not api_key:
        return "⚠️ Lỗi: Chưa cấu hình OPENROUTER_API_KEY"

    headers = {
        "Authorization": f"Bearer {api_key}",
        "HTTP-Referer": "https://daklak-coffee-bot.local",
        "X-Title": "DakLak Coffee Advisory",
        "Content-Type": "application/json"
    }
    payload = {
        "model": model_name,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.4
    }
    try:
        res = requests.post("https://openrouter.ai/api/v1/chat/completions", json=payload, headers=headers, timeout=35)
        if res.status_code != 200:
            return f"⚠️ OpenRouter lỗi {res.status_code}: {res.text[:100]}"
        return res.json()['choices'][0]['message']['content']
    except Exception as e:
        return f"⚠️ Lỗi kết nối OpenRouter ({model_name}): {str(e)}"

# ==========================================
# 4. HỘI ĐỒNG AI TRANH BIỆN (DEEPSEEK GỐC + 2 AI OPENROUTER)
# ==========================================
def run_debate_council(market_data, tech_indicators):
    arabica_ton = market_data['arabica']['price_usd_ton']
    robusta_ton = market_data['london']['price']
    gap = arabica_ton - robusta_ton

    data_summary = f"""
    - Sàn London (Robusta): {robusta_ton} USD/tấn (Kỹ thuật: MA20={tech_indicators['ma20']:.1f}, RSI={tech_indicators['rsi']:.1f})
    - Sàn NY / Brazil (Arabica): {arabica_ton} USD/tấn
    - Chênh lệch Arabica vs Robusta: {gap:.1f} USD/tấn
    - Giá xô Đắk Lắk: {market_data['domestic']} VNĐ/kg
    - Thời tiết BMT: Nhiệt độ {market_data['weather']['temp']}°C, Mưa {market_data['weather']['rain']}mm
    """

    # --- BƯỚC 1: DeepSeek Gốc lập kế hoạch thực chiến ---
    print("🤖 [1/3] DeepSeek gốc đang lập phương án...")
    proposal_1 = call_deepseek_native(f"Dữ liệu thị trường:\n{data_summary}\n\nBạn là Chuyên gia Thực chiến. Đề xuất ngay tỷ lệ Bán tiền tươi (Spot), Bán giao xa (Forward), và Giữ lại kho. Nêu rõ mức giá mục tiêu ngắn hạn.")

    # --- BƯỚC 2: Llama 3.3 (OpenRouter Free) soi rủi ro ---
    print("🛡️ [2/3] Llama 3.3 đang soi lỗ hổng rủi ro...")
    critique_2 = call_openrouter_free("meta-llama/llama-3.3-70b-instruct:free", f"Dữ liệu thị trường:\n{data_summary}\n\nĐề xuất của Chuyên gia:\n{proposal_1}\n\nBạn là Sĩ quan Quản trị Rủi ro. Hãy chỉ ra rủi ro sụt giảm giá dựa trên chỉ số MA20/RSI và yêu cầu vạch đỏ cắt lỗ khắt khe.")

    # --- BƯỚC 3: Gemini Flash (OpenRouter Free) phán quyết ---
    print("🏛️ [3/3] Gemini Flash đang đưa ra phán quyết chung cuộc...")
    final_report = call_openrouter_free("google/gemini-2.5-flash:free", f"""
    DỮ LIỆU ĐẦU VÀO:
    {data_summary}

    Ý KIẾN DEEPSEEK:
    {proposal_1}

    Ý KIẾN QUẢN TRỊ RỦI RO:
    {critique_2}

    Bạn là Chủ tịch Hội đồng Chiến lược Kho hàng (100–500 tấn Đắk Lắk). Hãy chốt bản lệnh thương mại SÚC TÍCH, DỄ HIỂU, TRỰC DIỆN:

    🌍 **1. THẾ TRẬN THỊ TRƯỜNG**
    - Thế giới & Brazil: [Đánh giá nguồn cung]
    - Đắk Lắk & Kỹ thuật: [Tổng hợp RSI/MA20 và tâm lý gom hàng]

    💼 **2. KẾ HOẠCH BÁN HÀNG & DÒNG TIỀN (Kho 100-500 tấn)**
    - **BÁN TIỀN TƯƠI (Spot)**: [%] — [Mức giá]
    - **CHỐT GIÁ TRƯỚC (Forward)**: [%] — [Mức giá]
    - **DỰ PHÒNG KHO**: [%] — [Mục đích]

    🛡️ **3. VẠCH ĐỎ AN TOÀN**
    - **Điểm xả hàng cắt lỗ**: [Ngưỡng giá xả gấp]
    - **Điểm chốt lời tiếp theo**: [Mức giá mục tiêu]

    📌 **4. LỆNH ĐIỀU HÀNH 1 DÒNG**
    [Một câu hành động dứt khoát nhất cho chủ kho]
    """)
    return final_report

# ==========================================
# 5. GỬI TELEGRAM
# ==========================================
def send_telegram_report(photo_path, report_text):
    bot_token, chat_id = os.environ.get("TELEGRAM_BOT_TOKEN"), os.environ.get("TELEGRAM_CHAT_ID")
    if not bot_token or not chat_id:
        print("⚠️ Thiếu cấu hình Telegram Token hoặc Chat ID")
        return

    if photo_path and os.path.exists(photo_path):
        requests.post(
            f"https://api.telegram.org/bot{bot_token}/sendPhoto",
            data={'chat_id': chat_id, 'caption': "🌐 **BIỂU ĐỒ KỸ THUẬT & DÒNG TIỀN (MA20 + RSI)**", 'parse_mode': 'Markdown'},
            files={'photo': open(photo_path, 'rb')},
            timeout=20
        )

    requests.post(
        f"https://api.telegram.org/bot{bot_token}/sendMessage",
        json={'chat_id': chat_id, 'text': f"🏛️ **BÁO CÁO HỘI ĐỒNG AI (DEEPSEEK + OPENROUTER)**\n\n{report_text}", 'parse_mode': 'Markdown'},
        timeout=10
    )

# ==========================================
# MAIN EXECUTION
# ==========================================
if __name__ == "__main__":
    print("🔄 Thu thập dữ liệu...")
    market_data = {
        "london": CoffeeDataCollector.get_london_robusta(),
        "arabica": CoffeeDataCollector.get_brazil_arabica(),
        "domestic": CoffeeDataCollector.get_vietnam_domestic_prices(),
        "weather": CoffeeDataCollector.get_daklak_weather()
    }
    
    print("📈 Vẽ biểu đồ kỹ thuật...")
    chart_file, current_p, ma20_val, rsi_val = generate_technical_chart(market_data['london']['price'])
    tech_indicators = {"ma20": ma20_val, "rsi": rsi_val}
    
    print("🏛️ Kích hoạt hội đồng AI tranh biện...")
    final_decision = run_debate_council(market_data, tech_indicators)
    
    print("🚀 Gửi báo cáo Telegram...")
    send_telegram_report(chart_file, final_decision)
    print("✅ Hoàn tất!")
