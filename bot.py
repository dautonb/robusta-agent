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

def technical_analyst_agent():
    """Agent 1: DeepSeek đóng vai trò chuyên gia phân tích kỹ thuật & định lượng"""
    if not DEEPSEEK_API_KEY:
        return "⚠️ Chưa cấu hình DeepSeek API Key."
    
    url = "https://api.deepseek.com/chat/completions"
    headers = {
        "Authorization": f"Bearer {DEEPSEEK_API_KEY}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": "deepseek-chat",
        "messages": [
            {"role": "system", "content": "Bạn là chuyên gia phân tích kỹ thuật thị trường nông sản và cà phê Robusta."},
            {"role": "user", "content": "Hãy đánh giá nhanh xu hướng giá Robusta hiện tại, xác định vùng cản kỹ thuật ngắn hạn và đưa ra phán đoán xác suất (Tăng/Giảm). Viết sắc sảo, thực chiến, dưới 80 từ."}
        ],
        "stream": False
    }
    try:
        res = requests.post(url, json=payload, headers=headers, timeout=15)
        return res.json()['choices']['message']['content']
    except Exception as e:
        return f"DeepSeek Agent bận đi uống cafe: {str(e)}"

def strategist_agent(tech_insight):
    """Agent 2: Gemini đóng vai trò tổng hợp và ra quyết định chiến lược cuối cùng"""
    if not GEMINI_API_KEY:
        return f"💡 **Phân tích kỹ thuật từ DeepSeek:**\n{tech_insight}\n\n*(Gemini chưa được cấu hình)*"

    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={GEMINI_API_KEY}"
    prompt = f"""
    Dựa trên báo cáo kỹ thuật từ DeepSeek Agent:
    "{tech_insight}"

    Hãy đóng vai trò cố vấn chiến lược cho thương lái cà phê, đưa ra lời khuyên hành động dứt khoát cuối cùng (GIỮ HÀNG hay XẢ KHO TỪNG PHẦN). 
    Định dạng Markdown ngắn gọn, sắc bén, không dài dòng.
    """
    payload = {"contents": [{"parts": [{"text": prompt}]}]}
    try:
        res = requests.post(url, json=payload, headers={'Content-Type': 'application/json'}, timeout=15)
        candidates = res.json().get('candidates')
        if candidates:
            return candidates[0].get('content', {}).get('parts', [{}])[0].get('text')
    except Exception as e:
        pass
    return tech_insight

if __name__ == "__main__":
    # Kích hoạt chuỗi Multi-Agent
    insight = technical_analyst_agent()
    final_decision = strategist_agent(insight)
    
    msg = "🤖 **MULTI-AGENT ROBUSTA BRIEFING**\n\n"
    msg += f"📊 **DeepSeek (Technical Analyst):**\n{insight}\n\n"
    msg += f"🧠 **Gemini (Chief Strategist):**\n{final_decision}"
    
    send_telegram(msg)
    print("Multi-Agent đã chạy và gửi báo cáo thành công!")
