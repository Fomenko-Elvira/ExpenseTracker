"""
БИЗНЕС-ПРИЛОЖЕНИЕ: Трекер доходов и расходов для малого бизнеса (Kivy).

Доработка ExpenseTracker из лекции. Домашнее задание:
  1. Графики Matplotlib через Kivy Garden   -> charts/
  2. Синхронизация с облаком (Firebase REST) -> cloud/
  3. Категории доходов и баланс              -> models/
"""

import csv
import os
import threading

from kivy.app import App
from kivy.clock import Clock
from kivy.lang import Builder
from kivy.properties import NumericProperty, StringProperty
from kivy.storage.jsonstore import JsonStore
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.popup import Popup
from kivy.uix.recycleview import RecycleView
from kivy.uix.recycleview.views import RecycleDataViewBehavior
from kivy.uix.screenmanager import Screen, ScreenManager

from charts.chart_widget import ChartBox  # noqa: F401  (нужен для tracker.kv)
from cloud import sync as cloud_sync
from models.transaction import (
    KIND_EXPENSE, KIND_INCOME, KIND_LABELS, LABEL_TO_KIND,
    calc_totals, categories_for, create_transaction, normalize,
    sorted_newest_first, sum_by_category,
)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_FILE = os.path.join(BASE_DIR, 'transactions.json')
EXPORT_FILE = os.path.join(BASE_DIR, 'transactions_export.csv')

# Загружаем KV-язык с описанием интерфейса
Builder.load_file(os.path.join(BASE_DIR, 'tracker.kv'))


# --- Виджеты списка ---

class TransactionRow(RecycleDataViewBehavior, BoxLayout):
    """Строка операции для RecycleView."""
    category = StringProperty('')
    description = StringProperty('')
    amount = NumericProperty(0)
    kind = StringProperty(KIND_EXPENSE)


class TransactionsRV(RecycleView):
    """Виджет для отображения списка операций."""


# --- Главный экран ---

class MainScreen(Screen):
    """Главный экран приложения."""
    total_income = NumericProperty(0)
    total_expenses = NumericProperty(0)
    balance = NumericProperty(0)
    status_text = StringProperty('')

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.store = JsonStore(DATA_FILE)   # локальное хранилище
        self.load_transactions()

    # ----- работа с данными -----

    def read_all(self):
        """Все операции из хранилища: {ключ: запись}."""
        return {key: normalize(self.store.get(key)) for key in self.store.keys()}

    def get_transactions(self):
        return list(self.read_all().values())

    def load_transactions(self):
        """Обновляет список на экране и итоги (доходы, расходы, баланс)."""
        items = sorted_newest_first(self.read_all())
        self.ids.rv.data = [
            {'kind': t['kind'], 'category': t['category'],
             'description': t['description'], 'amount': t['amount']}
            for t in items
        ]
        self.total_income, self.total_expenses, self.balance = calc_totals(items)

    def add_transaction(self, key, record):
        """Сохранение новой операции."""
        self.store.put(key, **record)
        self.load_transactions()
        self.status_text = ''

    # ----- окна -----

    def show_add_popup(self):
        AddTransactionPopup(main_screen=self).open()

    def show_message(self, title, message):
        """Утилита для показа сообщений и ошибок."""
        Popup(title=title, content=Label(text=message), size_hint=(0.7, 0.4)).open()

    def show_analytics(self):
        """Аналитика по категориям (доходы и расходы отдельно)."""
        transactions = self.get_transactions()
        content = BoxLayout(orientation='vertical', padding=10)
        for kind in (KIND_INCOME, KIND_EXPENSE):
            content.add_widget(Label(text=f'[b]{KIND_LABELS[kind]}ы[/b]', markup=True, font_size=18))
            totals = sum_by_category(transactions, kind)
            if not totals:
                content.add_widget(Label(text='нет данных', font_size=14))
            for category, total in totals.items():
                content.add_widget(Label(text=f'{category}: {total:.2f} руб.', font_size=16))
        Popup(title='Аналитика по категориям', content=content, size_hint=(0.8, 0.7)).open()

    def show_charts(self):
        """Переход на экран с графиками."""
        charts = self.manager.get_screen('charts')
        charts.update_chart(self.get_transactions())
        self.manager.current = 'charts'

    # ----- экспорт -----

    def export_data(self):
        """Экспорт данных в CSV."""
        try:
            # utf-8-sig, чтобы Excel правильно показал русские буквы
            with open(EXPORT_FILE, 'w', newline='', encoding='utf-8-sig') as f:
                writer = csv.writer(f)
                writer.writerow(['Тип', 'Категория', 'Описание', 'Сумма', 'Дата'])
                for t in sorted_newest_first(self.read_all()):
                    writer.writerow([KIND_LABELS[t['kind']], t['category'],
                                     t['description'], t['amount'], t['date']])
            self.show_message('Успех', 'Данные экспортированы в\ntransactions_export.csv')
        except Exception as e:
            self.show_message('Ошибка', str(e))

    # ----- облако -----

    def sync_with_cloud(self):
        """Запускает синхронизацию в отдельном потоке, чтобы окно не зависало."""
        if not cloud_sync.is_configured():
            self.status_text = 'Облако не настроено: укажите DATABASE_URL в cloud/config.py'
            return
        self.status_text = 'Синхронизация...'
        threading.Thread(target=self._sync_worker, args=(self.read_all(),), daemon=True).start()

    def _sync_worker(self, local):
        """Работает в фоновом потоке: только сеть, интерфейс не трогаем."""
        try:
            merged = cloud_sync.sync(local)
        except cloud_sync.CloudError as e:
            message = str(e)
            Clock.schedule_once(lambda dt, m=message: self._sync_failed(m))
            return
        Clock.schedule_once(lambda dt, data=merged: self._sync_done(data))

    def _sync_failed(self, message):
        self.status_text = message

    def _sync_done(self, merged):
        """Выполняется в потоке интерфейса: сохраняем то, чего не было локально."""
        for key, record in merged.items():
            if not self.store.exists(key):
                self.store.put(key, **normalize(record))
        self.load_transactions()
        self.status_text = f'Синхронизировано, операций: {len(merged)}'


