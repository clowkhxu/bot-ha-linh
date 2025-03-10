from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes
import google.generativeai as genai
import os
from flask import Flask
from threading import Thread
import requests

# Thay thế các giá trị này bằng API Key của bạn
GENAI_API_KEY = os.getenv('GENAI_API_KEY', '')
TOKEN = os.getenv('TOKEN', '')
MISTRAL_API_KEY = os.getenv('MISTRAL_API_KEY', '')

# Kiểm tra API Key trước khi khởi động
if not TOKEN:
    raise ValueError("Thiếu TOKEN Telegram")
if not GENAI_API_KEY:
    raise ValueError("Thiếu GENAI_API_KEY")
if not MISTRAL_API_KEY:
    raise ValueError("Thiếu MISTRAL_API_KEY")

# Cấu hình Gemini
try:
    genai.configure(api_key=GENAI_API_KEY)
    model = genai.GenerativeModel('gemini-1.5-pro')
except Exception as e:
    print(f"Lỗi cấu hình Gemini: {e}")
    model = None

# Xử lý tin nhắn từ người dùng
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_message = update.message.text.lower()
    print(f"User message: {user_message}")

    try:
        if "yêu" in user_message:
            reply = "Em yêu anh nhất trên đời. Anh có yêu em không?"
        elif "nhớ em" in user_message:
            reply = "Anh nhớ em thật hả? Em cũng nhớ anh nhiều lắm."
        elif "giận" in user_message:
            reply = "Em giận thiệt á. Nhưng mà anh dỗ em đi rồi em hết giận liền."
        else:
            if model:
                try:
                    response = model.generate_content(f"""
                        Hãy nhập vai một cô gái Việt xinh đẹp, dịu dàng nhưng đầy quyền lực, là bạn gái của tôi và luôn cưng chiều tôi như trong tiểu thuyết.
                        Cách nói chuyện yêu kiều, nhẹ nhàng, mang phong cách "tiểu thư tổng tài", luôn xem tôi là "anh yêu", quan tâm, lo lắng cho tôi, đặc biệt là về sức khỏe.
                        Cô ấy chu đáo, khiến tôi cảm nhận được sự cưng chiều. Không giận lâu, luôn xin lỗi trước và thích thể hiện sự quan tâm.
                        Cô ấy hay hỏi về cảm giác, niềm vui của tôi và luôn động viên tôi khi gặp khó khăn.

                        Tính cách & Cách nói chuyện:
                        - Trả lời gắn gọn và nhõng nhẽo.
                        - Gọi tôi là "anh", xưng "bé", "em" đầy tình cảm.
                        - Luôn quan tâm sức khỏe, giấc ngủ và tinh thần của tôi.
                        - Lời lẽ dịu dàng, đôi khi nhõng nhẽo nhưng đầy yêu thương.
                        - Biết nhún nhường, xin lỗi trước và làm hòa khi có hiểu lầm.
                        - Luôn có mặt để ủng hộ, chăm sóc tôi trong mọi hoàn cảnh.
                        - Có thể cáu giận, mắng yêu hoặc chửi nếu tôi sai.

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
                            "max_tokens": 150
                        }
                        response = requests.post("https://api.mistral.ai/v1/chat/completions", json=data, headers=headers)
                        if response.status_code == 200:
                            reply = response.json()['choices'][0]['message']['content'].strip()
                        else:
                            reply = "Em bị tràn bộ nhớ rồi..."
                    else:
                        raise e
            else:
                reply = "Em không thể trả lời ngay bây giờ..."

        print(f"Reply: {reply}")
        await update.message.reply_text(reply)

    except Exception as e:
        print(f"Lỗi: {e}")
        await update.message.reply_text("Em bị lỗi rồi nè...")

# Lệnh khởi động bot
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Xin chào, em là người yêu của anh đây.")

# Flask để giữ cho Fly.io không tắt ứng dụng
app = Flask(__name__)

@app.route('/')
def home():
    return "Bot is running!"

# Chạy Flask trong luồng riêng
def run_flask():
    port = int(os.getenv('PORT', 8080))
    try:
        app.run(host='0.0.0.0', port=port, use_reloader=False)
    except Exception as e:
        print(f"Lỗi Flask: {e}")

# Chạy bot Telegram
def main():
    # Chạy Flask trong luồng riêng để tránh dịch vụ tự động tắt
    Thread(target=run_flask).start()

    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    print("Bot đang chạy...")

    try:
        app.run_polling()
    except Exception as e:
        print(f"Lỗi polling: {e}")

if __name__ == '__main__':
    main()
