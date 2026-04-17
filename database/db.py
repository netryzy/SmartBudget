# database/db.py - ИСПРАВЛЕННЫЙ
import sqlite3
from datetime import datetime

def get_connection():
    conn = sqlite3.connect("finance.db")
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_connection()
    cursor = conn.cursor()

    # Таблица расходов с правильным типом даты
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS expenses (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        category TEXT,
        amount REAL,
        date TEXT DEFAULT (datetime('now', 'localtime'))
    )
    """)

    # Таблица доходов с правильным типом даты
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS income (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        amount REAL,
        source TEXT,
        date TEXT DEFAULT (datetime('now', 'localtime'))
    )
    """)

    conn.commit()
    conn.close()
    print("✅ База данных инициализирована")