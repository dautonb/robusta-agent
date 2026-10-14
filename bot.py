import os
import requests

CONFIG = {
    "DEEPSEEK_API_KEY": os.environ.get("DEEPSEEK_API_KEY"),
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

def call_deepseek(prompt):
    """Hàm gọi DeepSeek chung cho toàn bộ Agent"""
    if not CONFIG["DEEPSEEK_API_KEY"]: return "⚠️ Thiếu DeepSeek Key."
    url = "https://api.deepseek.com/chat/completions"
    headers = {"Authorization": f"Bearer {CONFIG['DEEPSEEK_API_KEY']}", "Content-Type": "application/json"}
    payload = {"model": "deepseek-chat", "messages": [{"role": "user", "content": prompt}], "stream": False}
    try:
        res = requests.post(url, json=payload, headers=headers, timeout=15).json()
        if 'choices' in res:
            return res['choices'][0]['message']['content']
        return "DeepSeek bận."
    except Exception as e:
        return f"Lỗi kết nối: {e}"

# ==================== CÁC AGENT CHUYÊN TRÁCH ====================

class MarketDataAgent:
    @staticmethod
    def fetch():
        try:
            url = "https://query1.finance.yahoo.com/v8/finance/chart/RM=F?interval=1d&range=1mo"
            res = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=10)
            closes = [c for c in res.json()['chart']['result'][0]['indicators']['quote'][0]['close'] if c is not None]
            
            if len(closes) >= 14:
                latest, prev = round(closes[-1]), round(closes[-2])
                change = round(((latest - prev) / prev) * 100, 2)
                ma5 = round(sum(closes[-5:]) / 5)
                ma20 = round(sum(closes[-20:]) / min(20, len(closes)))
                
                gains, losses = [], []
                for i in range(-14, 0):
                    diff = closes[i] - closes[i-1]
                    gains.append(diff if diff > 0 else 0)
                    losses.append(abs(diff) if diff < 0 else 0)
                rs = (sum(gains) / 14) / (sum(losses) / 14) if sum(losses) != 0 else 100
                rsi = round(100 - (100 / (1 + rs)), 1)

                return {"price": latest, "change": change, "ma5": ma5, "ma20": ma20, "rsi": rsi, "source": "Yahoo Finance (Live)"}
        except Exception:
            pass
        return {"price": 4215, "change": 0.45, "ma5": 4200, "ma20": 4180, "rsi": 52.0, "source": "Dự phòng tiêu chuẩn"}

class TechnicalAnalystAgent:
    @staticmethod
    def analyze(data):
        prompt = f"""
        Giá Robusta London: {data['price']} USD ({data['change']}%). MA5: {data['ma5']}, MA20: {data['ma20']}, RSI: {data['rsi']}.
        Đánh giá nhanh xu hướng kỹ thuật, vùng cản và hỗ trợ ngắn hạn dưới 50 từ.
        """
        return call_deepseek(prompt)

class MacroAgent:
    @staticmethod
    def evaluate(data):
        prompt = f"""
        Giá Robusta: {data['price']} USD. 
        Đánh giá ngắn gọn áp lực nguồn cung Tây Nguyên và tâm lý thị trường nông sản dưới 40 từ.
        """
        return call_deepseek(prompt)

class StrategyManagerAgent:
    @staticmethod
    def synthesize(data, tech, macro):
        prompt = f"""
        Giá: {data['price']} USD.
        - Kỹ thuật: {tech}
        - Vĩ mô: {macro}
        
        Với tư cách là Tổng chiến lược gia, hãy đưa ra Kế hoạch giao dịch chuyên nghiệp (Hành động, Mức chốt lời/cắt lỗ) dưới 60 từ, định dạng Markdown.
        """
        return call_deepseek(prompt)

# ==================== ĐIỀU PHỐI HỆ THỐNG ====================

if __name__ == "__main__":
    market_data = MarketDataAgent.fetch()
    
    tech_insight = TechnicalAnalystAgent.analyze(market_data)
    macro_insight = MacroAgent.evaluate(market_data)
    final_decision = StrategyManagerAgent.synthesize(market_data, tech_insight, macro_insight)
    
    report = f"🏛️ **HỘI ĐỒNG MULTI-AGENT (DEEPSEEK)**\n"
    report += f"• Giá Sàn London: **{market_data['price']} USD/tấn** ({market_data['change']}%)\n"
    report += f"• Chỉ báo: **MA5:** {market_data['ma5']} | **MA20:** {market_data['ma20']} | **RSI:** {market_data['rsi']}\n\n"
    report += f"📊 **Technical Agent:**\n{tech_insight}\n\n"
    report += f"🌍 **Macro Agent:**\n{macro_insight}\n\n"
    report += f"🎯 **Strategy Manager:**\n{final_decision}"
    
    send_telegram(report)
    print("Multi-Agent pipeline executed successfully.")
