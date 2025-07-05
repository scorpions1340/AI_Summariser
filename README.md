# AI Summariser - Асинхронный сервис суммаризации Telegram постов

Асинхронная библиотека для суммаризации постов из Telegram каналов с использованием FreeGPT API.

## Возможности

- 📊 Суммаризация постов из определенной папки в базе данных
- 🤖 Интеграция с FreeGPT для генерации кратких описаний
- 💬 Интерактивное общение с ИИ по поводу постов
- 🔗 Ссылки на оригинальные посты с временными метками
- ⚡ Асинхронная архитектура для высокой производительности
- 🔒 Безопасный доступ к базе данных
- 📦 Формат подключаемой библиотеки

## Установка

```bash
pip install -r requirements.txt
```

## Использование

```python
from ai_summariser import TelegramSummariser

# Инициализация сервиса
summariser = TelegramSummariser(db_path="path/to/tg_parser.db")

# Суммаризация постов из папки
summary = await summariser.summarise_folder(folder_id=1)

# Общение с ИИ о постах
response = await summariser.ask_about_posts(
    folder_id=1, 
    question="Какие основные темы обсуждались в последних постах?"
)
```

## Структура проекта

```
ai_summariser/
├── __init__.py
├── core/
│   ├── __init__.py
│   ├── database.py
│   ├── summariser.py
│   └── ai_client.py
├── models/
│   ├── __init__.py
│   └── schemas.py
├── utils/
│   ├── __init__.py
│   └── helpers.py
└── tests/
    └── test_summariser.py
```

## Лицензия

MIT License 