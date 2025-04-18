"""
Documentation query handler for F.A.M.I.L.Y. MCP Documentation Server.

This module provides functions to process natural language documentation queries
and convert them into appropriate database queries to retrieve project documentation.
"""

import asyncpg
import logging
import json
from typing import Dict, List, Any, Optional, Union, Tuple
import re
from datetime import datetime

from models.requests import MCPDocumentationRequest
from models.responses import (
    MCPDocumentationResponse,
    DocumentationItem,
    ComponentRelationship,
    VerificationRecord
)
from db.connection import get_db_connection, DB_CONFIG

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Константы для уровней уверенности
CONFIDENCE_LEVELS = {
    "high": 3,
    "medium": 2,
    "low": 1
}

async def get_diagram_by_name(
    conn: asyncpg.Connection, 
    diagram_name: str, 
    confidence_threshold: str = "low"
) -> Optional[Dict[str, Any]]:
    """
    Получение диаграммы по имени с учетом порога уверенности
    
    Args:
        conn: Подключение к базе данных
        diagram_name: Название диаграммы
        confidence_threshold: Минимальный порог уверенности
        
    Returns:
        Dict содержащий информацию о диаграмме или None если не найдена
    """
    # Преобразуем порог уверенности в числовое значение
    threshold_value = CONFIDENCE_LEVELS.get(confidence_threshold.lower(), 1)
    
    # Используем LIKE для нечеткого поиска по имени
    query = """
    SELECT d.id, d.name, d.description, d.diagram_type, 
           d.created_at, d.last_verified_at, d.confidence_level,
           COALESCE(jd.content, null) as json_content,
           COALESCE(xd.content, null) as xml_content
    FROM ami_documentation.diagrams d
    LEFT JOIN ami_documentation.json_diagrams jd ON d.id = jd.diagram_id
    LEFT JOIN ami_documentation.xml_diagrams xd ON d.id = xd.diagram_id
    WHERE d.name ILIKE $1
    """
    
    # Добавляем фильтр по уровню уверенности
    if confidence_threshold:
        conf_values = []
        for level, value in CONFIDENCE_LEVELS.items():
            if value >= threshold_value:
                conf_values.append(level)
        
        if conf_values:
            conf_placeholders = ", ".join([f"'{level}'" for level in conf_values])
            query += f" AND d.confidence_level IN ({conf_placeholders})"
    
    query += " ORDER BY d.last_verified_at DESC LIMIT 1"
    
    # Выполняем запрос
    row = await conn.fetchrow(query, f"%{diagram_name}%")
    
    if not row:
        return None
    
    # Форматируем результат
    result = dict(row)
    
    # Преобразуем JSON-строку в объект, если есть
    if result["json_content"]:
        result["json_content"] = json.loads(result["json_content"])
    
    return result

async def search_diagrams(
    conn: asyncpg.Connection, 
    search_terms: List[str],
    diagram_type: Optional[str] = None,
    component_filter: Optional[str] = None,
    confidence_threshold: str = "low"
) -> List[Dict[str, Any]]:
    """
    Поиск диаграмм, соответствующих условиям поиска
    
    Args:
        conn: Подключение к базе данных
        search_terms: Поисковые термины
        diagram_type: Тип диаграммы для фильтрации
        component_filter: Фильтр по компоненту
        confidence_threshold: Минимальный порог уверенности
        
    Returns:
        Список диаграмм, соответствующих условиям поиска
    """
    # Преобразуем порог уверенности в числовое значение
    threshold_value = CONFIDENCE_LEVELS.get(confidence_threshold.lower(), 1)
    
    # Базовый запрос
    query = """
    SELECT d.id, d.name, d.description, d.diagram_type, 
           d.created_at, d.last_verified_at, d.confidence_level,
           COALESCE(jd.content, null) as json_content,
           COALESCE(xd.content, null) as xml_content
    FROM ami_documentation.diagrams d
    LEFT JOIN ami_documentation.json_diagrams jd ON d.id = jd.diagram_id
    LEFT JOIN ami_documentation.xml_diagrams xd ON d.id = xd.diagram_id
    WHERE 1=1
    """
    
    # Добавляем условия фильтрации
    if search_terms:
        search_conditions = []
        for i, term in enumerate(search_terms):
            search_conditions.append(f"(d.name ILIKE ${i+1} OR d.description ILIKE ${i+1})")
        
        query += " AND (" + " OR ".join(search_conditions) + ")"
    
    if diagram_type:
        query += f" AND d.diagram_type = '{diagram_type}'"
    
    if component_filter:
        query += f" AND (d.name ILIKE '%{component_filter}%' OR d.description ILIKE '%{component_filter}%')"
    
    # Добавляем фильтр по уровню уверенности
    if confidence_threshold:
        conf_values = []
        for level, value in CONFIDENCE_LEVELS.items():
            if value >= threshold_value:
                conf_values.append(level)
        
        if conf_values:
            conf_placeholders = ", ".join([f"'{level}'" for level in conf_values])
            query += f" AND d.confidence_level IN ({conf_placeholders})"
    
    query += " ORDER BY d.last_verified_at DESC LIMIT 10"
    
    # Подготавливаем параметры запроса
    params = [f"%{term}%" for term in search_terms]
    
    # Выполняем запрос
    rows = await conn.fetch(query, *params)
    
    # Форматируем результаты
    results = []
    for row in rows:
        result = dict(row)
        
        # Преобразуем JSON-строку в объект, если есть
        if result["json_content"]:
            try:
                result["json_content"] = json.loads(result["json_content"])
            except json.JSONDecodeError:
                result["json_content"] = None
        
        results.append(result)
    
    return results

