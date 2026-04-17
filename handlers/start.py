# handlers/start.py - РАСШИРЕННЫЙ (добавлены все категории)
from aiogram import Router
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from database.queries import get_income, get_expenses, get_categories
from utils.ai_logic import smart_parse_expenses, smart_parse_income, detect_message_intent
from database.queries import add_expense_to_db, add_income_to_db
from services.ai_recommendations import get_ai_recommendations, check_category_limits
import re

router = Router()


def get_welcome_keyboard():
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🚀 Начать мониторить бюджет", callback_data="start_monitoring")],
            [InlineKeyboardButton(text="ℹ️ Как это работает", callback_data="how_it_works")]
        ]
    )
    return keyboard


def get_main_menu():
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="➕ Добавить трату", callback_data="add_expense"),
                InlineKeyboardButton(text="💰 Добавить доход", callback_data="add_income")
            ],
            [
                InlineKeyboardButton(text="📊 Статистика", callback_data="show_stats"),
                InlineKeyboardButton(text="🏦 Мой баланс", callback_data="show_balance")
            ],
            [
                InlineKeyboardButton(text="🤖 Рекомендации", callback_data="show_recommendations"),
                InlineKeyboardButton(text="🗑 Очистить всё", callback_data="clear_data")
            ],
            [
                InlineKeyboardButton(text="❓ Помощь", callback_data="help")
            ]
        ]
    )
    return keyboard


def get_back_keyboard():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="◀️ Назад в меню", callback_data="back_to_menu")]
        ]
    )


@router.message(Command("start"))
async def start(message: Message):
    welcome_text = """
🌟 Добро пожаловать в SmartBudget! 🌟

💰 Начни отслеживать расходы с нашим ботом!

🤖 Я умею:
• 📝 Записывать траты (просто напишите "бананы 400" или "жкх 4000")
• 💰 Добавлять доходы ("зарплата 50000")
• 📊 Показывать статистику ("статистика за неделю")
• 🤖 Давать рекомендации ("дай совет")

Просто напишите сумму и что купили - я пойму! 🚀
"""
    
    await message.answer(
        welcome_text,
        reply_markup=get_welcome_keyboard(),
        parse_mode="HTML"
    )


@router.message(Command("help"))
async def help_command(message: Message):
    text = """
❓ <b>ПОМОЩЬ</b>

<b>Что я умею понимать:</b>

📝 <b>Добавление трат:</b>
• "бананы 400" - Еда
• "жкх 4000" - Жильё
• "строительство 3500" - Жильё
• "телефон 300" - Связь
• "парикмахерская 2000" - Салоны красоты

💰 <b>Добавление доходов:</b>
• "зарплата 50000"
• "подарили 1000"

📊 <b>Запрос статистики:</b>
• "статистика за день"
• "статистика за неделю"

🤖 <b>Рекомендации:</b>
• "дай рекомендацию"
"""
    await message.answer(text, parse_mode="HTML", reply_markup=get_main_menu())


@router.message(Command("cancel"))
async def cancel_command(message: Message, state: any):
    from aiogram.fsm.context import FSMContext
    
    current_state = await state.get_state()
    
    if current_state:
        await state.clear()
        await message.answer("❌ Действие отменено", reply_markup=get_main_menu())
    else:
        await message.answer("❌ Нет активных действий", reply_markup=get_main_menu())


@router.callback_query(lambda c: c.data == "start_monitoring")
async def start_monitoring(callback_query: CallbackQuery):
    await callback_query.message.edit_text(
        "🎉 Отлично! Давайте начнем!\n\n"
        "📝 <b>Что вы можете делать:</b>\n\n"
        "1️⃣ <b>Писать в чат:</b>\n"
        "   • \"бананы 400\"\n"
        "   • \"жкх 4000\"\n"
        "   • \"строительство 3500\"\n"
        "   • \"зарплата 50000\"\n\n"
        "2️⃣ <b>Использовать кнопки меню</b>\n\n"
        "Начните прямо сейчас 👇",
        reply_markup=get_main_menu(),
        parse_mode="HTML"
    )
    await callback_query.answer()


