"""
Diagram API handler module for F.A.M.I.L.Y. MCP Documentation Server.

This module provides HTTP API endpoints for working with documentation diagrams.
It implements RESTful interfaces for diagram management and integrates with the
diagram model to ensure proper memory system integration.
"""

import logging
import json
from typing import Dict, Any, List, Optional, Union
from aiohttp import web

# Исправленный импорт на локальный путь
from models.diagram import DiagramModel

# Настройка логирования
logger = logging.getLogger(__name__)

class DiagramHandler:
    """
    Обработчик HTTP-запросов для взаимодействия с диаграммами документации.
    
    Предоставляет RESTful API для работы с системой документации проекта F.A.M.I.L.Y.
    
    Integration Points:
        - Использует DiagramModel для работы с данными диаграмм
        - Интегрируется с системой памяти АМИ через механизм верификации
        - Предоставляет API для внешних систем и интерфейсов
    """
    
    @staticmethod
    async def get_all_diagrams(request: web.Request) -> web.Response:
        """
        Получает список всех диаграмм.
        
        GET /api/diagrams
        
        Optional Query Parameters:
            - type: Фильтр по типу диаграммы
            - query: Поисковый запрос
            
        Returns:
            JSON с массивом диаграмм
        """
        try:
            diagram_type = request.query.get('type')
            search_query = request.query.get('query')
            
            if diagram_type:
                diagrams = await DiagramModel.get_diagrams_by_type(diagram_type)
            elif search_query:
                diagrams = await DiagramModel.search_diagrams(search_query)
            else:
                diagrams = await DiagramModel.get_all_diagrams()
            
            # Преобразуем datetime в строки для JSON-сериализации
            for diagram in diagrams:
                if diagram.get('created_at'):
                    diagram['created_at'] = diagram['created_at'].isoformat()
                if diagram.get('last_verified_at'):
                    diagram['last_verified_at'] = diagram['last_verified_at'].isoformat()
            
            return web.json_response({
                'success': True,
                'diagrams': diagrams,
                'count': len(diagrams)
            })
        
        except ValueError as e:
            logger.error(f"Ошибка в параметрах запроса: {str(e)}")
            return web.json_response({
                'success': False,
                'error': str(e)
            }, status=400)
        
        except Exception as e:
            logger.error(f"Ошибка при получении списка диаграмм: {str(e)}")
            return web.json_response({
                'success': False,
                'error': 'Ошибка сервера при получении списка диаграмм'
            }, status=500)
    
    @staticmethod
    async def get_diagram(request: web.Request) -> web.Response:
        """
        Получает информацию о диаграмме по ID.
        
        GET /api/diagrams/{diagram_id}
        
        Path Parameters:
            - diagram_id: ID диаграммы
            
        Returns:
            JSON с информацией о диаграмме
        """
        try:
            diagram_id = int(request.match_info['diagram_id'])
            diagram = await DiagramModel.get_diagram(diagram_id)
            
            if not diagram:
                return web.json_response({
                    'success': False,
                    'error': f'Диаграмма с ID {diagram_id} не найдена'
                }, status=404)
            
            # Преобразуем datetime в строки для JSON-сериализации
            if diagram.get('created_at'):
                diagram['created_at'] = diagram['created_at'].isoformat()
            if diagram.get('last_verified_at'):
                diagram['last_verified_at'] = diagram['last_verified_at'].isoformat()
            
            return web.json_response({
                'success': True,
                'diagram': diagram
            })
        
        except ValueError:
            return web.json_response({
                'success': False,
                'error': 'Неверный формат ID диаграммы'
            }, status=400)
        
        except Exception as e:
            logger.error(f"Ошибка при получении диаграммы: {str(e)}")
            return web.json_response({
                'success': False,
                'error': 'Ошибка сервера при получении диаграммы'
            }, status=500)
    
    @staticmethod
    async def create_diagram(request: web.Request) -> web.Response:
        """
        Создает новую диаграмму.
        
        POST /api/diagrams
        
        Request Body (JSON):
            - name: Имя диаграммы
            - description: Описание диаграммы
            - diagram_type: Тип диаграммы
            - content: Содержимое диаграммы
            - content_type: Тип содержимого ('json' или 'xml')
            
        Returns:
            JSON с ID созданной диаграммы
        """
        try:
            data = await request.json()
            
            required_fields = ['name', 'description', 'diagram_type', 'content']
            for field in required_fields:
                if field not in data:
                    return web.json_response({
                        'success': False,
                        'error': f'Отсутствует обязательное поле: {field}'
                    }, status=400)
            
            name = data['name']
            description = data['description']
            diagram_type = data['diagram_type']
            content = data['content']
            content_type = data.get('content_type', 'json')
            
            is_json = content_type.lower() == 'json'
            
            diagram_id = await DiagramModel.create_diagram(
                name=name,
                description=description,
                diagram_type=diagram_type,
                content=content,
                is_json=is_json
            )
            
            logger.info(f"Создана новая диаграмма: {name} (ID: {diagram_id})")
            
            return web.json_response({
                'success': True,
                'message': 'Диаграмма успешно создана',
                'diagram_id': diagram_id
            }, status=201)
        
        except ValueError as e:
            logger.error(f"Ошибка валидации данных диаграммы: {str(e)}")
            return web.json_response({
                'success': False,
                'error': str(e)
            }, status=400)
        
        except json.JSONDecodeError:
            logger.error("Ошибка декодирования JSON")
            return web.json_response({
                'success': False,
                'error': 'Неверный формат JSON'
            }, status=400)
        
        except Exception as e:
            logger.error(f"Ошибка при создании диаграммы: {str(e)}")
            return web.json_response({
                'success': False,
                'error': 'Ошибка сервера при создании диаграммы'
            }, status=500)
    
    @staticmethod
    async def update_diagram(request: web.Request) -> web.Response:
        """
        Обновляет существующую диаграмму.
        
        PUT /api/diagrams/{diagram_id}
        
        Path Parameters:
            - diagram_id: ID диаграммы
            
        Request Body (JSON):
            - name: Новое имя диаграммы (опционально)
            - description: Новое описание диаграммы (опционально)
            - content: Новое содержимое диаграммы (опционально)
            
        Returns:
            JSON с результатом обновления
        """
        try:
            diagram_id = int(request.match_info['diagram_id'])
            data = await request.json()
            
            name = data.get('name')
            description = data.get('description')
            content = data.get('content')
            
            if not any([name, description, content]):
                return web.json_response({
                    'success': False,
                    'error': 'Не указаны поля для обновления'
                }, status=400)
            
            success = await DiagramModel.update_diagram(
                diagram_id=diagram_id,
                name=name,
                description=description,
                content=content
            )
            
            if not success:
                return web.json_response({
                    'success': False,
                    'error': f'Диаграмма с ID {diagram_id} не найдена'
                }, status=404)
            
            logger.info(f"Диаграмма с ID {diagram_id} успешно обновлена")
            
            return web.json_response({
                'success': True,
                'message': 'Диаграмма успешно обновлена'
            })
        
        except ValueError:
            return web.json_response({
                'success': False,
                'error': 'Неверный формат ID диаграммы'
            }, status=400)
        
        except json.JSONDecodeError:
            return web.json_response({
                'success': False,
                'error': 'Неверный формат JSON'
            }, status=400)
        
        except Exception as e:
            logger.error(f"Ошибка при обновлении диаграммы: {str(e)}")
            return web.json_response({
                'success': False,
                'error': 'Ошибка сервера при обновлении диаграммы'
            }, status=500)
    
    @staticmethod
    async def delete_diagram(request: web.Request) -> web.Response:
        """
        Удаляет диаграмму.
        
        DELETE /api/diagrams/{diagram_id}
        
        Path Parameters:
            - diagram_id: ID диаграммы
            
        Returns:
            JSON с результатом удаления
        """
        try:
            diagram_id = int(request.match_info['diagram_id'])
            
            success = await DiagramModel.delete_diagram(diagram_id)
            
            if not success:
                return web.json_response({
                    'success': False,
                    'error': f'Диаграмма с ID {diagram_id} не найдена'
                }, status=404)
            
            logger.info(f"Диаграмма с ID {diagram_id} успешно удалена")
            
            return web.json_response({
                'success': True,
                'message': 'Диаграмма успешно удалена'
            })
        
        except ValueError:
            return web.json_response({
                'success': False,
                'error': 'Неверный формат ID диаграммы'
            }, status=400)
        
        except Exception as e:
            logger.error(f"Ошибка при удалении диаграммы: {str(e)}")
            return web.json_response({
                'success': False,
                'error': 'Ошибка сервера при удалении диаграммы'
            }, status=500)
    
    @staticmethod
    async def verify_diagram(request: web.Request) -> web.Response:
        """
        Верифицирует диаграмму.
        
        POST /api/diagrams/{diagram_id}/verify
        
        Path Parameters:
            - diagram_id: ID диаграммы
            
        Request Body (JSON):
            - verified_by: Имя верифицирующего (человек или АМИ)
            - status: Статус верификации ('approved', 'rejected', 'needs_revision')
            - notes: Заметки о верификации (опционально)
            
        Returns:
            JSON с результатом верификации
        """
        try:
            diagram_id = int(request.match_info['diagram_id'])
            data = await request.json()
            
            required_fields = ['verified_by', 'status']
            for field in required_fields:
                if field not in data:
                    return web.json_response({
                        'success': False,
                        'error': f'Отсутствует обязательное поле: {field}'
                    }, status=400)
            
            verified_by = data['verified_by']
            status = data['status']
            notes = data.get('notes')
            
            try:
                success = await DiagramModel.verify_diagram(
                    diagram_id=diagram_id,
                    verified_by=verified_by,
                    status=status,
                    notes=notes
                )
            except ValueError as e:
                return web.json_response({
                    'success': False,
                    'error': str(e)
                }, status=400)
            
            if not success:
                return web.json_response({
                    'success': False,
                    'error': f'Диаграмма с ID {diagram_id} не найдена'
                }, status=404)
            
            logger.info(f"Диаграмма с ID {diagram_id} верифицирована со статусом {status}")
            
            return web.json_response({
                'success': True,
                'message': f'Диаграмма верифицирована со статусом {status}'
            })
        
        except ValueError:
            return web.json_response({
                'success': False,
                'error': 'Неверный формат ID диаграммы'
            }, status=400)
        
        except json.JSONDecodeError:
            return web.json_response({
                'success': False,
                'error': 'Неверный формат JSON'
            }, status=400)
        
        except Exception as e:
            logger.error(f"Ошибка при верификации диаграммы: {str(e)}")
            return web.json_response({
                'success': False,
                'error': 'Ошибка сервера при верификации диаграммы'
            }, status=500)
    
    @staticmethod
    async def setup_routes(app: web.Application):
        """
        Настраивает маршруты API для диаграмм.
        
        Args:
            app: Экземпляр приложения aiohttp
        """
        app.router.add_get('/api/diagrams', DiagramHandler.get_all_diagrams)
        app.router.add_get('/api/diagrams/{diagram_id}', DiagramHandler.get_diagram)
        app.router.add_post('/api/diagrams', DiagramHandler.create_diagram)
        app.router.add_put('/api/diagrams/{diagram_id}', DiagramHandler.update_diagram)
        app.router.add_delete('/api/diagrams/{diagram_id}', DiagramHandler.delete_diagram)
        app.router.add_post('/api/diagrams/{diagram_id}/verify', DiagramHandler.verify_diagram)