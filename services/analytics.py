# services/analytics.py - ДОБАВЛЯЕМ ФУНКЦИЮ ДЛЯ РЕКОМЕНДАЦИЙ
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import os
from datetime import datetime, timedelta
from database.db import get_connection
from database.queries import get_expenses, get_income


def get_stats(user_id, days=None):
    """Получает статистику для конкретного пользователя"""
    expenses = get_expenses(user_id, days)
    income = get_income(user_id, days)
    
    return {
        "income": income,
        "expenses": expenses,
        "balance": income - expenses
    }


def get_categories_with_amount(user_id, days=None):
    """Получает категории с суммами за период"""
    conn = get_connection()
    cursor = conn.cursor()

    if days is not None:
        if days == 1:
            cursor.execute("""
                SELECT category, COALESCE(SUM(amount), 0) FROM expenses 
                WHERE user_id = ? AND DATE(date) = DATE('now', 'localtime')
                GROUP BY category
            """, (user_id,))
        else:
            date_from = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d %H:%M:%S')
            cursor.execute("""
                SELECT category, COALESCE(SUM(amount), 0) FROM expenses 
                WHERE user_id = ? AND date >= ? 
                GROUP BY category
            """, (user_id, date_from))
    else:
        cursor.execute("""
            SELECT category, COALESCE(SUM(amount), 0) FROM expenses 
            WHERE user_id = ? 
            GROUP BY category
        """, (user_id,))
    
    result = cursor.fetchall()
    conn.close()
    return result if result else []


def generate_expense_chart(user_id, days=None):
    """Генерирует круговую диаграмму расходов"""
    data = get_categories_with_amount(user_id, days)
    
    if not data:
        return None
    
    filtered = [(cat, amt) for cat, amt in data if amt and amt > 0]
    
    if not filtered:
        return None
    
    labels = [row[0] for row in filtered]
    values = [row[1] for row in filtered]
    
    plt.figure(figsize=(8, 8))
    
    colors = ['#ff6b6b', '#4ecdc4', '#45b7d1', '#96ceb4', '#ffeaa7', '#dfe6e9', '#74b9ff', '#a29bfe']
    
    plt.pie(
        values, 
        labels=labels, 
        autopct='%1.1f%%', 
        startangle=90,
        colors=colors[:len(labels)]
    )
    
    plt.title("Структура расходов", fontsize=14, fontweight='bold', pad=20)
    plt.axis('equal')
    
    timestamp = int(datetime.now().timestamp())
    path = f"expense_chart_{user_id}_{timestamp}.png"
    plt.savefig(path, dpi=100, bbox_inches='tight', facecolor='white')
    plt.close()
    
    return path


def compare_periods(user_id, days):
    """Сравнивает расходы за два периода"""
    current = get_expenses(user_id, days)
    
    if days == 1:
        previous = get_expenses(user_id, days * 2)
    else:
        previous = get_expenses(user_id, days * 2) - current
    
    if previous <= 0:
        return "📊 Нет данных для сравнения"
    
    diff = ((current - previous) / previous) * 100
    
    if diff > 0:
        return f"⚠️ Расходы выросли на {diff:.1f}% по сравнению с прошлым периодом"
    else:
        return f"✅ Расходы снизились на {abs(diff):.1f}% по сравнению с прошлым периодом"


def get_category_analysis(user_id, days=30):
    """Анализирует расходы по категориям и дает рекомендации"""
    categories = get_categories_with_amount(user_id, days)
    total = get_expenses(user_id, days)
    
    if total == 0:
        return None
    
    analysis = []
    for category, amount in categories:
        percent = (amount / total) * 100
        analysis.append({
            "category": category,
            "amount": amount,
            "percent": percent
        })
    
    return sorted(analysis, key=lambda x: x["percent"], reverse=True)