@router.callback_query(lambda c: c.data == "how_it_works")
async def how_it_works(callback_query: CallbackQuery):
    text = """
📚 <b>КАК РАБОТАЕТ БОТ:</b>

<b>1️⃣ Добавление трат:</b>
Просто напишите: "бананы 400" или "жкх 4000"

<b>2️⃣ Добавление доходов:</b>
Напишите: "зарплата 50000" или "подарили 1000"

<b>3️⃣ Получение статистики:</b>
• "статистика за день"
• "статистика за неделю"

<b>4️⃣ Рекомендации:</b>
• "дай совет"
• "как экономить"

💡 <b>Совет:</b> Чем чаще вы записываете траты, тем точнее анализ!
"""
    await callback_query.message.answer(text, reply_markup=get_back_keyboard(), parse_mode="HTML")
    await callback_query.answer()


@router.callback_query(lambda c: c.data == "back_to_menu")
async def back_to_menu(callback_query: CallbackQuery):
    await callback_query.message.edit_text(
        "📋 Главное меню",
        reply_markup=get_main_menu(),
        parse_mode="HTML"
    )
    await callback_query.answer()


@router.callback_query(lambda c: c.data == "show_balance")
async def show_balance(callback_query: CallbackQuery):
    user_id = callback_query.from_user.id
    income = get_income(user_id)
    expenses = get_expenses(user_id)
    balance = income - expenses
    
    text = f"""
🏦 <b>ВАШ БАЛАНС</b>

💰 Доходы: {income:.2f} руб.
💸 Расходы: {expenses:.2f} руб.
━━━━━━━━━━━━━━━━━━━━
✅ Баланс: {balance:.2f} руб.
"""
    await callback_query.message.answer(text, reply_markup=get_main_menu(), parse_mode="HTML")
    await callback_query.answer()


@router.callback_query(lambda c: c.data == "help")
async def help_menu(callback_query: CallbackQuery):
    text = """
❓ <b>ПОМОЩЬ</b>

<b>📝 Добавить траты:</b>
Напишите: "бананы 400" или "жкх 4000"

<b>💰 Добавить доход:</b>
Напишите: "зарплата 50000"

<b>📊 Статистика:</b>
Напишите: "статистика за неделю"

<b>🤖 Рекомендации:</b>
Напишите: "дай рекомендацию"
"""
    await callback_query.message.answer(text, reply_markup=get_main_menu(), parse_mode="HTML")
    await callback_query.answer()


@router.callback_query(lambda c: c.data == "clear_data")
async def clear_data(callback_query: CallbackQuery):
    import sqlite3
    conn = sqlite3.connect("finance.db")
    cursor = conn.cursor()
    cursor.execute("DELETE FROM expenses WHERE user_id=?", (callback_query.from_user.id,))
    cursor.execute("DELETE FROM income WHERE user_id=?", (callback_query.from_user.id,))
    conn.commit()
    conn.close()
    
    await callback_query.message.answer(
        "✅ Все данные очищены!",
        reply_markup=get_main_menu(),
        parse_mode="HTML"
    )
    await callback_query.answer()


@router.callback_query(lambda c: c.data == "show_recommendations")
async def show_recommendations(callback_query: CallbackQuery):
    user_id = callback_query.from_user.id
    
    processing_msg = await callback_query.message.answer(
        "🤖 ИИ анализирует ваши расходы...\n\nЭто может занять несколько секунд..."
    )
    
    try:
        recommendations = await get_ai_recommendations(user_id)
        
        await processing_msg.delete()
        await callback_query.message.answer(
            recommendations,
            reply_markup=get_main_menu(),
            parse_mode="HTML"
        )
        
    except Exception as e:
        await processing_msg.delete()
        print(f"Ошибка: {e}")
        await callback_query.message.answer(
            "❌ Не удалось получить рекомендации\n\nДобавьте больше трат и попробуйте снова.",
            reply_markup=get_main_menu(),
            parse_mode="HTML"
        )
    
    await callback_query.answer()


@router.callback_query(lambda c: c.data == "show_stats")
async def show_stats_menu(callback_query: CallbackQuery):
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
    
    from services.analytics import get_stats, compare_periods, generate_expense_chart
    from aiogram.types import FSInputFile
    import os
    
    stats = get_stats(user_id, days)
    expenses = stats['expenses']
    income = stats['income']
    balance = stats['balance']
    
    text = f"📊 <b>Статистика {period_name}</b>\n\n"
    text += f"💰 Доходы: {income:.2f} руб.\n"
    text += f"💸 Расходы: {expenses:.2f} руб.\n"
    text += f"{'='*30}\n"
    
    if balance >= 0:
        text += f"✅ Остаток: {balance:.2f} руб.\n"
    else:
        text += f"⚠️ Дефицит: {balance:.2f} руб.\n"
    
    if expenses > 0 and days:
        comparison = compare_periods(user_id, days)
        text += f"\n{comparison}"
    
    await callback_query.message.answer(text, parse_mode="HTML", reply_markup=get_main_menu())
    
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
    
    await callback_query.answer()


