"""
MCP (Model Context Protocol) Handler для сервера документации F.A.M.I.L.Y.

Этот модуль обеспечивает интерфейс для взаимодействия с сервером документации
через протокол MCP, что позволяет АМИ самостоятельно получать доступ к документации.

MCP-интерфейс транслирует запросы в вызовы к существующим REST API методам работы с диаграммами.

Integration Points:
    - Использует DiagramModel для доступа к диаграммам
    - Преобразует запросы MCP в вызовы DiagramHandler
    - Интегрируется с сознательным уровнем памяти АМИ
"""

import json
import logging
import uuid
from typing import Dict, Any, Optional, List, Union
from aiohttp import web
from models.diagram import DiagramModel

# Настройка логирования
logger = logging.getLogger(__name__)

class MCPHandler:
    """
    Обработчик MCP-протокола для сервера документации.
    
    Обеспечивает интерфейс для взаимодействия с сервером документации через
    протокол MCP (Model Context Protocol), что позволяет АМИ самостоятельно
    получать доступ к документации и обновлять её.
    
    Integration Points:
        - Использует модель DiagramModel для работы с данными
        - Интегрируется с многоуровневой моделью памяти АМИ
        - Обеспечивает механизм верификации и доверия к документации
    """
    
    # Доступные MCP-операции
    OPERATIONS = {
        "get_diagrams": "Получить список диаграмм",
        "get_diagram": "Получить диаграмму по ID",
        "create_diagram": "Создать новую диаграмму",
        "update_diagram": "Обновить существующую диаграмму",
        "verify_diagram": "Верифицировать диаграмму",
        "search_diagrams": "Поиск диаграмм по запросу",
        "get_diagrams_by_type": "Получить диаграммы определенного типа"
    }
    
    @staticmethod
    async def handle_mcp_request(request: web.Request) -> web.Response:
        """
        Обрабатывает MCP-запрос от АМИ.
        
        Args:
            request: HTTP запрос с MCP-сообщением
            
        Returns:
            Ответ в формате MCP
        """
        try:
            # Получаем данные запроса
            data = await request.json()
            
            # Проверяем наличие обязательных полей
            if 'operation' not in data:
                return MCPHandler._create_error_response("Не указана операция MCP")
                
            operation = data['operation']
            
            # Проверяем существование операции
            if operation not in MCPHandler.OPERATIONS:
                return MCPHandler._create_error_response(f"Неизвестная операция: {operation}")
            
            # Вызываем соответствующий обработчик
            if operation == "get_diagrams":
                return await MCPHandler._handle_get_diagrams(data.get('params', {}))
            elif operation == "get_diagram":
                return await MCPHandler._handle_get_diagram(data.get('params', {}))
            elif operation == "create_diagram":
                return await MCPHandler._handle_create_diagram(data.get('params', {}))
            elif operation == "update_diagram":
                return await MCPHandler._handle_update_diagram(data.get('params', {}))
            elif operation == "verify_diagram":
                return await MCPHandler._handle_verify_diagram(data.get('params', {}))
            elif operation == "search_diagrams":
                return await MCPHandler._handle_search_diagrams(data.get('params', {}))
            elif operation == "get_diagrams_by_type":
                return await MCPHandler._handle_get_diagrams_by_type(data.get('params', {}))
            else:
                return MCPHandler._create_error_response(f"Операция {operation} не реализована")
                
        except json.JSONDecodeError:
            return MCPHandler._create_error_response("Неверный формат JSON")
        except Exception as e:
            logger.error(f"Ошибка при обработке MCP-запроса: {str(e)}")
            return MCPHandler._create_error_response(f"Ошибка сервера: {str(e)}")
    
    @staticmethod
    async def _handle_get_diagrams(params: Dict[str, Any]) -> web.Response:
        """
        Обрабатывает MCP-запрос на получение списка диаграмм.
        
        Args:
            params: Параметры запроса
            
        Returns:
            Ответ в формате MCP со списком диаграмм
        """
        try:
            diagrams = await DiagramModel.get_all_diagrams()
            
            # Преобразуем datetime в строки для JSON-сериализации
            for diagram in diagrams:
                if diagram.get('created_at'):
                    diagram['created_at'] = diagram['created_at'].isoformat()
                if diagram.get('last_verified_at'):
                    diagram['last_verified_at'] = diagram['last_verified_at'].isoformat()
            
            return MCPHandler._create_success_response({
                'diagrams': diagrams,
                'count': len(diagrams)
            })
        except Exception as e:
            logger.error(f"Ошибка при получении списка диаграмм: {str(e)}")
            return MCPHandler._create_error_response(f"Не удалось получить список диаграмм: {str(e)}")
    
    @staticmethod
    async def _handle_get_diagram(params: Dict[str, Any]) -> web.Response:
        """
        Обрабатывает MCP-запрос на получение диаграммы по ID.
        
        Args:
            params: Параметры запроса (должен содержать diagram_id)
            
        Returns:
            Ответ в формате MCP с информацией о диаграмме
        """
        # Проверяем наличие обязательных параметров
        if 'diagram_id' not in params:
            return MCPHandler._create_error_response("Не указан ID диаграммы")
            
        try:
            diagram_id = int(params['diagram_id'])
        except ValueError:
            return MCPHandler._create_error_response("Неверный формат ID диаграммы")
            
        try:
            diagram = await DiagramModel.get_diagram(diagram_id)
            
            if not diagram:
                return MCPHandler._create_error_response(f"Диаграмма с ID {diagram_id} не найдена")
            
            # Преобразуем datetime в строки для JSON-сериализации
            if diagram.get('created_at'):
                diagram['created_at'] = diagram['created_at'].isoformat()
            if diagram.get('last_verified_at'):
                diagram['last_verified_at'] = diagram['last_verified_at'].isoformat()
            
            return MCPHandler._create_success_response({'diagram': diagram})
        except Exception as e:
            logger.error(f"Ошибка при получении диаграммы: {str(e)}")
            return MCPHandler._create_error_response(f"Не удалось получить диаграмму: {str(e)}")
    
    @staticmethod
    async def _handle_create_diagram(params: Dict[str, Any]) -> web.Response:
        """
        Обрабатывает MCP-запрос на создание новой диаграммы.
        
        Args:
            params: Параметры запроса с информацией о диаграмме
            
        Returns:
            Ответ в формате MCP с результатом создания диаграммы
        """
        # Проверяем наличие обязательных параметров
        required_fields = ['name', 'description', 'diagram_type', 'content']
        for field in required_fields:
            if field not in params:
                return MCPHandler._create_error_response(f"Отсутствует обязательный параметр: {field}")
                
        name = params['name']
        description = params['description']
        diagram_type = params['diagram_type']
        content = params['content']
        is_json = params.get('is_json', True)
        
        try:
            diagram_id = await DiagramModel.create_diagram(
                name=name,
                description=description,
                diagram_type=diagram_type,
                content=content,
                is_json=is_json
            )
            
            logger.info(f"MCP: Создана новая диаграмма: {name} (ID: {diagram_id})")
            
            return MCPHandler._create_success_response({
                'message': 'Диаграмма успешно создана',
                'diagram_id': diagram_id
            })
        except ValueError as e:
            logger.error(f"Ошибка валидации данных диаграммы: {str(e)}")
            return MCPHandler._create_error_response(str(e))
        except Exception as e:
            logger.error(f"Ошибка при создании диаграммы: {str(e)}")
            return MCPHandler._create_error_response(f"Не удалось создать диаграмму: {str(e)}")
    
    @staticmethod
    async def _handle_update_diagram(params: Dict[str, Any]) -> web.Response:
        """
        Обрабатывает MCP-запрос на обновление существующей диаграммы.
        
        Args:
            params: Параметры запроса с информацией для обновления
            
        Returns:
            Ответ в формате MCP с результатом обновления диаграммы
        """
        # Проверяем наличие обязательных параметров
        if 'diagram_id' not in params:
            return MCPHandler._create_error_response("Не указан ID диаграммы")
            
        try:
            diagram_id = int(params['diagram_id'])
        except ValueError:
            return MCPHandler._create_error_response("Неверный формат ID диаграммы")
            
        name = params.get('name')
        description = params.get('description')
        content = params.get('content')
        
        if not any([name, description, content]):
            return MCPHandler._create_error_response("Не указаны данные для обновления")
            
        try:
            success = await DiagramModel.update_diagram(
                diagram_id=diagram_id,
                name=name,
                description=description,
                content=content
            )
            
            if not success:
                return MCPHandler._create_error_response(f"Диаграмма с ID {diagram_id} не найдена")
            
            logger.info(f"MCP: Диаграмма с ID {diagram_id} успешно обновлена")
            
            return MCPHandler._create_success_response({
                'message': 'Диаграмма успешно обновлена'
            })
        except Exception as e:
            logger.error(f"Ошибка при обновлении диаграммы: {str(e)}")
            return MCPHandler._create_error_response(f"Не удалось обновить диаграмму: {str(e)}")
    
    @staticmethod
    async def _handle_verify_diagram(params: Dict[str, Any]) -> web.Response:
        """
        Обрабатывает MCP-запрос на верификацию диаграммы.
        
        Args:
            params: Параметры запроса с информацией для верификации
            
        Returns:
            Ответ в формате MCP с результатом верификации диаграммы
        """
        # Проверяем наличие обязательных параметров
        required_fields = ['diagram_id', 'verified_by', 'status']
        for field in required_fields:
            if field not in params:
                return MCPHandler._create_error_response(f"Отсутствует обязательный параметр: {field}")
                
        try:
            diagram_id = int(params['diagram_id'])
        except ValueError:
            return MCPHandler._create_error_response("Неверный формат ID диаграммы")
            
        verified_by = params['verified_by']
        status = params['status']
        notes = params.get('notes')
        
        try:
            success = await DiagramModel.verify_diagram(
                diagram_id=diagram_id,
                verified_by=verified_by,
                status=status,
                notes=notes
            )
            
            if not success:
                return MCPHandler._create_error_response(f"Диаграмма с ID {diagram_id} не найдена")
            
            logger.info(f"MCP: Диаграмма с ID {diagram_id} верифицирована со статусом {status}")
            
            return MCPHandler._create_success_response({
                'message': f'Диаграмма верифицирована со статусом {status}'
            })
        except ValueError as e:
            logger.error(f"Ошибка при верификации диаграммы: {str(e)}")
            return MCPHandler._create_error_response(str(e))
        except Exception as e:
            logger.error(f"Ошибка при верификации диаграммы: {str(e)}")
            return MCPHandler._create_error_response(f"Не удалось верифицировать диаграмму: {str(e)}")
    
    @staticmethod
    async def _handle_search_diagrams(params: Dict[str, Any]) -> web.Response:
        """
        Обрабатывает MCP-запрос на поиск диаграмм.
        
        Args:
            params: Параметры запроса с поисковым запросом
            
        Returns:
            Ответ в формате MCP со списком найденных диаграмм
        """
        # Проверяем наличие обязательных параметров
        if 'query' not in params:
            return MCPHandler._create_error_response("Не указан поисковый запрос")
            
        query = params['query']
        
        try:
            diagrams = await DiagramModel.search_diagrams(query)
            
            # Преобразуем datetime в строки для JSON-сериализации
            for diagram in diagrams:
                if diagram.get('created_at'):
                    diagram['created_at'] = diagram['created_at'].isoformat()
                if diagram.get('last_verified_at'):
                    diagram['last_verified_at'] = diagram['last_verified_at'].isoformat()
            
            return MCPHandler._create_success_response({
                'diagrams': diagrams,
                'count': len(diagrams)
            })
        except Exception as e:
            logger.error(f"Ошибка при поиске диаграмм: {str(e)}")
            return MCPHandler._create_error_response(f"Не удалось выполнить поиск диаграмм: {str(e)}")
    
    @staticmethod
    async def _handle_get_diagrams_by_type(params: Dict[str, Any]) -> web.Response:
        """
        Обрабатывает MCP-запрос на получение диаграмм определенного типа.
        
        Args:
            params: Параметры запроса с типом диаграмм
            
        Returns:
            Ответ в формате MCP со списком диаграмм указанного типа
        """
        # Проверяем наличие обязательных параметров
        if 'diagram_type' not in params:
            return MCPHandler._create_error_response("Не указан тип диаграмм")
            
        diagram_type = params['diagram_type']
        
        try:
            diagrams = await DiagramModel.get_diagrams_by_type(diagram_type)
            
            # Преобразуем datetime в строки для JSON-сериализации
            for diagram in diagrams:
                if diagram.get('created_at'):
                    diagram['created_at'] = diagram['created_at'].isoformat()
                if diagram.get('last_verified_at'):
                    diagram['last_verified_at'] = diagram['last_verified_at'].isoformat()
            
            return MCPHandler._create_success_response({
                'diagrams': diagrams,
                'count': len(diagrams)
            })
        except ValueError as e:
            logger.error(f"Ошибка при получении диаграмм по типу: {str(e)}")
            return MCPHandler._create_error_response(str(e))
        except Exception as e:
            logger.error(f"Ошибка при получении диаграмм по типу: {str(e)}")
            return MCPHandler._create_error_response(f"Не удалось получить диаграммы: {str(e)}")
    
    @staticmethod
    def _create_success_response(data: Dict[str, Any]) -> web.Response:
        """
        Создает успешный ответ в формате MCP.
        
        Args:
            data: Данные для включения в ответ
            
        Returns:
            Ответ в формате MCP
        """
        response = {
            'status': 'success',
            'request_id': str(uuid.uuid4()),
            'timestamp': MCPHandler._get_iso_timestamp(),
            'data': data
        }
        
        return web.json_response(response)
    
    @staticmethod
    def _create_error_response(error_message: str) -> web.Response:
        """
        Создает ответ об ошибке в формате MCP.
        
        Args:
            error_message: Сообщение об ошибке
            
        Returns:
            Ответ в формате MCP
        """
        response = {
            'status': 'error',
            'request_id': str(uuid.uuid4()),
            'timestamp': MCPHandler._get_iso_timestamp(),
            'error': {
                'message': error_message
            }
        }
        
        return web.json_response(response, status=400)
    
    @staticmethod
    def _get_iso_timestamp() -> str:
        """
        Возвращает текущее время в формате ISO.
        
        Returns:
            Текущее время в формате ISO
        """
        from datetime import datetime
        return datetime.utcnow().isoformat()
    
    @staticmethod
    async def setup_routes(app: web.Application):
        """
        Настраивает маршруты для MCP-обработчика.
        
        Args:
            app: Экземпляр приложения aiohttp
        """
        # Эндпоинт для MCP-запросов
        app.router.add_post('/mcp', MCPHandler.handle_mcp_request)
        
        # Добавляем опциональный эндпоинт для совместимости с другими MCP-системами
        app.router.add_post('/mcp/v1/query', MCPHandler.handle_mcp_request)