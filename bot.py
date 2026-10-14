import os
import requests
from datetime import datetime

GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
DEEPSEEK_API_KEY = os.environ.get("DEEPSEEK_API_KEY")
GROQ_API_KEY = os.environ.get("GROQ_API_KEY") # Thay thế OpenRouter bằng Groq cực kỳ ổn định
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")

def send_telegram(message):
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
        payload = {"chat_id": TELEGRAM_CHAT_ID, "text": message, "parse_mode": "Markdown"}
        requests.post(url, json=payload, timeout=10)
    except Exception as e:
        print(f"Lỗi gửi Telegram: {e}")

def fetch_chart_data():
    """Cào dữ liệu biểu đồ và tính toán MA5, MA20"""
    try:
        url = "https://query1.finance.yahoo.com/v8/finance/chart/RM=F?interval=1d&range=1mo"
        headers = {"User-Agent": "Mozilla/5.0"}
        res = requests.get(url, headers=headers, timeout=10)
        data = res.json()['chart']['result'][0]
        
        timestamps = data['timestamp']
        quotes = data['indicators']['quote'][0]
        closes = quotes['close']
        highs = quotes['high']
        lows = quotes['low']
        
        history = []
        for t, c, h, l in zip(timestamps, closes, highs, lows):
            if c is not None and h is not None and l is not None:
                dt = datetime.fromtimestamp(t).strftime('%d/%m')
                history.append({"date": dt, "close": round(c, 1), "high": round(h, 1), "low": round(l, 1)})
        
        if len(history) < 5: return None
        
        latest = history[-1]
        prev = history[-2]
        change_pct = round(((latest['close'] - prev['close']) / prev['close']) * 100, 2)
        
        recent_closes = [x['close'] for x in history]
        ma5 = round(sum(recent_closes[-5:]) / 5, 1)
        ma20 = round(sum(recent_closes[-20:]) / min(20, len(recent_closes)), 1)

        return {
            "latest_price": latest['close'],
            "change_pct": change_pct,
            "high": latest['high'],
            "low": latest['low'],
            "ma5": ma5,
            "ma20": ma20,
            "history_str": "\n".join([f"- Ngày {x['date']}: {x['close']} USD" for x in history[-5:]])
        }
    except Exception as e:
        return None

def agent_deepseek(data):
    """Agent 1: DeepSeek phân tích kỹ thuật"""
    if not DEEPSEEK_API_KEY: return "Chưa có DeepSeek Key."
    url = "https://api.deepseek.com/chat/completions"
    headers = {"Authorization": f"Bearer {DEEPSEEK_API_KEY}", "Content-Type": "application/json"}
    prompt = f"Giá Robusta: {data['latest_price']} USD ({data['change_pct']}%). MA5: {data['ma5']}, MA20: {data['ma20']}. Đánh giá xu hướng và vùng cản ngắn hạn dưới 70 từ."
    payload = {"model": "deepseek-chat", "messages": [{"role": "user", "content": prompt}], "stream": False}
    try:
        res = requests.post(url, json=payload, headers=headers, timeout=15)
        return res.json()['choices'][0]['message']['content']
    except Exception as e:
        return f"DeepSeek bận: {e}"

def agent_groq(data):
    """Agent 2: Groq siêu tốc đánh giá tâm lý vĩ mô"""
    if not GROQ_API_KEY: return "Chưa có Groq Key."
    url = "https://api.groq.com/openai/v1/chat/completions"
    headers = {"Authorization": f"Bearer {GROQ_API_KEY}", "Content-Type": "application/json"}
    payload = {
        "model": "llama-3.1-8b-instant",
        "messages": [{"role": "user", "content": "Góc nhìn nhanh về áp lực nguồn cung cà phê Tây Nguyên lúc này dưới 50 từ."}],
        "stream": False
    }
    try:
        res = requests.post(url, json=payload, headers=headers, timeout=15)
        return res.json()['choices'][0]['message']['content']
    except Exception as e:
        return f"Groq bận: {e}"

def agent_gemini(data, tech, macro):
    """Agent 3: Gemini chốt hạ chiến lược (Đã cập nhật model gemini-2.0-flash chuẩn)"""
    if not GEMINI_API_KEY: return f"Kỹ thuật: {tech}"
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={GEMINI_API_KEY}"
    prompt = f"Giá: {data['latest_price']} USD. Kỹ thuật: {tech}\nVĩ mô: {macro}\nKhuyên thương lái GIỮ HÀNG hay BÁN TỪNG PHẦN? Dưới 60 từ, Markdown."
    payload = {"contents": [{"parts": [{"text": prompt}]}]}
    try:
        res = requests.post(url, json=payload, headers={'Content-Type': 'application/json'}, timeout=15)
        candidates = res.json().get('candidates')
        if candidates:
            return candidates[0]['content']['parts'][0]['text']
        return "Gemini bận."
    except Exception as e:
        return f"Gemini bận: {e}"

if __name__ == "__main__":
    chart = fetch_chart_data()
    if chart:
        t_insight = agent_deepseek(chart)
        g_insight = agent_groq(chart)
        final_verdict = agent_gemini(chart, t_insight, g_insight)
        
        msg = f"📊 **HỘI ĐỒNG AI (DEEPSEEK + GROQ + GEMINI)**\n"
        msg += f"• Giá Sàn London: **{chart['latest_price']} USD** ({chart['change_pct']}%)\n\n"
        msg += f"📈 **DeepSeek (Technical):**\n{t_insight}\n\n"
        msg += f"⚡ **Groq (Macro/Speed):**\n{g_insight}\n\n"
        msg += f"🧠 **Gemini (Strategy Verdict):**\n{final_verdict}"
        
        send_telegram(msg)
        print("Đã hoàn thành vòng lặp Multi-Agent tối ưu!")
    else:
        send_telegram("⚠️ Lỗi kết nối dữ liệu biểu đồ.")
