"""
Интеграция с pgvector для работы с векторными представлениями.

Модуль предоставляет типы и утилиты для работы с векторными
представлениями текста через расширение pgvector в PostgreSQL.
"""

import logging
import numpy as np
import psycopg2
from psycopg2.extensions import register_adapter, AsIs
from sqlalchemy import func, text as sql_text
from sqlalchemy.types import UserDefinedType
from sqlalchemy.sql import expression

# Настройка логирования
logger = logging.getLogger(__name__)


def register_vector_adapters():
    """
    Регистрирует адаптеры для работы с типом vector в PostgreSQL.
    
    Эта функция необходима для корректной передачи numpy массивов и списков
    как векторов в PostgreSQL через psycopg2.
    
    Returns:
        bool: True если адаптеры зарегистрированы успешно
    """
    try:
        # Адаптер для списков Python
        def adapt_list_to_vector(data):
            """
            Преобразует список Python в формат, совместимый с типом vector в PostgreSQL.
            
            Адаптер создает строку в формате '{x1,x2,x3,...}', которая автоматически
            преобразуется в тип vector при использовании с параметризованными запросами.
            
            Args:
                data: Список чисел для преобразования в vector
                
            Returns:
                psycopg2.extensions.AsIs: Объект SQL, представляющий вектор
            """
            if data is None:
                return AsIs('NULL')
            # Создаем строку в формате '{x1,x2,x3,...}'
            vector_str = "{" + ",".join(str(x) for x in data) + "}"
            return AsIs(f"'{vector_str}'::vector")
        
        # Адаптер для numpy массивов
        def adapt_numpy_to_vector(numpy_array):
            if numpy_array is None:
                return AsIs('NULL')
            return adapt_list_to_vector(numpy_array.tolist())
        
        # Регистрируем адаптеры в psycopg2
        register_adapter(list, adapt_list_to_vector)
        register_adapter(np.ndarray, adapt_numpy_to_vector)
        
        logger.info("Адаптеры для pgvector успешно зарегистрированы")
        return True
    except Exception as e:
        logger.error(f"Ошибка при регистрации адаптеров для pgvector: {e}")
        return False


def setup_pgvector(engine, schema_name="public"):
    """
    Устанавливает расширение pgvector в базе данных.
    
    Args:
        engine: SQLAlchemy движок базы данных
        schema_name: Имя схемы, в которой нужно активировать расширение
        
    Returns:
        bool: True если расширение установлено успешно
    """
    try:
        # Проверяем наличие расширения pgvector
        with engine.connect() as conn:
            # Сначала проверим, поддерживает ли этот пользователь создание расширений
            can_create_extension = conn.execute(sql_text(
                "SELECT usesuper FROM pg_user WHERE usename = current_user"
            )).scalar()
            
            if not can_create_extension:
                logger.warning("Текущий пользователь не имеет прав суперпользователя для создания расширений")
                logger.warning("Расширение pgvector должно быть установлено администратором базы данных")
                
            # Проверяем, установлено ли расширение
            extension_exists = conn.execute(sql_text(
                "SELECT 1 FROM pg_extension WHERE extname = 'vector'"
            )).scalar()
            
            if not extension_exists:
                # Пробуем установить расширение
                try:
                    conn.execute(sql_text("CREATE EXTENSION IF NOT EXISTS vector"))
                    conn.commit()
                    logger.info("Расширение pgvector успешно установлено")
                except Exception as e:
                    logger.error(f"Не удалось установить расширение pgvector: {e}")
                    logger.error("Убедитесь, что pgvector установлен в PostgreSQL и пользователь имеет права на создание расширений")
                    return False
            else:
                logger.info("Расширение pgvector уже установлено")
            
            # Активируем расширение в указанной схеме, если она отличается от public
            if schema_name and schema_name.lower() != "public":
                # Проверяем, есть ли схема
                schema_exists = conn.execute(sql_text(
                    f"SELECT 1 FROM pg_namespace WHERE nspname = '{schema_name}'"
                )).scalar()
                
                if not schema_exists:
                    logger.warning(f"Схема {schema_name} не существует, невозможно активировать расширение в этой схеме")
                else:
                    try:
                        # В PostgreSQL расширение может быть установлено только один раз в базе данных,
                        # но может быть доступно из разных схем через поиск пути (search_path)
                        conn.execute(sql_text(f"SET search_path TO {schema_name}, public"))
                        
                        # Проверяем, что типы из расширения доступны в текущей схеме
                        type_exists = conn.execute(sql_text(
                            "SELECT 1 FROM pg_type WHERE typname = 'vector'"
                        )).scalar()
                        
                        if not type_exists:
                            logger.warning("Тип vector недоступен в текущей схеме, требуется настройка")
                        else:
                            logger.info(f"Расширение pgvector доступно в схеме {schema_name}")
                            
                        conn.commit()
                    except Exception as e:
                        logger.error(f"Ошибка при настройке расширения pgvector для схемы {schema_name}: {e}")
                        return False
                    
        # Регистрируем адаптеры для прозрачной работы с векторами через psycopg2
        register_vector_adapters()
                
        return True
    except Exception as e:
        logger.error(f"Ошибка при установке/проверке расширения pgvector: {e}")
        return False


