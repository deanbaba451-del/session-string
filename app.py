import os
import logging
import httpx
import asyncio
from flask import Flask
from threading import Thread
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes

# --- LOGGING YAPILANDIRMASI ---
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO
)
logger = logging.getLogger(__name__)

# --- FLASK SERVER (Health Check & Render Keep-Alive) ---
app = Flask(__name__)

@app.route('/health')
def health_check():
    return {"status": "running", "bot": "active"}, 200

def run_flask():
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False, use_reloader=False)

# --- TEMP MAIL MANTIĞI (Async httpx) ---
BASE_URL = "https://www.1secmail.com/api/v1/"

async def fetch_api(params):
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(BASE_URL, params=params, timeout=10.0)
            return response.json()
        except Exception as e:
            logger.error(f"API Hatası: {e}")
            return None

# --- BOT KOMUTLARI ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    logger.info(f"Start komutu: {user.id}")
    await update.message.reply_html(
        f"<b>🚀 Profesyonel Geçici Servis</b>\n\n"
        f"Hoş geldin {user.mention_html()}.\n"
        f"Gizliliğini korumak için aşağıdan yeni bir mail oluşturabilirsin."
        , reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("📧 Yeni Mail Oluştur", callback_data="gen_mail")]
        ])
    )

async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    data = query.data
    await query.answer()

    if data == "gen_mail":
        res = await fetch_api({"action": "genRandomMailbox", "count": 1})
        if res:
            email = res[0]
            login, domain = email.split('@')
            text = (f"🔍 <b>Adresiniz Hazır:</b>\n<code>{email}</code>\n\n"
                    f"<i>Mesajlar geldiğinde aşağıdan yenileyebilirsiniz.</i>")
            
            kb = [
                [InlineKeyboardButton("🔄 Gelen Kutusu Yenile", callback_data=f"check_{login}_{domain}")],
                [InlineKeyboardButton("🗑 Sil ve Yeni Al", callback_data="gen_mail")]
            ]
            await query.edit_message_text(text, parse_mode="HTML", reply_markup=InlineKeyboardMarkup(kb))

    elif data.startswith("check_"):
        _, login, domain = data.split('_')
        messages = await fetch_api({"action": "getMessages", "login": login, "domain": domain})
        
        if not messages:
            await query.answer("📭 Henüz mesaj yok (Bekleniyor...)", show_alert=False)
        else:
            txt = "📬 <b>Son Mesajlar:</b>\n\n"
            kb = []
            for msg in messages[:5]:
                txt += f"<b>Kimden:</b> {msg['from']}\n<b>Konu:</b> {msg['subject']}\n⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯\n"
                kb.append([InlineKeyboardButton(f"📖 {msg['subject'][:20]}...", callback_data=f"read_{login}_{domain}_{msg['id']}")])
            
            kb.append([InlineKeyboardButton("⬅️ Geri", callback_data="gen_mail")])
            await query.edit_message_text(txt, parse_mode="HTML", reply_markup=InlineKeyboardMarkup(kb))

# --- ANA ÇALIŞTIRICI ---
if __name__ == "__main__":
    token = os.environ.get("BOT_TOKEN")
    if not token:
        logger.error("BOT_TOKEN bulunamadı!")
        exit(1)

    # Flask'ı ayrı kolda başlat
    Thread(target=run_flask, daemon=True).start()

    # Botu kur
    application = Application.builder().token(token).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CallbackQueryHandler(handle_callback))

    logger.info("Bot ve Web Servis başlatılıyor...")
    application.run_polling(drop_pending_updates=True)
