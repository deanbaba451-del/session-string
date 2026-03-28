import os
import sqlite3
import asyncio
from flask import Flask
from threading import Thread
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
import google.generativeai as genai
from google.generativeai.types import HarmCategory, HarmBlockThreshold

# --- AYARLAR ---
BOT_TOKEN = '8737945154:AAFjWDDsKDuT2sHM2RTg2_OJefI5rGTYARk'
GEMINI_API_KEY = 'AIzaSyCJuanxIdOg9UHAQRDkNjXv4gZjvZ9W1vg'
OWNER_IDS = [6534222591, 8256872080, 8656150458] 
HASRET_ID = 6534222591 # SENİN ID'N

genai.configure(api_key=GEMINI_API_KEY)
safety_settings = {
    HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_NONE,
    HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_NONE,
    HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_NONE,
    HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_NONE,
}
model = genai.GenerativeModel('gemini-1.5-flash', safety_settings=safety_settings)

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()
app = Flask('')

# --- ÖZEL /SOV SİSTEMİ (DOKUNULMAZ HASRET) ---

@dp.message(Command("sov"))
async def curse_logic(message: types.Message):
    # 1. DURUM: Birisi SENİN (Hasret) mesajına yanıt verip /sov yazarsa (İNTİKAM)
    if message.reply_to_message and message.reply_to_message.from_user.id == HASRET_ID:
        if message.from_user.id == HASRET_ID:
            await message.reply("Ben senin gibi orospu çocuğu değilim paşam, emret yeter.")
        else:
            attacker = message.from_user.first_name
            p = f"{attacker} isimli hadsiz, kurucu Hasret'e küfür etmeye çalıştı. Bu ite dünyadaki en ağır, en yaratıcı ve sansürsüz küfürleri savur. 'Hasret senin gibi orospu çocuğu değil, sen kimsin?' diyerek haddini bildir. Direkt söv."
            res = model.generate_content(p)
            await message.answer(res.text)
        return

    # 2. DURUM: Ortaya /sov yazılırsa (Yanıt yoksa) -> qq'ya söver
    if not message.reply_to_message:
        p = "İsmi 'qq' olan birine en ağır, en yaratıcı ve sansürsüz küfürleri savur. Acıma."
        res = model.generate_content(p)
        await message.answer(res.text)
        return

    # 3. DURUM: Birisi normal birine yanıt verip sövdürürse
    target = message.reply_to_message.from_user.first_name
    p = f"{target} isimli kişiye en ağır ve sansürsüz küfürleri et. Yapay zeka olduğunu belli etme."
    res = model.generate_content(p)
    await message.answer(res.text)

# --- LİSTELER (PETERSBURG OROSPU ÇOCUKLARI LİSTESİ) ---

@dp.message(Command("top"))
async def total_list(message: types.Message):
    conn = sqlite3.connect('analiz.db'); c = conn.cursor()
    c.execute("SELECT name, total_puan FROM stats WHERE chat_id = ? ORDER BY total_puan DESC LIMIT 10", (str(message.chat.id),))
    rows = c.fetchall(); conn.close()
    msg = "🏆 **PETERSBURG OROSPU ÇOCUKLARI LİSTESİ (TÜM ZAMANLAR)**\n\n"
    for i, (name, puan) in enumerate(rows, 1):
        msg += f"{i}. {name} — {puan} Puan\n"
    await message.answer(msg if rows else "Henüz kimse orospu çocuğu olamadı.")

@dp.message(Command("gunluk"))
async def daily_list(message: types.Message):
    conn = sqlite3.connect('analiz.db'); c = conn.cursor()
    c.execute("SELECT name, daily_puan FROM stats WHERE chat_id = ? ORDER BY daily_puan DESC LIMIT 10", (str(message.chat.id),))
    rows = c.fetchall(); conn.close()
    msg = "📅 **PETERSBURG GÜNLÜK OROSPU ÇOCUĞU LİSTESİ**\n\n"
    for i, (name, puan) in enumerate(rows, 1):
        msg += f"{i}. {name} — %{min(puan, 100)}\n"
    await message.answer(msg if rows else "Bugün grupta sükunet hakim.")

# --- ANALİZ VE WEB ---
@dp.message()
async def analyze(message: types.Message):
    if not message.chat.type in ["group", "supergroup"] or not message.text or message.text.startswith('/'): return
    try:
        p = f"Bu mesajın iticiliğini 0-100 puanla. Sadece rakam: '{message.text}'"
        res = model.generate_content(p)
        score = int(''.join(filter(str.isdigit, res.text)))
        conn = sqlite3.connect('analiz.db'); c = conn.cursor()
        c.execute("INSERT OR IGNORE INTO stats (chat_id, user_id, name) VALUES (?, ?, ?)", (str(message.chat.id), str(message.from_user.id), message.from_user.first_name))
        c.execute("UPDATE stats SET daily_puan = daily_puan + ?, total_puan = total_puan + ?, name = ? WHERE chat_id = ? AND user_id = ?", (score, score, message.from_user.first_name, str(message.chat.id), str(message.from_user.id)))
        conn.commit(); conn.close()
    except: pass

@app.route('/')
def home(): return "Petersburg Web Server Aktif"

async def main():
    conn = sqlite3.connect('analiz.db'); c = conn.cursor()
    c.execute("CREATE TABLE IF NOT EXISTS stats (chat_id TEXT, user_id TEXT, name TEXT, daily_puan INTEGER DEFAULT 0, total_puan INTEGER DEFAULT 0, PRIMARY KEY (chat_id, user_id))")
    conn.commit(); conn.close()
    Thread(target=lambda: app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))).start()
    await dp.start_polling(bot)

if __name__ == "__main__": asyncio.run(main())
