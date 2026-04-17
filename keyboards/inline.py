#keyboards/inline.py
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

categories = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text="🍔 Еда", callback_data="food"),
     InlineKeyboardButton(text="🚕 Транспорт", callback_data="transport")],
    [InlineKeyboardButton(text="🎮 Развлечения", callback_data="fun"),
     InlineKeyboardButton(text="🛍 Покупки", callback_data="shop")]
])