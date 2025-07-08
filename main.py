from flask import Flask
from telegram_bot import app as telegram_app

app = telegram_app

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)