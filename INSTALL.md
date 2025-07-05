# Инструкции по установке и запуску

## Предварительные требования

1. **Python 3.8+**
2. **FreeGPT сервер** - должен быть запущен локально или доступен по сети
3. **База данных tg_parser.db** - с таблицами posts, channels, folders

## Установка

### 1. Клонирование и установка зависимостей

```bash
# Клонируйте репозиторий
git clone <your-repo-url>
cd AI_Summariser

# Создайте виртуальное окружение
python -m venv venv
source venv/bin/activate  # На Windows: venv\Scripts\activate

# Установите зависимости
pip install -r requirements.txt
```

### 2. Запуск FreeGPT сервера

Следуйте инструкциям из [FreeGPT репозитория](https://github.com/Mylinde/FreeGPT):

```bash
# Клонируйте FreeGPT
git clone https://github.com/Mylinde/freegpt.git
cd freegpt

# Установите зависимости
pip install -r requirements.txt

# Запустите сервер
python -B -m gunicorn --config gunicorn_config.py run:app
```

Сервер будет доступен по адресу: `http://127.0.0.1:1338`

## Использование

### 1. Простой пример

```python
import asyncio
from ai_summariser import TelegramSummariser

async def main():
    # Инициализация с путем к базе данных
    async with TelegramSummariser("/path/to/tg_parser.db") as summariser:
        
        # Получить список папок
        folders = await summariser.get_folders()
        print(f"Найдено папок: {len(folders)}")
        
        # Создать сводку по первой папке
        if folders:
            summary = await summariser.summarise_folder(
                folder_id=folders[0].id,
                limit=30,
                days_back=7
            )
            print(f"Сводка: {summary.overall_summary}")

asyncio.run(main())
```

### 2. CLI интерфейс

```bash
# Показать список папок
python -m ai_summariser.cli list --db /path/to/tg_parser.db

# Создать сводку
python -m ai_summariser.cli summarise --db /path/to/tg_parser.db --folder 1 --limit 50

# Задать вопрос ИИ
python -m ai_summariser.cli ask --db /path/to/tg_parser.db --folder 1 --question "Какие новости?"

# Поиск постов
python -m ai_summariser.cli search --db /path/to/tg_parser.db --folder 1 --term "новости"
```

### 3. Запуск примера

```bash
python example.py
```

## Конфигурация

### Настройка FreeGPT

В файле `ai_summariser/core/ai_client.py` можно изменить:

```python
# URL FreeGPT сервера
base_url: str = "http://127.0.0.1:1338"

# Таймаут запросов
timeout: int = 30

# Количество повторных попыток
max_retries: int = 3
```

### Настройка базы данных

Убедитесь, что база данных содержит правильную структуру:

```sql
-- Таблица папок
CREATE TABLE folders (
    id INTEGER PRIMARY KEY,
    user_id BIGINT,
    name VARCHAR(128) NOT NULL,
    created_at DATETIME
);

-- Таблица каналов
CREATE TABLE channels (
    id INTEGER PRIMARY KEY,
    folder_id INTEGER,
    tg_id BIGINT NOT NULL,
    username VARCHAR(128),
    title VARCHAR(256),
    created_at DATETIME,
    FOREIGN KEY(folder_id) REFERENCES folders (id)
);

-- Таблица постов
CREATE TABLE posts (
    id INTEGER PRIMARY KEY,
    channel_id INTEGER,
    tg_post_id BIGINT NOT NULL,
    date DATETIME NOT NULL,
    text TEXT,
    link VARCHAR(512),
    created_at DATETIME,
    FOREIGN KEY(channel_id) REFERENCES channels (id)
);
```

## Тестирование

```bash
# Запуск тестов
pytest tests/

# Запуск с подробным выводом
pytest -v tests/

# Запуск конкретного теста
pytest tests/test_summariser.py::test_summariser_basic
```

## Устранение неполадок

### 1. FreeGPT недоступен

```
Ошибка: FreeGPT health check failed
```

**Решение:**
- Убедитесь, что FreeGPT сервер запущен
- Проверьте URL в конфигурации
- Проверьте логи FreeGPT сервера

### 2. База данных не найдена

```
Ошибка: База данных не найдена
```

**Решение:**
- Проверьте путь к файлу базы данных
- Убедитесь, что файл существует и доступен для чтения

### 3. Ошибки импорта

```
Ошибка: ModuleNotFoundError
```

**Решение:**
- Убедитесь, что все зависимости установлены
- Проверьте виртуальное окружение
- Переустановите зависимости: `pip install -r requirements.txt`

### 4. Проблемы с кодировкой

```
Ошибка: UnicodeDecodeError
```

**Решение:**
- Убедитесь, что база данных содержит корректные UTF-8 данные
- Проверьте настройки кодировки в Python

## Производительность

### Рекомендации:

1. **Ограничивайте количество постов** для анализа (limit=50-100)
2. **Используйте фильтр по датам** (days_back=7-30)
3. **Кэшируйте результаты** для повторных запросов
4. **Мониторьте использование памяти** при работе с большими базами

### Мониторинг:

```python
import logging
logging.basicConfig(level=logging.INFO)

# В логах будет видна информация о запросах к ИИ и базе данных
```

## Безопасность

1. **Не передавайте базу данных** третьим лицам
2. **Ограничьте доступ** к FreeGPT серверу
3. **Используйте HTTPS** для внешних подключений
4. **Логируйте запросы** для аудита

## Поддержка

При возникновении проблем:

1. Проверьте логи
2. Убедитесь в корректности конфигурации
3. Запустите тесты
4. Создайте issue с подробным описанием проблемы 