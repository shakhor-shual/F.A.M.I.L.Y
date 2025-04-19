"""
Note handler module for F.A.M.I.L.Y. MCP Documentation Server.

This module provides handlers for working with development notes through the MCP protocol.
It implements the AMI memory system's note management functionality.
"""

import logging
import json
from typing import Dict, Any, Optional, List
from datetime import datetime

from models.mcp_types import MCPMessage, MCPError, DateTimeEncoder
from models.notes import NoteModel

logger = logging.getLogger(__name__)

class NoteHandler:
    """
    Обработчик для работы с заметками через MCP протокол.
    
    Реализует функциональность сознательного уровня памяти АМИ
    через управление заметками о процессе разработки.
    """
    
    @staticmethod
    async def handle_create_note(message: MCPMessage) -> MCPMessage:
        """
        Обрабатывает запрос на создание заметки.
        
        Args:
            message: MCP сообщение с данными для создания заметки
            
        Returns:
            MCP сообщение с результатом операции
        """
        try:
            content = message.content
            
            # Проверяем обязательные поля
            required_fields = ['title', 'content', 'category']
            for field in required_fields:
                if field not in content:
                    return MCPMessage.create(
                        type="error",
                        content={
                            "code": "MISSING_FIELD",
                            "message": f"Отсутствует обязательное поле: {field}"
                        }
                    )
            
            # Создаем заметку
            note_id = await NoteModel.create_note(
                title=content['title'],
                content=content['content'],
                category_name=content['category'],
                status=content.get('status', 'active'),
                priority=content.get('priority', 0),
                session_id=content.get('session_id'),
                parent_note_id=content.get('parent_note_id'),
                context=content.get('context'),
                tags=content.get('tags')
            )
            
            return MCPMessage.create(
                type="note_created",
                content={"note_id": note_id}
            )
            
        except Exception as e:
            logger.error(f"Ошибка при создании заметки: {str(e)}")
            return MCPMessage.create(
                type="error",
                content={
                    "code": "CREATE_NOTE_ERROR",
                    "message": str(e)
                }
            )
    
    @staticmethod
    async def handle_get_note(message: MCPMessage) -> MCPMessage:
        """
        Обрабатывает запрос на получение информации о заметке.
        
        Args:
            message: MCP сообщение с ID заметки
            
        Returns:
            MCP сообщение с информацией о заметке
        """
        try:
            content = message.content
            
            if 'note_id' not in content:
                return MCPMessage.create(
                    type="error",
                    content={
                        "code": "MISSING_FIELD",
                        "message": "Отсутствует обязательное поле: note_id"
                    }
                )
            
            note = await NoteModel.get_note(content['note_id'])
            
            if not note:
                return MCPMessage.create(
                    type="error",
                    content={
                        "code": "NOTE_NOT_FOUND",
                        "message": f"Заметка с ID {content['note_id']} не найдена"
                    }
                )
            
            # Преобразуем datetime объекты в строки
            serializable_note = json.loads(json.dumps(note, cls=DateTimeEncoder))
            
            return MCPMessage.create(
                type="note_info",
                content=serializable_note
            )
            
        except Exception as e:
            logger.error(f"Ошибка при получении заметки: {str(e)}")
            return MCPMessage.create(
                type="error",
                content={
                    "code": "GET_NOTE_ERROR",
                    "message": str(e)
                }
            )
    
    @staticmethod
    async def handle_update_note(message: MCPMessage) -> MCPMessage:
        """
        Обрабатывает запрос на обновление заметки.
        
        Args:
            message: MCP сообщение с данными для обновления
            
        Returns:
            MCP сообщение с результатом операции
        """
        try:
            content = message.content
            
            if 'note_id' not in content:
                return MCPMessage.create(
                    type="error",
                    content={
                        "code": "MISSING_FIELD",
                        "message": "Отсутствует обязательное поле: note_id"
                    }
                )
            
            success = await NoteModel.update_note(
                note_id=content['note_id'],
                title=content.get('title'),
                content=content.get('content'),
                status=content.get('status'),
                priority=content.get('priority'),
                category_name=content.get('category'),
                tags=content.get('tags')
            )
            
            if not success:
                return MCPMessage.create(
                    type="error",
                    content={
                        "code": "NOTE_NOT_FOUND",
                        "message": f"Заметка с ID {content['note_id']} не найдена"
                    }
                )
            
            return MCPMessage.create(
                type="note_updated",
                content={"note_id": content['note_id']}
            )
            
        except Exception as e:
            logger.error(f"Ошибка при обновлении заметки: {str(e)}")
            return MCPMessage.create(
                type="error",
                content={
                    "code": "UPDATE_NOTE_ERROR",
                    "message": str(e)
                }
            )
    
    @staticmethod
    async def handle_link_notes(message: MCPMessage) -> MCPMessage:
        """
        Обрабатывает запрос на создание связи между заметками.
        
        Args:
            message: MCP сообщение с данными для создания связи
            
        Returns:
            MCP сообщение с результатом операции
        """
        try:
            content = message.content
            
            required_fields = ['source_note_id', 'target_note_id', 'link_type']
            for field in required_fields:
                if field not in content:
                    return MCPMessage.create(
                        type="error",
                        content={
                            "code": "MISSING_FIELD",
                            "message": f"Отсутствует обязательное поле: {field}"
                        }
                    )
            
            success = await NoteModel.link_notes(
                source_note_id=content['source_note_id'],
                target_note_id=content['target_note_id'],
                link_type=content['link_type']
            )
            
            if not success:
                return MCPMessage.create(
                    type="error",
                    content={
                        "code": "LINK_EXISTS",
                        "message": "Связь между заметками уже существует"
                    }
                )
            
            return MCPMessage.create(
                type="notes_linked",
                content={
                    "source_note_id": content['source_note_id'],
                    "target_note_id": content['target_note_id'],
                    "link_type": content['link_type']
                }
            )
            
        except Exception as e:
            logger.error(f"Ошибка при создании связи между заметками: {str(e)}")
            return MCPMessage.create(
                type="error",
                content={
                    "code": "LINK_NOTES_ERROR",
                    "message": str(e)
                }
            )
    
    @staticmethod
    async def handle_search_notes(message: MCPMessage) -> MCPMessage:
        """
        Обрабатывает запрос на поиск заметок.
        
        Args:
            message: MCP сообщение с параметрами поиска
            
        Returns:
            MCP сообщение с результатами поиска
        """
        try:
            content = message.content
            
            notes = await NoteModel.search_notes(
                query=content.get('query'),
                category=content.get('category'),
                status=content.get('status'),
                priority=content.get('priority'),
                tags=content.get('tags'),
                session_id=content.get('session_id')
            )
            
            return MCPMessage.create(
                type="search_results",
                content={"notes": notes}
            )
            
        except Exception as e:
            logger.error(f"Ошибка при поиске заметок: {str(e)}")
            return MCPMessage.create(
                type="error",
                content={
                    "code": "SEARCH_NOTES_ERROR",
                    "message": str(e)
                }
            )
    
    @staticmethod
    async def handle_create_category(message: MCPMessage) -> MCPMessage:
        """
        Обрабатывает запрос на создание категории заметок.
        
        Args:
            message: MCP сообщение с данными категории
            
        Returns:
            MCP сообщение с результатом операции
        """
        try:
            content = message.content
            
            if 'name' not in content:
                return MCPMessage.create(
                    type="error",
                    content={
                        "code": "MISSING_FIELD",
                        "message": "Отсутствует обязательное поле: name"
                    }
                )
            
            category_id = await NoteModel.create_category(
                name=content['name'],
                description=content.get('description')
            )
            
            return MCPMessage.create(
                type="category_created",
                content={"category_id": category_id}
            )
            
        except Exception as e:
            logger.error(f"Ошибка при создании категории: {str(e)}")
            return MCPMessage.create(
                type="error",
                content={
                    "code": "CREATE_CATEGORY_ERROR",
                    "message": str(e)
                }
            )
    
    @staticmethod
    async def handle_create_tag(message: MCPMessage) -> MCPMessage:
        """
        Обрабатывает запрос на создание тега.
        
        Args:
            message: MCP сообщение с данными тега
            
        Returns:
            MCP сообщение с результатом операции
        """
        try:
            content = message.content
            
            if 'name' not in content:
                return MCPMessage.create(
                    type="error",
                    content={
                        "code": "MISSING_FIELD",
                        "message": "Отсутствует обязательное поле: name"
                    }
                )
            
            tag_id = await NoteModel.create_tag(
                name=content['name'],
                description=content.get('description')
            )
            
            return MCPMessage.create(
                type="tag_created",
                content={"tag_id": tag_id}
            )
            
        except Exception as e:
            logger.error(f"Ошибка при создании тега: {str(e)}")
            return MCPMessage.create(
                type="error",
                content={
                    "code": "CREATE_TAG_ERROR",
                    "message": str(e)
                }
            ) 