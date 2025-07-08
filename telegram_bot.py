import os
import openai
import requests
import datetime
import logging
import random
from flask import Flask
from apscheduler.schedulers.background import BackgroundScheduler
import sys

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler("bot.log"),
        logging.StreamHandler(sys.stdout)  # <-- це виводить у Render logs
    ]
)
# Flask app
app = Flask(__name__)

# Змінні середовища
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHANNEL = os.getenv("TELEGRAM_CHANNEL")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
openai.api_key = OPENAI_API_KEY

# Логування
logging.basicConfig(
    filename='bot.log',
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s'
)

# Типи постів
POST_TYPES = [
    "historical_event", "diplomatic_moment", "cultural_flashback"
]

IMAGE_PROMPTS = {
    "historical_event": "Ukrainian historical painting, dramatic, vintage tones",
    "diplomatic_moment": "Old diplomatic letter, quill, historical map, vintage style",
    "cultural_flashback": "Traditional Ukrainian culture, folklore, ancient background"
}

WRITING_STYLES = [
    "У стилі захопленого історика, який п'є каву",
    "Якби цю історію розповідав учитель, який любить меми",
    "У стилі блогу на канапі, з гумором і прикладами",
    "Легка оповідь, яка розповідає, чому це важливо сьогодні",
    "Як історик, що читає TikTok-коментарі"
]

POST_PROMPTS = {
    "historical_event": "Розкажи захопливо про важливу подію в історії України, яка сталася в цей день. Почни з емоційного гачка з емодзі, поясни значення події, додай цікавий факт, гумор і посилання на джерело.",
    "diplomatic_moment": "Розкажи про цікаву дипломатичну подію або угоду України з іншими державами. Поясни, що сталося, чому це важливо, з прикладом і джерелом. Додай гумору.",
    "cultural_flashback": "Напиши про українську культурну подію з минулого, традицію або факт, що формував ідентичність. Почни з емоційного гачка, поясни суть, додай порівняння, приклад і джерело."
}

def generate_post(post_type):
    try:
        prompt = (
            f"Ти пишеш пост у Telegram-канал 'Згадки минулого'. "
            f"Стиль: {random.choice(WRITING_STYLES)}. "
            f"Тип поста: {post_type}. "
            f"{POST_PROMPTS[post_type]} "
            f"Пиши українською. Обсяг — ~500 слів. У кінці — джерело (якщо є)."
        )
        response = openai.chat.completions.create(
            model="gpt-4",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.95,
            max_tokens=1600
        )
        return response.choices[0].message.content
    except Exception as e:
        logging.error(f"❌ GPT error: {str(e)}")
        return None

def generate_image(post_type):
    try:
        prompt = IMAGE_PROMPTS.get(post_type, "Historical Ukraine illustration")
        response = openai.images.generate(
            model="dall-e-3",
            prompt=prompt,
            n=1,
            size="1024x1024"
        )
        return response.data[0].url
    except Exception as e:
        logging.error(f"❌ Image error: {str(e)}")
        return None

def send_post(text):
    logging.info("➡️ send_post викликана")
    if not text:
        logging.warning("⚠️ Немає тексту для надсилання")
        return
    requests.post(
        f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage",
        data={"chat_id": TELEGRAM_CHANNEL, "text": text[:4096]}
    )

def send_image(image_url):
    if image_url:
        requests.post(
            f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendPhoto",
            data={"chat_id": TELEGRAM_CHANNEL, "photo": image_url}
        )

def generate_and_send_post(post_type):
    image_url = generate_image(post_type)
    send_image(image_url)
    text = generate_post(post_type)
    send_post(text)

def send_welcome_post():
    text = (
        "🕰️ Вітаємо у «Згадках минулого»!

"
        "Це канал, де історія України — не про зубріння, а про життя.
"
        "Щодня — нові історії:
"
        "📜 несподівані події
"
        "🤝 міжнародні зв’язки
"
        "😂 кумедні факти з минулого
"
        "🔍 усе — у стилі живого блогу"
    )
    send_post(text)

def generate_and_send():
    logging.info("🧪 generate_and_send() запущено")
    selected = random.sample(POST_TYPES, 3)
    for post_type in selected:
        logging.info(f"📤 Надсилаємо тип: {post_type}")
        generate_and_send_post(post_type)

def force_all_posts():
    for post_type in POST_TYPES:
        generate_and_send_post(post_type)

@app.route('/')
def home():
    return "🤖 Бот працює!"

@app.route('/force')
def route_force():
    generate_and_send()
    return "✅ Пост згенеровано"

@app.route('/force_all')
def route_force_all():
    force_all_posts()
    return "✅ Всі пости надіслані"

@app.route('/welcome')
def route_welcome():
    send_welcome_post()
    return "👋 Вітальний пост надіслано"

# Планувальник
scheduler = BackgroundScheduler()
scheduler.add_job(generate_and_send, 'cron', hour='7,13,20', minute=0)
scheduler.start()

if __name__ == '__main__':
    logging.info("✅ telegram_bot імпортовано як модуль для main.py")
