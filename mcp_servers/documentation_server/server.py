"""
F.A.M.I.L.Y. MCP Documentation Server

Основной файл сервера документации, который интегрирует все компоненты
и предоставляет API для работы с документацией проекта F.A.M.I.L.Y.

Integration Points:
    - Интегрируется с моделью памяти АМИ через системный уровень
    - Использует базу данных как хранилище документации
    - Предоставляет API для внешнего взаимодействия
    - Поддерживает взаимодействие по протоколу MCP для АМИ-системы
"""

import os
import logging
import asyncio
from aiohttp import web
import json
import signal
import sys

# Исправленные локальные импорты
from db.connection import setup_database, close_db_pool
from handlers.diagram_handler import DiagramHandler
from handlers.mcp_handler import MCPHandler  # Добавлен импорт MCP-обработчика

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('documentation_server.log')
    ]
)
logger = logging.getLogger(__name__)

class DocumentationServer:
    """
    Сервер документации проекта F.A.M.И.L.Y.
    
    Предоставляет API для работы с диаграммами, компонентной структурой
    и другими элементами документации системы.
    
    Integration Points:
        - Использует механизм памяти АМИ для хранения документации
        - Предоставляет механизмы верификации документации
        - Интегрируется с другими серверами MCP через API
    """
    
    def __init__(self, host='0.0.0.0', port=8080):
        """
        Инициализирует сервер документации.
        
        Args:
            host: Хост для запуска сервера
            port: Порт для запуска сервера
        """
        self.host = host
        self.port = port
        self.app = web.Application()
        
        # Настройка обработчиков сигналов завершения
        self._setup_signal_handlers()
        
        # Настройка обработчиков для запуска/остановки сервера
        self.app.on_startup.append(self._setup_routes)  # Инициализация маршрутов при запуске
        self.app.on_startup.append(self._on_startup)
        self.app.on_shutdown.append(self._on_shutdown)
    
    async def _setup_routes(self, app=None):
        """
        Настраивает маршруты API сервера
        
        Args:
            app: Экземпляр приложения, передается при вызове как обработчик события
        """
        # Используем переданный экземпляр приложения или self.app
        app = app or self.app
        
        # Основные маршруты сервера
        app.router.add_get('/', self.handle_root)
        app.router.add_get('/health', self.handle_health_check)
        
        # Маршруты для работы с диаграммами
        await DiagramHandler.setup_routes(app)
        
        # Маршруты для работы с MCP
        await MCPHandler.setup_routes(app)
        
        # Статические файлы для веб-интерфейса
        app.router.add_static('/static/', path='static', name='static')
    
    def _setup_signal_handlers(self):
        """Настраивает обработчики сигналов завершения"""
        for sig in (signal.SIGINT, signal.SIGTERM):
            signal.signal(sig, self._handle_exit_signal)
    
    def _handle_exit_signal(self, sig, frame):
        """Обрабатывает сигнал завершения работы"""
        logger.info(f"Получен сигнал завершения {sig}.")
        sys.exit(0)
    
    async def _on_startup(self, app):
        """
        Выполняет действия при запуске сервера.
        
        Args:
            app: Экземпляр приложения aiohttp
        """
        logger.info("Выполняется инициализация сервера документации...")
        
        # Инициализация базы данных
        logger.info("Настройка базы данных...")
        await setup_database()
        
        logger.info(f"Сервер запущен на http://{self.host}:{self.port}")
    
    async def _on_shutdown(self, app):
        """
        Выполняет действия при остановке сервера.
        
        Args:
            app: Экземпляр приложения aiohttp
        """
        logger.info("Выполняется остановка сервера...")
        
        # Закрытие пула соединений с базой данных
        await close_db_pool()
        
        logger.info("Сервер остановлен.")
    
    async def handle_root(self, request):
        """
        Обрабатывает запрос к корневому URL.
        
        Returns:
            HTML-страница с информацией о сервере
        """
        return web.Response(
            text="""
            <html>
                <head>
                    <title>F.A.M.I.L.Y. Documentation Server</title>
                    <style>
                        body { font-family: Arial, sans-serif; margin: 40px; line-height: 1.6; }
                        h1 { color: #333; }
                        .info { background-color: #f5f5f5; padding: 20px; border-radius: 5px; }
                    </style>
                </head>
                <body>
                    <h1>F.A.M.I.L.Y. Documentation Server</h1>
                    <div class="info">
                        <p>Сервер документации проекта F.A.M.I.L.Y.</p>
                        <p>API доступно по пути: <a href="/api/diagrams">/api/diagrams</a></p>
                        <p>Проверка состояния сервера: <a href="/health">/health</a></p>
                    </div>
                </body>
            </html>
            """,
            content_type='text/html'
        )
    
    async def handle_health_check(self, request):
        """
        Обрабатывает запрос проверки состояния сервера.
        
        Returns:
            JSON с информацией о состоянии сервера
        """
        return web.json_response({
            "status": "ok",
            "service": "documentation_server",
            "version": "0.1.0"
        })
    
    def run(self):
        """Запускает сервер"""
        web.run_app(self.app, host=self.host, port=self.port, access_log=logger)

def run_server():
    """Функция для запуска сервера из командной строки"""
    # Получение настроек из переменных окружения
    host = os.environ.get('DOCS_SERVER_HOST', '0.0.0.0')
    port = int(os.environ.get('DOCS_SERVER_PORT', 8080))
    
    # Создание и запуск сервера
    server = DocumentationServer(host=host, port=port)
    server.run()

# Создаем экземпляр сервера для доступа из uvicorn
server_instance = DocumentationServer()
app = server_instance.app

if __name__ == '__main__':
    run_server()