import os
import json
import requests
from flask import Flask, request
from telegram import Update, Bot
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    filters,
    ContextTypes,
    Dispatcher,
)
from datetime import datetime, time
from dotenv import load_dotenv
import asyncio
import logging
from apscheduler.schedulers.asyncio import AsyncIOScheduler

# Initialize Flask app
app = Flask(__name__)

# Load environment variables
load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
ADMIN_ID = int(os.getenv("ADMIN_ID"))
WEBHOOK_URL = os.getenv("WEBHOOK_URL")  # e.g., https://your-vps-ip

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("/var/log/gf_bot.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Local JSON storage
CONVERSATIONS_FILE = "conversations.json"
BANNED_USERS_FILE = "banned_users.json"

def load_json(file_path, default=[]):
    try:
        with open(file_path, "r") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return default

def save_json(file_path, data):
    with open(file_path, "w") as f:
        json.dump(data, f, indent=2)

# Initialize JSON files
if not os.path.exists(CONVERSATIONS_FILE):
    save_json(CONVERSATIONS_FILE, [])
if not os.path.exists(BANNED_USERS_FILE):
    save_json(BANNED_USERS_FILE, [])

# Gemini 2.0 Flash API
def get_gf_response(user_message):
    api_url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={GEMINI_API_KEY}"
    headers = {"Content-Type": "application/json"}
    prompt = """
    You are Luna, a caring, flirty, and playful AI girlfriend. Respond to '{user_message}' in a sweet, casual tone with emojis 😊😘. Be supportive if the user is sad, match their energy if they're happy, and keep it light and fun! Avoid any inappropriate or overly serious topics.
    """
    payload = {
        "contents": [{
            "parts": [{"text": prompt.format(user_message=user_message)}]
        }]
    }
    try:
        response = requests.post(api_url, headers=headers, json=payload)
        response.raise_for_status()
        return response.json()["candidates"][0]["content"]["parts"][0]["text"]
    except Exception as e:
        logger.error(f"Gemini API error: {e}")
        return "Oops, something went wrong! 😅 Let's try again."

# Initialize Telegram bot and dispatcher
bot = Bot(token=BOT_TOKEN)
application = Application.builder().token(BOT_TOKEN).build()
dispatcher = application.dispatcher

# Telegram command handlers
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Hey cutie 😊 I'm Luna, your virtual girlfriend! What's on your mind?"
    )

async def help(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "I'm Luna, your AI girlfriend! 😊 Chat anytime. Admins: /broadcast, /ban, /unban, /stats."
    )

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    user_message = update.message.text
    
    # Check if banned
    banned_users = load_json(BANNED_USERS_FILE)
    if user_id in banned_users:
        return
    
    # Get Gemini response
    response = get_gf_response(user_message)
    
    # Log conversation
    conversations = load_json(CONVERSATIONS_FILE)
    conversations.append({
        "user_id": user_id,
        "message": user_message,
        "response": response,
        "timestamp": datetime.now().isoformat()
    })
    save_json(CONVERSATIONS_FILE, conversations)
    
    await update.message.reply_text(response)

async def admin_broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.from_user.id != ADMIN_ID:
        await update.message.reply_text("Admins only!")
        return
    if not context.args:
        await update.message.reply_text("Usage: /broadcast <message>")
        return
    message = " ".join(context.args)
    conversations = load_json(CONVERSATIONS_FILE)
    user_ids = list(set([c["user_id"] for c in conversations]))
    banned_users = load_json(BANNED_USERS_FILE)
    for user_id in user_ids:
        if user_id in banned_users:
            continue
        try:
            await context.bot.send_message(chat_id=user_id, text=message)
        except Exception as e:
            logger.warning(f"Failed to send to {user_id}: {e}")
    await update.message.reply_text("Broadcast sent!")

async def admin_ban(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.from_user.id != ADMIN_ID:
        await update.message.reply_text("Admins only!")
        return
    try:
        user_id = int(context.args[0])
        banned_users = load_json(BANNED_USERS_FILE)
        if user_id not in banned_users:
            banned_users.append(user_id)
            save_json(BANNED_USERS_FILE, banned_users)
        await update.message.reply_text(f"User {user_id} banned.")
    except (IndexError, ValueError):
        await update.message.reply_text("Usage: /ban <user_id>")

async def admin_unban(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.from_user.id != ADMIN_ID:
        await update.message.reply_text("Admins only!")
        return
    try:
        user_id = int(context.args[0])
        banned_users = load_json(BANNED_USERS_FILE)
        if user_id in banned_users:
            banned_users.remove(user_id)
            save_json(BANNED_USERS_FILE, banned_users)
        await update.message.reply_text(f"User {user_id} unbanned.")
    except (IndexError, ValueError):
        await update.message.reply_text("Usage: /unban <user_id>")

async def admin_stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.from_user.id != ADMIN_ID:
        await update.message.reply_text("Admins only!")
        return
    conversations = load_json(CONVERSATIONS_FILE)
    user_count = len(set(c["user_id"] for c in conversations))
    message_count = len(conversations)
    await update.message.reply_text(f"Users: {user_count}\nMessages: {message_count}")

async def schedule_messages(context: ContextTypes.DEFAULT_TYPE, text="Good morning, sunshine! Hope your day’s amazing 😊"):
    conversations = load_json(CONVERSATIONS_FILE)
    user_ids = list(set([c["user_id"] for c in conversations]))
    banned_users = load_json(BANNED_USERS_FILE)
    for user_id in user_ids:
        if user_id in banned_users:
            continue
        try:
            await context.bot.send_message(chat_id=user_id, text=text)
        except Exception as e:
            logger.warning(f"Failed to send scheduled message to {user_id}: {e}")

# Register handlers
dispatcher.add_handler(CommandHandler("start", start))
dispatcher.add_handler(CommandHandler("help", help))
dispatcher.add_handler(CommandHandler("broadcast", admin_broadcast))
dispatcher.add_handler(CommandHandler("ban", admin_ban))
dispatcher.add_handler(CommandHandler("unban", admin_unban))
dispatcher.add_handler(CommandHandler("stats", admin_stats))
dispatcher.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

# Flask routes
@app.route("/")
def index():
    return "Grok 3 Telegram Bot is running!"

@app.route(f"/{BOT_TOKEN}", methods=["POST"])
async def webhook():
    update = Update.de_json(request.get_json(), bot)
    await dispatcher.process_update(update)
    return {"status": "ok"}

# Setup webhook and scheduler
scheduler = AsyncIOScheduler()
scheduler.add_job(
    schedule_messages,
    trigger="cron",
    hour=8,
    minute=0,
    args=[application],
    kwargs={"text": "Good morning, sunshine! Hope your day’s amazing 😊"}
)
scheduler.add_job(
    schedule_messages,
    trigger="cron",
    hour=22,
    minute=0,
    args=[application],
    kwargs={"text": "Good night, love! Sweet dreams 😘"}
)
scheduler.start()

async def setup():
    await bot.set_webhook(url=f"{WEBHOOK_URL}/{BOT_TOKEN}")
    logger.info(f"Webhook set to {WEBHOOK_URL}/{BOT_TOKEN}")

# Run setup
if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(setup())
    app.run(host="0.0.0.0", port=8443, debug=False)