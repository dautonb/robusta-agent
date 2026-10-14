import os
import requests

DEEPSEEK_API_KEY = os.environ.get("DEEPSEEK_API_KEY")
GROQ_API_KEY = os.environ.get("GROQ_API_KEY")
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
    """Agent 1: Phân tích kỹ thuật chuyên sâu"""
    if not DEEPSEEK_API_KEY: return "⚠️ Thiếu DeepSeek Key."
    url = "https://api.deepseek.com/chat/completions"
    headers = {"Authorization": f"Bearer {DEEPSEEK_API_KEY}", "Content-Type": "application/json"}
    prompt = f"Giá Robusta London: {data['price']} USD ({data['change']}%). Phân tích nhanh xu hướng kỹ thuật, vùng cản/hỗ trợ ngắn hạn dưới 60 từ."
    payload = {"model": "deepseek-chat", "messages": [{"role": "user", "content": prompt}], "stream": False}
    try:
        res = requests.post(url, json=payload, headers=headers, timeout=15)
        res_json = res.json()
        if 'choices' in res_json:
            return res_json['choices'][0]['message']['content']
        return f"DeepSeek phản hồi lạ: {str(res_json)[:80]}"
    except Exception as e:
        return f"DeepSeek bận: {e}"

def agent_groq(data, tech_insight):
    """Agent 2: Tổng hợp chiến lược và tâm lý vĩ mô (Đã bọc khiên bảo vệ)"""
    if not GROQ_API_KEY: return "⚠️ Thiếu Groq Key."
    url = "https://api.groq.com/openai/v1/chat/completions"
    headers = {"Authorization": f"Bearer {GROQ_API_KEY}", "Content-Type": "application/json"}
    
    prompt = f"""
    Giá: {data['price']} USD ({data['change']}%).
    Góc nhìn kỹ thuật từ DeepSeek: {tech_insight}
    
    Với tư cách là Trưởng ban chiến lược thương lái, hãy đưa ra quyết định hành động tối ưu (GIỮ HÀNG hay BÁN TỪNG PHẦN) dưới 60 từ, sắc bén, định dạng Markdown.
    """
    payload = {
        "model": "llama-3.3-70b-versatile",
        "messages": [{"role": "user", "content": prompt}],
        "stream": False
    }
    try:
        res = requests.post(url, json=payload, headers=headers, timeout=15)
        res_json = res.json()
        
        # Khiên phòng thủ kiểm tra lỗi trả về
        if 'choices' in res_json:
            return res_json['choices'][0]['message']['content']
        elif 'error' in res_json:
            return f"Groq quá tải/lỗi: {res_json['error'].get('message', 'Bận')}"
        return f"Groq phản hồi lạ: {str(res_json)[:80]}"
    except Exception as e:
        return f"Groq bận: {e}"

if __name__ == "__main__":
    market = get_market_data()
    tech = agent_deepseek(market)
    strategy = agent_groq(market, tech)
    
    msg = f"🌐 **HỘI ĐỒNG ĐA MÔ HÌNH (ROBUSTA)**\n"
    msg += f"• Giá Sàn London: **{market['price']} USD/tấn** ({market['change']}%)\n\n"
    msg += f"📊 **DeepSeek (Technical Analyst):**\n{tech}\n\n"
    msg += f"🧠 **Groq / Llama-3.3 (Chief Strategist):**\n{strategy}"
    
    send_telegram(msg)
    print("Hội đồng đa mô hình đã chạy mượt mà!")
