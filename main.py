import os
import sqlite3
import asyncio
from flask import Flask
from threading import Thread
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
import google.generativeai as genai
from datetime import datetime, timedelta

# --- AYARLAR ---
BOT_TOKEN = '8737945154:AAEJTTc4XqsyXGiZqwqyddC5h0J_7bBjW64'
GEMINI_API_KEY = 'AIzaSyCJuanxIdOg9UHAQRDkNjXv4gZjvZ9W1vg'
GRUP_ID = -1003873976696

# AI Yapılandırması
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel('gemini-1.5-flash')

# --- VERİTABANI ---
def db_setup():
    conn = sqlite3.connect('analiz.db')
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS stats 
                      (user_id TEXT PRIMARY KEY, name TEXT, puan INTEGER)''')
    conn.commit()
    conn.close()

def update_puan(user_id, name, ek_puan):
    conn = sqlite3.connect('analiz.db')
    cursor = conn.cursor()
    cursor.execute("INSERT OR IGNORE INTO stats (user_id, name, puan) VALUES (?, ?, 0)", (user_id, name))
    cursor.execute("UPDATE stats SET puan = puan + ?, name = ? WHERE user_id = ?", (ek_puan, name, user_id))
    conn.commit()
    conn.close()

def get_rankings():
    conn = sqlite3.connect('analiz.db')
    cursor = conn.cursor()
    cursor.execute("SELECT name, puan FROM stats ORDER BY puan DESC LIMIT 10")
    data = cursor.fetchall()
    conn.close()
    return data

def reset_db():
    conn = sqlite3.connect('analiz.db')
    cursor = conn.cursor()
    cursor.execute("DELETE FROM stats")
    conn.commit()
    conn.close()

# --- RENDER FLASK ---
app = Flask('')
@app.route('/')
def home(): return "Sessiz Analiz Aktif!"

def run_flask():
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))

# --- BOT MANTIĞI ---
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

@dp.message(Command("kim"))
async def manual_check(message: types.Message):
    rankings = get_rankings()
    if not rankings:
        await message.reply("Henüz veri yok.")
        return
    msg = "📊 **GÜNCEL OROSPU ÇOCUĞU SKORLARI** 📊\n\n"
    for i, (name, puan) in enumerate(rankings, 1):
        msg += f"{i}. {name} — %{min(puan, 100)} O.Ç.\n"
    await message.answer(msg)

@dp.message()
async def ai_collector(message: types.Message):
    if not message.chat.type in ["group", "supergroup"] or not message.text:
        return
    
    user_id = str(message.from_user.id)
    name = message.from_user.first_name
    
    try:
        # AI Analizi (Sessizce puanlar)
        prompt = f"Bu mesajı 'iticilik ve toksiklik' açısından 0-100 arası puanla. Sadece rakam: '{message.text}'"
        response = model.generate_content(prompt)
        score_str = ''.join(filter(str.isdigit, response.text))
        score = int(score_str) if score_str else 1
        update_puan(user_id, name, score)
    except:
        update_puan(user_id, name, 1)

# Gece 00:00 Raporu (TR Saati UTC+3)
async def timer_task():
    while True:
        now = (datetime.utcnow() + timedelta(hours=3)).strftime("%H:%M")
        if now == "00:00":
            rankings = get_rankings()
            if rankings:
                msg = f"📅 **{datetime.now().strftime('%d/%m/%Y')} GÜNÜN OROSPU ÇOCUĞU LİSTESİ**\n"
                msg += "--------------------------------------\n"
                for i, (name, puan) in enumerate(rankings, 1):
                    msg += f"{i}. {name} — %{min(puan, 100)} OROSPU ÇOCUĞU\n"
                msg += "\n_Yeni gün başladı, günahlar sıfırlandı._"
                await bot.send_message(GRUP_ID, msg)
                reset_db()
            await asyncio.sleep(60)
        await asyncio.sleep(30)

async def main():
    db_setup()
    Thread(target=run_flask).start()
    asyncio.create_task(timer_task())
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
