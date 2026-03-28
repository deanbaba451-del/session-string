import os
import asyncio
import aiohttp
from aiogram import Bot, Dispatcher, F
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, Message, CallbackQuery
from aiogram.filters import Command
from aiohttp import web

# --- RENDER.COM PORT DİNLEME (FLASK YERİNE AIOHTTP) ---
async def handle(request):
    return web.Response(text="Bot Aktif!")

async def start_web_server():
    app = web.Application()
    app.router.add_get('/', handle)
    runner = web.AppRunner(app)
    await runner.setup()
    # Render'ın verdiği portu buradan yakalıyor
    port = int(os.environ.get('PORT', 8080))
    site = web.TCPSite(runner, '0.0.0.0', port)
    await site.start()

# --- AYARLAR ---
TOKEN = "8606960539:AAGnZRWG0Lb4KnTgXdmBt0G1NQoAEJjyUD0"
BASE_URL = "https://arastir.sbs/api"

bot = Bot(token=TOKEN)
dp = Dispatcher()
user_action = {}

# --- GÖRSELDEKİ MENÜ SIRALAMASI ---
def main_menu():
    kb = [
        [InlineKeyboardButton(text="🏠 Anasayfa", callback_data="s_home")],
        [InlineKeyboardButton(text="👤 Ad Soyad Sorgula", callback_data="s_adsoyad")],
        [InlineKeyboardButton(text="💳 TC Sorgula", callback_data="s_tc")],
        [InlineKeyboardButton(text="🏢 İşyeri Sorgula", callback_data="s_isyeri")],
        [InlineKeyboardButton(text="📍 Adres Sorgula", callback_data="s_adres")],
        [InlineKeyboardButton(text="👨‍👩‍👧‍👦 Aile Sorgula", callback_data="s_aile")],
        [InlineKeyboardButton(text="🏘️ Sülale Sorgula", callback_data="s_sulale")],
        [InlineKeyboardButton(text="👶 Çocuk Sorgula", callback_data="s_cocuk")],
        [InlineKeyboardButton(text="📱 TC-GSM Sorgula", callback_data="s_tcgsm")],
        [InlineKeyboardButton(text="📞 GSM-TC Sorgula", callback_data="s_gsmtc")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=kb)

@dp.message(Command("start"))
async def start(message: Message):
    await message.answer(f"👋 Selam **{message.from_user.first_name}**,\nLütfen işlem seç:", 
                         reply_markup=main_menu(), parse_mode="Markdown")

@dp.callback_query(F.data.startswith("s_"))
async def callback(call: CallbackQuery):
    action = call.data.split("_")[1]
    user_action[call.from_user.id] = action
    
    prompts = {
        "adsoyad": "👤 Ad ve Soyad giriniz (Örn: Ali Veli):",
        "gsmtc": "📞 GSM No giriniz (0 olmadan):",
        "tc": "💳 11 Haneli TC giriniz:"
    }
    await call.message.answer(prompts.get(action, "📝 Sorgulanacak TC No giriniz:"))
    await call.answer()

@dp.message()
async def query(message: Message):
    uid = message.from_user.id
    if uid not in user_action: return
    
    act = user_action[uid]
    status = await message.reply("⌛ Veritabanı taranıyor...")
    
    async with aiohttp.ClientSession() as session:
        try:
            if act == "adsoyad":
                p = message.text.split()
                url = f"{BASE_URL}/adsoyad.php?adi={p[0]}&soyadi={p[1]}"
            elif act == "gsmtc":
                url = f"{BASE_URL}/gsmtc.php?gsm={message.text}"
            else:
                url = f"{BASE_URL}/{act}.php?tc={message.text}"
            
            async with session.get(url) as r:
                data = await r.json()
                if not data:
                    await status.edit("❌ Kayıt bulunamadı.")
                else:
                    # Gelen JSON verisini basitçe yazdırır, burayı görsele göre süsleyebilirsin
                    await status.edit(f"📋 **Sonuçlar:**\n\n`{str(data)}`", parse_mode="Markdown")
        except:
            await status.edit("⚠️ API hatası oluştu.")
    
    del user_action[uid]

async def main():
    # Hem web server'ı hem botu aynı anda başlatıyoruz
    await start_web_server()
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
