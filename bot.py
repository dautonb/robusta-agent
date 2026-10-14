import os
import requests

GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
DEEPSEEK_API_KEY = os.environ.get("DEEPSEEK_API_KEY")
OPENROUTER_API_KEY = os.environ.get("OPENROUTER_API_KEY")
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")

def send_telegram(message):
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
        payload = {"chat_id": TELEGRAM_CHAT_ID, "text": message, "parse_mode": "Markdown"}
        requests.post(url, json=payload, timeout=10)
    except Exception as e:
        print(f"Lỗi gửi Telegram: {e}")

def agent_deepseek():
    """Agent 1: Chuyên gia Phân tích Kỹ thuật & Định lượng"""
    if not DEEPSEEK_API_KEY: 
        return "⚠️ Chưa cấu hình DeepSeek API Key."
    
    url = "https://api.deepseek.com/chat/completions"
    headers = {"Authorization": f"Bearer {DEEPSEEK_API_KEY}", "Content-Type": "application/json"}
    payload = {
        "model": "deepseek-chat",
        "messages": [{"role": "user", "content": "Đánh giá ngắn xu hướng kỹ thuật giá Robusta London, nêu nhanh vùng cản dưới 50 từ."}],
        "stream": False
    }
    try:
        res = requests.post(url, json=payload, headers=headers, timeout=15)
        data = res.json()
        # Đã thêm [0] để trỏ chính xác vào phần tử list của choices
        return data['choices'][0]['message']['content']
    except Exception as e:
        return f"DeepSeek bận: {str(e)}"

def agent_openrouter():
    """Agent 2: Chuyên gia Vĩ mô & Tin tức"""
    if not OPENROUTER_API_KEY: 
        return "⚠️ Chưa cấu hình OpenRouter API Key."
    
    url = "https://openrouter.ai/api/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "HTTP-Referer": "https://github.com/robusta-agent",
        "Content-Type": "application/json"
    }
    payload = {
        "model": "google/gemma-2-9b-it:free",
        "messages": [{"role": "user", "content": "Góc nhìn nhanh về nguồn cung và tâm lý thị trường cà phê Tây Nguyên lúc này dưới 50 từ."}],
        "stream": False
    }
    try:
        res = requests.post(url, json=payload, headers=headers, timeout=15)
        data = res.json()
        return data['choices'][0]['message']['content']
    except Exception as e:
        return f"OpenRouter bận: {str(e)}"

def agent_gemini(tech, macro):
    """Agent 3: Trưởng ban Chiến lược tổng hợp ra quyết định"""
    if not GEMINI_API_KEY: 
        return f"Kỹ thuật: {tech}\nVĩ mô: {macro}"
    
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={GEMINI_API_KEY}"
    prompt = f"""
    Tổng hợp báo cáo từ 2 chuyên gia:
    1. Kỹ thuật (DeepSeek): {tech}
    2. Vĩ mô (OpenRouter): {macro}

    Hãy đưa ra lời khuyên hành động quyết đoán cuối cùng cho thương lái (GIỮ HÀNG hay BÁN TỪNG PHẦN). Ngắn gọn, sắc bén dưới 100 từ, định dạng Markdown.
    """
    payload = {"contents": [{"parts": [{"text": prompt}]}]}
    try:
        res = requests.post(url, json=payload, headers={'Content-Type': 'application/json'}, timeout=15)
        data = res.json()
        candidates = data.get('candidates')
        if candidates:
            return candidates[0].get('content', {}).get('parts', [{}])[0].get('text', 'Không có nội dung.')
    except Exception as e:
        return f"Gemini bận: {str(e)}"
    return "Gemini gặp sự cố tổng hợp."

if __name__ == "__main__":
    t_insight = agent_deepseek()
    m_insight = agent_openrouter()
    final_verdict = agent_gemini(t_insight, m_insight)
    
    msg = "🌐 **HỘI ĐỒNG 3 AI AGENT (ROBUSTA)**\n\n"
    msg += f"📊 **DeepSeek (Technical):**\n{t_insight}\n\n"
    msg += f"🌍 **OpenRouter (Macro):**\n{m_insight}\n\n"
    msg += f"🧠 **Gemini (Chief Strategy):**\n{final_verdict}"
    
    send_telegram(msg)
    print("Multi-Agent 3 mảnh đã chạy xong!")
