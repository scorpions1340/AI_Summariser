"""
Асинхронный менеджер базы данных для работы с tg_parser.db
"""

import aiosqlite
import asyncio
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from ai_summariser.models.schemas import Post, Channel, Folder


class DatabaseManager:
    """Асинхронный менеджер для работы с SQLite базой данных"""
    
    def __init__(self, db_path: str):
        self.db_path = db_path
        self._connection: Optional[aiosqlite.Connection] = None
    
    async def __aenter__(self):
        await self.connect()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()
    
    async def connect(self):
        """Установить соединение с базой данных"""
        if self._connection is None:
            self._connection = await aiosqlite.connect(self.db_path)
            self._connection.row_factory = aiosqlite.Row
    
    async def close(self):
        """Закрыть соединение с базой данных"""
        if self._connection:
            await self._connection.close()
            self._connection = None
    
    async def get_folders(self) -> List[Folder]:
        """Получить список всех папок"""
        await self.connect()
        if self._connection is None:
            return []
        async with self._connection.execute(
            "SELECT id, user_id, name, created_at FROM folders ORDER BY name"
        ) as cursor:
            rows = await cursor.fetchall()
            return [Folder(**dict(row)) for row in rows]
    
    async def get_folder(self, folder_id: int) -> Optional[Folder]:
        """Получить папку по ID"""
        await self.connect()
        if self._connection is None:
            return None
        async with self._connection.execute(
            "SELECT id, user_id, name, created_at FROM folders WHERE id = ?",
            (folder_id,)
        ) as cursor:
            row = await cursor.fetchone()
            return Folder(**dict(row)) if row else None
    
    async def get_channels_in_folder(self, folder_id: int) -> List[Channel]:
        """Получить каналы в папке"""
        await self.connect()
        if self._connection is None:
            return []
        async with self._connection.execute(
            """
            SELECT id, folder_id, tg_id, username, title, created_at 
            FROM channels 
            WHERE folder_id = ?
            ORDER BY title
            """,
            (folder_id,)
        ) as cursor:
            rows = await cursor.fetchall()
            return [Channel(**dict(row)) for row in rows]
    
    async def get_posts_by_folder(
        self, 
        folder_id: int, 
        limit: Optional[int] = None,
        days_back: Optional[int] = None
    ) -> List[Post]:
        """Получить посты из папки с фильтрацией"""
        await self.connect()
        if self._connection is None:
            return []
        
        query = """
            SELECT p.id, c.folder_id, p.channel_id, p.tg_post_id, p.date, p.text, p.link, p.created_at
            FROM posts p
            JOIN channels c ON p.channel_id = c.id
            WHERE c.folder_id = ?
        """
        params: List[Any] = [folder_id]
        
        if days_back:
            cutoff_date = datetime.now() - timedelta(days=days_back)
            query += " AND p.date >= ?"
            params.append(cutoff_date.isoformat())
        
        query += " ORDER BY p.date DESC"
        
        if limit:
            query += " LIMIT ?"
            params.append(limit)
        
        async with self._connection.execute(query, params) as cursor:
            rows = await cursor.fetchall()
            return [Post(**dict(row)) for row in rows]
    
    async def get_posts_by_channel(
        self, 
        channel_id: int, 
        limit: Optional[int] = None
    ) -> List[Post]:
        """Получить посты конкретного канала"""
        await self.connect()
        if self._connection is None:
            return []
        
        query = """
            SELECT p.id, c.folder_id, p.channel_id, p.tg_post_id, p.date, p.text, p.link, p.created_at
            FROM posts p
            JOIN channels c ON p.channel_id = c.id
            WHERE p.channel_id = ?
            ORDER BY p.date DESC
        """
        params: List[Any] = [channel_id]
        
        if limit:
            query += " LIMIT ?"
            params.append(limit)
        
        async with self._connection.execute(query, params) as cursor:
            rows = await cursor.fetchall()
            return [Post(**dict(row)) for row in rows]
    
    async def get_post_with_channel(self, post_id: int) -> Optional[Dict[str, Any]]:
        """Получить пост с информацией о канале"""
        await self.connect()
        if self._connection is None:
            return None
        async with self._connection.execute(
            """
            SELECT p.*, c.title as channel_title, c.username as channel_username
            FROM posts p
            JOIN channels c ON p.channel_id = c.id
            WHERE p.id = ?
            """,
            (post_id,)
        ) as cursor:
            row = await cursor.fetchone()
            return dict(row) if row else None
    
    async def search_posts(
        self, 
        folder_id: int, 
        search_term: str,
        limit: int = 50
    ) -> List[Post]:
        """Поиск постов по тексту в папке"""
        await self.connect()
        if self._connection is None:
            return []
        async with self._connection.execute(
            """
            SELECT p.id, c.folder_id, p.channel_id, p.tg_post_id, p.date, p.text, p.link, p.created_at
            FROM posts p
            JOIN channels c ON p.channel_id = c.id
            WHERE c.folder_id = ? AND p.text LIKE ?
            ORDER BY p.date DESC
            LIMIT ?
            """,
            (folder_id, f"%{search_term}%", limit)
        ) as cursor:
            rows = await cursor.fetchall()
            return [Post(**dict(row)) for row in rows] 