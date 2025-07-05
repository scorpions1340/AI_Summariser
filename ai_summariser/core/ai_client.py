"""
Клиент для работы с FreeGPT API (WebUI)
"""

import httpx
import asyncio
import uuid
from typing import Optional, Dict, Any, List
import json
import logging
from ..models.schemas import Post

logger = logging.getLogger(__name__)


class FreeGPTClient:
    """Асинхронный клиент для работы с FreeGPT API (WebUI)"""
    
    def __init__(
        self, 
        base_url: str = "http://127.0.0.1:1338",
        timeout: int = 30,
        max_retries: int = 3
    ):
        self.base_url = base_url.rstrip('/')
        self.timeout = timeout
        self.max_retries = max_retries
        self._client: Optional[httpx.AsyncClient] = None
    
    async def __aenter__(self):
        self._client = httpx.AsyncClient(
            timeout=self.timeout,
            limits=httpx.Limits(max_keepalive_connections=5, max_connections=10)
        )
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self._client:
            await self._client.aclose()
            self._client = None
    
    async def _make_request(
        self, 
        method: str, 
        endpoint: str, 
        data: Optional[Dict[str, Any]] = None,
        retry_count: int = 0
    ) -> Dict[str, Any]:
        """Выполнить HTTP запрос с повторными попытками"""
        if self._client is None:
            self._client = httpx.AsyncClient(timeout=self.timeout)
        client: httpx.AsyncClient = self._client
        
        url = f"{self.base_url}{endpoint}"
        
        try:
            if method.upper() == "POST":
                response = await client.post(url, json=data)
            else:
                response = await client.get(url)
            
            response.raise_for_status()
            return response.json()
            
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error {e.response.status_code}: {e.response.text}")
            if retry_count < self.max_retries:
                await asyncio.sleep(2 ** retry_count)  # Exponential backoff
                return await self._make_request(method, endpoint, data, retry_count + 1)
            raise
            
        except httpx.RequestError as e:
            logger.error(f"Request error: {e}")
            if retry_count < self.max_retries:
                await asyncio.sleep(2 ** retry_count)
                return await self._make_request(method, endpoint, data, retry_count + 1)
            raise
    
    async def _make_stream_request(self, prompt: str, model: str = "mixtral-8x7b", provider: str = "Auto") -> str:
        """Выполнить запрос к FreeGPT API с правильным форматом"""
        if self._client is None:
            self._client = httpx.AsyncClient(timeout=self.timeout)
        
        conversation_id = str(uuid.uuid4())
        url = f"{self.base_url}/backend-api/v2/conversation"
        
        # Формат запроса согласно FreeGPT API
        payload = {
            "temperature": 0.2,
            "top_k": 10,
            "typical_p": 0.8,
            "no_repeat_n": 2,
            "early_stopping": True,
            "frequency_WPF_penalty": 2.0,
            "max_tokens": 2048,
            "conversation_id": conversation_id,
            "action": "_ask",
            "model": model,
            "provider": f"g4f.Provider.{provider}" if provider != "Auto" else "Auto",
            "meta": {
                "id": str(uuid.uuid4()),
                "content": {
                    "conversation": [],
                    "internet_access": True,
                    "content_type": "text",
                    "parts": [
                        {
                            "content": prompt,
                            "role": "user",
                        },
                    ],
                },
            },
        }
        
        try:
            response = await self._client.post(url, json=payload)
            response.raise_for_status()
            
            # Обрабатываем stream response
            full_response = ""
            async for line in response.aiter_lines():
                if line.startswith("data: "):
                    try:
                        data = json.loads(line[6:])  # Убираем "data: "
                        if "content" in data:
                            full_response += data["content"]
                    except json.JSONDecodeError:
                        continue
            
            return full_response.strip()
            
        except Exception as e:
            logger.error(f"Error in stream request: {e}")
            raise
    
    async def health_check(self) -> bool:
        """Проверить доступность FreeGPT сервера"""
        try:
            if self._client is None:
                self._client = httpx.AsyncClient(timeout=self.timeout)
            
            response = await self._client.get(f"{self.base_url}/chat/")
            response.raise_for_status()
            return True
        except Exception as e:
            logger.warning(f"FreeGPT health check failed: {e}")
            return False
    
    async def generate_summary(self, posts: List[Post], max_length: int = 1000) -> str:
        """Сгенерировать краткое описание постов"""
        if not posts:
            return "Нет постов для анализа."
        
        # Подготавливаем контекст из постов
        context = self._prepare_posts_context(posts)
        
        prompt = f"""
        Проанализируй следующие посты из Telegram каналов и создай краткую сводку.
        
        Контекст постов:
        {context}
        
        Задача: Создай краткое описание (не более {max_length} символов) основных тем, 
        событий и трендов, которые обсуждались в этих постах. 
        Выдели ключевые моменты и общие тенденции.
        
        Ответ должен быть структурированным и информативным.
        """
        
        try:
            response = await self._make_stream_request(prompt, model="mixtral-8x7b")
            return response[:max_length] if response else "Ошибка при генерации сводки."
                
        except Exception as e:
            logger.error(f"Error generating summary: {e}")
            return f"Ошибка при генерации сводки: {str(e)}"
    
    async def answer_question(
        self, 
        posts: List[Post], 
        question: str,
        max_length: int = 1500
    ) -> str:
        """Ответить на вопрос о постах"""
        if not posts:
            return "Нет постов для анализа."
        
        context = self._prepare_posts_context(posts)
        
        prompt = f"""
        У тебя есть доступ к следующим постам из Telegram каналов:
        
        {context}
        
        Вопрос: {question}
        
        Задача: Ответь на вопрос, основываясь на информации из предоставленных постов. 
        Если в постах нет информации для ответа, честно скажи об этом.
        Ответ должен быть информативным и не превышать {max_length} символов.
        """
        
        try:
            response = await self._make_stream_request(prompt, model="mixtral-8x7b")
            return response[:max_length] if response else "Ошибка при генерации ответа."
                
        except Exception as e:
            logger.error(f"Error answering question: {e}")
            return f"Ошибка при генерации ответа: {str(e)}"
    
    async def extract_topics(self, posts: List[Post]) -> List[str]:
        """Извлечь основные темы из постов"""
        if not posts:
            return []
        
        context = self._prepare_posts_context(posts)
        
        prompt = f"""
        Проанализируй следующие посты и выдели 5-7 основных тем:
        
        {context}
        
        Задача: Выдели ключевые темы, которые обсуждались в постах. 
        Верни список тем в формате JSON массив строк.
        Пример: ["тема 1", "тема 2", "тема 3"]
        """
        
        try:
            response = await self._make_stream_request(prompt, model="mixtral-8x7b")
            
            if response:
                try:
                    # Пытаемся парсить JSON из ответа
                    topics_text = response
                    # Ищем JSON в ответе
                    start_idx = topics_text.find('[')
                    end_idx = topics_text.rfind(']') + 1
                    if start_idx != -1 and end_idx != 0:
                        json_str = topics_text[start_idx:end_idx]
                        topics = json.loads(json_str)
                        return topics[:7]  # Ограничиваем до 7 тем
                except (json.JSONDecodeError, ValueError):
                    # Если не удалось парсить JSON, извлекаем темы из текста
                    return self._extract_topics_from_text(response)
            
            return []
            
        except Exception as e:
            logger.error(f"Error extracting topics: {e}")
            return []
    
    def _prepare_posts_context(self, posts: List[Post]) -> str:
        """Подготовить контекст постов для ИИ"""
        context_parts = []
        
        for i, post in enumerate(posts[:20], 1):  # Ограничиваем до 20 постов
            date_str = post.date.strftime("%d.%m.%Y %H:%M")
            text_preview = (post.text[:200] + "...") if post.text and len(post.text) > 200 else (post.text or "Нет текста")
            
            context_parts.append(
                f"{i}. [{date_str}] {text_preview}"
            )
        
        return "\n".join(context_parts)
    
    def _extract_topics_from_text(self, text: str) -> List[str]:
        """Извлечь темы из текстового ответа"""
        # Простая эвристика для извлечения тем
        lines = text.split('\n')
        topics = []
        
        for line in lines:
            line = line.strip()
            if line and not line.startswith(('Задача:', 'Ответ:', 'Анализ:')):
                # Убираем номера и лишние символы
                clean_line = line.lstrip('0123456789.-* ')
                if len(clean_line) > 3 and len(clean_line) < 100:
                    topics.append(clean_line)
        
        return topics[:7]  # Возвращаем до 7 тем 