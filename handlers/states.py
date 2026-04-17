#handlers/states.py
from aiogram.fsm.state import StatesGroup, State

class ExpenseState(StatesGroup):
    category = State()
    amount = State()

class IncomeState(StatesGroup):
    amount = State()

class LimitState(StatesGroup):
    amount = State()