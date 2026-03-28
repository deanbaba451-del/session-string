import asyncio
import os
from flask import Flask
from threading import Thread
from aiogram import Bot, Dispatcher, types, executor

# --- YAPILANDIRMA ---
h = os.getenv("h") # Render'da değişken adını 'h' yap
OWNER_ID = 6534222591

# --- FLASK SERVER ---
app = Flask('')

@app.route('/')
def home():
    return "Bot Aktif!"

def run():
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 8080)))

def keep_alive():
    t = Thread(target=run)
    t.daemon = True
    t.start()

# --- BOT MANTIĞI ---
bot = Bot(token=h)
dp = Dispatcher(bot)

storage = {"content": None, "type": None, "is_spamming": False}

@dp.message_handler(commands=['cpspamla'])
async def start_spam(message: types.Message):
    if message.from_user.id != OWNER_ID:
        return
    if not storage["content"]:
        await message.reply("Hafıza boş!")
        return

    storage["is_spamming"] = True
    while storage["is_spamming"]:
        try:
            c, t = storage["content"], storage["type"]
            if t == "text": await bot.send_message(message.chat.id, c)
            elif t == "photo": await bot.send_photo(message.chat.id, c)
            elif t == "video": await bot.send_video(message.chat.id, c)
            elif t == "voice": await bot.send_voice(message.chat.id, c)
            elif t == "video_note": await bot.send_video_note(message.chat.id, c)
            elif t == "audio": await bot.send_audio(message.chat.id, c)
            elif t == "document": await bot.send_document(message.chat.id, c)
            await asyncio.sleep(0.2)
        except:
            await asyncio.sleep(1)

@dp.message_handler(commands=['cpdur'])
async def stop_spam(message: types.Message):
    if message.from_user.id == OWNER_ID:
        storage["is_spamming"] = False
        await message.answer("qq infaz verildi")

@dp.message_handler(content_types=types.ContentType.ANY)
async def store_media(message: types.Message):
    if message.from_user.id != OWNER_ID or (message.text and message.text.startswith('/')):
        return

    if message.text: storage["content"], storage["type"] = message.text, "text"
    elif message.photo: storage["content"], storage["type"] = message.photo[-1].file_id, "photo"
    elif message.video: storage["content"], storage["type"] = message.video.file_id, "video"
    elif message.voice: storage["content"], storage["type"] = message.voice.file_id, "voice"
    elif message.video_note: storage["content"], storage["type"] = message.video_note.file_id, "video_note"
    elif message.audio: storage["content"], storage["type"] = message.audio.file_id, "audio"
    elif message.document: storage["content"], storage["type"] = message.document.file_id, "document"
    await message.reply("Kaydedildi.")

if __name__ == '__main__':
    keep_alive()
    executor.start_polling(dp, skip_updates=True)