async def get_component_relationships(
    conn: asyncpg.Connection,
    component_name: Optional[str] = None
) -> List[Dict[str, Any]]:
    """
    Получение связей между компонентами
    
    Args:
        conn: Подключение к базе данных
        component_name: Имя компонента для фильтрации (опционально)
        
    Returns:
        Список связей между компонентами
    """
    # Базовый запрос
    query = """
    SELECT source_component, relationship_type, target_component, description
    FROM ami_documentation.component_relationships
    """
    
    # Добавляем условие фильтрации по компоненту
    params = []
    if component_name:
        query += " WHERE source_component ILIKE $1 OR target_component ILIKE $1"
        params.append(f"%{component_name}%")
    
    # Выполняем запрос
    rows = await conn.fetch(query, *params)
    
    # Форматируем результаты
    results = [dict(row) for row in rows]
    
    return results

async def get_verification_history(
    conn: asyncpg.Connection,
    diagram_name: Optional[str] = None
) -> List[Dict[str, Any]]:
    """
    Получение истории верификации
    
    Args:
        conn: Подключение к базе данных
        diagram_name: Имя диаграммы для фильтрации (опционально)
        
    Returns:
        Список записей истории верификации
    """
    # Проверяем существует ли таблица истории верификации
    table_exists = await conn.fetchval("""
    SELECT EXISTS (
        SELECT FROM information_schema.tables 
        WHERE table_schema = 'ami_documentation' 
        AND table_name = 'verification_history'
    )
    """)
    
    if not table_exists:
        return []
    
    # Базовый запрос
    query = """
    SELECT diagram_name, verified_at, verified_by, status, notes
    FROM ami_documentation.verification_history
    """
    
    # Добавляем условие фильтрации по имени диаграммы
    params = []
    if diagram_name:
        query += " WHERE diagram_name ILIKE $1"
        params.append(f"%{diagram_name}%")
    
    query += " ORDER BY verified_at DESC LIMIT 10"
    
    # Выполняем запрос
    rows = await conn.fetch(query, *params)
    
    # Форматируем результаты
    results = [dict(row) for row in rows]
    
    return results

async def extract_search_terms(query: str) -> List[str]:
    """
    Извлечение поисковых терминов из естественно-языкового запроса
    
    Args:
        query: Текст запроса на естественном языке
        
    Returns:
        Список поисковых терминов
    """
    # Простой алгоритм извлечения ключевых слов
    # Можно заменить на более сложный алгоритм в будущем
    
    # Удаляем знаки препинания и приводим к нижнему регистру
    clean_query = re.sub(r'[^\w\s]', ' ', query.lower())
    
    # Разбиваем на слова
    words = clean_query.split()
    
    # Исключаем стоп-слова
    stop_words = {
        'и', 'в', 'на', 'с', 'по', 'для', 'от', 'к', 'о', 'об', 'из', 'у', 
        'а', 'но', 'да', 'или', 'ни', 'чтобы', 'как', 'что', 'кто', 'где',
        'когда', 'какой', 'чей', 'который', 'этот', 'тот', 'мой', 'твой', 
        'его', 'её', 'их', 'наш', 'ваш', 'такой', 'всякий', 'каждый', 
        'любой', 'другой', 'иной', 'весь', 'все', 'сам', 'самый', 'один',
        'покажи', 'найди', 'расскажи', 'опиши'
    }
    
    filtered_words = [word for word in words if word not in stop_words]
    
    # Оставляем только слова из как минимум 3 букв
    filtered_words = [word for word in filtered_words if len(word) >= 3]
    
    # Если после фильтрации ничего не осталось, берем все слова длиннее 3 букв
    if not filtered_words:
        filtered_words = [word for word in words if len(word) >= 3]
    
    # Выбираем до 5 ключевых слов
    return filtered_words[:5]

