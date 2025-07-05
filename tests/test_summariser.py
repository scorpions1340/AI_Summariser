#!/usr/bin/env python3
"""
Тесты для AI Summariser
"""

import pytest
import asyncio
import tempfile
import os
import aiosqlite
from datetime import datetime
from unittest.mock import AsyncMock, patch

from ai_summariser.models.schemas import Post, Channel, Folder, Summary, AIResponse
from ai_summariser.core.database import DatabaseManager
from ai_summariser.core.ai_client import FreeGPTClient
from ai_summariser.core.summariser import TelegramSummariser


@pytest.fixture
def temp_db():
    """Создать временную тестовую БД"""
    with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
        db_path = f.name
    
    # Создаем таблицы в тестовой БД
    async def create_test_db():
        async with aiosqlite.connect(db_path) as conn:
            await conn.execute("""
                CREATE TABLE folders (
                    id INTEGER PRIMARY KEY,
                    user_id INTEGER,
                    name TEXT NOT NULL,
                    created_at TIMESTAMP
                )
            """)
            
            await conn.execute("""
                CREATE TABLE channels (
                    id INTEGER PRIMARY KEY,
                    folder_id INTEGER,
                    tg_id INTEGER,
                    username TEXT,
                    title TEXT,
                    created_at TIMESTAMP,
                    FOREIGN KEY (folder_id) REFERENCES folders (id)
                )
            """)
            
            await conn.execute("""
                CREATE TABLE posts (
                    id INTEGER PRIMARY KEY,
                    channel_id INTEGER,
                    tg_post_id INTEGER,
                    date TIMESTAMP,
                    text TEXT,
                    link TEXT,
                    created_at TIMESTAMP,
                    FOREIGN KEY (channel_id) REFERENCES channels (id)
                )
            """)
            
            # Добавляем тестовые данные
            await conn.execute(
                "INSERT INTO folders (id, name) VALUES (?, ?)",
                (1, "Тестовая папка")
            )
            
            await conn.execute(
                "INSERT INTO channels (id, folder_id, tg_id, title, username) VALUES (?, ?, ?, ?, ?)",
                (1, 1, 123456, "Тестовый канал", "test_channel")
            )
            
            await conn.execute(
                "INSERT INTO posts (id, channel_id, tg_post_id, date, text) VALUES (?, ?, ?, ?, ?)",
                (1, 1, 123, datetime.now().isoformat(), "Тестовый пост")
            )
            
            await conn.commit()
    
    asyncio.run(create_test_db())
    
    yield db_path
    
    # Удаляем временную БД
    os.unlink(db_path)


@pytest.mark.asyncio
async def test_database_manager(temp_db):
    """Тест менеджера базы данных"""
    async with DatabaseManager(temp_db) as db:
        folders = await db.get_folders()
        assert len(folders) == 1
        assert folders[0].name == "Тестовая папка"
        
        folder = await db.get_folder(1)
        assert folder is not None
        assert folder.name == "Тестовая папка"


@pytest.mark.asyncio
async def test_ai_client():
    """Тест ИИ-клиента с моком (без patch контекст-менеджера)"""
    client = FreeGPTClient()
    mock_httpx = AsyncMock()
    # Мокаем get/post/aclose
    mock_response = AsyncMock()
    mock_response.json = AsyncMock(return_value={
        "choices": [{"message": {"content": "Тестовый ответ"}}]
    })
    mock_response.raise_for_status = AsyncMock(return_value=None)
    mock_httpx.get.return_value = mock_response
    mock_httpx.post.return_value = mock_response
    mock_httpx.aclose = AsyncMock()
    client._client = mock_httpx

    health = await client.health_check()
    assert health is True
    test_posts = [
        Post(
            id=1,
            folder_id=1,
            channel_id=1,
            tg_post_id=123,
            text="Тестовый пост",
            date=datetime.now(),
            link="https://t.me/test/1"
        )
    ]
    summary = await client.generate_summary(test_posts)
    assert "Тестовый ответ" in summary


@pytest.mark.asyncio
async def test_summariser_basic(temp_db):
    """Базовый тест суммаризатора"""
    with patch('ai_summariser.core.ai_client.FreeGPTClient') as mock_ai_class:
        # Мокируем ИИ-клиент
        mock_ai_instance = AsyncMock()
        mock_ai_instance.health_check.return_value = False
        mock_ai_class.return_value = mock_ai_instance
        
        async with TelegramSummariser(temp_db) as summariser:
            folders = await summariser.get_folders()
            assert len(folders) == 1
            
            summary = await summariser.summarise_folder(
                folder_id=1,
                include_ai_summary=False
            )
            
            assert summary is not None
            assert summary.folder_name == "Тестовая папка"
            assert summary.total_posts == 1


@pytest.mark.asyncio
async def test_summariser_with_ai(temp_db):
    """Тест суммаризатора с ИИ"""
    mock_ai_instance = AsyncMock()
    mock_ai_instance.health_check.return_value = True
    mock_ai_instance.generate_summary.return_value = "ИИ-сводка"
    mock_ai_instance.extract_topics.return_value = ["тема 1", "тема 2"]
    async with TelegramSummariser(temp_db) as summariser:
        summariser.ai_client = mock_ai_instance
        summary = await summariser.summarise_folder(
            folder_id=1,
            include_ai_summary=True
        )
        assert summary is not None
        assert "ИИ-сводка" in summary.overall_summary


@pytest.mark.asyncio
async def test_ask_about_posts(temp_db):
    """Тест задавания вопросов"""
    mock_ai_instance = AsyncMock()
    mock_ai_instance.health_check.return_value = True
    mock_ai_instance.answer_question.return_value = "Ответ на вопрос"
    async with TelegramSummariser(temp_db) as summariser:
        summariser.ai_client = mock_ai_instance
        response = await summariser.ask_about_posts(
            folder_id=1,
            question="Тестовый вопрос"
        )
        assert response is not None
        assert "Ответ на вопрос" in response.answer


@pytest.mark.asyncio
async def test_search_and_summarise(temp_db):
    """Тест поиска и суммаризации"""
    mock_ai_instance = AsyncMock()
    mock_ai_instance.health_check.return_value = True
    mock_ai_instance.generate_summary.return_value = "Поисковая сводка"
    mock_ai_instance.extract_topics.return_value = ["поисковая тема"]
    async with TelegramSummariser(temp_db) as summariser:
        summariser.ai_client = mock_ai_instance
        result = await summariser.search_and_summarise(
            folder_id=1,
            search_term="Тестовый"
        )
        assert result is not None
        assert "Поисковая сводка" in result.overall_summary


@pytest.mark.asyncio
async def test_error_handling(temp_db):
    """Тест обработки ошибок"""
    async with TelegramSummariser(temp_db) as summariser:
        # Тест с несуществующей папкой
        summary = await summariser.summarise_folder(folder_id=999)
        assert summary is None
        
        # Тест вопроса к несуществующей папке
        response = await summariser.ask_about_posts(
            folder_id=999,
            question="Вопрос"
        )
        assert response is not None
        assert "не найдено" in response.answer.lower()


if __name__ == "__main__":
    pytest.main([__file__, "-v"]) 