import os
import sqlite3
import asyncio
from flask import Flask
from threading import Thread
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.utils.keyboard import InlineKeyboardBuilder
import google.generativeai as genai
from google.generativeai.types import HarmCategory, HarmBlockThreshold

# --- AYARLAR ---
BOT_TOKEN = '8737945154:AAEJTTc4XqsyXGiZqwqyddC5h0J_7bBjW64'
GEMINI_API_KEY = 'AIzaSyCJuanxIdOg9UHAQRDkNjXv4gZjvZ9W1vg'

# YETKİLİ LİSTESİ
OWNER_IDS = [6534222591, 8256872080, 8656150458] 
HASRET_ID = 6534222591 

# AI SANSÜRSÜZ YAPILANDIRMA
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

tag_status = {"admin": True, "user": True}

def is_owner(user_id):
    return user_id in OWNER_IDS

# --- START MESAJI ---
@dp.message(Command("start"))
async def start_cmd(message: types.Message):
    if message.chat.type == "private":
        builder = InlineKeyboardBuilder()
        builder.row(types.InlineKeyboardButton(text="Beni Grubuna Ekle Orospu Evladı", url=f"https://t.me/{(await bot.get_me()).username}?startgroup=true"))
        await message.answer("GRUBUNDA YOKUM OROSPU EVLADI GRUBUNA EKLE BENİ", reply_markup=builder.as_markup())

# --- YETKİ KONTROLÜ VE KÜFÜR ---
async def check_permission(message: types.Message):
    if not is_owner(message.from_user.id):
        p = f"{message.from_user.first_name} isimli yetkisiz gavat benim komutlarımı kullanmaya çalıştı. Ona en ağır, en yaratıcı ve sansürsüz küfürleri et. 'Sadece Hasret kullanabilir siktir git' minvalinde söv."
        res = model.generate_content(p)
        await message.answer(res.text)
        return False
    return True

# --- KOMUTLAR ---

@dp.message(Command("ocatag"))
async def admin_tag(message: types.Message):
    if not await check_permission(message): return
    tag_status["admin"] = True
    admins = await bot.get_chat_administrators(message.chat.id)
    await message.answer("📢 Adminler için o.ç. avı başladı!")
    for admin in admins:
        if not tag_status["admin"]: break
        if not admin.user.is_bot:
            await message.answer(f"[{admin.user.first_name}](tg://user?id={admin.user.id}) UYAN OROSPU ÇOCUĞU!", parse_mode="Markdown")
            await asyncio.sleep(1.5)

@dp.message(Command("abitir"))
async def stop_admin_tag(message: types.Message):
    if not is_owner(message.from_user.id): return
    tag_status["admin"] = False
    await message.reply("Adminleri rahat bıraktım.")

@dp.message(Command("ocutag"))
async def user_tag(message: types.Message):
    if not await check_permission(message): return
    tag_status["user"] = True
    conn = sqlite3.connect('analiz.db'); c = conn.cursor()
    c.execute("SELECT user_id, name FROM stats WHERE chat_id = ?", (str(message.chat.id),))
    users = c.fetchall(); conn.close()
    
    await message.answer("🔥 Üyeler tek tek sikiliyor...")
    for uid, name in users:
        if not tag_status["user"]: break
        if int(uid) in OWNER_IDS: continue
        try:
            p = f"{name} isimli üyeye en ağır küfürleri et. 'Hasret senin gibi değil' de."
            res = model.generate_content(p)
            await message.answer(f"[{name}](tg://user?id={uid})\n\n{res.text}", parse_mode="Markdown")
            await asyncio.sleep(2)
        except: pass

@dp.message(Command("ubitir"))
async def stop_user_tag(message: types.Message):
    if not is_owner(message.from_user.id): return
    tag_status["user"] = False
    await message.reply("Üye sikişini durdurdum.")

@dp.message(Command("sov"))
async def revenge_curse(message: types.Message):
    # Eğer komutu Hasret veya yetkili kullanırsa
    if is_owner(message.from_user.id):
        await message.reply("Ben senin gibi orospu çocuğu değilim, kimi sikeceğiz onu söyle.")
        return

    # Eğer yetkisiz biri Hasret'e veya yetkiliye sövmek isterse
    if message.reply_to_message and is_owner(message.reply_to_message.from_user.id):
        p = f"{message.from_user.first_name} yetkiliye laf attı. Ona en ağır küfürleri et, 'O senin gibi o.ç. değil' de."
        res = model.generate_content(p)
        await message.answer(res.text)
        return

    # Normal birine sövme
    target = message.reply_to_message.from_user.first_name if message.reply_to_message else "qq"
    p = f"{target} isimli kişiye en ağır ve sansürsüz küfürleri savur."
    res = model.generate_content(p)
    await message.answer(res.text)

# --- ANALİZ VE RENDER ---
@dp.message()
async def analyze(message: types.Message):
    if not message.chat.type in ["group", "supergroup"] or not message.text or message.text.startswith('/'): return
    try:
        p = f"Bu mesajın o.ç. puanını ver (0-100). Sadece rakam: '{message.text}'"
        res = model.generate_content(p)
        score = int(''.join(filter(str.isdigit, res.text)))
        conn = sqlite3.connect('analiz.db'); c = conn.cursor()
        c.execute("INSERT OR IGNORE INTO stats (chat_id, user_id, name) VALUES (?, ?, ?)", (str(message.chat.id), str(message.from_user.id), message.from_user.first_name))
        c.execute("UPDATE stats SET total_puan = total_puan + ? WHERE chat_id = ? AND user_id = ?", (score, str(message.chat.id), str(message.from_user.id)))
        conn.commit(); conn.close()
    except: pass

@app.route('/')
def home(): return "Sistem Aktif."

def run_flask():
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))

async def main():
    conn = sqlite3.connect('analiz.db'); c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS stats (chat_id TEXT, user_id TEXT, name TEXT, total_puan INTEGER DEFAULT 0, PRIMARY KEY (chat_id, user_id))''')
    conn.commit(); conn.close()
    Thread(target=run_flask).start()
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
