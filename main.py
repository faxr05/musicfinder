import os
import asyncio
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.utils.keyboard import InlineKeyboardBuilder
from yt_dlp import YoutubeDL
import nest_asyncio
nest_asyncio.apply()

# --- SOZLAMALAR ---
TOKEN = os.getenv("BOT_TOKEN")  # BotFather'dan olgan tokeningizni qo'ying

bot = Bot(token=TOKEN)
dp = Dispatcher()

# YouTube qidiruv sozlamalari
YDL_OPTIONS = {
    'format': 'bestaudio/best',
    'noplaylist': True,
    'quiet': True,
    'no_warnings': True,
}

# Yuklab olish sozlamalari
DOWNLOAD_OPTIONS = {
    'format': 'bestaudio/best',
    'outtmpl': 'downloads/%(title)s.%(ext)s',
    'postprocessors': [{
        'key': 'FFmpegExtractAudio',
        'preferredcodec': 'mp3',
        'preferredquality': '192',
    }],
    'quiet': True,
}

# 1. Qidiruv funksiyasi
def search_music(query):
    with YoutubeDL(YDL_OPTIONS) as ydl:
        try:
            results = ydl.extract_info(f"ytsearch5:{query}", download=False)['entries']
            return [{"title": r['title'], "url": r['webpage_url'], "id": r['id']} for r in results]
        except Exception:
            return []

# 2. Start buyrug'i
@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    await message.answer("Sizga qanday musiqa topib beray? Ismini yoki ijrochisini yozing.")

# 3. Matn kelganda qidirish
@dp.message(F.text)
async def handle_text(message: types.Message):
    status_msg = await message.answer("🔍 Qidiryapman...")
    tracks = search_music(message.text)

    if not tracks:
        await status_msg.edit_text("Hech narsa topilmadi 😔")
        return

    builder = InlineKeyboardBuilder()
    for track in tracks:
        # Har bir musiqa uchun tugma (ID orqali bog'lanadi)
        builder.row(types.InlineKeyboardButton(
            text=f"🎵 {track['title'][:45]}",
            callback_data=f"song_{track['id']}")
        )

    await status_msg.delete()
    await message.answer("Topilgan natijalar:", reply_markup=builder.as_markup())

# 4. Musiqa tanlanganda yuklash
@dp.callback_query(F.data.startswith("song_"))
async def download_song(callback: types.CallbackQuery):
    video_id = callback.data.replace("song_", "")
    url = f"https://www.youtube.com/watch?v={video_id}"

    await callback.message.edit_text("📥 Yuklanmoqda, iltimos kuting...")

    if not os.path.exists('downloads'):
        os.makedirs('downloads')

    try:
        with YoutubeDL(DOWNLOAD_OPTIONS) as ydl:
            info = ydl.extract_info(url, download=True)
            file_path = ydl.prepare_filename(info).replace(info['ext'], 'mp3')

        audio = types.FSInputFile(file_path)
        await callback.message.answer_audio(audio, caption="@SizningBotingiz")
        await callback.message.delete()

        # O'chirib tashlash
        os.remove(file_path)
    except Exception as e:
        await callback.message.answer(f"Xatolik: FFmpeg o'rnatilmagan yoki xato yuz berdi.")
        print(f"Xato: {e}")

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
