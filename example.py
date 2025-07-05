#!/usr/bin/env python3
"""
Пример использования AI Summariser
"""

import asyncio
import logging
from ai_summariser import TelegramSummariser

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

async def main():
    """Основная функция примера"""
    
    # Путь к базе данных (замените на свой)
    db_path = "/Users/apple/Desktop/Tg_Parser/tg_parser.db"
    
    # Инициализация сервиса
    async with TelegramSummariser(db_path) as summariser:
        
        print("🤖 AI Summariser - Пример использования")
        print("=" * 50)
        
        # Получаем список папок
        print("\n📁 Доступные папки:")
        folders = await summariser.get_folders()
        for folder in folders:
            print(f"  - {folder.id}: {folder.name}")
        
        if not folders:
            print("  Папки не найдены")
            return
        
        # Выбираем первую папку для примера
        folder_id = folders[0].id
        folder_name = folders[0].name
        
        print(f"\n📊 Анализируем папку: {folder_name} (ID: {folder_id})")
        
        # Создаем сводку по папке
        print("\n🔄 Создаем сводку...")
        summary = await summariser.summarise_folder(
            folder_id=folder_id,
            limit=30,  # Максимум 30 постов
            days_back=7,  # За последние 7 дней
            include_ai_summary=True
        )
        
        if summary:
            print(f"\n✅ Сводка создана!")
            print(f"📈 Всего постов: {summary.total_posts}")
            print(f"📅 Период: {summary.date_range}")
            
            if summary.main_topics:
                print(f"🎯 Основные темы:")
                for i, topic in enumerate(summary.main_topics, 1):
                    print(f"  {i}. {topic}")
            
            print(f"\n📝 Общая сводка:")
            print(summary.overall_summary)
            
            if summary.posts:
                print(f"\n📰 Последние посты:")
                for i, post in enumerate(summary.posts[:5], 1):
                    print(f"  {i}. [{post.date.strftime('%d.%m %H:%M')}] {post.channel_title}")
                    print(f"     {post.summary[:100]}...")
                    if post.link:
                        print(f"     🔗 {post.link}")
                    print()
        else:
            print("❌ Ошибка при создании сводки")
        
        # Пример вопроса к ИИ
        print("\n🤔 Задаем вопрос ИИ...")
        question = "Какие основные новости обсуждались в последних постах?"
        
        ai_response = await summariser.ask_about_posts(
            folder_id=folder_id,
            question=question,
            limit=20,
            days_back=7
        )
        
        if ai_response:
            print(f"\n❓ Вопрос: {ai_response.question}")
            print(f"🤖 Ответ: {ai_response.answer}")
            print(f"📊 Уверенность: {ai_response.confidence:.2f}")
            
            if ai_response.related_posts:
                print(f"🔗 Связанные посты: {len(ai_response.related_posts)}")
        else:
            print("❌ Ошибка при получении ответа от ИИ")
        
        # Пример поиска
        print("\n🔍 Пример поиска...")
        search_term = "новости"
        
        search_summary = await summariser.search_and_summarise(
            folder_id=folder_id,
            search_term=search_term,
            limit=20
        )
        
        if search_summary:
            print(f"\n✅ Поиск завершен!")
            print(f"🔍 Поисковый запрос: '{search_term}'")
            print(f"📈 Найдено постов: {search_summary.total_posts}")
            print(f"📝 Сводка по поиску:")
            print(search_summary.overall_summary)
        else:
            print("❌ Ошибка при поиске")

if __name__ == "__main__":
    asyncio.run(main()) 