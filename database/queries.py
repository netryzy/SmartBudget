# database/queries.py - ПОЛНАЯ ВЕРСИЯ
from database.db import get_connection
from datetime import datetime, timedelta
import sqlite3


# =====================
# РАСХОДЫ
# =====================

def add_expense_to_db(user_id, category, amount):
    try:
        conn = get_connection()
        cursor = conn.cursor()
        current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        cursor.execute(
            "INSERT INTO expenses (user_id, category, amount, date) VALUES (?, ?, ?, ?)",
            (user_id, category, amount, current_time)
        )
        conn.commit()
        print(f"✅ Добавлен расход: user_id={user_id}, category={category}, amount={amount}, date={current_time}")
        conn.close()
        return True
    except Exception as e:
        print(f"❌ Ошибка добавления расхода: {e}")
        return False


def get_expenses(user_id, days=None):
    """Получает расходы конкретного пользователя за период"""
    try:
        conn = get_connection()
        cursor = conn.cursor()

        if days is not None:
            if days == 1:
                today = datetime.now().strftime('%Y-%m-%d')
                cursor.execute("""
                    SELECT COALESCE(SUM(amount), 0) FROM expenses 
                    WHERE user_id = ? AND date LIKE ?
                """, (user_id, f"{today}%"))
            else:
                date_from = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d %H:%M:%S')
                cursor.execute("""
                    SELECT COALESCE(SUM(amount), 0) FROM expenses 
                    WHERE user_id = ? AND date >= ?
                """, (user_id, date_from))
        else:
            cursor.execute("""
                SELECT COALESCE(SUM(amount), 0) FROM expenses 
                WHERE user_id = ?
            """, (user_id,))

        result = cursor.fetchone()[0]
        conn.close()
        print(f"📊 get_expenses: user_id={user_id}, days={days}, result={result}")
        return float(result) if result else 0.0
    except Exception as e:
        print(f"❌ Ошибка get_expenses: {e}")
        return 0.0


def get_categories(user_id, days=None):
    """Получает расходы по категориям за период"""
    try:
        conn = get_connection()
        cursor = conn.cursor()

        if days is not None:
            if days == 1:
                today = datetime.now().strftime('%Y-%m-%d')
                cursor.execute("""
                    SELECT category, COALESCE(SUM(amount), 0)
                    FROM expenses
                    WHERE user_id = ? AND date LIKE ?
                    GROUP BY category
                """, (user_id, f"{today}%"))
            else:
                date_from = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d %H:%M:%S')
                cursor.execute("""
                    SELECT category, COALESCE(SUM(amount), 0)
                    FROM expenses
                    WHERE user_id = ? AND date >= ?
                    GROUP BY category
                """, (user_id, date_from))
        else:
            cursor.execute("""
                SELECT category, COALESCE(SUM(amount), 0)
                FROM expenses
                WHERE user_id = ?
                GROUP BY category
            """, (user_id,))

        result = cursor.fetchall()
        conn.close()
        return result if result else []
    except Exception as e:
        print(f"❌ Ошибка get_categories: {e}")
        return []


# =====================
# ДОХОДЫ
# =====================

def add_income_to_db(user_id, amount, source=None):
    try:
        conn = get_connection()
        cursor = conn.cursor()
        current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        cursor.execute(
            "INSERT INTO income (user_id, amount, source, date) VALUES (?, ?, ?, ?)",
            (user_id, amount, source, current_time)
        )
        conn.commit()
        print(f"✅ Добавлен доход: user_id={user_id}, amount={amount}, source={source}, date={current_time}")
        conn.close()
        return True
    except Exception as e:
        print(f"❌ Ошибка добавления дохода: {e}")
        return False


