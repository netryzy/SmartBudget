# services/ai_recommendations.py - ЛИМИТЫ ДЛЯ ВСЕХ КАТЕГОРИЙ
from openai import AsyncOpenAI
from config import OPENAI_API_KEY
from database.queries import get_expenses, get_income, get_categories, get_detailed_expenses, get_expenses_by_category_detail, get_top_expenses
from datetime import datetime, timedelta
import random

client = AsyncOpenAI(api_key=OPENAI_API_KEY, timeout=30.0)


def check_category_limits(user_id: int, category: str, added_amount: float) -> str:
    """
    Проверяет, не превышает ли пользователь лимиты по категории
    """
    # Получаем доход за последние 30 дней
    income_total = get_income(user_id, 30)
    
    if income_total == 0:
        return None
    
    # Получаем ВСЕ расходы по категории за последние 30 дней
    categories = get_categories(user_id, 30)
    current_category_expenses = 0
    for cat, amt in categories:
        if cat == category:
            current_category_expenses = amt
            break
    
    # Рассчитываем процент от дохода
    percent_of_income = (current_category_expenses / income_total) * 100
    
    # Получаем детальные траты по категории
    detailed_expenses = get_expenses_by_category_detail(user_id, category, 30)
    
    # Находим самую большую трату
    max_expense = 0
    for amt, _ in detailed_expenses:
        if amt > max_expense:
            max_expense = amt
    
    # ========== ЛИМИТЫ ДЛЯ ВСЕХ КАТЕГОРИЙ ==========
    limits = {
        'Еда': {'warning': 30, 'critical': 40, 
                'advice': 'Попробуйте готовить дома вместо кафе и ресторанов. Планируйте меню на неделю и покупайте продукты по списку.'},
        
        'Транспорт': {'warning': 10, 'critical': 15, 
                     'advice': 'Рассмотрите общественный транспорт вместо такси. При поездках на такси используйте каршеринг или делите поездку с друзьями.'},
        
        'Жильё': {'warning': 30, 'critical': 40, 
                 'advice': 'Проверьте, можно ли сэкономить на коммунальных услугах - установите счетчики, энергосберегающие лампы, выключайте приборы из розетки.'},
        
        'Здоровье': {'warning': 15, 'critical': 25,
                    'advice': 'Занимайтесь профилактикой, это дешевле лечения. Сравнивайте цены в разных аптеках, покупайте аналоги лекарств.'},
        
        'Салоны красоты': {'warning': 8, 'critical': 12, 
                          'advice': 'Ищите скидки, записывайтесь в дни акций, делайте процедуры реже или ищите более бюджетные варианты.'},
        
        'Подарки': {'warning': 10, 'critical': 15,
                   'advice': 'Подарки - это приятно, но можно экономить: делайте подарки своими руками, дарите впечатления вместо вещей.'},
        
        'Покупки': {'warning': 15, 'critical': 25, 
                   'advice': 'Перед покупкой подождите 24 часа - часто желание отпадает. Используйте кэшбэк и покупайте на распродажах.'},
        
        'Развлечения': {'warning': 10, 'critical': 15, 
                       'advice': 'Ищите бесплатные мероприятия, используйте скидочные купоны, устраивайте домашние кинопросмотры вместо походов в кино.'},
        
        'Образование': {'warning': 15, 'critical': 25,
                       'advice': 'Ищите бесплатные онлайн-курсы, пользуйтесь библиотеками, покупайте учебники б/у.'},
        
        'Путешествия': {'warning': 20, 'critical': 30,
                       'advice': 'Планируйте поездки заранее, используйте скидочные сайты, летайте лоукостерами, живите в хостелах.'},
        
        'Связь': {'warning': 5, 'critical': 8,
                 'advice': 'Проверьте свой тариф - возможно, есть более выгодный. Откажитесь от ненужных подписок.'},
        
        'Финансы': {'warning': 15, 'critical': 25,
                   'advice': 'Старайтесь не брать кредиты, платите по счетам вовремя, чтобы избежать штрафов и пеней.'},
        
        'Другое': {'warning': 15, 'critical': 25,
                  'advice': 'Попробуйте конкретизировать ваши траты, чтобы лучше понимать, куда уходят деньги.'}
    }
    
    # Если категории нет в limits, используем стандартные лимиты
    if category not in limits:
        limits[category] = {'warning': 15, 'critical': 25, 
                           'advice': 'Попробуйте проанализировать эту категорию расходов и найти способы экономии.'}
    
    limit = limits[category]
    
    # Формируем предупреждение в зависимости от процента
    if percent_of_income >= limit['critical']:
        return f"""
⚠️ <b>КРИТИЧЕСКОЕ ПРЕДУПРЕЖДЕНИЕ!</b>

Вы уже потратили <b>{current_category_expenses:.2f} руб.</b> на категорию "<b>{category}</b>", 
что составляет <b>{percent_of_income:.1f}%</b> от вашего дохода!

Рекомендуемая норма: до {limit['warning']}% от дохода

🔍 <b>Самая крупная трата:</b> {max_expense:.2f} руб.

💡 <b>Совет:</b> {limit['advice']}
🎯 <b>Цель:</b> Сократить расходы на {category} до {limit['warning']}% от дохода в следующем месяце
"""
    elif percent_of_income >= limit['warning']:
        return f"""
⚠️ <b>Внимание!</b>

Вы тратите многовато на категорию "<b>{category}</b>": 
<b>{current_category_expenses:.2f} руб.</b> ({percent_of_income:.1f}% от дохода)

Рекомендуемая норма: до {limit['warning']}% от дохода

🔍 <b>Самая крупная трата:</b> {max_expense:.2f} руб.

💡 <b>Совет:</b> {limit['advice']}
"""
    
    return None


