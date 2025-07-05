"""
Вспомогательные функции для AI Summariser
"""

from datetime import datetime, timedelta
from typing import List, Optional


def format_date_range(start_date: datetime, end_date: datetime) -> str:
    """Форматировать диапазон дат"""
    if start_date.date() == end_date.date():
        return start_date.strftime("%d.%m.%Y")
    else:
        return f"{start_date.strftime('%d.%m.%Y')} - {end_date.strftime('%d.%m.%Y')}"


def truncate_text(text: str, max_length: int = 200, suffix: str = "...") -> str:
    """Обрезать текст до указанной длины"""
    if not text:
        return ""
    
    if len(text) <= max_length:
        return text
    
    return text[:max_length - len(suffix)] + suffix


def create_post_link(channel_username: Optional[str], post_id: int) -> Optional[str]:
    """Создать ссылку на пост в Telegram"""
    if not channel_username:
        return None
    
    return f"https://t.me/{channel_username}/{post_id}"


def extract_keywords(text: str, max_keywords: int = 10) -> List[str]:
    """Извлечь ключевые слова из текста"""
    if not text:
        return []
    
    # Простые стоп-слова
    stop_words = {
        'и', 'в', 'на', 'с', 'по', 'для', 'от', 'до', 'из', 'за', 'под', 'над', 
        'при', 'про', 'о', 'об', 'а', 'но', 'или', 'что', 'как', 'где', 'когда', 
        'почему', 'это', 'то', 'так', 'все', 'еще', 'уже', 'только', 'даже', 
        'тоже', 'также', 'быть', 'был', 'была', 'были', 'было', 'есть', 'нет',
        'не', 'ни', 'же', 'ли', 'бы', 'как', 'так', 'то', 'это', 'вот', 'тут',
        'там', 'здесь', 'там', 'где', 'куда', 'откуда', 'когда', 'зачем', 'почему'
    }
    
    # Разбиваем на слова и фильтруем
    words = text.lower().split()
    word_count = {}
    
    for word in words:
        # Очищаем слово от знаков препинания
        clean_word = ''.join(c for c in word if c.isalnum())
        
        if (len(clean_word) > 2 and 
            clean_word not in stop_words and 
            not clean_word.isdigit()):
            word_count[clean_word] = word_count.get(clean_word, 0) + 1
    
    # Сортируем по частоте и возвращаем топ ключевых слов
    sorted_words = sorted(word_count.items(), key=lambda x: x[1], reverse=True)
    return [word for word, count in sorted_words[:max_keywords]]


def calculate_reading_time(text: str, words_per_minute: int = 200) -> int:
    """Рассчитать время чтения текста в минутах"""
    if not text:
        return 0
    
    word_count = len(text.split())
    return max(1, word_count // words_per_minute)


def is_recent_post(post_date: datetime, days: int = 7) -> bool:
    """Проверить, является ли пост недавним"""
    cutoff_date = datetime.now() - timedelta(days=days)
    return post_date >= cutoff_date


def group_posts_by_date(posts: List, days_group: int = 1) -> dict:
    """Сгруппировать посты по датам"""
    groups = {}
    
    for post in posts:
        # Округляем дату до дня
        date_key = post.date.date()
        if date_key not in groups:
            groups[date_key] = []
        groups[date_key].append(post)
    
    return groups


def sanitize_text(text: str) -> str:
    """Очистить текст от лишних символов"""
    if not text:
        return ""
    
    # Убираем лишние пробелы и переносы строк
    text = ' '.join(text.split())
    
    # Ограничиваем длину
    if len(text) > 1000:
        text = text[:1000] + "..."
    
    return text 