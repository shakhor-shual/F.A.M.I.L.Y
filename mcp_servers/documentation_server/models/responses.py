"""
Response models for Documentation MCP Server.

This module defines Pydantic models for formatting responses according to MCP protocol.
"""

from pydantic import BaseModel, Field
from typing import Dict, List, Optional, Any, Union
from datetime import datetime

class DocumentationItem(BaseModel):
    """
    Модель отдельного элемента документации
    
    Attributes:
        title: Название элемента документации
        description: Описание элемента
        type: Тип элемента (component, diagram, relationship)
        confidence_level: Уровень уверенности в актуальности (low, medium, high)
        last_verified_at: Дата последней верификации
        content: Содержимое документации (может быть различных типов)
    """
    title: str
    description: Optional[str] = None
    type: str
    confidence_level: str
    last_verified_at: Optional[datetime] = None
    content: Any
    
class ComponentRelationship(BaseModel):
    """
    Модель связи между компонентами
    
    Attributes:
        source: Исходный компонент
        target: Целевой компонент
        type: Тип связи (uses, extends, implements, etc.)
        description: Описание связи
    """
    source: str
    target: str
    type: str
    description: Optional[str] = None
    
class VerificationRecord(BaseModel):
    """
    Запись о верификации документации
    
    Attributes:
        verified_at: Дата верификации
        verified_by: Кем верифицировано
        status: Статус верификации
        notes: Заметки по верификации
    """
    verified_at: datetime
    verified_by: Optional[str] = None
    status: str
    notes: Optional[str] = None

class MCPDocumentationResponse(BaseModel):
    """
    Модель ответа MCP-сервера документации
    
    Attributes:
        query: Исходный запрос
        timestamp: Время генерации ответа
        results: Список найденных элементов документации
        relationships: Список связей между компонентами (если применимо)
        verification_history: История верификации (если запрошена)
        format: Формат ответа
        confidence_analysis: Анализ уверенности в данных
    """
    query: str
    timestamp: datetime = Field(default_factory=datetime.now)
    results: List[DocumentationItem]
    relationships: Optional[List[ComponentRelationship]] = None
    verification_history: Optional[List[VerificationRecord]] = None
    format: str
    confidence_analysis: Dict[str, Any] = Field(
        default_factory=lambda: {
            "overall": "medium",
            "components": {},
            "explanation": "Базовая оценка уверенности"
        }
    )