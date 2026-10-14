import os
import requests

def send_telegram(msg):
    token = os.environ.get("TELEGRAM_BOT_TOKEN")
    chat_id = os.environ.get("TELEGRAM_CHAT_ID")
    if token and chat_id:
        try:
            requests.post(f"https://api.telegram.org/bot{token}/sendMessage", json={"chat_id": chat_id, "text": msg}, timeout=5)
        except Exception as e:
            print(f"Lỗi gửi Telegram: {e}")

if __name__ == "__main__":
    try:
        # Kiểm tra xem thiếu Secret nào không
        missing = []
        for key in ["TELEGRAM_BOT_TOKEN", "TELEGRAM_CHAT_ID", "DEEPSEEK_API_KEY", "GROQ_API_KEY", "GEMINI_API_KEY"]:
            if not os.environ.get(key):
                missing.append(key)
        
        if missing:
            send_telegram(f"⚠️ Bot thiếu các Secrets sau trên GitHub: {', '.join(missing)}")
        else:
            send_telegram("✅ Hệ thống Multi-Agent đã thông mạch! Các chìa khóa đều đủ.")
            
    except Exception as e:
        send_telegram(f"🔥 Lỗi nghiêm trọng khi khởi chạy: {str(e)}")
