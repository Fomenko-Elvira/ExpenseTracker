"""
Модель данных: доходы, расходы, категории и баланс.

Здесь нет ничего из Kivy — это чистая бизнес-логика,
поэтому её легко проверять тестами (см. папку tests).
"""
import math
import time
import uuid
from datetime import datetime

KIND_EXPENSE = 'expense'
KIND_INCOME = 'income'

# Как тип операции выглядит для пользователя
KIND_LABELS = {KIND_EXPENSE: 'Расход', KIND_INCOME: 'Доход'}
LABEL_TO_KIND = {label: kind for kind, label in KIND_LABELS.items()}

# Категории расходов — из лекции, категории доходов — новые (задание 3)
EXPENSE_CATEGORIES = ['Офис', 'Зарплаты', 'Маркетинг', 'Логистика', 'Налоги', 'Прочее']
INCOME_CATEGORIES = ['Продажи', 'Услуги', 'Инвестиции', 'Прочее']

DATE_FORMAT = '%Y-%m-%d %H:%M:%S'


def categories_for(kind):
    """Список категорий для выбранного типа операции."""
    return INCOME_CATEGORIES if kind == KIND_INCOME else EXPENSE_CATEGORIES


def normalize(record):
    """
    Приводит запись к единому виду.
    Записи из лекции не имеют поля kind — считаем их расходами.
    """
    kind = record.get('kind', KIND_EXPENSE)
    if kind not in KIND_LABELS:
        kind = KIND_EXPENSE
    try:
        amount = float(record.get('amount', 0))
    except (TypeError, ValueError):
        amount = 0.0
    return {
        'kind': kind,
        'category': record.get('category', ''),
        'description': record.get('description', ''),
        'amount': amount,
        'date': record.get('date', ''),
    }


def make_key():
    """
    Уникальный ключ записи.
    Без точки в ключе: Firebase не разрешает '.' в ключах,
    а datetime.timestamp() из лекции даёт дробное число с точкой.
    """
    return f"t_{int(time.time() * 1000)}_{uuid.uuid4().hex[:6]}"


def create_transaction(kind, category, description, amount):
    """
    Проверяет введённые данные и возвращает пару (ключ, запись).
    При ошибке бросает ValueError с понятным текстом.
    """
    if kind not in KIND_LABELS:
        raise ValueError('Неизвестный тип операции')

    try:
        amount = float(str(amount).replace(',', '.'))
    except ValueError:
        raise ValueError('Введите корректную сумму')
    if not math.isfinite(amount) or amount <= 0:
        raise ValueError('Сумма должна быть больше нуля')

    if category not in categories_for(kind):
        raise ValueError('Выберите категорию')
    if not description.strip():
        raise ValueError('Заполните описание')

    record = {
        'kind': kind,
        'category': category,
        'description': description.strip(),
        'amount': round(amount, 2),
        'date': datetime.now().strftime(DATE_FORMAT),
    }
    return make_key(), record


def calc_totals(transactions):
    """Возвращает (доходы, расходы, баланс). Баланс = доходы - расходы."""
    income = sum(t['amount'] for t in transactions if t['kind'] == KIND_INCOME)
    expenses = sum(t['amount'] for t in transactions if t['kind'] == KIND_EXPENSE)
    return round(income, 2), round(expenses, 2), round(income - expenses, 2)


def sum_by_category(transactions, kind):
    """Суммы по категориям для одного типа операций: {'Офис': 1500.0, ...}"""
    result = {}
    for t in transactions:
        if t['kind'] == kind:
            result[t['category']] = round(result.get(t['category'], 0) + t['amount'], 2)
    return result


def sorted_newest_first(records):
    """Из словаря {ключ: запись} делает список, новые операции сверху."""
    return sorted(records.values(), key=lambda t: t['date'], reverse=True)
