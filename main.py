# main.py - УБЕДИТЕСЬ ЧТО ВСЕ РОУТЕРЫ ПОДКЛЮЧЕНЫ
import asyncio
import logging
from aiogram import Bot, Dispatcher
from aiogram.types import BotCommand
from aiogram.fsm.storage.memory import MemoryStorage
from config import BOT_TOKEN
from database.db import init_db
from handlers import start, expenses, income, stats

# Настройка логирования
logging.basicConfig(level=logging.INFO)


async def set_commands(bot: Bot):
    """Устанавливает команды бота"""
    commands = [
        BotCommand(command="start", description="🚀 Запустить бота"),
        BotCommand(command="help", description="❓ Помощь"),
        BotCommand(command="cancel", description="❌ Отменить действие"),
    ]
    await bot.set_my_commands(commands)
    print("✅ Команды установлены")


async def main():
    # Инициализация БД
    init_db()
    print("✅ База данных инициализирована")
    
    # Создание бота и диспетчера
    bot = Bot(token=BOT_TOKEN)
    storage = MemoryStorage()
    dp = Dispatcher(storage=storage)
    
    # Установка команд
    await set_commands(bot)
    
    # Подключение роутеров (ВАЖНО: порядок имеет значение)
    dp.include_router(start.router)      # Сначала команды start, help, cancel
    dp.include_router(income.router)     # Потом доходы
    dp.include_router(expenses.router)   # Потом расходы
    dp.include_router(stats.router)      # Потом статистика
    
    print("🚀 Бот SmartBudget запущен и готов к работе!")
    print("💬 Бот слушает сообщения...")
    print("📝 Доступные команды: /start, /help, /cancel")
    
    # Запуск поллинга
    await dp.start_polling(bot)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 Бот остановлен")