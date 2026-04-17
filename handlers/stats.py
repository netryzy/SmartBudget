# handlers/stats.py - ИСПРАВЛЕННЫЙ (возвращает меню)
from aiogram import Router
from aiogram.types import CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton, FSInputFile
from services.analytics import generate_expense_chart, compare_periods, get_stats
from database.queries import get_expenses, get_income
import os

router = Router()


def get_main_menu():
    from handlers.start import get_main_menu
    return get_main_menu()


@router.callback_query(lambda c: c.data == 'show_stats')
async def show_stats(callback_query: CallbackQuery):
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📆 За сегодня", callback_data="stats_day"),
         InlineKeyboardButton(text="📅 За неделю", callback_data="stats_week")],
        [InlineKeyboardButton(text="📊 За месяц", callback_data="stats_month"),
         InlineKeyboardButton(text="📈 За год", callback_data="stats_year")],
        [InlineKeyboardButton(text="🏦 За всё время", callback_data="stats_all"),
         InlineKeyboardButton(text="◀️ Назад в меню", callback_data="back_to_menu")]
    ])
    
    await callback_query.message.edit_text(
        "📊 Выберите период для статистики:",
        reply_markup=keyboard,
        parse_mode="HTML"
    )
    await callback_query.answer()


@router.callback_query(lambda c: c.data.startswith('stats_'))
async def handle_stats_period(callback_query: CallbackQuery):
    period = callback_query.data.split('_')[1]
    user_id = callback_query.from_user.id
    
    days_map = {
        'day': 1,
        'week': 7,
        'month': 30,
        'year': 365,
        'all': None
    }
    
    days = days_map.get(period)
    
    period_names = {
        'day': 'за сегодня',
        'week': 'за последние 7 дней',
        'month': 'за последние 30 дней',
        'year': 'за последний год',
        'all': 'за всё время'
    }
    
    period_name = period_names.get(period, 'за период')
    
    # Получаем статистику
    stats = get_stats(user_id, days)
    expenses = stats['expenses']
    income = stats['income']
    balance = stats['balance']
    
    print(f"Статистика: период={period}, days={days}, расходы={expenses}, доходы={income}")
    
    # Формируем текст
    text = f"📊 Статистика {period_name}\n\n"
    text += f"💰 Доходы: {income:.2f} руб.\n"
    text += f"💸 Расходы: {expenses:.2f} руб.\n"
    text += f"{'='*30}\n"
    
    if balance >= 0:
        text += f"✅ Остаток: {balance:.2f} руб.\n"
    else:
        text += f"⚠️ Дефицит: {balance:.2f} руб.\n"
    
    # Сравнение с прошлым периодом
    if expenses > 0:
        if days:
            comparison = compare_periods(user_id, days)
        else:
            comparison = compare_periods(user_id, 30)
        text += f"\n{comparison}"
    else:
        text += f"\n📊 Добавьте траты, чтобы увидеть сравнение"
    
    # Отправляем результат и показываем меню
    await callback_query.message.answer(text, parse_mode="HTML", reply_markup=get_main_menu())
    
    # Отправляем график если есть расходы
    if expenses > 0:
        chart = generate_expense_chart(user_id, days)
        if chart and os.path.exists(chart):
            try:
                await callback_query.message.answer_photo(
                    FSInputFile(chart),
                    caption="📈 Структура расходов"
                )
                os.remove(chart)
            except Exception as e:
                print(f"Ошибка: {e}")
    else:
        await callback_query.message.answer(
            "📭 Нет данных для построения графика.\nДобавьте траты через кнопку ➕ Добавить трату",
            parse_mode="HTML"
        )
    
    await callback_query.answer()