async def process_documentation_query(request: MCPDocumentationRequest) -> MCPDocumentationResponse:
    """
    Обработка запроса документации
    
    Args:
        request: Запрос документации
        
    Returns:
        Ответ с запрошенной документацией
    """
    logger.info(f"Обработка запроса документации: {request.query}")
    
    # Подключаемся к базе данных
    conn = None
    try:
        # Создаем подключение к базе данных
        conn = await asyncpg.connect(
            host=DB_CONFIG["host"],
            port=DB_CONFIG["port"],
            user=DB_CONFIG["user"],
            password=DB_CONFIG["password"],
            database=DB_CONFIG["database"]
        )
        
        # Извлекаем поисковые термины из запроса
        search_terms = await extract_search_terms(request.query)
        logger.info(f"Извлеченные поисковые термины: {search_terms}")
        
        # Ищем диаграммы, соответствующие запросу
        diagrams = await search_diagrams(
            conn,
            search_terms,
            request.diagram_type,
            request.component_filter,
            request.confidence_threshold
        )
        
        # Если найдены диаграммы, получаем связи между компонентами
        relationships = []
        if diagrams and request.component_filter:
            relationships = await get_component_relationships(conn, request.component_filter)
        
        # Если запрошена история верификации, получаем ее
        verification_history = []
        if request.include_history and diagrams:
            diagram_names = [d["name"] for d in diagrams]
            for name in diagram_names:
                history = await get_verification_history(conn, name)
                verification_history.extend(history)
        
        # Формируем ответ
        results = []
        for diagram in diagrams:
            content = None
            if diagram["json_content"] and request.format == "json":
                content = diagram["json_content"]
            elif diagram["xml_content"] and request.format == "xml":
                content = diagram["xml_content"]
            else:
                # Если формат не соответствует или контент отсутствует, используем базовую информацию
                content = {
                    "name": diagram["name"],
                    "description": diagram["description"],
                    "type": diagram["diagram_type"],
                    "created_at": str(diagram["created_at"])
                }
            
            item = DocumentationItem(
                title=diagram["name"],
                description=diagram["description"],
                type=diagram["diagram_type"],
                confidence_level=diagram["confidence_level"],
                last_verified_at=diagram["last_verified_at"],
                content=content
            )
            results.append(item)
        
        # Форматируем связи между компонентами
        relationship_items = []
        for rel in relationships:
            relationship = ComponentRelationship(
                source=rel["source_component"],
                target=rel["target_component"],
                type=rel["relationship_type"],
                description=rel.get("description")
            )
            relationship_items.append(relationship)
        
        # Форматируем историю верификации
        verification_items = []
        for ver in verification_history:
            verification = VerificationRecord(
                verified_at=ver["verified_at"],
                verified_by=ver.get("verified_by"),
                status=ver["status"],
                notes=ver.get("notes")
            )
            verification_items.append(verification)
        
        # Анализируем уверенность в данных
        confidence_analysis = {
            "overall": "medium",  # Базовое значение
            "components": {},
            "explanation": "Базовая оценка уверенности"
        }
        
        if diagrams:
            confidence_levels = [d["confidence_level"] for d in diagrams if d["confidence_level"]]
            if confidence_levels:
                # Вычисляем общий уровень уверенности
                confidence_values = [CONFIDENCE_LEVELS.get(level.lower(), 1) for level in confidence_levels]
                avg_confidence = sum(confidence_values) / len(confidence_values)
                
                if avg_confidence >= 2.5:
                    overall = "high"
                elif avg_confidence >= 1.5:
                    overall = "medium"
                else:
                    overall = "low"
                
                confidence_analysis["overall"] = overall
                confidence_analysis["explanation"] = f"На основе {len(confidence_levels)} диаграмм"
        
        # Создаем ответ
        response = MCPDocumentationResponse(
            query=request.query,
            results=results,
            relationships=relationship_items if relationship_items else None,
            verification_history=verification_items if verification_items else None,
            format=request.format,
            confidence_analysis=confidence_analysis
        )
        
        return response
    
    except Exception as e:
        logger.error(f"Ошибка при обработке запроса документации: {str(e)}")
        raise
    
    finally:
        if conn:
            await conn.close()