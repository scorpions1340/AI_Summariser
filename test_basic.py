#!/usr/bin/env python3
"""
Простой тест для проверки базовой функциональности AI Summariser
"""

import asyncio
import sys
import os
from pathlib import Path

# Добавляем текущую директорию в путь для импорта
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from ai_summariser import TelegramSummariser


async def test_basic_functionality():
    """Тест базовой функциональности"""
    
    # Путь к базе данных (замените на свой)
    db_path = "/Users/apple/Desktop/Tg_Parser/tg_parser.db"
    
    # Проверяем существование файла
    if not Path(db_path).exists():
        print(f"❌ База данных не найдена: {db_path}")
        print("Пожалуйста, укажите правильный путь к файлу tg_parser.db")
        return False
    
    try:
        print("🔍 Тестирование AI Summariser...")
        
        # Инициализация сервиса
        async with TelegramSummariser(db_path) as summariser:
            
            # Тест 1: Получение списка папок
            print("\n📁 Тест 1: Получение списка папок")
            folders = await summariser.get_folders()
            print(f"✅ Найдено папок: {len(folders)}")
            
            if folders:
                for folder in folders[:3]:  # Показываем первые 3 папки
                    print(f"   - {folder.id}: {folder.name}")
            
            # Тест 2: Получение информации о папке
            if folders:
                print(f"\n📊 Тест 2: Информация о папке {folders[0].id}")
                folder_info = await summariser.get_folder_info(folders[0].id)
                if folder_info:
                    print(f"✅ Папка: {folder_info.name}")
                else:
                    print("❌ Не удалось получить информацию о папке")
            
            # Тест 3: Создание сводки (без ИИ для быстрого теста)
            if folders:
                print(f"\n📝 Тест 3: Создание сводки для папки {folders[0].id}")
                summary = await summariser.summarise_folder(
                    folder_id=folders[0].id,
                    limit=10,  # Ограничиваем для быстрого теста
                    days_back=30,
                    include_ai_summary=False  # Отключаем ИИ для быстрого теста
                )
                
                if summary:
                    print(f"✅ Сводка создана!")
                    print(f"   📈 Всего постов: {summary.total_posts}")
                    print(f"   📅 Период: {summary.date_range}")
                    print(f"   📝 Краткое описание: {summary.overall_summary[:100]}...")
                else:
                    print("❌ Не удалось создать сводку")
            
            # Тест 4: Поиск постов
            if folders:
                print(f"\n🔍 Тест 4: Поиск постов в папке {folders[0].id}")
                search_summary = await summariser.search_and_summarise(
                    folder_id=folders[0].id,
                    search_term="новости",
                    limit=5
                )
                
                if search_summary:
                    print(f"✅ Поиск завершен!")
                    print(f"   🔍 Найдено постов: {search_summary.total_posts}")
                else:
                    print("❌ Не удалось выполнить поиск")
        
        print("\n🎉 Все базовые тесты пройдены успешно!")
        return True
        
    except Exception as e:
        print(f"\n❌ Ошибка при тестировании: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_ai_functionality():
    """Тест ИИ функциональности (требует запущенный FreeGPT сервер)"""
    
    db_path = "/Users/apple/Desktop/Tg_Parser/tg_parser.db"
    
    if not Path(db_path).exists():
        print("❌ База данных не найдена для ИИ теста")
        return False
    
    try:
        print("\n🤖 Тестирование ИИ функциональности...")
        
        async with TelegramSummariser(db_path) as summariser:
            
            folders = await summariser.get_folders()
            if not folders:
                print("❌ Нет папок для тестирования ИИ")
                return False
            
            # Тест ИИ-сводки
            print(f"\n📝 Тест ИИ-сводки для папки {folders[0].id}")
            summary = await summariser.summarise_folder(
                folder_id=folders[0].id,
                limit=5,
                days_back=7,
                include_ai_summary=True
            )
            
            if summary and "ИИ-сервис недоступен" not in summary.overall_summary:
                print("✅ ИИ-сводка создана успешно!")
                print(f"   🎯 Темы: {', '.join(summary.main_topics[:3])}")
            else:
                print("⚠️ ИИ-сервис недоступен или произошла ошибка")
            
            # Тест вопроса к ИИ
            print(f"\n❓ Тест вопроса к ИИ")
            response = await summariser.ask_about_posts(
                folder_id=folders[0].id,
                question="Какие основные темы обсуждались?",
                limit=5,
                days_back=7
            )
            
            if response and "недоступен" not in response.answer.lower():
                print("✅ Ответ от ИИ получен!")
                print(f"   🤖 Ответ: {response.answer[:100]}...")
            else:
                print("⚠️ ИИ-сервис недоступен для вопросов")
        
        return True
        
    except Exception as e:
        print(f"❌ Ошибка при тестировании ИИ: {e}")
        return False


async def main():
    """Основная функция тестирования"""
    
    print("🧪 Тестирование AI Summariser")
    print("=" * 50)
    
    # Базовые тесты
    basic_success = await test_basic_functionality()
    
    if basic_success:
        # ИИ тесты (опционально)
        print("\n" + "=" * 50)
        print("💡 Для полного тестирования ИИ функциональности убедитесь, что:")
        print("   1. FreeGPT сервер запущен на http://127.0.0.1:1338")
        print("   2. В базе данных есть посты для анализа")
        
        user_input = input("\nХотите протестировать ИИ функциональность? (y/n): ")
        if user_input.lower() in ['y', 'yes', 'да']:
            await test_ai_functionality()
    
    print("\n🏁 Тестирование завершено!")


if __name__ == "__main__":
    asyncio.run(main()) 