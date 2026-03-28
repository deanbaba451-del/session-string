import os, threading, asyncio
from flask import Flask
from telethon import TelegramClient
from telethon.sessions import StringSession
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes, ConversationHandler

app = Flask(__name__)
@app.route('/')
def h(): return "ok", 200

def run():
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 8080)))

ID, HASH, PHONE, CODE, PASS = range(5)

async def start(u, c):
    c.user_data.clear() # her startta hafızayı temizle
    await u.message.reply_text("api_id?")
    return ID

async def get_id(u, c):
    c.user_data['i'] = u.message.text
    await u.message.reply_text("api_hash?")
    return HASH

async def get_hash(u, c):
    c.user_data['h'] = u.message.text
    await u.message.reply_text("phone?")
    return PHONE

async def get_phone(u, c):
    c.user_data['p'] = u.message.text
    try:
        # cihaz bilgilerini daha standart bir hale getirdik
        cl = TelegramClient(
            StringSession(), 
            int(c.user_data['i']), 
            c.user_data['h'],
            device_model="iPhone",
            system_version="iOS 17",
            app_version="10.0"
        )
        await cl.connect()
        s = await cl.send_code_request(c.user_data['p'])
        c.user_data['cl'], c.user_data['sh'] = cl, s.phone_code_hash
        await u.message.reply_text("code?")
        return CODE
    except Exception as e:
        await u.message.reply_text(f"error: {str(e).lower()}")
        return ConversationHandler.END

async def get_code(u, c):
    cl, p, sh = c.user_data['cl'], c.user_data['p'], c.user_data['sh']
    try:
        await cl.sign_in(p, u.message.text, phone_code_hash=sh)
        await u.message.reply_text(f"`{cl.session.save()}`", parse_mode='Markdown')
        await cl.disconnect()
        return ConversationHandler.END
    except Exception as e:
        if "password" in str(e).lower():
            await u.message.reply_text("password?")
            return PASS
        await u.message.reply_text(f"error: {str(e).lower()}")
        return ConversationHandler.END

async def get_pass(u, c):
    cl = c.user_data['cl']
    try:
        await cl.sign_in(password=u.message.text)
        await u.message.reply_text(f"`{cl.session.save()}`", parse_mode='Markdown')
        await cl.disconnect()
    except Exception as e:
        await u.message.reply_text(f"error: {str(e).lower()}")
    return ConversationHandler.END

def main():
    bot = Application.builder().token(os.environ.get("BOT_TOKEN")).build()
    conv = ConversationHandler(
        entry_points=[CommandHandler('start', start)],
        states={
            ID: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_id)],
            HASH: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_hash)],
            PHONE: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_phone)],
            CODE: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_code)],
            PASS: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_pass)],
        },
        fallbacks=[CommandHandler('start', start)],
        allow_reentry=True
    )
    bot.add_handler(conv)
    bot.run_polling()

if __name__ == "__main__":
    threading.Thread(target=run, daemon=True).start()
    main()
