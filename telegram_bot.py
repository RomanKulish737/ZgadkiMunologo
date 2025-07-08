import os
import openai
import requests
import datetime
import logging
import random
from flask import Flask
from apscheduler.schedulers.background import BackgroundScheduler
import sys
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
logging.basicConfig(filename='bot.log', level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')

# Типи постів
POST_TYPES = [
    "historical_event", "ukraine_in_world", "diplomatic_moment",
    "funny_fact", "military_history", "scientific_past",
    "unexpected_connection", "cultural_flashback", "economy_tale", "tech_then"
]

# Промпти зображень
IMAGE_PROMPTS = {
    "historical_event": "Historical painting style, Ukraine, antique colors",
    "ukraine_in_world": "Ukraine map and globe, vintage atlas look",
    "diplomatic_moment": "Old treaty signing, historical figures, parchment",
    "funny_fact": "Humorous historical caricature, Slavic style",
    "military_history": "Battle scene, historical soldiers, moody atmosphere",
    "scientific_past": "Old lab tools, candlelight, scholar atmosphere",
    "unexpected_connection": "Two different eras blended, time travel vibe",
    "cultural_flashback": "Traditional clothes and modern elements mix",
    "economy_tale": "Old coins, markets, vintage documents",
    "tech_then": "Old gadgets or machines, sepia, detailed drawing"
}

WRITING_STYLES = [
    "У стилі іронічного історика, який розповідає друзям у пабі",
    "Якби це розповідав ютубер з каналу 'історія для чайників'",
    "Як розмова дідуся з онуком — із прикладами, гумором і життям",
    "Легкий блог у стилі 'Було і пройшло, але цікаво!'",
    "Ніби це сторіз із минулого, але без дат в лоб"
]

POST_PROMPTS = {
    "historical_event": "Розкажи цікаву історичну подію з історії України у вигляді блогу з гумором, прикладом, метафорами.",
    "ukraine_in_world": "Розкрий історичний факт про міжнародні відносини України. Поясни доступно, додай жарт або несподіваний поворот.",
    "diplomatic_moment": "Описати важливий дипломатичний момент України. Стиль — блог, з порівняннями, іронією і прикладом.",
    "funny_fact": "Розкажи смішний або дивний факт з української історії. Поясни чому це цікаво, додай гумору.",
    "military_history": "Оглянь одну знакову битву або військову подію. Без героїзації, але з емоцією, прикладом, і деталями.",
    "scientific_past": "Опиши внесок українських науковців у минулому. Покажи приклад, додай історію або цікавинку.",
    "unexpected_connection": "Покажи несподіваний зв’язок між подіями/особами. Блог, як розповідь з жартом.",
    "cultural_flashback": "Згадай цікаву історію з культурного життя. Поясни, як це вплинуло. Стиль — живий блог.",
    "economy_tale": "Опиши економічну ситуацію або кейс з історії. Подай це як історію, з аналогіями до сучасності.",
    "tech_then": "Історія якогось старого винаходу, пристрою, що був в Україні. З гумором і прикладом."
}

def generate_post(post_type):
    try:
        prompt = (
            f"Ти створюєш пост у Telegram-канал 'Згадки минулого'. "
            f"Стиль: {random.choice(WRITING_STYLES)}. "
            f"{POST_PROMPTS[post_type]} "
            f"Додай емоційний вступ із емодзі, живу подачу (400–700 слів), гумор і джерело наприкінці, якщо є. Українською мовою."
        )
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.9,
            max_tokens=1800
        )
        return response.choices[0].message["content"]
    except Exception as e:
        logging.error(f"❌ GPT error: {str(e)}")
        return None

def generate_image(post_type):
    try:
        prompt = IMAGE_PROMPTS.get(post_type, "Historical Ukrainian concept art")
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
    try:
        response = requests.post(
            f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage",
            data={"chat_id": TELEGRAM_CHANNEL, "text": text[:4096]}
        )
        logging.info(f"📨 Відповідь Telegram sendMessage: {response.status_code} - {response.text}")
    except Exception as e:
        logging.error(f"❌ Telegram помилка надсилання тексту: {str(e)}")
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
        "🕰️ Вітаємо у «Згадках минулого»!\n\n"

        "Це канал, де історія України — не про зубріння, а про життя.\n"
        "Щодня — нові історії:n"
        "📜 несподівані події\n"
        "🤝 міжнародні зв’язки\n"
        "😂 кумедні факти з минулого\n"
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
    return "🤖 Бот «Згадки минулого» працює."

@app.route('/force')
def route_force():
    generate_and_send()
    return "✅ 3 пости надіслано."

@app.route('/force_all')
def route_force_all():
    force_all_posts()
    return "✅ Усі типи постів надіслано."

@app.route('/welcome')
def route_welcome():
    send_welcome_post()
    return "👋 Вітальний пост надіслано."

scheduler = BackgroundScheduler()
scheduler.add_job(generate_and_send, 'cron', hour='6,12,18', minute=0)  # Kyiv time (UTC+3)
scheduler.start()

if __name__ == '__main__':
    logging.info("✅ Бот запущено.")
