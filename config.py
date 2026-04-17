# config.py
import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# Проверка наличия ключа
if not OPENAI_API_KEY:
    print("⚠️ ВНИМАНИЕ: OPENAI_API_KEY не найден в .env файле!")
    print("Умный ввод через нейросеть не будет работать.")