import os
import asyncio
import aiohttp
from aiogram import Bot, Dispatcher, F
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, Message, CallbackQuery
from aiogram.filters import Command
from aiohttp import web

# --- RENDER PORT AYARI (BOTUN KAPANMAMASI İÇİN) ---
async def handle(request):
    return web.Response(text="Bot Aktif!")

async def start_web_server():
    app = web.Application()
    app.router.add_get('/', handle)
    runner = web.AppRunner(app)
    await runner.setup()
    # Render'ın verdiği portu otomatik yakalar
    site = web.TCPSite(runner, '0.0.0.0', int(os.environ.get('PORT', 8080)))
    await site.start()

# --- BOT AYARLARI ---
TOKEN = "8606960539:AAGnZRWG0Lb4KnTgXdmBt0G1NQoAEJjyUD0"
BASE_URL = "https://arastir.sbs/api"

bot = Bot(token=TOKEN)
dp = Dispatcher()

# --- GÖRSELDEKİ ANA MENÜ ---
def main_menu():
    kb = [
        [InlineKeyboardButton(text="🏠 Anasayfa", callback_data="m_home")],
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

# --- SORGULAMA DURUMU ---
user_action = {}

@dp.message(Command("start"))
async def start(message: Message):
    await message.reply(f"👋 Merhaba **{message.from_user.first_name}**,\n\n👇 Lütfen işlemini seç.", 
                        reply_markup=main_menu(), parse_mode="Markdown")

@dp.callback_query(F.data.startswith("s_"))
async def handle_callback(call: CallbackQuery):
    action = call.data.split("_")[1]
    user_action[call.from_user.id] = action
    
    texts = {
        "adsoyad": "👤 Ad ve Soyad giriniz (Örn: Ahmet Yılmaz):",
        "gsmtc": "📞 GSM No giriniz (Başında 0 olmadan):",
        "tc": "💳 11 Haneli TC No giriniz:"
    }
    await call.message.answer(texts.get(action, "📝 Lütfen sorgulanacak TC No giriniz:"))
    await call.answer()

@dp.message()
async def query_handler(message: Message):
    uid = message.from_user.id
    if uid not in user_action: return
    
    action = user_action[uid]
    status = await message.reply("🔍 Veritabanı taranıyor...")
    
    async with aiohttp.ClientSession() as session:
        try:
            # API İstek Hazırlığı
            if action == "adsoyad":
                parts = message.text.split()
                url = f"{BASE_URL}/adsoyad.php?adi={parts[0]}&soyadi={parts[1]}"
            elif action == "gsmtc":
                url = f"{BASE_URL}/gsmtc.php?gsm={message.text}"
            else:
                url = f"{BASE_URL}/{action}.php?tc={message.text}"
            
            async with session.get(url) as resp:
                data = await resp.json()
                
                if not data:
                    await status.edit("🔍 Kayıt bulunamadı.")
                else:
                    # Görseldeki gibi sonuç formatı
                    res = "📋 **Sorgu Sonuçları:**\n\n"
                    if isinstance(data, list):
                        for item in data[:3]: # Çoklu kayıtta ilk 3'ü göster
                            res += f"👤 {item.get('adi')} {item.get('soyadi')}\n🆔 TC: `{item.get('tc')}`\n\n"
                    else:
                        res += f"👤 Ad Soyad: {data.get('adi')} {data.get('soyadi')}\n🆔 TC: `{data.get('tc')}`"
                    
                    await status.edit(res, parse_mode="Markdown")
        except:
            await status.edit("⚠️ API hatası oluştu.")
    
    del user_action[uid]

async def main():
    await start_web_server()
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
