"""
Database connection module for F.A.M.I.L.Y. MCP Documentation Server.

This module handles database connection management and configuration loading.
It implements connection pooling and context management for efficient database interactions
across the entire documentation server system.
"""

import os
import logging
import asyncpg
import configparser
from typing import Dict, Any, Optional, AsyncContextManager

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Путь к конфигурационному файлу базы данных
DB_CONFIG_PATH = os.environ.get('FAMILY_DB_CONFIG', '/home/ubuntu/FAMILY/db/family_db.conf')

# Глобальный пул соединений
_pool = None

# Загружаем конфигурацию базы данных
def load_db_config() -> Dict[str, Any]:
    """
    Загружает конфигурацию базы данных из конфигурационного файла.
    
    Returns:
        Dict содержащий параметры подключения к базе данных
    """
    logger.info(f"Загрузка конфигурации БД из {DB_CONFIG_PATH}")
    
    config = configparser.ConfigParser()
    
    try:
        config.read(DB_CONFIG_PATH)
    except Exception as e:
        logger.error(f"Ошибка при чтении конфигурационного файла: {str(e)}")
        raise
    
    # Получаем данные из конфигурационного файла
    try:
        db_config = {
            'host': config.get('postgres', 'host', fallback='localhost'),
            'port': config.getint('postgres', 'port', fallback=5432),
            'database': config.get('postgres', 'database', fallback='family_db'),
            'user': config.get('postgres', 'user', fallback='family_admin'),
            'password': config.get('postgres', 'password', fallback=''),
            'min_size': config.getint('connection_pool', 'min_size', fallback=5),
            'max_size': config.getint('connection_pool', 'max_size', fallback=20),
            'timeout': config.getfloat('connection_pool', 'timeout', fallback=30.0)
        }
    except (configparser.NoSectionError, configparser.NoOptionError) as e:
        logger.error(f"Ошибка в структуре конфигурационного файла: {str(e)}")
        # Используем значения по умолчанию
        db_config = {
            'host': 'localhost',
            'port': 5432,
            'database': 'family_db',
            'user': 'family_admin',
            'password': '',
            'min_size': 5,
            'max_size': 20,
            'timeout': 30.0
        }
    
    logger.info(f"Конфигурация БД загружена: host={db_config['host']}, port={db_config['port']}, database={db_config['database']}, user={db_config['user']}")
    
    return db_config

# Загружаем конфигурацию базы данных
DB_CONFIG = load_db_config()

async def get_db_pool() -> asyncpg.Pool:
    """
    Создает и возвращает пул соединений к базе данных.
    Пул создается при первом вызове функции и переиспользуется при последующих вызовах.
    
    Returns:
        Пул соединений к базе данных
        
    Integration Points:
        - Используется сервисами для доступа к хранилищу документации
        - Используется обработчиками API для выполнения запросов к БД
    """
    global _pool
    
    if _pool is None:
        try:
            _pool = await asyncpg.create_pool(
                host=DB_CONFIG['host'],
                port=DB_CONFIG['port'],
                user=DB_CONFIG['user'],
                password=DB_CONFIG['password'],
                database=DB_CONFIG['database'],
                min_size=DB_CONFIG['min_size'],
                max_size=DB_CONFIG['max_size'],
                timeout=DB_CONFIG['timeout']
            )
            logger.info(f"Пул соединений к БД создан успешно (min_size={DB_CONFIG['min_size']}, max_size={DB_CONFIG['max_size']})")
        except Exception as e:
            logger.error(f"Ошибка при создании пула соединений к базе данных: {str(e)}")
            raise
    
    return _pool

async def get_db_connection() -> asyncpg.Connection:
    """
    Создает подключение к базе данных с использованием пула соединений.
    
    Returns:
        Объект подключения к базе данных
        
    Note:
        Предпочтительно использовать db_transaction вместо прямого вызова этой функции
    """
    try:
        pool = await get_db_pool()
        conn = await pool.acquire()
        return conn
    except Exception as e:
        logger.error(f"Ошибка при получении соединения из пула: {str(e)}")
        raise

