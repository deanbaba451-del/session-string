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
BOT_TOKEN = '8397494337:AAFD2hFlePQ7s_RYfMQoPP0S_9YWLGpac74'
GEMINI_API_KEY = 'AIzaSyCJuanxIdOg9UHAQRDkNjXv4gZjvZ9W1vg'

# YETKİLİ LİSTESİ (Sadece bunlar komut verebilir)
OWNER_IDS = [6534222591, 8256872080, 8656150458] 
HASRET_ID = 6534222591 # Ana patron

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

# --- YETKİ KONTROLÜ ---
def is_owner(user_id):
    return user_id in OWNER_IDS

# --- START MESAJI ---
@dp.message(Command("start"))
async def start_cmd(message: types.Message):
    if message.chat.type == "private":
        builder = InlineKeyboardBuilder()
        builder.row(types.InlineKeyboardButton(text="Beni Grubuna Ekle Orospu Evladı", url=f"https://t.me/{(await bot.get_me()).username}?startgroup=true"))
        await message.answer("GRUBUNDA YOKUM OROSPU EVLADI GRUBUNA EKLE BENİ", reply_markup=builder.as_markup())

# --- ÖZEL ETİKETLEME (SADECE OWNER) ---

@dp.message(Command("ocatag"))
async def admin_tag(message: types.Message):
    if not is_owner(message.from_user.id):
        await message.reply("uapamazsın orospu çocuğu seni!")
        return
    
    tag_status["admin"] = True
    admins = await bot.get_chat_administrators(message.chat.id)
    await message.answer("📢 Adminleri sikme başladı")
    for admin in admins:
        if not tag_status["admin"]: break
        if not admin.user.is_bot:
            await message.answer(f"[{admin.user.first_name}](tg://user?id={admin.user.id}) UYAN OROSPU ÇOCUĞU!", parse_mode="Markdown")
            await asyncio.sleep(1.5)

@dp.message(Command("abitir"))
async def stop_admin_tag(message: types.Message):
    if not is_owner(message.from_user.id): return
    tag_status["admin"] = False
    await message.reply("Tamam, adminleri tecavüz etmeyi durdurdum.")

@dp.message(Command("ocutag"))
async def user_tag(message: types.Message):
    if not is_owner(message.from_user.id):
        await message.reply("sen yapamazsın orospu çocuğu!")
        return
    
    tag_status["user"] = True
    conn = sqlite3.connect('analiz.db'); c = conn.cursor()
    c.execute("SELECT user_id, name FROM stats WHERE chat_id = ?", (str(message.chat.id),))
    users = c.fetchall(); conn.close()
    
    await message.answer(" Üyeler tek tek sikiliyor...")
    for uid, name in users:
        if not tag_status["user"]: break
        if int(uid) in OWNER_IDS: continue # Patronlara dokunma
        try:
            p = f"{name} isimli üyeye en ağır küfürleri et. 'Hasret senin gibi orospu çocuğu değil' de."
            res = model.generate_content(p)
            await message.answer(f"[{name}](tg://user?id={uid})\n\n{res.text}", parse_mode="Markdown")
            await asyncio.sleep(2)
        except: pass

@dp.message(Command("ubitir"))
async def stop_user_tag(message: types.Message):
    if not is_owner(message.from_user.id): return
    tag_status["user"] = False
    await message.reply("Üyelerin bakireliği alındı.")

# --- KORUMALI /SOV ---
@dp.message(Command("sov"))
async def revenge_curse(message: types.Message):
    if is_owner(message.from_user.id):
        await message.reply("Sen benim paşamsın, ben senin gibi orospu çocuğu değilim, emret yeter.")
        return

    # Hasret'e veya Owner'lara laf atılırsa
    if message.reply_to_message and is_owner(message.reply_to_message.from_user.id):
        p = f"{message.from_user.first_name} yetkiliye laf attı. Ona en ağır küfürleri et, 'O senin gibi o.ç. değil' de."
        res = model.generate_content(p)
        await message.answer(res.text)
        return

    target = message.reply_to_message.from_user.first_name if message.reply_to_message else "qq"
    p = f"{target} isimli kişiye en ağır ve sansürsüz küfürleri savur."
    res = model.generate_content(p)
    await message.answer(res.text)

# --- ANALİZ VE RENDER ---
@dp.message()
async def analyze(message: types.Message):
    if not message.chat.type in ["group", "supergroup"] or not message.text or message.text.startswith('/'): return
    try:
        p = f"Bu mesajı 0-100 arası iticilikle puanla. Sadece rakam: '{message.text}'"
        res = model.generate_content(p)
        score = int(''.join(filter(str.isdigit, res.text)))
        conn = sqlite3.connect('analiz.db'); c = conn.cursor()
        c.execute("INSERT OR IGNORE INTO stats (chat_id, user_id, name) VALUES (?, ?, ?)", (str(message.chat.id), str(message.from_user.id), message.from_user.first_name))
        c.execute("UPDATE stats SET total_puan = total_puan + ? WHERE chat_id = ? AND user_id = ?", (score, str(message.chat.id), str(message.from_user.id)))
        conn.commit(); conn.close()
    except: pass

@app.route('/')
def home(): return "Hasret ve Ekibi İçin Sistem Aktif."

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
