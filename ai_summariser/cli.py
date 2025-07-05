#!/usr/bin/env python3
"""
CLI интерфейс для AI Summariser
"""

import asyncio
import argparse
import json
import logging
from pathlib import Path
from typing import Optional

from . import TelegramSummariser


def setup_logging(verbose: bool = False):
    """Настройка логирования"""
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )


async def list_folders(db_path: str):
    """Показать список папок"""
    async with TelegramSummariser(db_path) as summariser:
        folders = await summariser.get_folders()
        
        if not folders:
            print("Папки не найдены")
            return
        
        print("📁 Доступные папки:")
        for folder in folders:
            print(f"  {folder.id}: {folder.name}")


async def summarise_folder(
    db_path: str,
    folder_id: int,
    limit: Optional[int] = None,
    days_back: Optional[int] = None,
    output_file: Optional[str] = None,
    format_output: str = "text"
):
    """Создать сводку по папке"""
    async with TelegramSummariser(db_path) as summariser:
        summary = await summariser.summarise_folder(
            folder_id=folder_id,
            limit=limit if limit is not None else 20,
            days_back=days_back if days_back is not None else 7
        )
        
        if not summary:
            print("❌ Ошибка при создании сводки")
            return
        
        if format_output == "json":
            output = json.dumps(summary.model_dump(), indent=2, ensure_ascii=False)
        else:
            output = format_summary_text(summary)
        
        if output_file:
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(output)
            print(f"✅ Сводка сохранена в {output_file}")
        else:
            print(output)


async def ask_question(
    db_path: str,
    folder_id: int,
    question: str,
    limit: Optional[int] = None,
    days_back: Optional[int] = None,
    output_file: Optional[str] = None
):
    """Задать вопрос ИИ"""
    async with TelegramSummariser(db_path) as summariser:
        response = await summariser.ask_about_posts(
            folder_id=folder_id,
            question=question,
            limit=limit if limit is not None else 20,
            days_back=days_back if days_back is not None else 7
        )
        
        if not response:
            print("❌ Ошибка при получении ответа")
            return
        
        output = f"""
❓ Вопрос: {response.question}

🤖 Ответ: {response.answer}

📊 Уверенность: {response.confidence:.2f}
🔗 Связанные посты: {len(response.related_posts)}
        """.strip()
        
        if output_file:
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(output)
            print(f"✅ Ответ сохранен в {output_file}")
        else:
            print(output)


async def search_posts(
    db_path: str,
    folder_id: int,
    search_term: str,
    limit: Optional[int] = None,
    output_file: Optional[str] = None
):
    """Поиск постов"""
    async with TelegramSummariser(db_path) as summariser:
        summary = await summariser.search_and_summarise(
            folder_id=folder_id,
            search_term=search_term,
            limit=limit if limit is not None else 20
        )
        
        if not summary:
            print("❌ Ошибка при поиске")
            return
        
        output = f"""
🔍 Поисковый запрос: "{search_term}"
📈 Найдено постов: {summary.total_posts}
📅 Период: {summary.date_range}

📝 Сводка:
{summary.overall_summary}

🎯 Основные темы:
{chr(10).join(f"  • {topic}" for topic in summary.main_topics)}
        """.strip()
        
        if output_file:
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(output)
            print(f"✅ Результаты поиска сохранены в {output_file}")
        else:
            print(output)


def format_summary_text(summary) -> str:
    """Форматировать сводку в текстовом виде"""
    output = f"""
📊 Сводка по папке: {summary.folder_name}
📈 Всего постов: {summary.total_posts}
📅 Период: {summary.date_range}

🎯 Основные темы:
{chr(10).join(f"  • {topic}" for topic in summary.main_topics)}

📝 Общая сводка:
{summary.overall_summary}

📰 Последние посты:
"""
    
    for i, post in enumerate(summary.posts[:10], 1):
        output += f"""
  {i}. [{post.date.strftime('%d.%m.%Y %H:%M')}] {post.channel_title}
     {post.summary}
"""
        if post.link:
            output += f"     🔗 {post.link}\n"
    
    return output.strip()


def main():
    """Основная функция CLI"""
    parser = argparse.ArgumentParser(
        description="AI Summariser - Асинхронный сервис суммаризации Telegram постов",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Примеры использования:
  %(prog)s list --db /path/to/tg_parser.db
  %(prog)s summarise --db /path/to/tg_parser.db --folder 1 --limit 50
  %(prog)s ask --db /path/to/tg_parser.db --folder 1 --question "Какие новости?"
  %(prog)s search --db /path/to/tg_parser.db --folder 1 --term "новости"
        """
    )
    
    parser.add_argument(
        "--db", "--database",
        required=True,
        help="Путь к базе данных tg_parser.db"
    )
    
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Подробный вывод"
    )
    
    subparsers = parser.add_subparsers(dest="command", help="Доступные команды")
    
    # Команда list
    list_parser = subparsers.add_parser("list", help="Показать список папок")
    
    # Команда summarise
    summarise_parser = subparsers.add_parser("summarise", help="Создать сводку по папке")
    summarise_parser.add_argument("--folder", "-f", type=int, required=True, help="ID папки")
    summarise_parser.add_argument("--limit", "-l", type=int, help="Максимальное количество постов")
    summarise_parser.add_argument("--days-back", "-d", type=int, help="Количество дней назад")
    summarise_parser.add_argument("--output", "-o", help="Файл для сохранения результата")
    summarise_parser.add_argument("--format", choices=["text", "json"], default="text", help="Формат вывода")
    
    # Команда ask
    ask_parser = subparsers.add_parser("ask", help="Задать вопрос ИИ")
    ask_parser.add_argument("--folder", "-f", type=int, required=True, help="ID папки")
    ask_parser.add_argument("--question", "-q", required=True, help="Вопрос к ИИ")
    ask_parser.add_argument("--limit", "-l", type=int, help="Максимальное количество постов")
    ask_parser.add_argument("--days-back", "-d", type=int, help="Количество дней назад")
    ask_parser.add_argument("--output", "-o", help="Файл для сохранения результата")
    
    # Команда search
    search_parser = subparsers.add_parser("search", help="Поиск постов")
    search_parser.add_argument("--folder", "-f", type=int, required=True, help="ID папки")
    search_parser.add_argument("--term", "-t", required=True, help="Поисковый запрос")
    search_parser.add_argument("--limit", "-l", type=int, help="Максимальное количество результатов")
    search_parser.add_argument("--output", "-o", help="Файл для сохранения результата")
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    # Проверяем существование базы данных
    if not Path(args.db).exists():
        print(f"❌ База данных не найдена: {args.db}")
        return
    
    setup_logging(args.verbose)
    
    try:
        if args.command == "list":
            asyncio.run(list_folders(args.db))
        elif args.command == "summarise":
            asyncio.run(summarise_folder(
                args.db, args.folder, args.limit, args.days_back, args.output, args.format
            ))
        elif args.command == "ask":
            asyncio.run(ask_question(
                args.db, args.folder, args.question, args.limit, args.days_back, args.output
            ))
        elif args.command == "search":
            asyncio.run(search_posts(
                args.db, args.folder, args.term, args.limit, args.output
            ))
    except KeyboardInterrupt:
        print("\n⚠️ Операция прервана пользователем")
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        if args.verbose:
            raise


if __name__ == "__main__":
    main() 