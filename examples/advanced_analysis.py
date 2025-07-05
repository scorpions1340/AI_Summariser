#!/usr/bin/env python3
"""
Пример продвинутого анализа с AI Summariser
"""

import asyncio
import json
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional

from ai_summariser import TelegramSummariser

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class AdvancedAnalyzer:
    """Класс для продвинутого анализа постов"""
    
    def __init__(self, db_path: str):
        self.db_path = db_path
        self.summariser: Optional[TelegramSummariser] = None
    
    async def __aenter__(self):
        self.summariser = await TelegramSummariser(self.db_path).__aenter__()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.summariser:
            await self.summariser.__aexit__(exc_type, exc_val, exc_tb)
        self.summariser = None
    
    async def analyze_all_folders(self) -> Dict:
        """Анализ всех папок"""
        assert self.summariser is not None
        folders = await self.summariser.get_folders()
        analysis = {
            "total_folders": len(folders),
            "folders": [],
            "summary": {
                "total_posts": 0,
                "date_range": "",
                "main_topics": [],
                "sentiment": "neutral"
            }
        }
        
        all_posts = 0
        all_topics = []
        dates = []
        
        for folder in folders:
            folder_analysis = await self.analyze_folder(folder.id)
            analysis["folders"].append(folder_analysis)
            
            all_posts += folder_analysis["total_posts"]
            all_topics.extend(folder_analysis["main_topics"])
            if folder_analysis["date_range"]:
                dates.append(folder_analysis["date_range"])
        
        # Общая статистика
        analysis["summary"]["total_posts"] = all_posts
        analysis["summary"]["main_topics"] = list(set(all_topics))[:10]  # Уникальные темы
        
        if dates:
            analysis["summary"]["date_range"] = f"{min(dates)} - {max(dates)}"
        
        return analysis
    
    async def analyze_folder(self, folder_id: int) -> Dict:
        """Анализ конкретной папки"""
        assert self.summariser is not None
        folder_info = await self.summariser.get_folder_info(folder_id)
        if not folder_info:
            return {"error": f"Папка {folder_id} не найдена"}
        
        # Получаем сводку
        summary = await self.summariser.summarise_folder(
            folder_id=folder_id,
            limit=50,
            days_back=30
        )
        
        if not summary:
            return {
                "folder_id": folder_id,
                "folder_name": folder_info.name,
                "error": "Не удалось создать сводку"
            }
        
        # Анализируем темы
        topic_analysis = await self.analyze_topics(summary.main_topics)
        
        # Анализируем активность
        activity_analysis = await self.analyze_activity(summary)
        
        return {
            "folder_id": folder_id,
            "folder_name": folder_info.name,
            "total_posts": summary.total_posts,
            "date_range": summary.date_range,
            "main_topics": summary.main_topics,
            "overall_summary": summary.overall_summary,
            "topic_analysis": topic_analysis,
            "activity_analysis": activity_analysis,
            "recent_posts": [
                {
                    "date": post.date.isoformat(),
                    "channel": post.channel_title,
                    "summary": post.summary,
                    "link": post.link
                }
                for post in summary.posts[:10]
            ]
        }
    
    async def analyze_topics(self, topics: List[str]) -> Dict:
        """Анализ тем"""
        if not topics:
            return {"error": "Нет тем для анализа"}
        
        # Задаем вопросы ИИ для анализа тем
        questions = [
            "Какие из этих тем наиболее актуальны?",
            "Какие темы вызывают наибольший интерес?",
            "Есть ли негативные темы в списке?"
        ]
        
        topic_analysis = {
            "total_topics": len(topics),
            "topic_categories": [],
            "ai_insights": {}
        }
        
        # Простая категоризация тем
        categories = {
            "технологии": ["искусственный интеллект", "технологии", "программирование", "машинное обучение"],
            "новости": ["новости", "события", "анонсы"],
            "проблемы": ["проблемы", "ошибки", "сбои", "задержки"],
            "развлечения": ["игры", "фильмы", "музыка", "развлечения"]
        }
        
        for topic in topics:
            for category, keywords in categories.items():
                if any(keyword in topic.lower() for keyword in keywords):
                    topic_analysis["topic_categories"].append({
                        "topic": topic,
                        "category": category
                    })
                    break
            else:
                topic_analysis["topic_categories"].append({
                    "topic": topic,
                    "category": "другое"
                })
        
        return topic_analysis
    
    async def analyze_activity(self, summary) -> Dict:
        """Анализ активности"""
        return {
            "posts_per_day": summary.total_posts / 7 if summary.total_posts > 0 else 0,
            "activity_level": "высокая" if summary.total_posts > 20 else "средняя" if summary.total_posts > 10 else "низкая",
            "channels_count": len(set(post.channel_title for post in summary.posts)),
            "date_span": summary.date_range
        }
    
    async def generate_report(self, analysis: Dict, output_file: Optional[str] = None) -> str:
        """Генерация отчета"""
        report = f"""
# Отчет AI Summariser
## Дата: {datetime.now().strftime('%d.%m.%Y %H:%M')}

## Общая статистика
- 📁 Всего папок: {analysis['total_folders']}
- 📊 Всего постов: {analysis['summary']['total_posts']}
- 📅 Период: {analysis['summary']['date_range']}

## Основные темы
{chr(10).join(f"- {topic}" for topic in analysis['summary']['main_topics'])}

## Анализ по папкам
"""
        
        for folder in analysis["folders"]:
            if "error" in folder:
                folder_name = folder.get('folder_name', f"Папка {folder.get('folder_id', 'N/A')}")
                report += f"\n### {folder_name}\n"
                report += f"❌ {folder['error']}\n"
                continue
            
            report += f"""
### {folder['folder_name']}
- 📈 Постов: {folder['total_posts']}
- 📅 Период: {folder['date_range']}
- 🎯 Основные темы: {', '.join(folder['main_topics'][:5])}
- 📊 Уровень активности: {folder['activity_analysis']['activity_level']}

**Сводка:**
{folder['overall_summary']}

**Последние посты:**
"""
            
            for i, post in enumerate(folder['recent_posts'][:3], 1):
                report += f"{i}. [{post['date'][:10]}] {post['channel']}\n"
                report += f"   {post['summary'][:100]}...\n"
                if post['link']:
                    report += f"   🔗 {post['link']}\n"
                report += "\n"
        
        if output_file is not None:
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(report)
            logger.info(f"Отчет сохранен в {output_file}")
        
        return report


