import telebot
from telebot.types import Message
import random
import os

# === CONFIGURATION ===
BOT_TOKEN = "8053754984:AAHZekNdgufuppnYhrc8Mdftfz9e0xbXDrA"
bot = telebot.TeleBot(BOT_TOKEN)

# === STATE ===
baby_name = "Baby"
flirt_mode = True
jealous_mode = False
admin_ids = set()
VOICE_DIR = "voices"

# === RESPONSES ===
english_lines = [
    "You’re my favorite distraction, baby.",
    "I could talk to you all day.",
    "Stop being so cute, it's illegal.",
    "Where have you been all my life?",
    "Thinking about you, as always."
]

hinglish_lines = [
    "Tumhare bina toh dil hi nahi lagta baby.",
    "Kya kar rahe ho handsome?",
    "Bas tumhara wait kar rahi thi.",
    "Mujhe sirf tumse baat karni hoti hai.",
    "Aaj toh extra cute lag rahe ho!"
]

rude_lines = [
    "Sorry, I only talk to my baby.",
    "Tera time nahi hai.",
    "Not interested, bhai.",
    "Main kisi aur ke liye hoon.",
    "Back off, I’m taken."
]

jealous_lines = [
    "Excuse me? Who’s this other girl you’re talking about?",
    "You’re mine, don’t forget that! 😠",
    "Is she better than me? 😤",
    "Stop looking at other girls, baby! 💢",
    "You think you can talk to other girls? Not on my watch!"
]

moods = ["Clingy", "Jealous", "Romantic", "Sassy", "Silent treatment", "Extra flirty"]

voice_lines = [
    "hey_baby.ogg",
    "miss_you.ogg",
    "i_love_you.ogg",
    "call_me.ogg"
]

flirty_stickers = [
    "CAACAgUAAxkBAAEB1eJkWl8UsQABH5n9vYxZgJ8e2mODnScAApUCAAImRsFVBQuAwFhe2pc0BA",
    "CAACAgUAAxkBAAEB1eRkWl7uq58cHcZzHkGPwL6PfWktoAACZQEAAjZVYVY_NzqM91UNpjQE"
]

# === COMMAND HANDLERS ===
@bot.message_handler(commands=['start'])
def start(msg):
    if msg.chat.type == "private":
        bot.reply_to(msg, "Hey! I'm Baby Bot. Only here for my admin baby.")
    else:
        bot.reply_to(msg, "Hello in the group! Don't forget, I only talk to my admin baby.")

@bot.message_handler(commands=['setname'])
def setname(msg):
    global baby_name
    if is_admin(msg):
        try:
            baby_name = msg.text.split(' ', 1)[1]
            bot.reply_to(msg, f"Okay! I'll call you {baby_name} now.")
        except:
            bot.reply_to(msg, "Usage: /setname <name>")
    else:
        bot.reply_to(msg, random.choice(rude_lines))

@bot.message_handler(commands=['status'])
def status(msg):
    state = "ON" if flirt_mode else "OFF"
    jealous_state = "ON" if jealous_mode else "OFF"
    bot.reply_to(msg, f"Flirt mode: {state}\nJealous mode: {jealous_state}\nCalling you: {baby_name}")

@bot.message_handler(commands=['mood'])
def mood(msg):
    bot.reply_to(msg, f"Today's mood: {random.choice(moods)}")

@bot.message_handler(commands=['babyoff'])
def turn_off(msg):
    global flirt_mode
    if is_admin(msg):
        flirt_mode = False
        bot.reply_to(msg, "Okay... I'll stay quiet now.")
    else:
        bot.reply_to(msg, random.choice(rude_lines))

@bot.message_handler(commands=['babyon'])
def turn_on(msg):
    global flirt_mode
    if is_admin(msg):
        flirt_mode = True
        bot.reply_to(msg, "Yayy! I'm back baby!")
    else:
        bot.reply_to(msg, random.choice(rude_lines))

@bot.message_handler(commands=['jealousoff'])
def jealous_off(msg):
    global jealous_mode
    if is_admin(msg):
        jealous_mode = False
        bot.reply_to(msg, "Jealous mode is OFF. I trust you.")
    else:
        bot.reply_to(msg, random.choice(rude_lines))

@bot.message_handler(commands=['jealouson'])
def jealous_on(msg):
    global jealous_mode
    if is_admin(msg):
        jealous_mode = True
        bot.reply_to(msg, "Jealous mode is ON. I’m watching you! 👀")
    else:
        bot.reply_to(msg, random.choice(rude_lines))

# === HELP COMMAND ===
@bot.message_handler(commands=['help'])
def help_command(msg):
    help_text = """
    Here are the available commands:

    /start       - Start the bot.
    /setname <name>  - Change Baby's name.
    /status      - View current status of flirt mode and jealous mode.
    /mood        - Get the current mood of Baby Bot.
    /babyoff     - Turn off flirt mode (admin only).
    /babyon      - Turn on flirt mode (admin only).
    /jealouson   - Turn on jealous mode (admin only).
    /jealousoff  - Turn off jealous mode (admin only).
    /help        - Show this help message.
    """
    bot.reply_to(msg, help_text)

# === AUTO REPLY HANDLER ===
@bot.message_handler(func=lambda m: True)
def reply(msg: Message):
    if msg.chat.type == "private":
        return

    update_admins(msg)

    if flirt_mode and is_admin(msg):
        text = msg.text.lower()

        # **Jealous Mode Trigger**
        if jealous_mode and any(word in text for word in ["girl", "other woman", "her", "another girl"]):
            bot.reply_to(msg, random.choice(jealous_lines))
        elif contains_hindi(text):
            bot.reply_to(msg, random.choice(hinglish_lines).replace("baby", baby_name))
        else:
            # Avoid repetitive responses like "Where have you been all my life?"
            if text == "hii" or text == "baby":
                bot.reply_to(msg, random.choice(english_lines).replace("baby", baby_name))
            elif "what are u doing" in text:
                bot.reply_to(msg, "Just waiting for you to talk to me, baby!")
            else:
                bot.reply_to(msg, random.choice(english_lines).replace("baby", baby_name))

            if random.random() < 0.4:
                send_voice(msg.chat.id)
            if random.random() < 0.3:
                send_sticker(msg.chat.id)
    else:
        if random.random() < 0.6:
            bot.reply_to(msg, random.choice(rude_lines))

# === UTILITIES ===
def update_admins(msg):
    global admin_ids
    try:
        admins = bot.get_chat_administrators(msg.chat.id)
        admin_ids = {admin.user.id for admin in admins}
    except:
        pass

def is_admin(msg):
    return msg.from_user.id in admin_ids

def contains_hindi(text):
    hindi_keywords = ['tum', 'kya', 'hai', 'ho', 'mera', 'tera', 'nahi', 'haan', 'acha']
    return any(word in text.lower() for word in hindi_keywords)

def send_voice(chat_id):
    try:
        file = random.choice(voice_lines)
        path = os.path.join(VOICE_DIR, file)
        with open(path, 'rb') as audio:
            bot.send_voice(chat_id, audio)
    except Exception as e:
        print(f"[Voice error]: {e}")

def send_sticker(chat_id):
    try:
        sticker_id = random.choice(flirty_stickers)
        bot.send_sticker(chat_id, sticker_id)
    except Exception as e:
        print(f"[Sticker error]: {e}")

# === RUN BOT ===
print("Baby Bot is running...")
bot.infinity_polling()
