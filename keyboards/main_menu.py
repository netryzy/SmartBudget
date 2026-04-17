#keyboards/main_menu.py
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

main_menu = ReplyKeyboardMarkup(
    keyboard=[
        [
            KeyboardButton(text="💰 Добавить доход"),
            KeyboardButton(text="💸 Добавить расход")
        ],
        [
            KeyboardButton(text="📊 Моя статистика"),
            KeyboardButton(text="⚙️ Установить лимит")
        ]
    ],
    resize_keyboard=True
)