# --- Окно добавления операции ---

class AddTransactionPopup(Popup):
    """Попап для добавления дохода или расхода."""

    def __init__(self, main_screen, **kwargs):
        super().__init__(**kwargs)
        self.main_screen = main_screen
        self.update_categories(self.ids.kind_spinner.text)

    def update_categories(self, kind_text):
        """При смене типа (Расход/Доход) показываем нужные категории."""
        spinner = self.ids.get('category_spinner')
        if spinner is None:      # окно ещё собирается
            return
        spinner.values = categories_for(LABEL_TO_KIND.get(kind_text, KIND_EXPENSE))
        spinner.text = 'Выберите категорию'

    def save_transaction(self):
        """Сохранение операции."""
        try:
            key, record = create_transaction(
                kind=LABEL_TO_KIND[self.ids.kind_spinner.text],
                category=self.ids.category_spinner.text,
                description=self.ids.description_input.text,
                amount=self.ids.amount_input.text,
            )
        except ValueError as e:
            self.main_screen.show_message('Ошибка', str(e))
            return
        self.main_screen.add_transaction(key, record)
        self.dismiss()


# --- Экран с графиками ---

class ChartsScreen(Screen):
    """Второй экран: графики Matplotlib."""

    def update_chart(self, transactions=None):
        if transactions is None:
            transactions = self.manager.get_screen('main').get_transactions()
        self.ids.chart.update_chart(transactions)

    def go_back(self):
        self.manager.current = 'main'


# --- Основное приложение ---

class ExpenseTrackerApp(App):
    """Основной класс приложения."""

    def build(self):
        self.title = 'Business Expense Tracker'
        sm = ScreenManager()
        sm.add_widget(MainScreen(name='main'))
        sm.add_widget(ChartsScreen(name='charts'))
        return sm

    def on_pause(self):
        """Обработка паузы на мобильных устройствах."""
        return True

    def on_resume(self):
        """Обработка возобновления работы."""
        pass


# --- Точка входа ---
if __name__ == '__main__':
    ExpenseTrackerApp().run()
