# utils/ai_logic.py - УЛУЧШЕННОЕ РАСПОЗНАВАНИЕ ПОДАРКОВ
import json
import re
import sys
import os
from openai import AsyncOpenAI
from config import OPENAI_API_KEY

# Настройка кодировки
if sys.platform == 'darwin':
    import locale
    locale.setlocale(locale.LC_ALL, 'en_US.UTF-8')

sys.stdout.reconfigure(encoding='utf-8')
os.environ['PYTHONIOENCODING'] = 'utf-8'

# Инициализация OpenAI
client = AsyncOpenAI(api_key=OPENAI_API_KEY, timeout=30.0)

# Расширенные категории
CATEGORIES = {
    'Еда': ['еда', 'продукты', 'ресторан', 'кафе', 'обед', 'ужин', 'завтрак', 'пицца', 'бургер', 
            'кофе', 'чай', 'хлеб', 'молоко', 'сыр', 'мясо', 'овощи', 'фрукты', 'сладости',
            'йогурт', 'огурцы', 'помидоры', 'крупы', 'макароны', 'суши', 'фастфуд', 'супермаркет',
            'продуктовый', 'магазин', 'столовая', 'ланч', 'перекус', 'сок', 'вода', 'банан', 'яблоко'],
    
    'Транспорт': ['транспорт', 'такси', 'метро', 'автобус', 'бензин', 'заправка', 'парковка', 'трамвай', 
                  'троллейбус', 'электричка', 'поезд', 'проезд', 'билет', 'uber', 'яндекс такси',
                  'маршрутка', 'авиабилет', 'самолет', 'поездка', 'дорога', 'топливо'],
    
    'Жильё': ['жильё', 'квартира', 'аренда', 'коммуналка', 'жкх', 'свет', 'вода', 'газ', 'отопление', 
              'ремонт', 'сантехник', 'электрик', 'домофон', 'коммунальные'],
    
    'Здоровье': ['здоровье', 'аптека', 'лекарства', 'врач', 'больница', 'стоматолог', 'анализы', 
                 'витамины', 'бады', 'медосмотр', 'страховка', 'фитнес', 'спортзал', 'бассейн',
                 'таблетки', 'лечение', 'диагностика', 'прививка'],
    
    'Салоны красоты': ['парикмахерская', 'парикмахер', 'стрижка', 'постригся', 'салон красоты', 
                       'маникюр', 'педикюр', 'брови', 'ресницы', 'барбершоп', 'укладка', 
                       'покраска', 'салон', 'бьюти', 'визаж', 'мейкап', 'косметолог', 
                       'ногти', 'ламинирование', 'красота', 'постригся'],
    
    'Подарки': ['подарок', 'подарил', 'презент', 'сюрприз', 'подарил другу', 'купил подарок'],
    
    'Покупки': ['покупки', 'одежда', 'обувь', 'техника', 'маркетплейс', 'вещи', 'аксессуары', 'мебель',
                'посуда', 'бытовая техника', 'кроссовки', 'сумка', 'часы', 'ювелирка'],
    
    'Развлечения': ['развлечения', 'кино', 'театр', 'концерт', 'игры', 'бар', 'клуб', 
                    'боулинг', 'квест', 'парк', 'аттракционы', 'хобби', 'рыбалка', 'охота', 'караоке'],
    
    'Образование': ['образование', 'курсы', 'учеба', 'книги', 'учебники', 'репетитор', 'тренинг', 
                    'вебинар', 'школа', 'университет', 'детский сад', 'тренировка'],
    
    'Путешествия': ['путешествия', 'отпуск', 'отель', 'гостиница', 'хостел', 'виза', 'экскурсия', 
                    'тур', 'путёвка', 'чемодан', 'багаж', 'турфирма', 'авиабилеты'],
    
    'Связь': ['связь', 'телефон', 'интернет', 'мобильная связь', 'роуминг', 'мессенджер', 
              'подписка', 'ютуб', 'нетфликс', 'телевидение', 'сим-карта', 'тариф'],
    
    'Финансы': ['кредит', 'ипотека', 'налог', 'штраф', 'комиссия', 'проценты', 'страховка',
                'пеня', 'долг', 'рассрочка', 'банк']
}


