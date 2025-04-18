#!/usr/bin/env python3
"""
Скрипт для запуска MCP-сервера документации проекта F.A.M.I.L.Y.

Этот сервер предоставляет АМИ-инженерам возможность запрашивать документацию
из базы данных PostgreSQL через Model Context Protocol (MCP).
"""

import os
import sys
import logging
from dotenv import load_dotenv

# Добавляем родительскую директорию в путь для импорта
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("mcp_server")

# Загрузка переменных окружения
load_dotenv()

# Импортируем сервер после настройки путей и логирования
from server import run_server

def main():
    """
    Основная функция для запуска MCP-сервера документации.
    """
    try:
        # Получаем настройки из переменных окружения
        host = os.environ.get('MCP_DOCS_SERVER_HOST', '0.0.0.0')
        port = int(os.environ.get('MCP_DOCS_SERVER_PORT', '8001'))
        
        logger.info(f"Запуск MCP-сервера документации на {host}:{port}")
        
        # Запускаем сервер
        run_server()
        
    except Exception as e:
        logger.error(f"Ошибка при запуске MCP-сервера документации: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()