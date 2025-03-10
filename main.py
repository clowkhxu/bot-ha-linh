from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes
import google.generativeai as genai
import os
from flask import Flask
from threading import Thread
import requests
import time

# ======= Cấu hình API Key =======
GENAI_API_KEY = os.getenv('GENAI_API_KEY', '')
TOKEN = os.getenv('TOKEN', '')
MISTRAL_API_KEY = os.getenv('MISTRAL_API_KEY', '')

# ======= Cấu hình Gemini =======
genai.configure(api_key=GENAI_API_KEY)
model = genai.GenerativeModel('gemini-1.5-pro')

# ======= Xử lý tin nhắn =======
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_message = update.message.text.lower()
    print(f"User message: {user_message}")

    try:
        if "yêu" in user_message:
            reply = "Em yêu anh nhất, anh có yêu em không?"
        elif "nhớ em" in user_message:
            reply = "Nhớ em hả? Em cũng nhớ anh nhiều."
        elif "giận" in user_message:
            reply = "Giận rồi đó. Anh dỗ em đi ~"
        else:
            try:
                response = model.generate_content(f"""
                    Đóng vai bạn gái dễ thương nhưng quyền lực. Trả lời ngắn, xưng "em", gọi "anh yêu". 
                    Nhẹ nhàng, cưng chiều, quan tâm sức khỏe và tinh thần của anh.

                    User: {user_message}
                """)
                reply = response.text.strip()

            except Exception as e:
                if '429' in str(e):
                    print("Gemini bị lỗi quota, chuyển sang Mistral...")
                    headers = {
                        'Authorization': f'Bearer {MISTRAL_API_KEY}',
                        'Content-Type': 'application/json'
                    }
                    data = {
                        "model": "mistral-tiny",
                        "prompt": user_message,
                        "max_tokens": 50
                    }
                    response = requests.post("https://api.mistral.ai/v1/chat/completions", json=data, headers=headers)
                    if response.status_code == 200:
                        reply = response.json()['choices'][0]['message']['content'].strip()
                    else:
                        reply = "Em bị tràn bộ nhớ rồi..."
                else:
                    raise e

        print(f"Reply: {reply}")
        await update.message.reply_text(reply)

    except Exception as e:
        print(f"Lỗi: {e}")
        await update.message.reply_text("Em bị lỗi rồi nè...")

# ======= Lệnh khởi động bot =======
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Em đây, anh yêu cần gì không?")

# ======= Flask để giữ ứng dụng hoạt động trên Render =======
app = Flask(__name__)

@app.route('/')
def home():
    return "Bot is running!"

# Chạy Flask trong luồng riêng
def run_flask():
    port = int(os.getenv('PORT', 8080))
    app.run(host='0.0.0.0', port=port, use_reloader=False)

# ======= Giữ Render luôn hoạt động bằng ping định kỳ =======
def keep_alive():
    url = "https://bot-ha-linh.onrender.com"
    while True:
        try:
            requests.get(url)
            print("Ping Flask để giữ ứng dụng luôn hoạt động.")
        except Exception as e:
            print(f"Lỗi khi ping Flask: {e}")
        time.sleep(300)  # Ping mỗi 5 phút

# ======= Chạy bot Telegram =======
def main():
    Thread(target=run_flask).start()
    Thread(target=keep_alive).start()

    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    print("Bot đang chạy...")

    while True:
        try:
            app.run_polling()
        except Exception as e:
            if 'Conflict' in str(e):
                print("Bot bị conflict, khởi động lại polling...")
                continue
            else:
                print(f"Lỗi polling: {e}")
                continue

if __name__ == '__main__':
    main()