def get_income(user_id, days=None):
    """Получает доходы конкретного пользователя за период"""
    try:
        conn = get_connection()
        cursor = conn.cursor()

        if days is not None:
            if days == 1:
                today = datetime.now().strftime('%Y-%m-%d')
                cursor.execute("""
                    SELECT COALESCE(SUM(amount), 0) FROM income 
                    WHERE user_id = ? AND date LIKE ?
                """, (user_id, f"{today}%"))
            else:
                date_from = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d %H:%M:%S')
                cursor.execute("""
                    SELECT COALESCE(SUM(amount), 0) FROM income 
                    WHERE user_id = ? AND date >= ?
                """, (user_id, date_from))
        else:
            cursor.execute("""
                SELECT COALESCE(SUM(amount), 0) FROM income 
                WHERE user_id = ?
            """, (user_id,))

        result = cursor.fetchone()[0]
        conn.close()
        print(f"📊 get_income: user_id={user_id}, days={days}, result={result}")
        return float(result) if result else 0.0
    except Exception as e:
        print(f"❌ Ошибка get_income: {e}")
        return 0.0


def get_income_sources(user_id, days=None):
    """Получает доходы по источникам за период"""
    try:
        conn = get_connection()
        cursor = conn.cursor()

        if days is not None:
            if days == 1:
                today = datetime.now().strftime('%Y-%m-%d')
                cursor.execute("""
                    SELECT source, COALESCE(SUM(amount), 0)
                    FROM income
                    WHERE user_id = ? AND source IS NOT NULL AND date LIKE ?
                    GROUP BY source
                """, (user_id, f"{today}%"))
            else:
                date_from = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d %H:%M:%S')
                cursor.execute("""
                    SELECT source, COALESCE(SUM(amount), 0)
                    FROM income
                    WHERE user_id = ? AND source IS NOT NULL AND date >= ?
                    GROUP BY source
                """, (user_id, date_from))
        else:
            cursor.execute("""
                SELECT source, COALESCE(SUM(amount), 0)
                FROM income
                WHERE user_id = ? AND source IS NOT NULL
                GROUP BY source
            """, (user_id,))

        result = cursor.fetchall()
        conn.close()
        return result if result else []
    except Exception as e:
        print(f"❌ Ошибка get_income_sources: {e}")
        return []


# =====================
# ДЕТАЛЬНЫЕ ТРАТЫ (ДЛЯ АНАЛИТИКИ)
# =====================

def get_detailed_expenses(user_id, days=30):
    """Получает детальные траты пользователя за период"""
    try:
        conn = get_connection()
        cursor = conn.cursor()
        
        date_from = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d %H:%M:%S')
        cursor.execute("""
            SELECT category, amount, date 
            FROM expenses 
            WHERE user_id = ? AND date >= ?
            ORDER BY date DESC
        """, (user_id, date_from))
        
        result = cursor.fetchall()
        conn.close()
        return result
    except Exception as e:
        print(f"Ошибка get_detailed_expenses: {e}")
        return []


def get_expenses_by_category_detail(user_id, category, days=30):
    """Получает детальные траты по конкретной категории"""
    try:
        conn = get_connection()
        cursor = conn.cursor()
        
        date_from = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d %H:%M:%S')
        cursor.execute("""
            SELECT amount, date 
            FROM expenses 
            WHERE user_id = ? AND category = ? AND date >= ?
            ORDER BY date DESC
        """, (user_id, category, date_from))
        
        result = cursor.fetchall()
        conn.close()
        return result
    except Exception as e:
        print(f"Ошибка get_expenses_by_category_detail: {e}")
        return []


def get_top_expenses(user_id, limit=5, days=30):
    """Получает самые большие траты пользователя"""
    try:
        conn = get_connection()
        cursor = conn.cursor()
        
        date_from = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d %H:%M:%S')
        cursor.execute("""
            SELECT category, amount, date 
            FROM expenses 
            WHERE user_id = ? AND date >= ?
            ORDER BY amount DESC
            LIMIT ?
        """, (user_id, date_from, limit))
        
        result = cursor.fetchall()
        conn.close()
        return result
    except Exception as e:
        print(f"Ошибка get_top_expenses: {e}")
        return []