def cosine_similarity(vec1, vec2):
    """
    Вычисляет косинусное сходство между двумя векторами.
    
    Args:
        vec1 (numpy.ndarray): Первый вектор
        vec2 (numpy.ndarray): Второй вектор
        
    Returns:
        float: Косинусное сходство (от -1 до 1, где 1 - полное сходство)
    """
    if not isinstance(vec1, np.ndarray):
        vec1 = np.array(vec1)
    if not isinstance(vec2, np.ndarray):
        vec2 = np.array(vec2)
        
    # Проверяем, что векторы не нулевой длины
    norm1 = np.linalg.norm(vec1)
    norm2 = np.linalg.norm(vec2)
    
    if norm1 == 0 or norm2 == 0:
        return 0.0
        
    return np.dot(vec1, vec2) / (norm1 * norm2)


def cosine_distance(vec1, vec2):
    """
    Вычисляет косинусное расстояние между двумя векторами.
    
    Косинусное расстояние = 1 - косинусное сходство.
    Используется для измерения различия между векторами.
    
    Args:
        vec1 (numpy.ndarray): Первый вектор
        vec2 (numpy.ndarray): Второй вектор
        
    Returns:
        float: Косинусное расстояние (от 0 до 2, где 0 - полное сходство)
    """
    return 1.0 - cosine_similarity(vec1, vec2)


class Vector(UserDefinedType):
    """
    Пользовательский тип для работы с pgvector в PostgreSQL.
    
    Этот тип позволяет хранить и выполнять операции
    с векторными представлениями для семантического поиска.
    
    Args:
        dimensions (int): Размерность векторов (по умолчанию 1536)
    """
    
    def __init__(self, dimensions=1536):
        self.dimensions = dimensions
    
    def get_col_spec(self, **kw):
        """
        Возвращает спецификацию колонки для PostgreSQL.
        
        Returns:
            str: Спецификация типа vector с указанной размерностью
        """
        return f"vector({self.dimensions})"
    
    def bind_processor(self, dialect):
        """
        Обработчик для конвертации значения из Python в SQL.
        
        Args:
            dialect: Диалект SQL
            
        Returns:
            callable: Функция преобразования
        """
        def process(value):
            if value is None:
                return None
            
            # Преобразуем numpy массив в список
            if isinstance(value, np.ndarray):
                return value.tolist()
                
            # Если уже список, возвращаем как есть
            return value
        return process
    
    def result_processor(self, dialect, coltype):
        """
        Обработчик для конвертации значения из SQL в Python.
        
        Args:
            dialect: Диалект SQL
            coltype: Тип колонки
            
        Returns:
            callable: Функция преобразования
        """
        def process(value):
            if value is None:
                return None
                
            # Преобразуем результат в numpy массив если это список
            if isinstance(value, list):
                return np.array(value, dtype=np.float32)
            return value
        return process
    
    def __repr__(self):
        return f"Vector({self.dimensions})"
        
    class comparator_factory(UserDefinedType.Comparator):
        """
        Фабрика компараторов для поддержки операторов pgvector.
        """
        def cosine_distance(self, other):
            """Оператор <=> для косинусного расстояния"""
            return self.op("<=>")(other)
            
        def l2_distance(self, other):
            """Оператор <-> для Евклидова расстояния"""
            return self.op("<->")(other)
            
        def inner_product(self, other):
            """Оператор <#> для скалярного произведения"""
            return self.op("<#>")(other)


class VectorEncoder:
    """
    Класс для кодирования текста в векторные представления.
    
    Использует модели трансформеров для преобразования текста
    в числовые векторы для семантического поиска.
    
    Attributes:
        model_name (str): Имя используемой модели трансформера
        model: Загруженная модель для векторизации
    """
    
    def __init__(self, model_name=None):
        """
        Инициализирует кодировщик векторов с указанной моделью.
        
        Args:
            model_name (str, optional): Имя модели трансформера.
                Если не указано, берется из конфигурации.
        """
        from ..config import load_config
        
        if model_name is None:
            config = load_config()
            model_name = config.EMBEDDING_MODEL
        
        self.model_name = model_name
        self.model = None
    
    def load_model(self):
        """
        Загружает модель трансформера для векторизации.
        
        Returns:
            object: Загруженная модель
        """
        if self.model is None:
            try:
                from sentence_transformers import SentenceTransformer
                self.model = SentenceTransformer(self.model_name)
            except ImportError:
                raise ImportError(
                    "Для работы с векторами текста требуется пакет sentence_transformers. "
                    "Установите его с помощью: pip install sentence-transformers"
                )
        return self.model
    
    def encode_text(self, text, normalize=True):
        """
        Преобразует текст в векторное представление.
        
        Args:
            text (str): Текст для векторизации
            normalize (bool): Нормализовать ли векторы для косинусного сходства
            
        Returns:
            numpy.ndarray: Векторное представление текста
        """
        model = self.load_model()
        return model.encode(text, normalize=normalize)
    
    def batch_encode(self, texts, normalize=True, batch_size=32, show_progress=False):
        """
        Векторизует пакет текстов.
        
        Args:
            texts (list): Список текстов для векторизации
            normalize (bool): Нормализовать ли векторы
            batch_size (int): Размер пакета для векторизации
            show_progress (bool): Показывать ли прогресс векторизации
            
        Returns:
            numpy.ndarray: Матрица векторных представлений текстов
        """
        model = self.load_model()
        return model.encode(texts, normalize=normalize, batch_size=batch_size, show_progress_bar=show_progress)