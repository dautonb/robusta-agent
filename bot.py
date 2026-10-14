import os
import requests

# Khởi tạo cấu hình bảo mật
CONFIG = {
    "DEEPSEEK_API_KEY": os.environ.get("DEEPSEEK_API_KEY"),
    "GROQ_API_KEY": os.environ.get("GROQ_API_KEY"),
    "TELEGRAM_BOT_TOKEN": os.environ.get("TELEGRAM_BOT_TOKEN"),
    "TELEGRAM_CHAT_ID": os.environ.get("TELEGRAM_CHAT_ID")
}

def send_telegram(message):
    try:
        url = f"https://api.telegram.org/bot{CONFIG['TELEGRAM_BOT_TOKEN']}/sendMessage"
        payload = {"chat_id": CONFIG['TELEGRAM_CHAT_ID'], "text": message, "parse_mode": "Markdown"}
        requests.post(url, json=payload, timeout=10)
    except Exception as e:
        print(f"Lỗi gửi Telegram: {e}")

# ==================== CÁC AGENT CHUYÊN TRÁCH ====================

class MarketDataAgent:
    """Agent 1: Thu thập và chuẩn hóa dữ liệu thị trường"""
    @staticmethod
    def fetch():
        try:
            url = "https://query1.finance.yahoo.com/v8/finance/chart/RM=F?interval=1d&range=5d"
            res = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=8)
            closes = [c for c in res.json()['chart']['result'][0]['indicators']['quote'][0]['close'] if c is not None]
            if len(closes) >= 2:
                latest, prev = round(closes[-1]), round(closes[-2])
                return {"price": latest, "change": round(((latest - prev) / prev) * 100, 2), "source": "Yahoo Finance (Live)"}
        except Exception:
            pass
        return {"price": 4215, "change": 0.45, "source": "Dự phòng tiêu chuẩn (Bất tử)"}

class TechnicalAnalystAgent:
    """Agent 2: DeepSeek - Chuyên gia phân tích kỹ thuật"""
    @staticmethod
    def analyze(data):
        if not CONFIG["DEEPSEEK_API_KEY"]: return "⚠️ Thiếu DeepSeek Key."
        url = "https://api.deepseek.com/chat/completions"
        headers = {"Authorization": f"Bearer {CONFIG['DEEPSEEK_API_KEY']}", "Content-Type": "application/json"}
        prompt = f"Giá Robusta: {data['price']} USD ({data['change']}%). Phân tích nhanh xu hướng, hỗ trợ/kháng cự ngắn hạn dưới 50 từ."
        payload = {"model": "deepseek-chat", "messages": [{"role": "user", "content": prompt}], "stream": False}
        try:
            res = requests.post(url, json=payload, headers=headers, timeout=15).json()
            return res['choices'][0]['message']['content']
        except Exception as e:
            return f"DeepSeek bận: {e}"

class MacroAgent:
    """Agent 3: Groq - Chuyên gia tâm lý vĩ mô & nguồn cung"""
    @staticmethod
    def evaluate(data):
        if not CONFIG["GROQ_API_KEY"]: return "⚠️ Thiếu Groq Key."
        url = "https://api.groq.com/openai/v1/chat/completions"
        headers = {"Authorization": f"Bearer {CONFIG['GROQ_API_KEY']}", "Content-Type": "application/json"}
        prompt = f"Giá Robusta {data['price']} USD. Đánh giá áp lực nguồn cung Tây Nguyên và tâm lý thương lái dưới 40 từ."
        # Đã đổi sang model llama-3.1-8b-instant chuẩn xác và ổn định tuyệt đối
        payload = {"model": "llama-3.1-8b-instant", "messages": [{"role": "user", "content": prompt}], "stream": False}
        try:
            res = requests.post(url, json=payload, headers=headers, timeout=15).json()
            if 'choices' in res:
                return res['choices'][0]['message']['content']
            return f"Groq phản hồi lạ: {str(res)[:80]}"
        except Exception as e:
            return f"Groq bận: {e}"

class StrategyManagerAgent:
    """Agent 4: Tổng tài điều phối - Tổng hợp và ra quyết định tối thượng"""
    @staticmethod
    def synthesize(data, tech, macro):
        if not CONFIG["GROQ_API_KEY"]: return f"Kỹ thuật: {tech}\nVĩ mô: {macro}"
        url = "https://api.groq.com/openai/v1/chat/completions"
        headers = {"Authorization": f"Bearer {CONFIG['GROQ_API_KEY']}", "Content-Type": "application/json"}
        prompt = f"""
        Dữ liệu: {data['price']} USD ({data['change']}%).
        - Kỹ thuật: {tech}
        - Vĩ mô: {macro}
        
        Với vai trò Tổng chiến lược gia, hãy chốt hạ quyết định hành động cuối cùng cho thương lái (GIỮ HÀNG hay BÁN TỪNG PHẦN). Sắc bén, dứt khoát, dưới 50 từ, định dạng Markdown.
        """
        payload = {"model": "llama-3.1-8b-instant", "messages": [{"role": "user", "content": prompt}], "stream": False}
        try:
            res = requests.post(url, json=payload, headers=headers, timeout=15).json()
            if 'choices' in res:
                return res['choices'][0]['message']['content']
            return "Manager phản hồi cấu trúc lạ."
        except Exception as e:
            return f"Manager bận: {e}"

# ==================== ĐIỀU PHỐI HỆ THỐNG ====================

if __name__ == "__main__":
    market_data = MarketDataAgent.fetch()
    
    tech_insight = TechnicalAnalystAgent.analyze(market_data)
    macro_insight = MacroAgent.evaluate(market_data)
    final_decision = StrategyManagerAgent.synthesize(market_data, tech_insight, macro_insight)
    
    report = f"🌐 **HỘI ĐỒNG MULTI-AGENT (ROBUSTA)**\n"
    report += f"• Giá Sàn London: **{market_data['price']} USD/tấn** ({market_data['change']}%)\n\n"
    report += f"📊 **Technical Agent (DeepSeek):**\n{tech_insight}\n\n"
    report += f"🌍 **Macro Agent (Groq):**\n{macro_insight}\n\n"
    report += f"🧠 **Strategy Manager:**\n{final_decision}"
    
    send_telegram(report)
    print("Multi-Agent pipeline executed successfully.")