async def smart_parse_income(text: str) -> dict:
    """Парсинг доходов через нейросеть"""
    print(f"💰 Анализирую доход: {text}")
    
    text_lower = text.lower()
    
    # КЛЮЧЕВОЕ ПРАВИЛО: если есть "подарили" в ЛЮБОЙ форме - это доход
    gift_income_patterns = [
        'подарили',
        'подарили друзья',
        'подарили подарок',
        'подарок на',
        'друзья подарили'
    ]
    
    for pattern in gift_income_patterns:
        if pattern in text_lower:
            numbers = re.findall(r'(\d+(?:[.,]\d+)?)', text)
            if numbers:
                amount = float(numbers[0].replace(',', '.'))
                print(f"🎁 Распознан ПОДАРОК как ДОХОД: {amount}")
                return {"amount": amount, "source": "подарок"}
    
    # Обычные доходы
    try:
        response = await client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "Ты - финансовый ассистент. Найди сумму дохода в тексте. Верни JSON: {\"amount\": сумма, \"source\": \"источник\"}. Если нет суммы, верни {\"amount\": 0}"},
                {"role": "user", "content": text}
            ],
            temperature=0.1,
            max_tokens=100
        )
        
        content = response.choices[0].message.content
        content = content.replace("```json", "").replace("```", "").strip()
        
        result = json.loads(content)
        return result
        
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        numbers = re.findall(r'(\d+(?:[.,]\d+)?)', text)
        if numbers:
            amount = float(numbers[0].replace(',', '.'))
            return {"amount": amount, "source": ""}
        return None


async def smart_parse_expenses(text: str) -> dict:
    """Умный парсинг трат через нейросеть"""
    print(f"🤖 Нейросеть анализирует траты: {text}")
    
    text_lower = text.lower()
    
    # КЛЮЧЕВОЕ ПРАВИЛО: "подарили" в ЛЮБОЙ форме - это ДОХОД, а не расход
    gift_income_patterns = [
        'подарили',
        'подарили друзья',
        'подарили подарок',
        'друзья подарили'
    ]
    
    for pattern in gift_income_patterns:
        if pattern in text_lower:
            print(f"🎁 '{pattern}' распознано как ДОХОД, возвращаем пустой словарь")
            return {}
    
    # "подарил" (я подарил) - это РАСХОД
    if 'подарил' in text_lower and 'подарили' not in text_lower:
        print("🎁 'Подарил' распознано как РАСХОД в категорию Подарки")
        numbers = re.findall(r'(\d+(?:[.,]\d+)?)', text)
        if numbers:
            amount = float(numbers[0].replace(',', '.'))
            return {"Подарки": amount}
    
    # "купил подарок" - это РАСХОД
    if 'купил подарок' in text_lower or 'потратил на подарок' in text_lower:
        print("🎁 'Купил подарок' распознано как РАСХОД")
        numbers = re.findall(r'(\d+(?:[.,]\d+)?)', text)
        if numbers:
            amount = float(numbers[0].replace(',', '.'))
            return {"Подарки": amount}
    
    # "постригся" - это расход в салоны красоты
    if 'постригся' in text_lower:
        print("💇 'Постригся' распознано как РАСХОД в Салоны красоты")
        numbers = re.findall(r'(\d+(?:[.,]\d+)?)', text)
        if numbers:
            amount = float(numbers[0].replace(',', '.'))
            return {"Салоны красоты": amount}
    
    try:
        response = await client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": """Ты - финансовый ассистент. Верни JSON с тратами.

ВАЖНЕЙШИЕ ПРАВИЛА (СЛЕДУЙ ИМ СТРОГО):
1. 'подарили', 'подарили друзья', 'подарили подарок' - это ДОХОД. НИКОГДА не добавляй в расходы. Верни {}.
2. 'подарил' (я подарил кому-то) - это РАСХОД в категорию 'Подарки'
3. 'купил подарок' - это РАСХОД в категорию 'Подарки'
4. 'постригся' - это РАСХОД в категорию 'Салоны красоты'
5. 'сходил в парикмахерскую' - это РАСХОД в категорию 'Салоны красоты'

Категории: Еда, Транспорт, Жильё, Здоровье, Салоны красоты, Подарки, Покупки, Развлечения

Примеры:
'подарили друзья 1000р' -> {}
'подарил другу 1000р' -> {"Подарки": 1000}
'постригся 1600р' -> {"Салоны красоты": 1600}

