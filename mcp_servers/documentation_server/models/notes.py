"""
Note model module for F.A.M.I.L.Y. MCP Documentation Server.

This module provides a model for working with development notes in the F.A.M.I.L.Y. project.
It implements the principles of the AMI memory system through note management and categorization.
"""

import logging
import json
from typing import Dict, List, Optional, Any, Union
from datetime import datetime
import uuid

from db.connection import db_transaction

logger = logging.getLogger(__name__)

class NoteModel:
    """
    Модель для работы с заметками о процессе разработки.
    
    Интегрируется с сознательным уровнем памяти АМИ через систему категоризации
    и связывания заметок.
    """
    
    STATUSES = ["active", "completed", "archived"]
    PRIORITIES = [0, 1, 2]  # low, medium, high
    LINK_TYPES = ["depends_on", "related_to", "blocks", "implements"]
    
    @staticmethod
    async def create_tag(name: str, description: Optional[str] = None) -> int:
        """
        Создает новый тег.
        
        Args:
            name: Название тега
            description: Описание тега
            
        Returns:
            ID созданного тега
        """
        async with db_transaction() as conn:
            tag_id = await conn.fetchval("""
                INSERT INTO ami_documentation.tags(name, description)
                VALUES($1, $2)
                ON CONFLICT (name) DO UPDATE SET description = $2
                RETURNING id
            """, name, description)
            
            logger.info(f"Создан тег {name} с ID {tag_id}")
            return tag_id
    
    @staticmethod
    async def create_category(name: str, description: Optional[str] = None) -> int:
        """
        Создает новую категорию для заметок.
        
        Args:
            name: Название категории
            description: Описание категории
            
        Returns:
            ID созданной категории
        """
        async with db_transaction() as conn:
            category_id = await conn.fetchval("""
                INSERT INTO ami_documentation.note_categories(name, description)
                VALUES($1, $2)
                ON CONFLICT (name) DO UPDATE SET description = $2
                RETURNING id
            """, name, description)
            
            logger.info(f"Создана категория {name} с ID {category_id}")
            return category_id
    
    @staticmethod
    async def create_note(
        title: str,
        content: str,
        category_name: str,
        status: str = "active",
        priority: int = 0,
        session_id: Optional[str] = None,
        parent_note_id: Optional[int] = None,
        context: Optional[Dict[str, Any]] = None,
        tags: Optional[List[str]] = None
    ) -> int:
        """
        Создает новую заметку.
        
        Args:
            title: Заголовок заметки
            content: Содержимое заметки
            category_name: Название категории
            status: Статус заметки (active/completed/archived)
            priority: Приоритет (0: low, 1: medium, 2: high)
            session_id: ID сессии, в которой создана заметка
            parent_note_id: ID родительской заметки
            context: Дополнительный контекст в формате JSON
            tags: Список тегов
            
        Returns:
            ID созданной заметки
        """
        if status not in NoteModel.STATUSES:
            raise ValueError(f"Неподдерживаемый статус: {status}")
        if priority not in NoteModel.PRIORITIES:
            raise ValueError(f"Неподдерживаемый приоритет: {priority}")
        
        async with db_transaction() as conn:
            # Получаем ID категории
            category_id = await conn.fetchval("""
                SELECT id FROM ami_documentation.note_categories
                WHERE name = $1
            """, category_name)
            
            if not category_id:
                raise ValueError(f"Категория {category_name} не найдена")
            
            # Создаем заметку
            note_id = await conn.fetchval("""
                INSERT INTO ami_documentation.notes(
                    title, content, category_id, status, priority,
                    session_id, parent_note_id, context
                )
                VALUES($1, $2, $3, $4, $5, $6, $7, $8)
                RETURNING id
            """, title, content, category_id, status, priority,
                session_id, parent_note_id, json.dumps(context) if context else None)
            
            # Добавляем теги, если они указаны
            if tags:
                for tag_name in tags:
                    # Создаем тег, если его нет
                    tag_id = await conn.fetchval("""
                        INSERT INTO ami_documentation.tags(name)
                        VALUES($1)
                        ON CONFLICT (name) DO UPDATE SET name = $1
                        RETURNING id
                    """, tag_name)
                    
                    # Связываем тег с заметкой
                    await conn.execute("""
                        INSERT INTO ami_documentation.note_tags(note_id, tag_id)
                        VALUES($1, $2)
                        ON CONFLICT DO NOTHING
                    """, note_id, tag_id)
            
            logger.info(f"Создана заметка {title} с ID {note_id}")
            return note_id
    
    @staticmethod
    async def get_note(note_id: int) -> Optional[Dict[str, Any]]:
        """
        Получает информацию о заметке по ID.
        
        Args:
            note_id: ID заметки
            
        Returns:
            Словарь с информацией о заметке или None, если заметка не найдена
        """
        async with db_transaction() as conn:
            # Получаем базовую информацию о заметке
            note = await conn.fetchrow("""
                SELECT n.id, n.title, n.content, n.status, n.priority,
                       n.created_at, n.updated_at, n.completed_at,
                       n.session_id, n.parent_note_id, n.context,
                       c.name as category_name
                FROM ami_documentation.notes n
                JOIN ami_documentation.note_categories c ON c.id = n.category_id
                WHERE n.id = $1
            """, note_id)
            
            if not note:
                return None
            
            # Получаем теги заметки
            tags = await conn.fetch("""
                SELECT t.name
                FROM ami_documentation.tags t
                JOIN ami_documentation.note_tags nt ON nt.tag_id = t.id
                WHERE nt.note_id = $1
            """, note_id)
            
            # Получаем связанные заметки
            links = await conn.fetch("""
                SELECT nl.target_note_id, nl.link_type
                FROM ami_documentation.note_links nl
                WHERE nl.source_note_id = $1
            """, note_id)
            
            result = dict(note)
            result['tags'] = [tag['name'] for tag in tags]
            result['links'] = [dict(link) for link in links]
            
            return result
    
    @staticmethod
    async def update_note(
        note_id: int,
        title: Optional[str] = None,
        content: Optional[str] = None,
        status: Optional[str] = None,
        priority: Optional[int] = None,
        category_name: Optional[str] = None,
        tags: Optional[List[str]] = None
    ) -> bool:
        """
        Обновляет информацию о заметке.
        
        Args:
            note_id: ID заметки
            title: Новый заголовок
            content: Новое содержимое
            status: Новый статус
            priority: Новый приоритет
            category_name: Новая категория
            tags: Новые теги
            
        Returns:
            True если обновление успешно, иначе False
        """
        if status and status not in NoteModel.STATUSES:
            raise ValueError(f"Неподдерживаемый статус: {status}")
        if priority and priority not in NoteModel.PRIORITIES:
            raise ValueError(f"Неподдерживаемый приоритет: {priority}")
        
        async with db_transaction() as conn:
            # Проверяем существование заметки
            exists = await conn.fetchval("""
                SELECT EXISTS(SELECT 1 FROM ami_documentation.notes WHERE id = $1)
            """, note_id)
            
            if not exists:
                return False
            
            # Обновляем базовую информацию
            update_fields = []
            update_values = []
            
            if title is not None:
                update_fields.append("title = $" + str(len(update_values) + 1))
                update_values.append(title)
            
            if content is not None:
                update_fields.append("content = $" + str(len(update_values) + 1))
                update_values.append(content)
            
            if status is not None:
                update_fields.append("status = $" + str(len(update_values) + 1))
                update_values.append(status)
                if status == "completed":
                    update_fields.append("completed_at = CURRENT_TIMESTAMP")
            
            if priority is not None:
                update_fields.append("priority = $" + str(len(update_values) + 1))
                update_values.append(priority)
            
            if category_name is not None:
                category_id = await conn.fetchval("""
                    SELECT id FROM ami_documentation.note_categories
                    WHERE name = $1
                """, category_name)
                
                if not category_id:
                    raise ValueError(f"Категория {category_name} не найдена")
                
                update_fields.append("category_id = $" + str(len(update_values) + 1))
                update_values.append(category_id)
            
            if update_fields:
                update_query = "UPDATE ami_documentation.notes SET " + ", ".join(update_fields)
                update_query += f", updated_at = CURRENT_TIMESTAMP WHERE id = ${len(update_values) + 1}"
                update_values.append(note_id)
                
                await conn.execute(update_query, *update_values)
            
            # Обновляем теги, если они указаны
            if tags is not None:
                # Удаляем старые теги
                await conn.execute("""
                    DELETE FROM ami_documentation.note_tags
                    WHERE note_id = $1
                """, note_id)
                
                # Добавляем новые теги
                for tag_name in tags:
                    tag_id = await conn.fetchval("""
                        INSERT INTO ami_documentation.tags(name)
                        VALUES($1)
                        ON CONFLICT (name) DO UPDATE SET name = $1
                        RETURNING id
                    """, tag_name)
                    
                    await conn.execute("""
                        INSERT INTO ami_documentation.note_tags(note_id, tag_id)
                        VALUES($1, $2)
                        ON CONFLICT DO NOTHING
                    """, note_id, tag_id)
            
            return True
    
    @staticmethod
    async def link_notes(
        source_note_id: int,
        target_note_id: int,
        link_type: str
    ) -> bool:
        """
        Создает связь между заметками.
        
        Args:
            source_note_id: ID исходной заметки
            target_note_id: ID целевой заметки
            link_type: Тип связи
            
        Returns:
            True если связь создана, иначе False
        """
        if link_type not in NoteModel.LINK_TYPES:
            raise ValueError(f"Неподдерживаемый тип связи: {link_type}")
        
        async with db_transaction() as conn:
            try:
                await conn.execute("""
                    INSERT INTO ami_documentation.note_links(
                        source_note_id, target_note_id, link_type
                    )
                    VALUES($1, $2, $3)
                """, source_note_id, target_note_id, link_type)
                return True
            except asyncpg.UniqueViolationError:
                return False
    
    @staticmethod
    async def search_notes(
        query: Optional[str] = None,
        category: Optional[str] = None,
        status: Optional[str] = None,
        priority: Optional[int] = None,
        tags: Optional[List[str]] = None,
        session_id: Optional[str] = None,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """
        Поиск заметок по различным критериям.
        
        Args:
            query: Поисковый запрос (ищется в заголовке и содержимом)
            category: Категория заметок
            status: Статус заметок
            priority: Приоритет заметок
            tags: Список тегов
            session_id: ID сессии
            limit: Максимальное количество результатов
            
        Returns:
            Список найденных заметок
        """
        async with db_transaction() as conn:
            conditions = []
            values = []
            param_count = 0
            
            if query:
                param_count += 1
                conditions.append(f"(n.title ILIKE ${param_count} OR n.content ILIKE ${param_count})")
                values.append(f"%{query}%")
            
            if category:
                param_count += 1
                conditions.append(f"c.name = ${param_count}")
                values.append(category)
            
            if status:
                param_count += 1
                conditions.append(f"n.status = ${param_count}")
                values.append(status)
            
            if priority is not None:
                param_count += 1
                conditions.append(f"n.priority = ${param_count}")
                values.append(priority)
            
            if session_id:
                param_count += 1
                conditions.append(f"n.session_id = ${param_count}")
                values.append(session_id)
            
            if tags:
                param_count += 1
                conditions.append(f"""
                    EXISTS (
                        SELECT 1 FROM ami_documentation.note_tags nt
                        JOIN ami_documentation.tags t ON t.id = nt.tag_id
                        WHERE nt.note_id = n.id AND t.name = ANY(${param_count})
                    )
                """)
                values.append(tags)
            
            where_clause = " AND ".join(conditions) if conditions else "TRUE"
            
            notes = await conn.fetch(f"""
                SELECT n.id, n.title, n.content, n.status, n.priority,
                       n.created_at, n.updated_at, n.completed_at,
                       n.session_id, n.parent_note_id, n.context,
                       c.name as category_name
                FROM ami_documentation.notes n
                JOIN ami_documentation.note_categories c ON c.id = n.category_id
                WHERE {where_clause}
                ORDER BY n.created_at DESC
                LIMIT ${param_count + 1}
            """, *values, limit)
            
            return [dict(note) for note in notes] 