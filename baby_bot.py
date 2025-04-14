import logging
import requests
from telegram import Update, InputMediaPhoto
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters

# --- CONFIG ---
ADMIN_IDS = [1866961136, 1807014348]
HUGGINGFACE_API = "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"
PEXELS_API = "7nwHEnHBPmNh8RDVsIIXnaKd6BH257Io4Sncj5NRd8XijTj9zcfE4vZg"
GEMINI_API_KEY = "AIzaSyDAm_zAas5YQdQTCI2WoxYDEOXZfwpXUDc"

logging.basicConfig(level=logging.INFO)

# --- Hugging Face Chat Function ---
def ask_huggingface(prompt):
    headers = {"Authorization": f"Bearer {HUGGINGFACE_API}"}
    json_data = {"inputs": prompt}
    response = requests.post("https://api-inference.huggingface.co/models/microsoft/DialoGPT-medium", headers=headers, json=json_data)
    if response.status_code == 200 and isinstance(response.json(), dict):
        return response.json().get("generated_text", "Sorry, I can't talk right now.")
    else:
        return "Sorry, I can't talk right now."

# --- Gemini AI Chat Function ---
def ask_gemini(prompt):
    url = f"https://generativelanguage.googleapis.com/v1beta2/models/text-bison-001:generateText?key={GEMINI_API_KEY}"
    data = {
        "prompt": {"text": prompt},
        "temperature": 0.9,
        "candidateCount": 1
    }
    r = requests.post(url, json=data)
    if r.status_code == 200:
        result = r.json()
        return result["candidates"][0]["output"]
    return "Sorry, I'm feeling shy right now."

# --- Pexels Image Fetcher ---
def get_romantic_image():
    headers = {"Authorization": PEXELS_API}
    params = {"query": "romantic couple", "per_page": 1}
    r = requests.get("https://api.pexels.com/v1/search", headers=headers, params=params)
    data = r.json()
    if data.get("photos"):
        return data["photos"][0]["src"]["original"]
    return None

# --- Commands ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Hi babe! I'm your virtual girlfriend. Just talk to me anytime!")

async def image(update: Update, context: ContextTypes.DEFAULT_TYPE):
    url = get_romantic_image()
    if url:
        await update.message.reply_photo(photo=url, caption="Here's something romantic for you!")
    else:
        await update.message.reply_text("Couldn't find an image right now!")

async def dateidea(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("How about a cozy movie night with popcorn and cuddles?")

async def vibe(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("You can choose my vibe: sweet, clingy, chill, flirty. (Coming soon!)")

async def mood(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("I'm feeling extra cuddly today!")

async def hug(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    if user_id in ADMIN_IDS:
        await update.message.reply_text("*wraps arms around you tightly* I love hugging you!")
    else:
        await update.message.reply_text("I only hug my special one!")

async def kiss(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    if user_id in ADMIN_IDS:
        await update.message.reply_text("*gives you a soft kiss on the cheek* You're the best!")
    else:
        await update.message.reply_text("Sorry, kisses are only for my love!")

# --- Message Auto-Reply ---
async def chat(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    user_text = update.message.text
    is_admin = user_id in ADMIN_IDS

    # Customize prompt based on user
    if is_admin:
        prompt = f"Act like a sweet, romantic girlfriend. Reply lovingly to: {user_text}"
    else:
        prompt = f"Talk like a friendly chatbot. Respond to: {user_text}"

    try:
        reply = ask_gemini(prompt)
    except:
        reply = ask_huggingface(prompt)

    await update.message.reply_text(reply)

# --- Main ---
app = ApplicationBuilder().token("7637073475:AAEuGTS_TKertVJz1ZYjwwtM2d0KP-8l1qA").build()

app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("image", image))
app.add_handler(CommandHandler("dateidea", dateidea))
app.add_handler(CommandHandler("vibe", vibe))
app.add_handler(CommandHandler("mood", mood))
app.add_handler(CommandHandler("hug", hug))
app.add_handler(CommandHandler("kiss", kiss))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, chat))

app.run_polling()