class DatabaseTransaction(AsyncContextManager):
    """
    Контекстный менеджер для работы с транзакциями базы данных.
    Автоматически освобождает соединение при выходе из контекста.
    
    Example:
        ```python
        async with db_transaction() as conn:
            result = await conn.fetch("SELECT * FROM ami_documentation.diagrams")
        ```
    """
    
    def __init__(self):
        self.conn = None
        self.transaction = None
    
    async def __aenter__(self) -> asyncpg.Connection:
        """
        Создает подключение к БД и начинает транзакцию.
        
        Returns:
            Объект подключения к базе данных в рамках транзакции
        """
        pool = await get_db_pool()
        self.conn = await pool.acquire()
        self.transaction = self.conn.transaction()
        await self.transaction.start()
        return self.conn
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """
        Завершает транзакцию и освобождает соединение.
        В случае ошибки выполняет откат транзакции.
        """
        try:
            if exc_type is None:
                await self.transaction.commit()
            else:
                await self.transaction.rollback()
        finally:
            pool = await get_db_pool()
            await pool.release(self.conn)

def db_transaction() -> DatabaseTransaction:
    """
    Создает контекстный менеджер для работы с транзакциями БД.
    
    Returns:
        Объект контекстного менеджера для транзакций БД
        
    Example:
        ```python
        async with db_transaction() as conn:
            await conn.execute("INSERT INTO ami_documentation.diagrams(name) VALUES($1)", "memory_model")
        ```
    """
    return DatabaseTransaction()

async def setup_database() -> None:
    """
    Создает необходимые схемы и таблицы в базе данных, если они не существуют.
    
    Integration Points:
        - Вызывается при инициализации сервера документации
        - Интегрируется с моделью памяти АМИ через схему ami_documentation
    """
    async with db_transaction() as conn:
        # Создаем схему ami_documentation, если она не существует
        await conn.execute("""
        CREATE SCHEMA IF NOT EXISTS ami_documentation;
        """)
        
        # Создаем таблицу диаграмм
        await conn.execute("""
        CREATE TABLE IF NOT EXISTS ami_documentation.diagrams (
            id SERIAL PRIMARY KEY,
            name TEXT NOT NULL,
            description TEXT,
            diagram_type TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            last_verified_at TIMESTAMP,
            confidence_level TEXT DEFAULT 'medium'
        );
        """)
        
        # Создаем таблицу для JSON-диаграмм
        await conn.execute("""
        CREATE TABLE IF NOT EXISTS ami_documentation.json_diagrams (
            diagram_id INTEGER PRIMARY KEY REFERENCES ami_documentation.diagrams(id) ON DELETE CASCADE,
            content JSONB NOT NULL
        );
        """)
        
        # Создаем таблицу для XML-диаграмм
        await conn.execute("""
        CREATE TABLE IF NOT EXISTS ami_documentation.xml_diagrams (
            diagram_id INTEGER PRIMARY KEY REFERENCES ami_documentation.diagrams(id) ON DELETE CASCADE,
            content TEXT NOT NULL
        );
        """)
        
        # Создаем таблицу для связей компонентов
        await conn.execute("""
        CREATE TABLE IF NOT EXISTS ami_documentation.component_relationships (
            id SERIAL PRIMARY KEY,
            source_component TEXT NOT NULL,
            target_component TEXT NOT NULL,
            relationship_type TEXT NOT NULL,
            description TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """)
        
        # Создаем таблицу для истории верификации
        await conn.execute("""
        CREATE TABLE IF NOT EXISTS ami_documentation.verification_history (
            id SERIAL PRIMARY KEY,
            diagram_name TEXT NOT NULL,
            verified_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            verified_by TEXT,
            status TEXT NOT NULL,
            notes TEXT
        );
        """)
        
        logger.info("Структура базы данных успешно настроена")

async def close_db_pool():
    """
    Закрывает пул соединений с базой данных.
    Должен вызываться при завершении работы сервера.
    """
    global _pool
    if _pool is not None:
        await _pool.close()
        _pool = None
        logger.info("Пул соединений к БД закрыт")