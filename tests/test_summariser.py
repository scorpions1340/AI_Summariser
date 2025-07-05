"""
Тесты для AI Summariser
"""

import pytest
import asyncio
import tempfile
import aiosqlite
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, patch

from ai_summariser import TelegramSummariser
from ai_summariser.models.schemas import Post, Channel, Folder


@pytest.fixture
async def test_db():
    """Создать тестовую базу данных"""
    db_fd, db_path = tempfile.mkstemp()
    
    # Создаем тестовую базу
    async with aiosqlite.connect(db_path) as db:
        # Создаем таблицы
        await db.execute("""
            CREATE TABLE folders (
                id INTEGER PRIMARY KEY,
                user_id BIGINT,
                name VARCHAR(128) NOT NULL,
                created_at DATETIME
            )
        """)
        
        await db.execute("""
            CREATE TABLE channels (
                id INTEGER PRIMARY KEY,
                folder_id INTEGER,
                tg_id BIGINT NOT NULL,
                username VARCHAR(128),
                title VARCHAR(256),
                created_at DATETIME,
                FOREIGN KEY(folder_id) REFERENCES folders (id)
            )
        """)
        
        await db.execute("""
            CREATE TABLE posts (
                id INTEGER PRIMARY KEY,
                channel_id INTEGER,
                tg_post_id BIGINT NOT NULL,
                date DATETIME NOT NULL,
                text TEXT,
                link VARCHAR(512),
                created_at DATETIME,
                FOREIGN KEY(channel_id) REFERENCES channels (id)
            )
        """)
        
        # Добавляем тестовые данные
        await db.execute(
            "INSERT INTO folders (id, name) VALUES (?, ?)",
            (1, "Тестовая папка")
        )
        
        await db.execute(
            "INSERT INTO channels (id, folder_id, tg_id, username, title) VALUES (?, ?, ?, ?, ?)",
            (1, 1, 123456, "test_channel", "Тестовый канал")
        )
        
        # Добавляем тестовые посты
        test_posts = [
            (1, 1, 1001, datetime.now() - timedelta(days=1), "Первый тестовый пост", None),
            (2, 1, 1002, datetime.now() - timedelta(hours=12), "Второй тестовый пост", None),
            (3, 1, 1003, datetime.now() - timedelta(hours=6), "Третий тестовый пост", None),
        ]
        
        for post in test_posts:
            await db.execute(
                "INSERT INTO posts (id, channel_id, tg_post_id, date, text, link) VALUES (?, ?, ?, ?, ?, ?)",
                post
            )
        
        await db.commit()
    
    yield db_path
    
    # Очистка
    import os
    os.close(db_fd)
    os.unlink(db_path)


@pytest.mark.asyncio
async def test_database_manager(test_db):
    """Тест менеджера базы данных"""
    from ai_summariser.core.database import DatabaseManager
    
    async with DatabaseManager(test_db) as db:
        # Тест получения папок
        folders = await db.get_folders()
        assert len(folders) == 1
        assert folders[0].name == "Тестовая папка"
        
        # Тест получения каналов
        channels = await db.get_channels_in_folder(1)
        assert len(channels) == 1
        assert channels[0].title == "Тестовый канал"
        
        # Тест получения постов
        posts = await db.get_posts_by_folder(1)
        assert len(posts) == 3
        assert all(isinstance(post, Post) for post in posts)


@pytest.mark.asyncio
async def test_ai_client():
    """Тест клиента ИИ"""
    from ai_summariser.core.ai_client import FreeGPTClient
    
    # Мокаем HTTP клиент
    with patch('httpx.AsyncClient') as mock_client:
        mock_response = AsyncMock()
        mock_response.json.return_value = {"response": "Тестовый ответ"}
        mock_response.raise_for_status.return_value = None
        
        mock_client_instance = AsyncMock()
        mock_client_instance.post.return_value = mock_response
        mock_client.return_value = mock_client_instance
        
        async with FreeGPTClient("http://test.com") as client:
            # Тест генерации сводки
            test_posts = [
                Post(id=1, channel_id=1, tg_post_id=1001, date=datetime.now(), text="Тестовый пост")
            ]
            
            summary = await client.generate_summary(test_posts)
            assert "Тестовый ответ" in summary


@pytest.mark.asyncio
async def test_summariser_basic(test_db):
    """Базовый тест суммаризатора"""
    with patch('ai_summariser.core.ai_client.FreeGPTClient.health_check', return_value=False):
        async with TelegramSummariser(test_db) as summariser:
            # Тест получения папок
            folders = await summariser.get_folders()
            assert len(folders) == 1
            
            # Тест создания сводки без ИИ
            summary = await summariser.summarise_folder(
                folder_id=1,
                include_ai_summary=False
            )
            
            assert summary is not None
            assert summary.folder_name == "Тестовая папка"
            assert summary.total_posts == 3
            assert len(summary.posts) == 3


@pytest.mark.asyncio
async def test_summariser_with_ai(test_db):
    """Тест суммаризатора с ИИ"""
    with patch('ai_summariser.core.ai_client.FreeGPTClient.health_check', return_value=True), \
         patch('ai_summariser.core.ai_client.FreeGPTClient.generate_summary', return_value="ИИ сводка"), \
         patch('ai_summariser.core.ai_client.FreeGPTClient.extract_topics', return_value=["тема1", "тема2"]):
        
        async with TelegramSummariser(test_db) as summariser:
            summary = await summariser.summarise_folder(
                folder_id=1,
                include_ai_summary=True
            )
            
            assert summary is not None
            assert "ИИ сводка" in summary.overall_summary
            assert len(summary.main_topics) == 2


@pytest.mark.asyncio
async def test_ask_about_posts(test_db):
    """Тест вопроса к ИИ"""
    with patch('ai_summariser.core.ai_client.FreeGPTClient.health_check', return_value=True), \
         patch('ai_summariser.core.ai_client.FreeGPTClient.answer_question', return_value="Ответ на вопрос"):
        
        async with TelegramSummariser(test_db) as summariser:
            response = await summariser.ask_about_posts(
                folder_id=1,
                question="Тестовый вопрос"
            )
            
            assert response is not None
            assert response.question == "Тестовый вопрос"
            assert "Ответ на вопрос" in response.answer


@pytest.mark.asyncio
async def test_search_and_summarise(test_db):
    """Тест поиска и суммаризации"""
    with patch('ai_summariser.core.ai_client.FreeGPTClient.health_check', return_value=True), \
         patch('ai_summariser.core.ai_client.FreeGPTClient.generate_summary', return_value="Поисковая сводка"), \
         patch('ai_summariser.core.ai_client.FreeGPTClient.extract_topics', return_value=["поиск"]):
        
        async with TelegramSummariser(test_db) as summariser:
            summary = await summariser.search_and_summarise(
                folder_id=1,
                search_term="тестовый"
            )
            
            assert summary is not None
            assert "поиск" in summary.folder_name.lower()
            assert "Поисковая сводка" in summary.overall_summary


@pytest.mark.asyncio
async def test_error_handling(test_db):
    """Тест обработки ошибок"""
    async with TelegramSummariser(test_db) as summariser:
        # Тест несуществующей папки
        summary = await summariser.summarise_folder(folder_id=999)
        assert summary is None
        
        # Тест вопроса к несуществующей папке
        response = await summariser.ask_about_posts(folder_id=999, question="Вопрос")
        assert response is not None
        assert "не найдено" in response.answer.lower()


if __name__ == "__main__":
    pytest.main([__file__]) 