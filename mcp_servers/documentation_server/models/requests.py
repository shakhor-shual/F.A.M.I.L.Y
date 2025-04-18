"""
Request models for Documentation MCP Server.

This module defines Pydantic models for request validation according to MCP protocol.
"""

from pydantic import BaseModel, Field
from typing import Dict, List, Optional, Any, Union

class MCPDocumentationRequest(BaseModel):
    """
    Модель запроса документации по протоколу MCP.
    
    Attributes:
        query (str): Текст запроса на естественном языке
        component_filter (Optional[str]): Фильтр по компоненту (если указан)
        diagram_type (Optional[str]): Тип диаграммы (architecture, deployment, class, etc.)
        confidence_threshold (Optional[str]): Минимальный порог уверенности (low, medium, high)
        format (Optional[str]): Формат ответа (json, xml, text)
        include_history (Optional[bool]): Включать ли историю изменений
    """
    query: str = Field(..., description="Основной запрос на естественном языке")
    component_filter: Optional[str] = Field(None, description="Фильтр по названию компонента")
    diagram_type: Optional[str] = Field(None, description="Тип диаграммы или документации")
    confidence_threshold: Optional[str] = Field("low", description="Минимальный порог уверенности (low, medium, high)")
    format: Optional[str] = Field("json", description="Формат ответа (json, xml, text)")
    include_history: Optional[bool] = Field(False, description="Включать ли историю изменений")
    
    class Config:
        schema_extra = {
            "example": {
                "query": "Опиши архитектуру многоуровневой системы памяти",
                "component_filter": "memory_system",
                "diagram_type": "architecture",
                "confidence_threshold": "medium",
                "format": "json",
                "include_history": True
            }
        }

class ComponentSearchRequest(BaseModel):
    """Request format for searching specific components"""
    component_name: str
    level_name: Optional[str] = None
    include_relationships: bool = True
    include_verification_status: bool = True


class ArchitectureLevelRequest(BaseModel):
    """Request format for querying entire architecture levels"""
    level_name: str
    include_components: bool = True
    include_services: bool = True
    confidence_threshold: Optional[str] = None  # high, medium, low