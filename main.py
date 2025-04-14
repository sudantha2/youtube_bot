import os
import logging
from flask import Flask
from downloader import download_video
from telegram import (
    InlineQueryResultArticle, InputTextMessageContent, Update,
    InlineKeyboardMarkup, InlineKeyboardButton
)
from telegram.ext import (
    ApplicationBuilder, ContextTypes, InlineQueryHandler,
    CallbackQueryHandler, CommandHandler
)
import uuid
import yt_dlp

TOKEN = os.getenv("BOT_TOKEN")

app = Flask(__name__)  # for Render ping

@app.route('/')
def home():
    return 'Bot is running!'

# ========== INLINE SEARCH ==========
async def inline_query_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.inline_query.query
    if not query:
        return

    results = []
    with yt_dlp.YoutubeDL({'quiet': True}) as ydl:
        search_results = ydl.extract_info(f"ytsearch5:{query}", download=False)['entries']
        for entry in search_results:
            results.append(
                InlineQueryResultArticle(
                    id=str(uuid.uuid4()),
                    title=entry['title'],
                    input_message_content=InputTextMessageContent(
                        message_text=f"🎬 *{entry['title']}*\nChannel: {entry.get('channel') or entry.get('uploader')}\nDuration: {entry['duration']} seconds\n\nSelect download format:",
                        parse_mode='Markdown'
                    ),
                    reply_markup=InlineKeyboardMarkup([
                        [
                            InlineKeyboardButton("144p", callback_data=f"{entry['webpage_url']}|144p"),
                            InlineKeyboardButton("360p", callback_data=f"{entry['webpage_url']}|360p"),
                            InlineKeyboardButton("720p", callback_data=f"{entry['webpage_url']}|720p"),
                        ],
                        [
                            InlineKeyboardButton("1080p", callback_data=f"{entry['webpage_url']}|1080p"),
                            InlineKeyboardButton("MP3", callback_data=f"{entry['webpage_url']}|mp3")
                        ]
                    ]),
                    description=entry.get('description', '')[:50],
                    thumb_url=entry.get('thumbnail')
                )
            )

    await update.inline_query.answer(results, cache_time=1)

# ========== HANDLE DOWNLOAD ==========
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    url, format_ = query.data.split("|")
    audio = format_.lower() == "mp3"
    msg = await query.message.reply_text("📥 Downloading, please wait...")

    try:
        file_path = download_video(url, quality=format_, audio_only=audio)
        with open(file_path, 'rb') as f:
            if audio:
                await query.message.reply_audio(audio=f)
            else:
                await query.message.reply_video(video=f)
        os.remove(file_path)
    except Exception as e:
        await msg.edit_text(f"❌ Error: {str(e)}")

# ========== START ==========
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Hi! Type @YourBotName in any chat to search YouTube and download videos 🎬")

def run_bot():
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

    from threading import Thread
    Thread(target=run_bot).start()

    app_bot = ApplicationBuilder().token(TOKEN).build()
    app_bot.add_handler(InlineQueryHandler(inline_query_handler))
    app_bot.add_handler(CallbackQueryHandler(button_handler))
    app_bot.add_handler(CommandHandler("start", start))
    app_bot.run_polling()
