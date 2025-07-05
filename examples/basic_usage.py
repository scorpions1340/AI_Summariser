#!/usr/bin/env python3
"""
Пример базового использования AI Summariser
"""

import asyncio
import logging
from pathlib import Path

from ai_summariser import TelegramSummariser

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def basic_summarization():
    """Базовый пример суммаризации"""
    
    # Путь к базе данных
    db_path = "/path/to/your/tg_parser.db"
    
    # Проверяем существование файла
    if not Path(db_path).exists():
        logger.error(f"База данных не найдена: {db_path}")
        return
    
    async with TelegramSummariser(db_path) as summariser:
        try:
            # Получаем список папок
            folders = await summariser.get_folders()
            logger.info(f"Найдено папок: {len(folders)}")
            
            if not folders:
                logger.warning("Папки не найдены в базе данных")
                return
            
            # Создаем сводку для первой папки
            folder_id = folders[0].id
            logger.info(f"Создаем сводку для папки: {folders[0].name} (ID: {folder_id})")
            
            summary = await summariser.summarise_folder(
                folder_id=folder_id,
                limit=20,  # Максимум 20 постов
                days_back=7  # За последние 7 дней
            )
            
            if summary:
                print(f"\n📊 Сводка по папке: {summary.folder_name}")
                print(f"📈 Всего постов: {summary.total_posts}")
                print(f"📅 Период: {summary.date_range}")
                
                print(f"\n🎯 Основные темы:")
                for topic in summary.main_topics:
                    print(f"  • {topic}")
                
                print(f"\n📝 Общая сводка:")
                print(summary.overall_summary)
                
                print(f"\n📰 Последние посты:")
                for i, post in enumerate(summary.posts[:5], 1):
                    print(f"  {i}. [{post.date.strftime('%d.%m.%Y %H:%M')}] {post.channel_title}")
                    print(f"     {post.summary}")
                    if post.link:
                        print(f"     🔗 {post.link}")
                    print()
            else:
                logger.error("Не удалось создать сводку")
                
        except Exception as e:
            logger.error(f"Ошибка при создании сводки: {e}")


async def ask_questions():
    """Пример задавания вопросов ИИ"""
    
    db_path = "/path/to/your/tg_parser.db"
    
    async with TelegramSummariser(db_path) as summariser:
        try:
            # Получаем первую папку
            folders = await summariser.get_folders()
            if not folders:
                logger.warning("Папки не найдены")
                return
            
            folder_id = folders[0].id
            
            # Задаем разные вопросы
            questions = [
                "Какие основные проблемы обсуждались в постах?",
                "Какие позитивные новости были?",
                "Какие технологические тренды упоминались?",
                "Что говорилось про искусственный интеллект?"
            ]
            
            for question in questions:
                print(f"\n❓ Вопрос: {question}")
                
                response = await summariser.ask_about_posts(
                    folder_id=folder_id,
                    question=question,
                    limit=20,
                    days_back=7
                )
                
                if response:
                    print(f"🤖 Ответ: {response.answer}")
                    print(f"📊 Уверенность: {response.confidence:.2f}")
                    print(f"🔗 Связанные посты: {len(response.related_posts)}")
                else:
                    print("❌ Не удалось получить ответ")
                
                print("-" * 50)
                
        except Exception as e:
            logger.error(f"Ошибка при задавании вопросов: {e}")


async def search_content():
    """Пример поиска по контенту"""
    
    db_path = "/path/to/your/tg_parser.db"
    
    async with TelegramSummariser(db_path) as summariser:
        try:
            folders = await summariser.get_folders()
            if not folders:
                logger.warning("Папки не найдены")
                return
            
            folder_id = folders[0].id
            
            # Поисковые запросы
            search_terms = ["технологии", "новости", "проблемы", "искусственный интеллект"]
            
            for term in search_terms:
                print(f"\n🔍 Поиск: '{term}'")
                
                result = await summariser.search_and_summarise(
                    folder_id=folder_id,
                    search_term=term,
                    limit=20
                )
                
                if result:
                    print(f"📈 Найдено постов: {result.total_posts}")
                    print(f"📅 Период: {result.date_range}")
                    print(f"📝 Сводка: {result.overall_summary}")
                    
                    print(f"🎯 Основные темы:")
                    for topic in result.main_topics:
                        print(f"  • {topic}")
                else:
                    print("❌ Поиск не дал результатов")
                
                print("-" * 50)
                
        except Exception as e:
            logger.error(f"Ошибка при поиске: {e}")


async def main():
    """Основная функция"""
    print("🚀 AI Summariser - Примеры использования")
    print("=" * 50)
    
    # Пример 1: Базовая суммаризация
    print("\n1️⃣ Базовая суммаризация")
    await basic_summarization()
    
    # Пример 2: Вопросы к ИИ
    print("\n2️⃣ Вопросы к ИИ")
    await ask_questions()
    
    # Пример 3: Поиск по контенту
    print("\n3️⃣ Поиск по контенту")
    await search_content()
    
    print("\n✅ Примеры завершены!")


if __name__ == "__main__":
    # Запускаем примеры
    asyncio.run(main()) 