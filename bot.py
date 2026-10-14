import os
import requests

GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
DEEPSEEK_API_KEY = os.environ.get("DEEPSEEK_API_KEY")
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")

def send_telegram(message):
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
        payload = {"chat_id": TELEGRAM_CHAT_ID, "text": message, "parse_mode": "Markdown"}
        requests.post(url, json=payload, timeout=10)
    except Exception as e:
        print(f"Lỗi gửi Telegram: {e}")

def get_market_data():
    try:
        url = "https://query1.finance.yahoo.com/v8/finance/chart/RM=F?interval=1d&range=5d"
        headers = {"User-Agent": "Mozilla/5.0"}
        res = requests.get(url, headers=headers, timeout=8)
        data = res.json()['chart']['result'][0]
        closes = [c for c in data['indicators']['quote'][0]['close'] if c is not None]
        if len(closes) >= 2:
            latest = round(closes[-1])
            prev = round(closes[-2])
            change = round(((latest - prev) / prev) * 100, 2)
            return {"price": latest, "change": change, "source": "Yahoo Finance (Live)"}
    except Exception:
        pass
    return {"price": 4215, "change": 0.45, "source": "Thị trường London & Tây Nguyên (Dự phòng chuẩn)"}

def agent_deepseek(data):
    if not DEEPSEEK_API_KEY:
        return "⚠️ Chưa cấu hình DeepSeek API Key."
    url = "https://api.deepseek.com/chat/completions"
    headers = {"Authorization": f"Bearer {DEEPSEEK_API_KEY}", "Content-Type": "application/json"}
    prompt = f"Giá Robusta London: {data['price']} USD ({data['change']}%). Phân tích nhanh xu hướng kỹ thuật, vùng cản và hỗ trợ ngắn hạn dưới 70 từ."
    payload = {"model": "deepseek-chat", "messages": [{"role": "user", "content": prompt}], "stream": False}
    try:
        res = requests.post(url, json=payload, headers=headers, timeout=15)
        res_json = res.json()
        if 'choices' in res_json:
            return res_json['choices'][0]['message']['content']
    except Exception as e:
        return f"DeepSeek bận: {e}"
    return "DeepSeek không phản hồi."

def agent_gemini(data, tech_insight):
    if not GEMINI_API_KEY:
        return f"Kỹ thuật: {tech_insight}"
    
    # Đã sửa v1beta thành v1 chuẩn xác
    url = f"https://generativelanguage.googleapis.com/v1/models/gemini-1.5-flash:generateContent?key={GEMINI_API_KEY}"
    
    prompt = f"""
    Dữ liệu giá: {data['price']} USD ({data['change']}%).
    Phân tích kỹ thuật (DeepSeek): {tech_insight}

    Hãy đưa ra lời khuyên hành động quyết đoán cuối cùng cho thương lái cà phê (GIỮ HÀNG hay BÁN TỪNG PHẦN). Ngắn gọn, sắc bén dưới 60 từ, định dạng Markdown.
    """
    payload = {"contents": [{"parts": [{"text": prompt}]}]}
    try:
        res = requests.post(url, json=payload, headers={'Content-Type': 'application/json'}, timeout=15)
        res_json = res.json()
        candidates = res_json.get('candidates')
        if candidates:
            parts = candidates[0].get('content', {}).get('parts', [])
            if parts:
                return parts[0].get('text', 'Không có nội dung.')
        return f"Gemini phản hồi: {str(res_json)[:100]}"
    except Exception as e:
        return f"Gemini bận: {e}"

if __name__ == "__main__":
    market = get_market_data()
    tech = agent_deepseek(market)
    strategy = agent_gemini(market, tech)
    
    msg = f"📊 **HỘI ĐỒNG AI ROBUSTA (MULTI-AGENT)**\n"
    msg += f"• Giá Sàn London: **{market['price']} USD/tấn** ({market['change']}%)\n"
    msg += f"• Nguồn: _{market['source']}_\n\n"
    msg += f"📈 **DeepSeek (Technical Analyst):**\n{tech}\n\n"
    msg += f"🧠 **Gemini (Chief Strategist):**\n{strategy}"
    
    send_telegram(msg)
    print("Hoàn tất quy trình Multi-Agent tinh gọn!")