ВЕРНИ ТОЛЬКО JSON. БЕЗ ПОЯСНЕНИЙ."""},
                {"role": "user", "content": text}
            ],
            temperature=0.1,
            max_tokens=300
        )
        
        content = response.choices[0].message.content
        content = content.replace("```json", "").replace("```", "").strip()
        
        print(f"📥 Ответ нейросети: {content}")
        
        if not content or content == '':
            return {}
            
        result = json.loads(content)
        
        if isinstance(result, dict):
            for category in result:
                result[category] = float(result[category])
            return result
        else:
            return {}
            
    except json.JSONDecodeError as e:
        print(f"❌ Ошибка JSON: {e}")
        return manual_parse_expenses(text)
    except Exception as e:
        print(f"❌ Ошибка нейросети: {e}")
        return manual_parse_expenses(text)


def manual_parse_expenses(text: str) -> dict:
    """Ручной парсинг (резервный)"""
    result = {}
    text_lower = text.lower()
    
    # Подарили в ЛЮБОЙ форме - доход, не добавляем
    if 'подарили' in text_lower:
        print("🎁 'Подарили' - доход, пропускаем")
        return {}
    
    # Подарил - расход
    if 'подарил' in text_lower:
        numbers = re.findall(r'(\d+(?:[.,]\d+)?)', text)
        if numbers:
            amount = float(numbers[0].replace(',', '.'))
            result['Подарки'] = result.get('Подарки', 0) + amount
            return result
    
    # Постригся - расход
    if 'постригся' in text_lower:
        numbers = re.findall(r'(\d+(?:[.,]\d+)?)', text)
        if numbers:
            amount = float(numbers[0].replace(',', '.'))
            result['Салоны красоты'] = result.get('Салоны красоты', 0) + amount
            return result
    
    # Разбиваем на части
    parts = re.split(r'[,и]\s+', text)
    
    for part in parts:
        part = part.strip().lower()
        if not part or len(part) < 3:
            continue
        
        numbers = re.findall(r'(\d+(?:[.,]\d+)?)\s*р(?:уб)?\.?', part)
        if not numbers:
            continue
        
        amount = float(numbers[0].replace(',', '.'))
        category = detect_category_by_keyword(part)
        result[category] = result.get(category, 0) + amount
    
    return result


def detect_category_by_keyword(text: str) -> str:
    """Определяет категорию по ключевым словам"""
    text_lower = text.lower()
    
    # Подарки (когда вы дарите)
    if 'подарок' in text_lower or 'подарил' in text_lower:
        return 'Подарки'
    
    # Салоны красоты
    beauty_keywords = ['парикмахерская', 'парикмахер', 'стрижка', 'постригся', 'салон красоты', 
                       'маникюр', 'педикюр', 'брови', 'ресницы', 'барбершоп']
    for keyword in beauty_keywords:
        if keyword in text_lower:
            return 'Салоны красоты'
    
    # Транспорт
    transport_keywords = ['такси', 'автобус', 'метро', 'проезд', 'транспорт', 'маршрутка']
    for keyword in transport_keywords:
        if keyword in text_lower:
            return 'Транспорт'
    
    # Еда
    food_keywords = ['кафе', 'ресторан', 'кофе', 'чай', 'еда', 'продукты', 'обед', 'супермаркет',
                     'банан', 'яблоко', 'хлеб', 'молоко', 'сыр', 'мясо', 'магазин']
    for keyword in food_keywords:
        if keyword in text_lower:
            return 'Еда'
    
    return 'Другое'


async def detect_message_intent(text: str) -> str:
    """Определяет намерение пользователя"""
    text_lower = text.lower()
    
    # Подарили в ЛЮБОЙ форме - ДОХОД
    if 'подарили' in text_lower:
        return 'income'
    
    # Подарил - РАСХОД
    if 'подарил' in text_lower:
        return 'expense'
    
    # Постригся - РАСХОД
    if 'постригся' in text_lower:
        return 'expense'
    
    # Доходы
    if any(word in text_lower for word in ['доход', 'зарплата', 'получил', 'перевели', 'зачислили']):
        return 'income'
    
    # Траты
    if any(word in text_lower for word in ['потратил', 'купил', 'оплатил', 'заплатил', 'сходил']):
        return 'expense'
    
    if re.search(r'\d+', text_lower):
        return 'expense'
    
    return 'unknown'