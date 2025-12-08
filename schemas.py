from typing import List, Optional, Literal, Union
from pydantic import BaseModel, Field


class ChatMessage(BaseModel):
    """
    Модель для передачи контекста (истории переписки)
    """

    role: Literal["user", "assistant", "system"]
    content: str

class ChatRequest(BaseModel):
    """
    Главная модель для чата.
    Фронт отправляет запросы через неё.
    """

    query: str = Field(..., min_length=5, description="Вопрос пользователя")
    history: List[ChatMessage] = Field(default=[], description="История диалога для контекста")

class DocumentMetadata(BaseModel):
    """
    Метаданные документа для передачи источников на фронт.
    """

    doc_id: str
    url: str
    best_chunk: str = Field(..., description="Наиболее релевантный фрагмент текста")
    score: float


class SourcesEventData(BaseModel):
    """
    Данные для события с передачей источников.
    type='sources'
    """

    items: List[DocumentMetadata]

class TokenEventData(BaseModel):
    """
    Данные для события с передачей токенов LLM.
    type='token'
    """

    text: str

class ErrorEventData(BaseModel):
    """
    Данные для события с передачей ошибки.
    type='error'
    """

    message: str


class BaseStreamEvent(BaseModel):
    type: str

class SourcesEvent(BaseStreamEvent):
    type: Literal["sources"] = "sources"
    data: SourcesEventData

class TokenEvent(BaseStreamEvent):
    type: Literal["token"] = "token"
    data: str

class ErrorEvent(BaseStreamEvent):
    type: Literal["error"] = "error"
    data: str