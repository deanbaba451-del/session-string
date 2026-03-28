import os
import asyncio
import threading
from flask import Flask
from telethon import TelegramClient
from telethon.sessions import StringSession
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes, ConversationHandler

app = Flask(__name__)
@app.route('/')
def health(): return "terminal_yok_ama_cozum_var", 200

def run_flask():
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)

# Konuşma Durumları
ID, HASH, PHONE, CODE, 2FA = range(5)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("welcome king. let's get that string session.\nsend your **API_ID**:")
    return ID

async def get_id(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['id'] = update.message.text
    await update.message.reply_text("now send your **API_HASH**:")
    return HASH

async def get_hash(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['hash'] = update.message.text
    await update.message.reply_text("send your **PHONE NUMBER** (with + and country code):")
    return PHONE

async def get_phone(update: Update, context: ContextTypes.DEFAULT_TYPE):
    phone = update.message.text
    context.user_data['phone'] = phone
    
    # Telethon başlat
    client = TelegramClient(StringSession(), int(context.user_data['id']), context.user_data['hash'])
    await client.connect()
    
    try:
        sent = await client.send_code_request(phone)
        context.user_data['client'] = client
        context.user_data['phone_hash'] = sent.phone_code_hash
        await update.message.reply_text("check your telegram messages and send the **LOGIN CODE**:")
        return CODE
    except Exception as e:
        await update.message.reply_text(f"error: {str(e)}")
        return ConversationHandler.END

async def get_code(update: Update, context: ContextTypes.DEFAULT_TYPE):
    code = update.message.text
    client = context.user_data['client']
    phone = context.user_data['phone']
    phone_hash = context.user_data['phone_hash']
    
    try:
        await client.sign_in(phone, code, phone_code_hash=phone_hash)
        string = client.session.save()
        await update.message.reply_text(f"here is your string session (KEEP IT SECRET):\n\n`{string}`", parse_mode='Markdown')
        await client.disconnect()
        return ConversationHandler.END
    except Exception as e:
        if "Two-step verification" in str(e) or "password" in str(e).lower():
            await update.message.reply_text("2FA enabled. send your **PASSWORD**:")
            return 2FA
        await update.message.reply_text(f"error: {str(e)}")
        return ConversationHandler.END

async def get_2fa(update: Update, context: ContextTypes.DEFAULT_TYPE):
    password = update.message.text
    client = context.user_data['client']
    try:
        await client.sign_in(password=password)
        string = client.session.save()
        await update.message.reply_text(f"done! here is your string session:\n\n`{string}`", parse_mode='Markdown')
        await client.disconnect()
        return ConversationHandler.END
    except Exception as e:
        await update.message.reply_text(f"error: {str(e)}")
        return ConversationHandler.END

def main():
    bot_token = os.environ.get("BOT_TOKEN")
    app_bot = Application.builder().token(bot_token).build()
    
    conv = ConversationHandler(
        entry_points=[CommandHandler('start', start)],
        states={
            ID: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_id)],
            HASH: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_hash)],
            PHONE: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_phone)],
            CODE: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_code)],
            2FA: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_2fa)],
        },
        fallbacks=[CommandHandler('cancel', lambda u,c: ConversationHandler.END)]
    )
    
    app_bot.add_handler(conv)
    app_bot.run_polling()

if __name__ == "__main__":
    threading.Thread(target=run_flask, daemon=True).start()
    main()
