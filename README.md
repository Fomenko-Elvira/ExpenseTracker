# Business Expense Tracker (Kivy)

Трекер доходов и расходов для малого бизнеса. Доработка учебного примера ExpenseTracker из лекции 6  
(«Разработка мобильного приложения»).

## Что сделано (домашнее задание)

1. **Графики** — Matplotlib внутри Kivy через Kivy Garden (`charts/`): круговая диаграмма расходов по категориям и столбики «доходы / расходы / баланс».
2. **Синхронизация с облаком** — Firebase Realtime Database через REST API (`cloud/`) с авторизацией через Firebase Authentication (email и пароль).
3. **Категории доходов и баланс** — операции бывают двух типов (доход/расход), у каждого свои категории, на экране автоматически считается баланс (`models/`).

Из лекции сохранено: ScreenManager + Screen, KV Language, Properties, JsonStore, RecycleView, аналитика по категориям, экспорт в CSV.

## Установка

```bash
pip install -r requirements.txt
```

Если `kivy-garden.matplotlib` не ставится, попробуйте `pip install --pre kivy-garden.matplotlib`.

## Запуск

```bash
python main.py
```

(запускать как обычный файл, не в Jupyter/Colab).

## Облако

Для синхронизации используется Firebase Realtime Database с авторизацией через Firebase Authentication.

Адрес базы и API-ключ указываются в `cloud/config.py` (`DATABASE_URL` и `API_KEY`).

Email и пароль пользователя Firebase передаются через переменные окружения `FIREBASE_EMAIL` и `FIREBASE_PASSWORD`. В PyCharm их можно задать в настройках запуска приложения (Run/Debug Configurations).

При нажатии кнопки «Синхронизация» приложение:

1. Авторизуется в Firebase Authentication.
2. Загружает операции из облачной базы данных.
3. Объединяет локальные и облачные операции.
4. Отправляет обновлённые данные в Firebase Realtime Database.

Данные каждого пользователя хранятся отдельно по пути `users/<uid>/transactions`. Доступ к ним ограничен правилами безопасности Firebase.

**Синхронизация успешно проверена:** две тестовые операции сохранены в Firebase Realtime Database.

Для демонстрации без Firebase в проекте также предусмотрен тестовый сервер (`cloud/fake_server.py`). Его использование требует отдельной настройки подключения.

## Тесты

```bash
python -m unittest discover -v
```

## Структура

```text
main.py            приложение: экраны, JsonStore, экспорт
tracker.kv         интерфейс (KV Language)
models/            операции, категории, баланс
charts/            графики Matplotlib (Kivy Garden)
cloud/             авторизация и синхронизация с Firebase (REST)
tests/             автотесты
requirements.txt   зависимости
README.md          описание проекта
```

## Результат

Разработано приложение для учёта доходов и расходов малого бизнеса с категориями операций, расчётом баланса, аналитикой, графиками и экспортом в CSV.

Реализована синхронизация с Firebase Realtime Database через REST API с авторизацией пользователя. Успешно проверено сохранение операций в облачной базе данных.