# =====================
# УНИВЕРСАЛЬНЫЙ ОБРАБОТЧИК СООБЩЕНИЙ
# =====================

@router.message()
async def handle_any_message(message: Message):
    """Универсальный обработчик для любых сообщений"""
    text = message.text.strip()
    print(f"📨 Получено сообщение: {text}")
    
    # Пропускаем команды
    if text.startswith('/'):
        print("Это команда, пропускаем")
        return
    
    user_id = message.from_user.id
    text_lower = text.lower()
    
    # ===== ОБРАБОТКА ЗАПРОСОВ РЕКОМЕНДАЦИЙ =====
    recommendation_keywords = ['рекомендац', 'совет', 'как экономить', 'дай совет', 'помоги', 'что делать']
    if any(keyword in text_lower for keyword in recommendation_keywords):
        print("🔍 Распознан запрос рекомендаций")
        processing_msg = await message.answer("🤖 Анализирую ваши финансы...")
        try:
            recommendations = await get_ai_recommendations(user_id)
            await processing_msg.delete()
            await message.answer(recommendations, parse_mode="HTML")
        except Exception as e:
            await processing_msg.delete()
            print(f"Ошибка: {e}")
            await message.answer("❌ Не удалось получить рекомендации. Добавьте больше данных о тратах.")
        return
    
    # ===== ОБРАБОТКА ЗАПРОСОВ СТАТИСТИКИ =====
    if 'статистик' in text_lower or 'покажи статистику' in text_lower:
        print("🔍 Распознан запрос статистики")
        from services.analytics import get_stats, compare_periods, generate_expense_chart
        from aiogram.types import FSInputFile
        import os
        
        days = 30
        period_name = "за 30 дней"
        
        if 'день' in text_lower or 'сегодня' in text_lower:
            days = 1
            period_name = "за сегодня"
        elif 'недел' in text_lower:
            days = 7
            period_name = "за 7 дней"
        elif 'месяц' in text_lower:
            days = 30
            period_name = "за 30 дней"
        
        stats = get_stats(user_id, days)
        expenses = stats['expenses']
        income = stats['income']
        balance = stats['balance']
        
        response = f"📊 <b>Статистика {period_name}</b>\n\n"
        response += f"💰 Доходы: {income:.2f} руб.\n"
        response += f"💸 Расходы: {expenses:.2f} руб.\n"
        response += f"{'✅' if balance >= 0 else '⚠️'} Баланс: {balance:.2f} руб.\n"
        
        await message.answer(response, parse_mode="HTML")
        
        if expenses > 0:
            chart = generate_expense_chart(user_id, days)
            if chart and os.path.exists(chart):
                try:
                    await message.answer_photo(
                        FSInputFile(chart),
                        caption="📈 Структура ваших расходов"
                    )
                    os.remove(chart)
                except Exception as e:
                    print(f"Ошибка отправки графика: {e}")
        return
    
    # ===== ОБРАБОТКА ДОХОДОВ =====
    income_keywords = ['зарплат', 'получил', 'перевели', 'зачислили', 'пришло', 'начислили']
    
    # Проверка на подарок (вам подарили)
    if 'подарили' in text_lower:
        print("🎁 Распознан подарок как ДОХОД")
        numbers = re.findall(r'(\d+(?:[.,]\d+)?)', text)
        if numbers:
            amount = float(numbers[0].replace(',', '.'))
            add_income_to_db(user_id, amount, "подарок")
            await message.answer(f"✅ <b>Доход добавлен!</b>\n\n💰 Сумма: {amount:.2f} руб.\n📌 Источник: подарок", parse_mode="HTML")
        return
    
    if any(keyword in text_lower for keyword in income_keywords):
        print("🔍 Распознан доход")
        numbers = re.findall(r'(\d+(?:[.,]\d+)?)', text)
        if numbers:
            amount = float(numbers[0].replace(',', '.'))
            add_income_to_db(user_id, amount, "")
            await message.answer(f"✅ <b>Доход добавлен!</b>\n\n💰 Сумма: {amount:.2f} руб.", parse_mode="HTML")
        return
    
    # ===== ОБРАБОТКА ТРАТ =====
    numbers = re.findall(r'(\d+(?:[.,]\d+)?)', text)
    if numbers:
        print("🔍 Распознаны потенциальные траты")
        processing_msg = await message.answer("🧠 Анализирую траты...")
        try:
            total_amount = sum(float(n.replace(',', '.')) for n in numbers)
            
            # ========== РАСШИРЕННЫЕ КЛЮЧЕВЫЕ СЛОВА ДЛЯ КАЖДОЙ КАТЕГОРИИ ==========
            
            # 1. Жильё (расширенный)
            housing_keywords = [
                # Основные слова
                'квартир', 'аренд', 'жильё', 'жилье', 'коммуналк', 'жкх', 'свет', 'вода', 'газ', 
                'отопление', 'ремонт', 'строительство', 'стройка', 'стройматериалы', 'сантехник', 
                'электрик', 'домофон', 'коммунальн', 'пломбир', 'мосэнерго', 'водоканал',
                # С предлогами
                'за квартиру', 'за аренду', 'на ремонт', 'на стройку', 'на строительство',
                'за свет', 'за воду', 'за газ', 'за отопление', 'за коммуналку',
                # Дополнительно
                'ипотек', 'квартплат', 'жилплощадь', 'недвижимость', 'дача', 'загородный дом',
                'капремонт', 'отделка', 'евроремонт', 'квартира', 'комната', 'общежитие'
            ]

            # 2. Связь (расширенный)
            communication_keywords = [
                # Основные слова
                'телефон', 'интернет', 'связь', 'мобильн', 'роуминг', 'подписк', 'ютуб', 
                'нетфликс', 'спотифай', 'билайн', 'мтс', 'мегафон', 'теле2', 'йота', 'тим',
                # С предлогами
                'за телефон', 'за интернет', 'на связь', 'на телефон', 'на интернет',
                'за подписку', 'за ютуб', 'за нетфликс', 'за спотифай',
                # Дополнительно
                'сим-карта', 'симка', 'тариф', 'мессенджер', 'вотсап', 'телеграм',
                'домашний интернет', 'мобильный интернет', 'безлимит', 'гигабайты'
            ]

            # 3. Еда (расширенный)
            food_keywords = [
                # Фрукты и ягоды
                'банан', 'яблоко', 'груша', 'апельсин', 'мандарин', 'лимон', 'киви', 'виноград',
                'клубника', 'малина', 'арбуз', 'дыня', 'персик', 'абрикос', 'слива', 'вишня',
                'черешня', 'гранат', 'ананас', 'манго', 'папайя', 'инжир', 'хурма', 'черника',
                'голубика', 'ежевика', 'смородина', 'крыжовник', 'клюква', 'брусника',
                # Овощи
                'помидор', 'огурец', 'картофель', 'морковь', 'свекла', 'лук', 'чеснок', 'капуста',
                'брокколи', 'цветная капуста', 'перец', 'баклажан', 'кабачок', 'тыква', 'редис',
                'редька', 'сельдерей', 'петрушка', 'укроп', 'салат', 'шпинат', 'щавель', 'репа',
                # Продукты
                'хлеб', 'молоко', 'кефир', 'йогурт', 'творог', 'сметана', 'масло', 'сыр', 'колбаса',
                'мясо', 'курица', 'рыба', 'яйца', 'крупы', 'рис', 'гречка', 'макароны', 'мука',
                'сахар', 'соль', 'специи', 'кофе', 'чай', 'сок', 'вода', 'газировка', 'сладости',
                'печенье', 'конфеты', 'шоколад', 'мороженое', 'торт', 'пицца', 'бургер', 'суши',
                'роллы', 'суп', 'борщ', 'каша', 'пюре', 'котлета', 'сосиска', 'пельмени', 'вареники',
                'блины', 'оладьи', 'сырники', 'запеканка', 'омлет', 'яичница', 'бутерброд',
                # Места и действия
                'еда', 'продукты', 'кафе', 'ресторан', 'столовая', 'супермаркет', 'магазин',
                'продуктовый', 'обед', 'ужин', 'завтрак', 'перекус', 'ланч', 'фастфуд',
                'доставка еды', 'доставка продуктов', 'еда на вынос',
                # С предлогами
                'на еду', 'на продукты', 'на обед', 'на ужин', 'в кафе', 'в ресторане',
                'на кофе', 'на чай', 'за продуктами', 'в супермаркете', 'за едой'
            ]

            # 4. Салоны красоты (расширенный)
            beauty_keywords = [
                # Основные слова
                'парикмахер', 'стрижк', 'постриг', 'салон', 'маникюр', 'педикюр', 'брови', 
                'ресницы', 'косметолог', 'ногти', 'покраска', 'укладка', 'барбершоп',
                'бритье', 'борода', 'усы', 'каре', 'боб', 'мелирование', 'тонирование',
                'ламинирование', 'ботокс', 'штукатурка', 'чистка лица', 'пилинг', 'массаж',
                'спа', 'бьюти', 'визаж', 'мейкап', 'бб-покрытие', 'перманент', 'татуаж',
                # С предлогами
                'в парикмахерской', 'на стрижку', 'на маникюр', 'на педикюр', 'на брови',
                'на ресницы', 'в салоне', 'на покраску', 'на укладку', 'в барбершопе',
                # Дополнительно
                'уход за лицом', 'уход за телом', 'обертывание', 'депиляция', 'эпиляция',
                'лазерная эпиляция', 'шоколадное обертывание', 'антицеллюлитный'
            ]

            # 5. Подарки (расширенный)
            gift_keywords = [
                'подарил', 'презент', 'сюрприз', 'дарить', 'вручил', 'подарочный',
                # С предлогами
                'на подарок', 'за подарок', 'подарил другу', 'подарил маме', 'подарил папе',
                'подарил сестре', 'подарил брату', 'подарил жене', 'подарил мужу',
                'купил подарок', 'выбрал подарок', 'заказал подарок'
            ]

            # 6. Транспорт (расширенный)
            transport_keywords = [
                # Основные слова
                'такси', 'метро', 'автобус', 'проезд', 'транспорт', 'маршрутка', 'бензин', 
                'заправка', 'электричка', 'поезд', 'билет', 'трамвай', 'троллейбус', 
                'машина', 'автомобиль', 'авто', 'тс', 'транспортное средство',
                'грузовик', 'фура', 'мотоцикл', 'скутер', 'велосипед', 'самокат',
                'авиабилет', 'самолет', 'вертолет', 'корабль', 'паром', 'теплоход',
                # С предлогами
                'на машину', 'на авто', 'на такси', 'на метро', 'на автобусе', 'на маршрутке',
                'на электричке', 'на поезде', 'на трамвае', 'на троллейбусе', 'на бензин',
                'на заправку', 'на такси', 'на проезд', 'на билеты', 'за бензин',
                # Дополнительно
                'каршеринг', 'убери', 'gett', 'яндекс такси', 'ситимобил', 'болт',
                'ОСАГО', 'КАСКО', 'техосмотр', 'шины', 'колеса', 'ремонт авто', 'мойка авто'
            ]

            # 7. Здоровье (расширенный)
            health_keywords = [
                # Основные слова
                'аптека', 'лекарств', 'врач', 'больниц', 'стоматолог', 'анализ', 'витамины',
                'медосмотр', 'фитнес', 'спортзал', 'бассейн', 'таблетки', 'лечение',
                'диагностика', 'прививка', 'укол', 'капельница', 'рецепт', 'медикаменты',
                # С предлогами
                'в аптеке', 'на лекарства', 'к врачу', 'в больницу', 'на анализы',
                'на витамины', 'в спортзал', 'в бассейн', 'на лечение', 'на прививку',
                # Дополнительно
                'медстраховка', 'дмс', 'полис', 'скорая', 'вызов врача', 'осмотр',
                'операция', 'хирургия', 'физиотерапия', 'массаж лечебный', 'реабилитация'
            ]

            # 8. Покупки (расширенный)
            shopping_keywords = [
                # Основные слова
                'одежда', 'обувь', 'техник', 'маркетплейс', 'вещи', 'аксессуары', 'мебель',
                'посуда', 'бытовая техника', 'кроссовки', 'сумка', 'часы', 'ювелирк',
                'футболка', 'джинсы', 'брюки', 'куртка', 'пальто', 'шапка', 'шарф',
                'перчатки', 'носки', 'белье', 'пижама', 'халат', 'тапочки', 'сандалии',
                'сапоги', 'туфли', 'лодочки', 'кеды', 'сникерсы', 'лэптоп', 'ноутбук',
                'компьютер', 'планшет', 'телевизор', 'холодильник', 'стиралка', 'микроволновка',
                'чайник', 'утюг', 'пылесос', 'наушники', 'колонка', 'зарядка', 'чехол',
                # С предлогами
                'на одежду', 'на обувь', 'на технику', 'на маркетплейсе', 'на вещи',
                'в магазине', 'на мебель', 'на посуду', 'на бытовую технику'
            ]

            # 9. Развлечения (расширенный)
            entertainment_keywords = [
                # Основные слова
                'кино', 'театр', 'концерт', 'игры', 'бар', 'клуб', 'боулинг', 'квест', 
                'парк', 'аттракцион', 'хобби', 'караоке', 'выставка', 'музей', 'цирк',
                'аквапарк', 'зоопарк', 'квеструм', 'виртуальная реальность', 'пейнтбол',
                'страйкбол', 'бильярд', 'покер', 'настольные игры', 'плейстейшен', 'ксбокс',
                'компьютерные игры', 'мобильные игры', 'подписка на игры',
                # С предлогами
                'в кино', 'в театр', 'на концерт', 'на игры', 'в бар', 'в клуб', 'на боулинг',
                'на квест', 'в парк', 'на аттракционы', 'на хобби', 'в караоке', 'в музей'
            ]

            # 10. Образование (расширенный)
            education_keywords = [
                # Основные слова
                'курсы', 'учеба', 'книги', 'учебник', 'репетитор', 'тренинг', 'вебинар', 'школа',
                'университет', 'институт', 'колледж', 'академия', 'лекция', 'семинар', 'мастеркласс',
                'тренировка', 'обучение', 'повышение квалификации', 'профпереподготовка',
                'магистратура', 'аспирантура', 'диплом', 'сертификат', 'аттестат',
                # С предлогами
                'на курсы', 'на учебу', 'на книги', 'на учебники', 'репетитору', 'на тренинг',
                'на вебинар', 'в школу', 'в университет', 'на обучение', 'за образование'
            ]

            # 11. Путешествия (расширенный)
            travel_keywords = [
                # Основные слова
                'отель', 'гостиница', 'хостел', 'виза', 'экскурсия', 'тур', 'путешестви',
                'отпуск', 'авиабилет', 'поезд билет', 'турпутевка', 'впечатления',
                'поездка', 'командировка', 'турфирма', 'тревел', 'бронирование',
                'апартаменты', 'вилла', 'кемпинг', 'турбаза', 'санаторий',
                # С предлогами
                'в отель', 'в гостиницу', 'в хостел', 'на визу', 'на экскурсию', 'в тур',
                'в отпуск', 'на авиабилеты', 'на поезд', 'на путешествие', 'за путевкой',
                'в командировку', 'в поездку'
            ]

            # 12. Финансы (расширенный)
            finance_keywords = [
                # Основные слова
                'кредит', 'ипотека', 'налог', 'штраф', 'комиссия', 'проценты', 'страховка', 'долг',
                'займ', 'микрозайм', 'пеня', 'неустойка', 'госпошлина', 'алименты', 'рассрочка',
                'банк', 'банковские услуги', 'обслуживание счета', 'снятие наличных',
                # С предлогами
                'по кредиту', 'за кредит', 'по ипотеке', 'на налоги', 'на штраф', 'за комиссию',
                'на страховку', 'по долгу', 'в банке', 'за обслуживание'
            ]

            # 13. Домашние питомцы (добавим новую категорию)
            pets_keywords = [
                'корм', 'ветеринар', 'зоомагазин', 'наполнитель', 'игрушки для кошек',
                'игрушки для собак', 'поводок', 'ошейник', 'миска', 'лежак', 'клетка',
                'аквариум', 'террариум', 'сухой корм', 'влажный корм', 'лекарства для животных',
                'прививки для животных', 'груминг', 'стрижка собак', 'передержка',
                # С предлогами
                'на корм', 'ветеринару', 'в зоомагазине', 'для кота', 'для собаки', 'для хомяка'
            ]

            # 14. Косметика (отдельно от салонов)
            cosmetics_keywords = [
                'косметика', 'парфюм', 'духи', 'туалетная вода', 'помада', 'тушь', 'тени',
                'тональный крем', 'пудра', 'румяна', 'хайлайтер', 'консилер', 'карандаш для глаз',
                'подводка', 'база под макияж', 'праймер', 'фиксатор', 'мицеллярная вода',
                'пенка для умывания', 'скраб', 'пилинг', 'маска для лица', 'сыворотка',
                'крем для лица', 'крем для рук', 'крем для ног', 'лосьон', 'бальзам',
                'шампунь', 'кондиционер', 'маска для волос', 'масло для волос', 'лак для волос',
                'мусс', 'пенка', 'воск', 'гель для душа', 'мыло', 'гель для бритья',
                # С предлогами
                'на косметику', 'на парфюм', 'в магазине косметики', 'за духами'
            ]

            # 15. Алкоголь и табак (дополнительная категория)
            alcohol_tobacco_keywords = [
                'алкоголь', 'пиво', 'вино', 'шампанское', 'водка', 'коньяк', 'ром', 'виски',
                'джин', 'текила', 'ликер', 'наливка', 'коктейль', 'сигареты', 'табак',
                'вейп', 'жидкость для вейпа', 'испаритель', 'айкос', 'стики', 'нюхательный табак',
                # С предлогами
                'на алкоголь', 'на пиво', 'на вино', 'на сигареты', 'в вейпшопе'
            ]
            # ========== ОПРЕДЕЛЕНИЕ КАТЕГОРИИ ==========
            category = "Другое"
            
            if any(keyword in text_lower for keyword in pets_keywords):
                category = "Питомцы"
            elif any(keyword in text_lower for keyword in alcohol_tobacco_keywords):
                category = "Алкоголь и табак"
            elif any(keyword in text_lower for keyword in cosmetics_keywords):
                category = "Косметика"
            elif any(keyword in text_lower for keyword in housing_keywords):
                category = "Жильё"
            elif any(keyword in text_lower for keyword in communication_keywords):
                category = "Связь"
            elif any(keyword in text_lower for keyword in beauty_keywords):
                category = "Салоны красоты"
            elif any(keyword in text_lower for keyword in gift_keywords):
                category = "Подарки"
            elif any(keyword in text_lower for keyword in transport_keywords):
                category = "Транспорт"
            elif any(keyword in text_lower for keyword in health_keywords):
                category = "Здоровье"
            elif any(keyword in text_lower for keyword in shopping_keywords):
                category = "Покупки"
            elif any(keyword in text_lower for keyword in entertainment_keywords):
                category = "Развлечения"
            elif any(keyword in text_lower for keyword in education_keywords):
                category = "Образование"
            elif any(keyword in text_lower for keyword in travel_keywords):
                category = "Путешествия"
            elif any(keyword in text_lower for keyword in finance_keywords):
                category = "Финансы"
            elif any(keyword in text_lower for keyword in food_keywords):
                category = "Еда"
            
            # Сохраняем трату
            add_expense_to_db(user_id, category, total_amount)
            
            await processing_msg.delete()
            
            response = f"✅ <b>Траты добавлены!</b>\n\n"
            response += f"📋 <b>Распознано:</b>\n"
            response += f"  • {category}: {total_amount:.2f} руб.\n"
            response += f"\n💰 <b>Итого:</b> {total_amount:.2f} руб."
            
            income = get_income(user_id)
            expenses = get_expenses(user_id)
            balance = income - expenses
            response += f"\n\n🏦 Баланс: {balance:.2f} руб."
            
            await message.answer(response, parse_mode="HTML")
            
            warning = check_category_limits(user_id, category, total_amount)
            if warning:
                await message.answer(warning, parse_mode="HTML")
                
        except Exception as e:
            await processing_msg.delete()
            print(f"Ошибка: {e}")
            await message.answer("❌ Ошибка при обработке трат", parse_mode="HTML")
        return
    
    # Если ничего не распознали
    await message.answer(
        "🤔 Я не понял ваше сообщение.\n\n"
        "📝 <b>Примеры правильного формата:</b>\n"
        "• бананы 400 - Еда\n"
        "• жкх 4000 - Жильё\n"
        "• строительство 3500 - Жильё\n"
        "• телефон 300 - Связь\n"
        "• парикмахерская 2000 - Салоны красоты\n\n"
        "Просто напишите продукт/услугу и сумму!",
        parse_mode="HTML"
    )