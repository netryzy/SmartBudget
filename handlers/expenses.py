# handlers/expenses.py - УПРОЩЕННАЯ ВЕРСИЯ
from aiogram import Router
from aiogram.types import CallbackQuery, Message, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from services.ai_recommendations import get_ai_recommendations 
from database.queries import add_expense_to_db, get_expenses, get_income
from utils.ai_logic import smart_parse_expenses

router = Router()


class ExpenseState(StatesGroup):
    waiting_for_input = State()  # Упростили до одного состояния


def get_main_menu():
    from handlers.start import get_main_menu
    return get_main_menu()


def get_cancel_keyboard():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="❌ Отмена", callback_data="cancel_expense")]
        ]
    )


def get_balance_text(user_id):
    income = get_income(user_id)
    expenses = get_expenses(user_id)
    balance = income - expenses
    return f"\n\n🏦 Баланс: {balance:.2f} руб."


@router.callback_query(lambda c: c.data == 'cancel_expense')
async def cancel_expense(callback_query: CallbackQuery, state: FSMContext):
    await state.clear()
    await callback_query.message.answer(
        "❌ Отменено",
        reply_markup=get_main_menu()
    )
    await callback_query.answer()


@router.callback_query(lambda c: c.data == 'add_expense')
async def add_expense(callback_query: CallbackQuery, state: FSMContext):
    await state.set_state(ExpenseState.waiting_for_input)
    await callback_query.message.answer(
        "🤖 <b>Введите ваши траты</b>\n\n"
        "Просто напишите, что и сколько потратили:\n\n"
        "📝 <b>Примеры:</b>\n"
        "• потратил 200р на огурцы, 300р на йогурт, 500р такси\n"
        "• купил хлеб 50р, молоко 80р, проезд 45р\n"
        "• кофе 150р, обед в кафе 450р\n\n"
        "🧠 <b>Нейросеть сама определит категории!</b>\n\n"
        "Или нажмите ❌ Отмена",
        reply_markup=get_cancel_keyboard(),
        parse_mode="HTML"
    )
    await callback_query.answer()


@router.message(ExpenseState.waiting_for_input)
async def process_expense_input(message: Message, state: FSMContext):
    """Обработка введенных трат"""
    text = message.text.strip()
    
    if text == '/cancel':
        await state.clear()
        await message.answer("❌ Отменено", reply_markup=get_main_menu())
        return
    
    # Отправляем сообщение о обработке
    processing_msg = await message.answer("🧠 Нейросеть анализирует ваши траты...")
    
    try:
        # Используем нейросеть для парсинга
        expenses_dict = await smart_parse_expenses(text)
        
        print(f"Распознано нейросетью: {expenses_dict}")
        
        if not expenses_dict:
            await processing_msg.delete()
            await message.answer(
                "❌ Не удалось распознать траты\n\n"
                "Попробуйте написать понятнее:\n"
                "<i>потратил 200р на огурцы, 300р на йогурт</i>\n\n"
                "Или используйте /start для главного меню",
                parse_mode="HTML"
            )
            return
        
        # Сохраняем траты
        total_amount = 0
        saved_items = []
        
        for category, amount in expenses_dict.items():
            if amount > 0:
                add_expense_to_db(message.from_user.id, category, amount)
                saved_items.append(f"  • {category}: {amount:.2f} руб.")
                total_amount += amount
        
        # Формируем ответ
        response = "✅ <b>Траты успешно добавлены!</b>\n\n"
        response += "📋 <b>Распознано:</b>\n"
        response += "\n".join(saved_items)
        response += f"\n\n💰 <b>Итого:</b> {total_amount:.2f} руб."
        response += get_balance_text(message.from_user.id)
        
        await processing_msg.delete()
        await message.answer(response, reply_markup=get_main_menu(), parse_mode="HTML")
        await state.clear()
        
    except Exception as e:
        await processing_msg.delete()
        print(f"Ошибка при обработке: {e}")
        import traceback
        traceback.print_exc()
        await message.answer(
            "❌ Произошла ошибка при обработке\n\n"
            "Попробуйте еще раз или используйте /start",
            reply_markup=get_main_menu()
        )