async def main():
    """Основная функция"""
    print("🚀 AI Summariser - Продвинутый анализ")
    print("=" * 50)
    
    db_path = "/path/to/your/tg_parser.db"
    
    if not Path(db_path).exists():
        logger.error(f"База данных не найдена: {db_path}")
        return
    
    async with AdvancedAnalyzer(db_path) as analyzer:
        try:
            # Анализируем все папки
            print("📊 Анализируем все папки...")
            analysis = await analyzer.analyze_all_folders()
            
            # Генерируем отчет
            print("📝 Генерируем отчет...")
            report = await analyzer.generate_report(
                analysis, 
                output_file="analysis_report.md"
            )
            
            # Выводим краткую статистику
            print(f"\n📈 Краткая статистика:")
            print(f"   Папок: {analysis['total_folders']}")
            print(f"   Постов: {analysis['summary']['total_posts']}")
            print(f"   Тем: {len(analysis['summary']['main_topics'])}")
            
            # Сохраняем JSON для дальнейшего анализа
            with open("analysis_data.json", "w", encoding="utf-8") as f:
                json.dump(analysis, f, ensure_ascii=False, indent=2, default=str)
            
            print(f"\n✅ Анализ завершен!")
            print(f"   📄 Отчет: analysis_report.md")
            print(f"   📊 Данные: analysis_data.json")
            
        except Exception as e:
            logger.error(f"Ошибка при анализе: {e}")


if __name__ == "__main__":
    asyncio.run(main()) 