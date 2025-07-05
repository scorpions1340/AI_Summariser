# 🚀 Быстрый старт AI Summariser

## Минимальная настройка

### 1. Установка зависимостей
```bash
pip install -r requirements.txt
```

### 2. Проверка базы данных
Убедитесь, что файл `tg_parser.db` существует и содержит данные.

### 3. Быстрый тест
```bash
python test_basic.py
```

## Простое использование

### Базовый пример (без ИИ)
```python
import asyncio
from ai_summariser import TelegramSummariser

async def main():
    async with TelegramSummariser("/path/to/tg_parser.db") as summariser:
        # Получить папки
        folders = await summariser.get_folders()
        
        # Создать сводку без ИИ
        summary = await summariser.summarise_folder(
            folder_id=folders[0].id,
            limit=20,
            include_ai_summary=False
        )
        
        print(f"Постов: {summary.total_posts}")
        print(f"Сводка: {summary.overall_summary}")

asyncio.run(main())
```

### С ИИ (требует FreeGPT)
```python
# Сначала запустите FreeGPT сервер
# git clone https://github.com/Mylinde/freegpt.git
# cd freegpt && python -B -m gunicorn --config gunicorn_config.py run:app

async def main():
    async with TelegramSummariser("/path/to/tg_parser.db") as summariser:
        # Сводка с ИИ
        summary = await summariser.summarise_folder(
            folder_id=1,
            include_ai_summary=True
        )
        
        # Вопрос к ИИ
        response = await summariser.ask_about_posts(
            folder_id=1,
            question="Какие новости?"
        )
        
        print(response.answer)
```

## CLI команды

```bash
# Список папок
python -m ai_summariser.cli list --db /path/to/tg_parser.db

# Быстрая сводка
python -m ai_summariser.cli summarise --db /path/to/tg_parser.db --folder 1 --limit 10

# Поиск
python -m ai_summariser.cli search --db /path/to/tg_parser.db --folder 1 --term "новости"
```

## Структура базы данных

Убедитесь, что в `tg_parser.db` есть таблицы:
- `folders` - папки
- `channels` - каналы
- `posts` - посты

## Устранение проблем

### Ошибка "База данных не найдена"
- Проверьте путь к файлу
- Убедитесь, что файл существует

### Ошибка "ИИ-сервис недоступен"
- Запустите FreeGPT сервер
- Проверьте URL в настройках

### Ошибки импорта
- Установите зависимости: `pip install -r requirements.txt`
- Проверьте Python версию (3.8+)

## Что дальше?

1. Изучите `example.py` для более сложных примеров
2. Прочитайте `README.md` для полной документации
3. Посмотрите `INSTALL.md` для детальной настройки
4. Запустите тесты: `pytest tests/` 