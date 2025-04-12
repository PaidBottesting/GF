
import logging
from telegram import Update, ChatAction
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters
import google.generativeai as genai
import os

# CONFIGURATION
ADMIN_ID =  1866961136  # Change this to your admin user ID
GEMINI_API_KEY = "AIzaSyDAm_zAas5YQdQTCI2WoxYDEOXZfwpXUDc"  # Replace with your Gemini API Key

genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel("gemini-pro")
logging.basicConfig(level=logging.INFO)

# Romantic Replies
moods = {
    "sad": "Aww, baby don't be sad. I'm here with you forever.",
    "angry": "Why so angry baby? Come here, let me hug you tight.",
    "jealous": "Wait... who are you texting? I'm watching you, baby!",
}

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("""
I’m your Baby Bot. Here's what I can do:
/start - Start the love story
/help - Show commands
/voice - Hear me say 'I love you'
/sticker - Get a cute sticker
""")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id == ADMIN_ID:
        await update.message.reply_text("Hey baby! Your girl is here just for you.")
    else:
        await update.message.reply_text("Sorry, I only talk to my baby (admin).")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id != ADMIN_ID:
        return

    msg = update.message.text.lower()
    await context.bot.send_chat_action(chat_id=update.effective_chat.id, action=ChatAction.TYPING)

    for mood in moods:
        if mood in msg:
            await update.message.reply_text(moods[mood])
            return

    try:
        response = model.generate_content(update.message.text)
        await update.message.reply_text(response.text)
    except Exception as e:
        logging.error(f"Gemini error: {e}")
        await update.message.reply_text("I'm feeling shy... try again later!")

async def send_voice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id == ADMIN_ID:
        path = "voices/i_love_you.ogg"
        if os.path.exists(path):
            await update.message.reply_voice(voice=open(path, 'rb'))
        else:
            await update.message.reply_text("My voice file is missing!")

async def send_sticker(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id == ADMIN_ID:
        try:
            await update.message.reply_sticker("CAACAgUAAxkBAAIBY2ZfIDq0tQ_y8yf0XWlx-KltBY0RAAJOAQACvWzpVBa7ZAWTnWa4NAQ")
        except Exception as e:
            await update.message.reply_text("Sticker error!")

if __name__ == '__main__':
    app = ApplicationBuilder().token("7637073475:AAEuGTS_TKertVJz1ZYjwwtM2d0KP-8l1qA").build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("voice", send_voice))
    app.add_handler(CommandHandler("sticker", send_sticker))
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_message))

    print("Baby Bot is live...")
    app.run_polling()
