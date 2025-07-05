"""
Основной класс для суммаризации Telegram постов
"""

import asyncio
import logging
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta

from ai_summariser.core.database import DatabaseManager
from ai_summariser.core.ai_client import FreeGPTClient
from ai_summariser.models.schemas import Post, Summary, PostSummary, AIResponse, Folder

logger = logging.getLogger(__name__)


class TelegramSummariser:
    """Основной класс для суммаризации Telegram постов с использованием ИИ"""
    
    def __init__(
        self, 
        db_path: str,
        freegpt_url: str = "http://127.0.0.1:1337",
        timeout: int = 30
    ):
        self.db_manager = DatabaseManager(db_path)
        self.ai_client = FreeGPTClient(freegpt_url, timeout)
        self._cache: Dict[str, Any] = {}
        self._cache_ttl = 300  # 5 минут
    
    async def __aenter__(self):
        await self.db_manager.connect()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.db_manager.close()
    
    async def get_folders(self) -> List[Folder]:
        """Получить список всех папок"""
        return await self.db_manager.get_folders()
    
    async def get_folder_info(self, folder_id: int) -> Optional[Folder]:
        """Получить информацию о папке"""
        return await self.db_manager.get_folder(folder_id)
    
    async def summarise_folder(
        self, 
        folder_id: int,
        limit: Optional[int] = 50,
        days_back: Optional[int] = 7,
        include_ai_summary: bool = True
    ) -> Optional[Summary]:
        """
        Создать сводку по папке
        
        Args:
            folder_id: ID папки
            limit: Максимальное количество постов для анализа
            days_back: Количество дней назад для фильтрации
            include_ai_summary: Включить ИИ-сводку
        """
        try:
            # Получаем информацию о папке
            folder = await self.db_manager.get_folder(folder_id)
            if not folder:
                logger.error(f"Folder {folder_id} not found")
                return None
            
            # Получаем посты из папки
            posts = await self.db_manager.get_posts_by_folder(
                folder_id, limit=limit, days_back=days_back
            )
            
            if not posts:
                return Summary(
                    folder_name=folder.name,
                    total_posts=0,
                    date_range="Нет данных",
                    main_topics=[],
                    posts=[],
                    overall_summary="В указанный период постов не найдено."
                )
            
            # Получаем каналы для создания ссылок
            channels = await self.db_manager.get_channels_in_folder(folder_id)
            channel_map = {c.id: c for c in channels}
            
            # Создаем краткие описания постов
            post_summaries = []
            for post in posts[:20]:  # Ограничиваем для ИИ-анализа
                channel = channel_map.get(post.channel_id)
                channel_title = channel.title if channel else "Неизвестный канал"
                
                # Создаем ссылку на пост
                post_link = None
                if post.link:
                    post_link = post.link
                elif channel and channel.username:
                    post_link = f"https://t.me/{channel.username}/{post.tg_post_id}"
                
                post_summaries.append(PostSummary(
                    post_id=post.id,
                    channel_title=channel_title or "",
                    date=post.date,
                    summary=post.text[:200] + "..." if post.text and len(post.text) > 200 else (post.text or "Нет текста"),
                    link=post_link
                ))
            
            # Определяем диапазон дат
            dates = [post.date for post in posts]
            date_range = f"{min(dates).strftime('%d.%m.%Y')} - {max(dates).strftime('%d.%m.%Y')}"
            
            # Генерируем ИИ-сводку если требуется
            overall_summary = ""
            main_topics = []
            
            if include_ai_summary and posts:
                try:
                    # Проверяем доступность ИИ
                    if await self.ai_client.health_check():
                        # Извлекаем темы
                        main_topics = await self.ai_client.extract_topics(posts[:20])
                        
                        # Генерируем общую сводку
                        overall_summary = await self.ai_client.generate_summary(posts[:20])
                    else:
                        overall_summary = "ИИ-сервис недоступен. Показаны только краткие описания постов."
                        main_topics = self._extract_simple_topics(posts)
                except Exception as e:
                    logger.error(f"Error generating AI summary: {e}")
                    overall_summary = f"Ошибка при генерации ИИ-сводки: {str(e)}"
                    main_topics = self._extract_simple_topics(posts)
            else:
                main_topics = self._extract_simple_topics(posts)
                overall_summary = f"Проанализировано {len(posts)} постов из {len(channels)} каналов."
            
            return Summary(
                folder_name=folder.name,
                total_posts=len(posts),
                date_range=date_range,
                main_topics=main_topics,
                posts=post_summaries,
                overall_summary=overall_summary
            )
            
        except Exception as e:
            logger.error(f"Error summarising folder {folder_id}: {e}")
            return None
    
    async def ask_about_posts(
        self, 
        folder_id: int, 
        question: str,
        limit: int = 50,
        days_back: Optional[int] = 7
    ) -> Optional[AIResponse]:
        """
        Задать вопрос ИИ о постах в папке
        
        Args:
            folder_id: ID папки
            question: Вопрос к ИИ
            limit: Максимальное количество постов для анализа
            days_back: Количество дней назад для фильтрации
        """
        try:
            # Получаем посты
            posts = await self.db_manager.get_posts_by_folder(
                folder_id, limit=limit, days_back=days_back
            )
            
            if not posts:
                return AIResponse(
                    question=question,
                    answer="В указанный период постов не найдено для анализа.",
                    related_posts=[],
                    confidence=0.0
                )
            
            # Проверяем доступность ИИ
            if not await self.ai_client.health_check():
                return AIResponse(
                    question=question,
                    answer="ИИ-сервис недоступен. Попробуйте позже.",
                    related_posts=[],
                    confidence=0.0
                )
            
            # Получаем ответ от ИИ
            answer = await self.ai_client.answer_question(posts[:20], question)
            
            # Находим связанные посты (простая эвристика)
            related_posts = self._find_related_posts(posts, question)
            
            return AIResponse(
                question=question,
                answer=answer,
                related_posts=related_posts,
                confidence=0.8  # Базовая уверенность
            )
            
        except Exception as e:
            logger.error(f"Error asking about posts in folder {folder_id}: {e}")
            return AIResponse(
                question=question,
                answer=f"Ошибка при обработке вопроса: {str(e)}",
                related_posts=[],
                confidence=0.0
            )
    
    async def search_and_summarise(
        self, 
        folder_id: int, 
        search_term: str,
        limit: int = 30
    ) -> Optional[Summary]:
        """
        Поиск постов и создание сводки по результатам
        
        Args:
            folder_id: ID папки
            search_term: Поисковый запрос
            limit: Максимальное количество результатов
        """
        try:
            # Ищем посты
            posts = await self.db_manager.search_posts(folder_id, search_term, limit)
            
            if not posts:
                return Summary(
                    folder_name=f"Поиск: {search_term}",
                    total_posts=0,
                    date_range="Нет результатов",
                    main_topics=[],
                    posts=[],
                    overall_summary=f"По запросу '{search_term}' ничего не найдено."
                )
            
            # Получаем информацию о папке
            folder = await self.db_manager.get_folder(folder_id)
            folder_name = folder.name if folder else f"Папка {folder_id}"
            
            # Получаем каналы
            channels = await self.db_manager.get_channels_in_folder(folder_id)
            channel_map = {c.id: c for c in channels}
            
            # Создаем описания постов
            post_summaries = []
            for post in posts:
                channel = channel_map.get(post.channel_id)
                channel_title = channel.title if channel else "Неизвестный канал"
                
                post_link = None
                if post.link:
                    post_link = post.link
                elif channel and channel.username:
                    post_link = f"https://t.me/{channel.username}/{post.tg_post_id}"
                
                post_summaries.append(PostSummary(
                    post_id=post.id,
                    channel_title=channel_title or "",
                    date=post.date,
                    summary=post.text[:200] + "..." if post.text and len(post.text) > 200 else (post.text or "Нет текста"),
                    link=post_link
                ))
            
            # Определяем диапазон дат
            dates = [post.date for post in posts]
            date_range = f"{min(dates).strftime('%d.%m.%Y')} - {max(dates).strftime('%d.%m.%Y')}"
            
            # Генерируем ИИ-сводку
            overall_summary = ""
            main_topics = []
            
            try:
                if await self.ai_client.health_check():
                    main_topics = await self.ai_client.extract_topics(posts)
                    overall_summary = await self.ai_client.generate_summary(posts)
                else:
                    overall_summary = f"Найдено {len(posts)} постов по запросу '{search_term}'."
                    main_topics = self._extract_simple_topics(posts)
            except Exception as e:
                logger.error(f"Error generating AI summary for search: {e}")
                overall_summary = f"Найдено {len(posts)} постов по запросу '{search_term}'."
                main_topics = self._extract_simple_topics(posts)
            
            return Summary(
                folder_name=f"{folder_name} - Поиск: {search_term}",
                total_posts=len(posts),
                date_range=date_range,
                main_topics=main_topics,
                posts=post_summaries,
                overall_summary=overall_summary
            )
            
        except Exception as e:
            logger.error(f"Error searching and summarising in folder {folder_id}: {e}")
            return None
    
    def _extract_simple_topics(self, posts: List[Post]) -> List[str]:
        """Простое извлечение тем без ИИ"""
        # Простая эвристика для извлечения тем
        word_count = {}
        common_words = {'и', 'в', 'на', 'с', 'по', 'для', 'от', 'до', 'из', 'за', 'под', 'над', 'при', 'про', 'о', 'об', 'а', 'но', 'или', 'что', 'как', 'где', 'когда', 'почему', 'это', 'то', 'так', 'все', 'еще', 'уже', 'только', 'даже', 'тоже', 'также'}
        
        for post in posts:
            if post.text:
                words = post.text.lower().split()
                for word in words:
                    word = word.strip('.,!?;:()[]{}"\'-')
                    if len(word) > 3 and word not in common_words:
                        word_count[word] = word_count.get(word, 0) + 1
        
        # Возвращаем топ-5 слов
        sorted_words = sorted(word_count.items(), key=lambda x: x[1], reverse=True)
        return [word for word, count in sorted_words[:5]]
    
    def _find_related_posts(self, posts: List[Post], question: str) -> List[int]:
        """Найти посты, связанные с вопросом"""
        question_words = set(question.lower().split())
        related_posts = []
        
        for post in posts:
            if post.text:
                post_words = set(post.text.lower().split())
                # Простая проверка пересечения слов
                if len(question_words & post_words) > 0:
                    related_posts.append(post.id)
        
        return related_posts[:5]  # Возвращаем до 5 связанных постов 