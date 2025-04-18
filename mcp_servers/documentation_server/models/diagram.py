"""
Diagram model module for F.A.M.I.L.Y. MCP Documentation Server.

This module provides a model for working with documentation diagrams in the F.A.M.I.L.Y. project.
It implements the principles of the AMI memory system through diagram classification 
and integration with the documentation database.
"""

import logging
import json
from typing import Dict, List, Optional, Any, Union
from datetime import datetime

# Исправленный импорт на локальный путь
from db.connection import db_transaction

logger = logging.getLogger(__name__)

class DiagramModel:
    """
    Модель для работы с диаграммами документации проекта F.A.M.I.L.Y.
    
    Интегрируется с сознательным уровнем памяти АМИ через систему верификации
    и категоризации диаграмм.
    
    Integration Points:
        - Использует систему соединений с БД из модуля db.connection
        - Используется обработчиками API для работы с диаграммами
        - Интегрируется с системой памяти АМИ через механизмы верификации
    """
    
    DIAGRAM_TYPES = ["architecture", "component", "relationship", "sequence", "state", "memory_system"]
    CONFIDENCE_LEVELS = ["low", "medium", "high", "verified"]
    
    @staticmethod
    async def create_diagram(name: str, description: str, diagram_type: str, 
                           content: Union[Dict, str], is_json: bool = True) -> int:
        """
        Создает новую диаграмму в системе документации.
        
        Args:
            name: Название диаграммы
            description: Описание диаграммы
            diagram_type: Тип диаграммы (из списка DIAGRAM_TYPES)
            content: Содержимое диаграммы (JSON или XML)
            is_json: Флаг типа содержимого (JSON или XML)
            
        Returns:
            ID созданной диаграммы
        """
        if diagram_type not in DiagramModel.DIAGRAM_TYPES:
            raise ValueError(f"Неподдерживаемый тип диаграммы: {diagram_type}. Доступные типы: {DiagramModel.DIAGRAM_TYPES}")
        
        async with db_transaction() as conn:
            # Создаем запись в таблице диаграмм
            diagram_id = await conn.fetchval("""
                INSERT INTO ami_documentation.diagrams(name, description, diagram_type)
                VALUES($1, $2, $3)
                RETURNING id
            """, name, description, diagram_type)
            
            # Преобразуем словарь в JSON-строку, если это необходимо
            if is_json and isinstance(content, dict):
                # Преобразуем словарь Python в JSON-строку для PostgreSQL JSONB
                json_content = json.dumps(content)
                
                await conn.execute("""
                    INSERT INTO ami_documentation.json_diagrams(diagram_id, content)
                    VALUES($1, $2::jsonb)
                """, diagram_id, json_content)
            elif is_json:
                # Если это уже JSON-строка, используем её напрямую
                await conn.execute("""
                    INSERT INTO ami_documentation.json_diagrams(diagram_id, content)
                    VALUES($1, $2::jsonb)
                """, diagram_id, content)
            else:
                # Для XML-содержимого
                await conn.execute("""
                    INSERT INTO ami_documentation.xml_diagrams(diagram_id, content)
                    VALUES($1, $2)
                """, diagram_id, content)
            
            logger.info(f"Создана диаграмма {name} типа {diagram_type} с ID {diagram_id}")
            
            return diagram_id
    
    @staticmethod
    async def get_diagram(diagram_id: int) -> Optional[Dict[str, Any]]:
        """
        Получает информацию о диаграмме по ID.
        
        Args:
            diagram_id: ID диаграммы
            
        Returns:
            Словарь с информацией о диаграмме или None, если диаграмма не найдена
        """
        async with db_transaction() as conn:
            # Получаем базовую информацию о диаграмме
            diagram = await conn.fetchrow("""
                SELECT id, name, description, diagram_type, created_at, 
                      last_verified_at, confidence_level
                FROM ami_documentation.diagrams
                WHERE id = $1
            """, diagram_id)
            
            if not diagram:
                logger.warning(f"Диаграмма с ID {diagram_id} не найдена")
                return None
            
            # Преобразуем результат запроса в словарь
            result = dict(diagram)
            
            # Пробуем получить JSON-содержимое
            json_content = await conn.fetchval("""
                SELECT content FROM ami_documentation.json_diagrams
                WHERE diagram_id = $1
            """, diagram_id)
            
            if json_content:
                result["content"] = json_content
                result["content_type"] = "json"
            else:
                # Если JSON не найден, пробуем XML
                xml_content = await conn.fetchval("""
                    SELECT content FROM ami_documentation.xml_diagrams
                    WHERE diagram_id = $1
                """, diagram_id)
                
                if xml_content:
                    result["content"] = xml_content
                    result["content_type"] = "xml"
                else:
                    result["content"] = None
                    result["content_type"] = None
            
            return result
    
    @staticmethod
    async def get_all_diagrams() -> List[Dict[str, Any]]:
        """
        Получает список всех диаграмм (без содержимого).
        
        Returns:
            Список диаграмм
        """
        async with db_transaction() as conn:
            diagrams = await conn.fetch("""
                SELECT id, name, description, diagram_type, created_at, 
                      last_verified_at, confidence_level
                FROM ami_documentation.diagrams
                ORDER BY created_at DESC
            """)
            
            return [dict(diagram) for diagram in diagrams]
    
    @staticmethod
    async def update_diagram(diagram_id: int, name: Optional[str] = None, 
                           description: Optional[str] = None, 
                           content: Optional[Union[Dict, str]] = None) -> bool:
        """
        Обновляет информацию о диаграмме.
        
        Args:
            diagram_id: ID диаграммы
            name: Новое название диаграммы (опционально)
            description: Новое описание диаграммы (опционально)
            content: Новое содержимое диаграммы (опционально)
            
        Returns:
            True если обновление успешно, иначе False
        """
        async with db_transaction() as conn:
            # Проверяем существование диаграммы и получаем её текущий тип содержимого
            diagram = await conn.fetchrow("""
                SELECT id, name, description, diagram_type
                FROM ami_documentation.diagrams
                WHERE id = $1
            """, diagram_id)
            
            if not diagram:
                logger.warning(f"Диаграмма с ID {diagram_id} не найдена для обновления")
                return False
            
            # Обновляем базовую информацию, если она предоставлена
            update_fields = []
            update_values = []
            
            if name is not None:
                update_fields.append("name = $" + str(len(update_values) + 1))
                update_values.append(name)
                
            if description is not None:
                update_fields.append("description = $" + str(len(update_values) + 1))
                update_values.append(description)
            
            if update_fields:
                update_query = "UPDATE ami_documentation.diagrams SET " + ", ".join(update_fields)
                update_query += f" WHERE id = ${len(update_values) + 1}"
                update_values.append(diagram_id)
                
                await conn.execute(update_query, *update_values)
            
            # Обновляем содержимое, если оно предоставлено
            if content is not None:
                # Определяем тип содержимого (JSON или XML)
                is_json = isinstance(content, dict)
                
                # Проверяем, есть ли уже содержимое в JSON-таблице
                json_exists = await conn.fetchval("""
                    SELECT EXISTS(SELECT 1 FROM ami_documentation.json_diagrams WHERE diagram_id = $1)
                """, diagram_id)
                
                # Проверяем, есть ли уже содержимое в XML-таблице
                xml_exists = await conn.fetchval("""
                    SELECT EXISTS(SELECT 1 FROM ami_documentation.xml_diagrams WHERE diagram_id = $1)
                """, diagram_id)
                
                if is_json:
                    if json_exists:
                        # Обновляем существующее JSON-содержимое
                        await conn.execute("""
                            UPDATE ami_documentation.json_diagrams
                            SET content = $1
                            WHERE diagram_id = $2
                        """, content, diagram_id)
                    else:
                        # Создаем новую запись JSON-содержимого
                        await conn.execute("""
                            INSERT INTO ami_documentation.json_diagrams(diagram_id, content)
                            VALUES($1, $2)
                        """, diagram_id, content)
                        
                        # Удаляем XML-содержимое, если оно существует
                        if xml_exists:
                            await conn.execute("""
                                DELETE FROM ami_documentation.xml_diagrams
                                WHERE diagram_id = $1
                            """, diagram_id)
                else:
                    # Аналогично для XML
                    if xml_exists:
                        await conn.execute("""
                            UPDATE ami_documentation.xml_diagrams
                            SET content = $1
                            WHERE diagram_id = $2
                        """, content, diagram_id)
                    else:
                        await conn.execute("""
                            INSERT INTO ami_documentation.xml_diagrams(diagram_id, content)
                            VALUES($1, $2)
                        """, diagram_id, content)
                        
                        if json_exists:
                            await conn.execute("""
                                DELETE FROM ami_documentation.json_diagrams
                                WHERE diagram_id = $1
                            """, diagram_id)
            
            logger.info(f"Диаграмма с ID {diagram_id} успешно обновлена")
            return True
    
    @staticmethod
    async def delete_diagram(diagram_id: int) -> bool:
        """
        Удаляет диаграмму из системы.
        
        Args:
            diagram_id: ID диаграммы
            
        Returns:
            True если удаление успешно, иначе False
        """
        async with db_transaction() as conn:
            # Проверяем существование диаграммы
            exists = await conn.fetchval("""
                SELECT EXISTS(SELECT 1 FROM ami_documentation.diagrams WHERE id = $1)
            """, diagram_id)
            
            if not exists:
                logger.warning(f"Диаграмма с ID {diagram_id} не найдена для удаления")
                return False
            
            # Удаляем диаграмму (каскадное удаление также удалит связанные записи)
            await conn.execute("""
                DELETE FROM ami_documentation.diagrams
                WHERE id = $1
            """, diagram_id)
            
            logger.info(f"Диаграмма с ID {diagram_id} успешно удалена")
            return True
    
    @staticmethod
    async def verify_diagram(diagram_id: int, verified_by: str, 
                           status: str, notes: Optional[str] = None) -> bool:
        """
        Верифицирует диаграмму, обновляет статус и уровень достоверности.
        
        Args:
            diagram_id: ID диаграммы
            verified_by: Имя верифицирующего (человек или АМИ)
            status: Статус верификации ('approved', 'rejected', 'needs_revision')
            notes: Заметки о верификации (опционально)
            
        Returns:
            True если верификация успешна, иначе False
            
        Integration Points:
            - Фиксация результатов верификации диаграммы в памяти АМИ
            - Создание событий для изменения состояния AMI
        """
        valid_statuses = ['approved', 'rejected', 'needs_revision']
        
        if status not in valid_statuses:
            raise ValueError(f"Неверный статус верификации: {status}. Допустимые значения: {valid_statuses}")
        
        async with db_transaction() as conn:
            # Проверяем существование диаграммы
            exists = await conn.fetchval("""
                SELECT EXISTS(SELECT 1 FROM ami_documentation.diagrams WHERE id = $1)
            """, diagram_id)
            
            if not exists:
                logger.warning(f"Диаграмма с ID {diagram_id} не найдена для верификации")
                return False
            
            # Получаем имя диаграммы для использования в записи истории
            diagram_name = await conn.fetchval("""
                SELECT name FROM ami_documentation.diagrams WHERE id = $1
            """, diagram_id)
            
            # Добавляем запись в историю верификации
            await conn.execute("""
                INSERT INTO ami_documentation.verification_history
                (diagram_name, verified_by, status, notes)
                VALUES($1, $2, $3, $4)
            """, diagram_name, verified_by, status, notes)
            
            # Обновляем информацию о диаграмме
            confidence_level = 'verified' if status == 'approved' else 'medium'
            
            await conn.execute("""
                UPDATE ami_documentation.diagrams
                SET last_verified_at = CURRENT_TIMESTAMP,
                    confidence_level = $1
                WHERE id = $2
            """, confidence_level, diagram_id)
            
            logger.info(f"Диаграмма {diagram_name} (ID: {diagram_id}) верифицирована со статусом {status}")
            return True
            
    @staticmethod
    async def get_diagrams_by_type(diagram_type: str) -> List[Dict[str, Any]]:
        """
        Получает список диаграмм определенного типа.
        
        Args:
            diagram_type: Тип диаграммы
            
        Returns:
            Список диаграмм указанного типа
        """
        if diagram_type not in DiagramModel.DIAGRAM_TYPES:
            raise ValueError(f"Неподдерживаемый тип диаграммы: {diagram_type}. Доступные типы: {DiagramModel.DIAGRAM_TYPES}")
        
        async with db_transaction() as conn:
            diagrams = await conn.fetch("""
                SELECT id, name, description, diagram_type, created_at, 
                      last_verified_at, confidence_level
                FROM ami_documentation.diagrams
                WHERE diagram_type = $1
                ORDER BY created_at DESC
            """, diagram_type)
            
            return [dict(diagram) for diagram in diagrams]
    
    @staticmethod
    async def search_diagrams(query: str) -> List[Dict[str, Any]]:
        """
        Ищет диаграммы по имени или описанию.
        
        Args:
            query: Поисковый запрос
            
        Returns:
            Список найденных диаграмм
        """
        search_term = f"%{query}%"
        
        async with db_transaction() as conn:
            diagrams = await conn.fetch("""
                SELECT id, name, description, diagram_type, created_at, 
                      last_verified_at, confidence_level
                FROM ami_documentation.diagrams
                WHERE name ILIKE $1 OR description ILIKE $1
                ORDER BY created_at DESC
            """, search_term)
            
            return [dict(diagram) for diagram in diagrams]