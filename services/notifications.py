#services/notifications.py
from database.queries import get_income, get_expenses


def check_limits(user_id):
    income = get_income(user_id)
    expenses = get_expenses(user_id)

    if income == 0:
        return None

    ratio = expenses / income

    if ratio > 0.9:
        return "🚨 Почти все деньги потрачены!"

    if ratio < 0.3:
        return "🔥 Отлично! Ты хорошо экономишь!"

    return None