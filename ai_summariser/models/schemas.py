"""
Схемы данных для AI Summariser
"""

from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, HttpUrl


class Post(BaseModel):
    """Модель поста из Telegram"""
    id: int
    channel_id: int
    tg_post_id: int
    date: datetime
    text: Optional[str] = None
    link: Optional[str] = None
    created_at: Optional[datetime] = None


class Channel(BaseModel):
    """Модель канала"""
    id: int
    folder_id: int
    tg_id: int
    username: Optional[str] = None
    title: Optional[str] = None
    created_at: Optional[datetime] = None


class Folder(BaseModel):
    """Модель папки"""
    id: int
    user_id: Optional[int] = None
    name: str
    created_at: Optional[datetime] = None


class PostSummary(BaseModel):
    """Краткое описание поста"""
    post_id: int
    channel_title: str
    date: datetime
    summary: str
    link: Optional[str] = None


class Summary(BaseModel):
    """Общая сводка по папке"""
    folder_name: str
    total_posts: int
    date_range: str
    main_topics: List[str]
    posts: List[PostSummary]
    overall_summary: str


class AIResponse(BaseModel):
    """Ответ от ИИ"""
    question: str
    answer: str
    related_posts: List[int]
    confidence: float = 0.0 