async def get_ai_recommendations(user_id: int) -> str:
    """Получает живые, персонализированные рекомендации"""
    expenses_total = get_expenses(user_id, 30)
    income_total = get_income(user_id, 30)
    categories = get_categories(user_id, 30)
    top_expenses = get_top_expenses(user_id, 5, 30)
    
    if expenses_total == 0:
        return "📭 У вас пока нет данных для анализа.\n\nДобавьте траты за несколько дней, и я смогу дать вам персональные рекомендации!"
    
    balance = income_total - expenses_total
    
    response = f"🤖 <b>Анализ твоих финансов</b> 📊\n\n"
    response += f"💰 <b>Доходы:</b> {income_total:.2f} руб.\n"
    response += f"💸 <b>Расходы:</b> {expenses_total:.2f} руб.\n"
    response += f"{'✅' if balance >= 0 else '⚠️'} <b>Баланс:</b> {balance:.2f} руб.\n\n"
    
    # Анализ категорий с превышением лимитов
    if categories and income_total > 0:
        response += f"📊 <b>Анализ категорий:</b>\n"
        
        limits_info = {
            'Еда': 30, 'Транспорт': 10, 'Жильё': 30, 'Здоровье': 15,
            'Салоны красоты': 8, 'Подарки': 10, 'Покупки': 15, 'Развлечения': 10,
            'Образование': 15, 'Путешествия': 20, 'Связь': 5, 'Финансы': 15, 'Другое': 15
        }
        
        problem_categories = []
        for cat, amt in categories:
            percent = (amt / income_total) * 100
            norm = limits_info.get(cat, 15)
            if percent > norm:
                problem_categories.append((cat, amt, percent, norm))
        
        if problem_categories:
            for cat, amt, percent, norm in sorted(problem_categories, key=lambda x: x[2], reverse=True)[:3]:
                response += f"• <b>{cat}</b>: {amt:.2f} руб. ({percent:.1f}% от дохода) - норма до {norm}%\n"
                if cat == 'Жильё':
                    response += f"  💡 Совет: Проверьте коммунальные платежи, возможно, есть переплата.\n"
                elif cat == 'Связь':
                    response += f"  💡 Совет: Смените тариф на более выгодный, откажитесь от ненужных подписок.\n"
                elif cat == 'Салоны красоты':
                    response += f"  💡 Совет: Ищите скидки, записывайтесь в дни акций.\n"
                elif cat == 'Подарки':
                    response += f"  💡 Совет: Делайте подарки своими руками, это дешевле и душевнее.\n"
                elif cat == 'Транспорт':
                    response += f"  💡 Совет: Используйте общественный транспорт вместо такси.\n"
                elif cat == 'Еда':
                    response += f"  💡 Совет: Готовьте дома, планируйте меню на неделю.\n"
                elif cat == 'Развлечения':
                    response += f"  💡 Совет: Ищите бесплатные мероприятия.\n"
                else:
                    response += f"  💡 Совет: Постарайтесь сократить расходы в этой категории.\n"
            response += "\n"
        else:
            response += f"✅ Отлично! Все ваши расходы в пределах нормы.\n\n"
    
    # Топ траты
    if top_expenses:
        response += f"🔍 <b>Самые крупные траты за месяц:</b>\n"
        for i, (cat, amt, date) in enumerate(top_expenses[:3], 1):
            percent = (amt / income_total * 100) if income_total > 0 else 0
            response += f"{i}. {cat}: {amt:.2f} руб. ({percent:.1f}% от дохода)\n"
        response += "\n"
    
    # Общие советы
    response += f"💡 <b>Общие советы по экономии:</b>\n"
    response += f"• Откладывайте 10-20% от каждого дохода\n"
    response += f"• Ведите учет трат ежедневно\n"
    response += f"• Перед крупной покупкой подождите 3 дня\n"
    response += f"• Используйте кэшбэк и бонусы\n"
    
    return response