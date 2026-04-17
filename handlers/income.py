# handlers/income.py - УПРОЩЕННАЯ ВЕРСИЯ
from aiogram import Router
from aiogram.types import CallbackQuery, Message, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from database.queries import add_income_to_db, get_income, get_expenses
from utils.ai_logic import smart_parse_income

router = Router()


class IncomeState(StatesGroup):
    waiting_for_input = State()


def get_main_menu():
    from handlers.start import get_main_menu
    return get_main_menu()


def get_cancel_keyboard():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="❌ Отмена", callback_data="cancel_income")]
        ]
    )


@router.callback_query(lambda c: c.data == 'cancel_income')
async def cancel_income(callback_query: CallbackQuery, state: FSMContext):
    await state.clear()
    await callback_query.message.answer("❌ Отменено", reply_markup=get_main_menu())
    await callback_query.answer()


@router.callback_query(lambda c: c.data == 'add_income')
async def add_income(callback_query: CallbackQuery, state: FSMContext):
    await state.set_state(IncomeState.waiting_for_input)
    await callback_query.message.answer(
        "💰 <b>Введите ваш доход</b>\n\n"
        "📝 <b>Примеры:</b>\n"
        "• зарплата 50000\n"
        "• получил 15000 за фриланс\n"
        "• перевели 30000\n\n"
        "Или нажмите ❌ Отмена",
        reply_markup=get_cancel_keyboard(),
        parse_mode="HTML"
    )
    await callback_query.answer()


@router.message(IncomeState.waiting_for_input)
async def process_income_input(message: Message, state: FSMContext):
    text = message.text.strip()
    
    if text == '/cancel':
        await state.clear()
        await message.answer("❌ Отменено", reply_markup=get_main_menu())
        return
    
    processing_msg = await message.answer("💰 Обрабатываю доход...")
    
    try:
        result = await smart_parse_income(text)
        
        if result and result.get("amount", 0) > 0:
            add_income_to_db(message.from_user.id, result["amount"], result.get("source", ""))
            
            response = f"✅ <b>Доход добавлен!</b>\n\n"
            response += f"💰 Сумма: {result['amount']:.2f} руб."
            
            await processing_msg.delete()
            await message.answer(response, reply_markup=get_main_menu(), parse_mode="HTML")
        else:
            await processing_msg.delete()
            await message.answer(
                "❌ Не удалось распознать доход\n\n"
                "Попробуйте: зарплата 50000",
                reply_markup=get_main_menu()
            )
        
        await state.clear()
        
    except Exception as e:
        await processing_msg.delete()
        print(f"Ошибка: {e}")
        await message.answer("❌ Ошибка", reply_markup=get_main_menu())