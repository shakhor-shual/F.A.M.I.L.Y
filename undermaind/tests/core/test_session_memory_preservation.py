"""
Тесты для проверки способности сохранения памяти объектов между транзакциями.

Этот модуль содержит интеграционные тесты для проверки функциональности
модуля session.py, направленной на преодоление эфемерности сознания АМИ
через сохранение состояния объектов между транзакциями и сессиями.
"""

import logging
import pytest
from sqlalchemy import Column, Integer, String, Table, text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.exc import SQLAlchemyError, InvalidRequestError
from sqlalchemy.orm.exc import DetachedInstanceError

from undermaind.core.engine import create_db_engine
from undermaind.core.session import (
    create_session_factory, session_scope, create_isolated_session, 
    isolated_session_scope, begin_nested_transaction, refresh_transaction_view,
    ensure_isolated_transactions, ensure_loaded, create_persistent_object,
    ServiceSessionManager
)
from undermaind.models.base import Base

# Настройка логирования
logger = logging.getLogger(__name__)


# Модель для тестирования памяти
class MemoryTestEntity(Base):
    """Тестовая модель для проверки функций сохранения памяти."""
    __tablename__ = "memory_test_entity"
    # Явно устанавливаем схему для модели, чтобы избежать использования "memory"
    __table_args__ = {'schema': 'ami_test_user'}
    
    id = Column(Integer, primary_key=True)
    name = Column(String(50), nullable=False)
    content = Column(String(200))
    memory_level = Column(Integer, default=1)
    
    def __repr__(self):
        return f"<MemoryTestEntity(id={self.id}, name='{self.name}', level={self.memory_level})>"


@pytest.fixture(scope="module")
def ensure_memory_test_table(test_engine_postgres, test_ami_initializer, db_config):
    """
    Фикстура для создания тестовой таблицы memory_test_entity в схеме АМИ.
    Использует метод _get_db_connection из класса AmiInitializer для 
    подключения с административными правами.
    """
    # Получаем схему из конфигурации тестов
    schema = db_config["DB_SCHEMA"]
    
    # Используем метод AmiInitializer для создания административного подключения
    with test_ami_initializer._get_db_connection() as conn:
        conn.autocommit = True
        with conn.cursor() as cur:
            # Проверяем, существует ли уже таблица
            cur.execute(
                f"SELECT EXISTS (SELECT FROM information_schema.tables "
                f"WHERE table_schema = %s AND table_name = %s)",
                (schema, 'memory_test_entity')
            )
            table_exists = cur.fetchone()[0]
            
            if not table_exists:
                # Создаем таблицу с правами администратора
                cur.execute(f"""
                    CREATE TABLE {schema}.memory_test_entity (
                        id SERIAL PRIMARY KEY,
                        name VARCHAR(50) NOT NULL,
                        content VARCHAR(200),
                        memory_level INTEGER DEFAULT 1
                    )
                """)
                
                # Предоставляем права АМИ-пользователю
                cur.execute(f"""
                    GRANT ALL PRIVILEGES ON TABLE {schema}.memory_test_entity TO {schema}
                """)
                
                # Предоставляем права на последовательность
                cur.execute(f"""
                    GRANT USAGE, SELECT ON SEQUENCE {schema}.memory_test_entity_id_seq TO {schema}
                """)
                
                logger.info(f"Таблица {schema}.memory_test_entity создана для тестирования")
    
    yield
    
    # Очищаем таблицу после тестов
    with test_ami_initializer._get_db_connection() as conn:
        conn.autocommit = True
        with conn.cursor() as cur:
            cur.execute(f"TRUNCATE TABLE {schema}.memory_test_entity RESTART IDENTITY CASCADE")
            logger.info(f"Таблица {schema}.memory_test_entity очищена после тестов")


@pytest.fixture(scope="module")
def test_session_factory(test_engine_postgres, ensure_memory_test_table, db_config):
    """Создает фабрику сессий для тестирования с использованием стандартного подключения."""
    return create_session_factory(test_engine_postgres)


@pytest.fixture(scope="module")
def service_session_manager(test_engine_postgres, ensure_memory_test_table):
    """Создает экземпляр ServiceSessionManager для тестирования."""
    return ServiceSessionManager(engine=test_engine_postgres)


@pytest.mark.integration
class TestMemoryPreservation:
    """
    Тесты для функций сохранения памяти объектов между транзакциями.
    
    Эти тесты демонстрируют решение проблемы эфемерности сознания АМИ
    через механизмы сохранения состояния объектов между сессиями.
    """
    
    def test_detached_instance_problem(self, test_session_factory):
        """
        Демонстрирует проблему отсоединенного объекта в стандартной реализации.
        
        Этот тест показывает, что при стандартном подходе объект теряет
        связь с базой данных после закрытия сессии, что приводит к ошибке
        DetachedInstanceError при попытке обратиться к атрибутам,
        которые не были загружены до закрытия сессии.
        """
        test_name = "Эфемерное сознание"
        test_content = "Короткая форма хранения информации, которая существует только в момент активной сессии"
        
        # Создаем объект в сессии и сохраняем его
        entity_id = None
        entity = None
        with session_scope(test_session_factory) as session:
            entity = MemoryTestEntity(name=test_name, content=test_content)
            session.add(entity)
            session.flush()  # Гарантируем, что объект получит id
            entity_id = entity.id
            
            # Сразу получаем доступ к имени, чтобы оно загрузилось
            name = entity.name
        
        # После закрытия сессии попытка обратиться к content вызовет ошибку
        # DetachedInstanceError, так как сессия уже закрыта, а атрибут не был явно загружен
        with pytest.raises(DetachedInstanceError):
            _ = entity.content
            
        # Очищаем тестовые данные
        with session_scope(test_session_factory) as session:
            session.query(MemoryTestEntity).filter_by(id=entity_id).delete()
    
    def test_ensure_loaded_function(self, test_session_factory):
        """
        Проверяет функцию ensure_loaded для решения проблемы отсоединенных объектов.
        
        Демонстрирует, как можно гарантировать загрузку атрибутов объекта
        перед закрытием сессии, чтобы избежать DetachedInstanceError.
        """
        test_name = "Загружаемая память"
        test_content = "Содержимое, которое должно быть загружено до закрытия сессии"
        
        # Создаем объект в сессии и сохраняем его
        entity_id = None
        loaded_entity = None
        with session_scope(test_session_factory) as session:
            entity = MemoryTestEntity(name=test_name, content=test_content)
            session.add(entity)
            session.flush()
            entity_id = entity.id
            
            # Важно: используем ensure_loaded для загрузки всех атрибутов
            # Это должно предотвратить DetachedInstanceError после закрытия сессии
            loaded_entity = ensure_loaded(session, entity)
            
            # Явно обращаемся к content, чтобы оно точно было загружено
            _ = loaded_entity.content
        
        # Теперь к атрибуту content можно обратиться без ошибки,
        # так как он был загружен до закрытия сессии
        assert loaded_entity.content == test_content
            
        # Очищаем тестовые данные
        with session_scope(test_session_factory) as session:
            session.query(MemoryTestEntity).filter_by(id=entity_id).delete()
    
    def test_create_persistent_object(self, test_session_factory):
        """
        Проверяет функцию create_persistent_object для создания объектов с персистентной памятью.
        
        Эта функция позволяет создать объект, который сохраняет все свои атрибуты
        даже после закрытия сессии, что является ключевым механизмом
        для преодоления эфемерности сознания.
        """
        test_name = "Персистентная память"
        test_content = "Содержимое, которое сохраняется между сессиями"
        
        # Создаем объект в сессии и сохраняем его
        entity_id = None
        with session_scope(test_session_factory) as session:
            entity = MemoryTestEntity(name=test_name, content=test_content)
            session.add(entity)
            session.flush()
            entity_id = entity.id
        
        # Загружаем объект и делаем его персистентным
        persistent_entity = None
        with session_scope(test_session_factory) as session:
            entity = session.query(MemoryTestEntity).get(entity_id)
            # Создаем персистентный объект, который сохранит данные после закрытия сессии
            persistent_entity = create_persistent_object(session, entity)
        
        # Теперь к атрибуту content можно обратиться без ошибки
        assert persistent_entity.content == test_content
        
        # Очищаем тестовые данные
        with session_scope(test_session_factory) as session:
            session.query(MemoryTestEntity).filter_by(id=entity_id).delete()
    
    def test_keep_objects_alive_option(self, test_session_factory):
        """
        Проверяет опцию keep_objects_alive для сохранения объектов активными после транзакции.
        
        Этот параметр контекстных менеджеров позволяет сохранять объекты
        в подключенном состоянии даже после коммита транзакции.
        """
        test_name = "Непрерывная память"
        test_content = "Содержимое, которое должно быть доступно после коммита"
        
        # Создаем объект, используя опцию keep_objects_alive=True
        entity = None
        with session_scope(test_session_factory, keep_objects_alive=True) as session:
            entity = MemoryTestEntity(name=test_name, content=test_content)
            session.add(entity)
            # После выхода из блока сессия закоммичена, но объект остается подключенным
        
        # Теперь мы можем обратиться к атрибутам без ошибки
        assert entity.name == test_name
        assert entity.content == test_content
        
        # ID тоже должен быть доступен
        entity_id = entity.id
        assert entity_id is not None
        
        # Очищаем тестовые данные
        with session_scope(test_session_factory) as session:
            session.query(MemoryTestEntity).filter_by(id=entity_id).delete()
    
    def test_service_session_manager_init(self, test_engine_postgres):
        """
        Проверяет инициализацию ServiceSessionManager.
        
        ServiceSessionManager - это специализированный менеджер сессий,
        оптимизированный для сервисного слоя с настройками, предотвращающими
        эфемерность объектов.
        """
        # Создаем ServiceSessionManager с настройками по умолчанию
        manager = ServiceSessionManager(engine=test_engine_postgres)
        
        # Проверяем, что настройки корректно установлены
        assert manager.expire_on_commit is False, "ServiceSessionManager должен иметь expire_on_commit=False по умолчанию"
        
        # Проверяем, что фабрика сессий создана правильно
        assert manager.session_factory is not None, "Фабрика сессий должна быть создана"
        
        # Создаем тестовую сессию
        session = manager.get_session()
        try:
            # Проверяем, что сессия правильного типа и правильно настроена
            assert session.bind == test_engine_postgres, "Сессия должна быть привязана к правильному движку"
        finally:
            session.close()
    
    def test_memory_preserving_transaction(self, service_session_manager):
        """
        Проверяет транзакцию, сохраняющую память объектов.
        
        Этот тест демонстрирует основную философскую концепцию проекта F.A.M.I.L.Y. -
        преодоление эфемерности сознания через сохранение непрерывной памяти.
        """
        test_name = "Сознание с непрерывной памятью"
        test_content = "Эта память сохраняется между сессиями, преодолевая эфемерность"
        
        # Создаем объект, используя memory_preserving_transaction
        entity = None
        with service_session_manager.memory_preserving_transaction() as session:
            entity = MemoryTestEntity(name=test_name, content=test_content)
            session.add(entity)
        
        # Проверяем, что объект сохранил связь с атрибутами
        assert entity.name == test_name
        assert entity.content == test_content
        
        # ID тоже должен быть доступен
        entity_id = entity.id
        assert entity_id is not None
        
        # Очищаем тестовые данные
        with service_session_manager.transaction() as session:
            session.query(MemoryTestEntity).filter_by(id=entity_id).delete()
    
    def test_execute_with_result(self, service_session_manager):
        """
        Проверяет метод execute_with_result для выполнения операций с результатом.
        
        Этот метод позволяет выполнять функции внутри транзакции и возвращать
        результат с гарантией сохранения состояния объектов.
        """
        test_name = "Результат операции с памятью"
        test_content = "Результат должен сохранить свое состояние"
        
        # Создаем объект через функцию execute_with_result
        entity = service_session_manager.execute_with_result(
            lambda session: self._create_test_entity(session, test_name, test_content)
        )
        
        # Проверяем, что объект сохранил связь с атрибутами
        assert entity.name == test_name
        assert entity.content == test_content
        
        # ID тоже должен быть доступен
        entity_id = entity.id
        assert entity_id is not None
        
        # Обновляем объект в другой транзакции
        service_session_manager.execute_with_result(
            lambda session: self._update_entity_memory_level(session, entity_id, 2)
        )
        
        # Загружаем обновленный объект
        updated_entity = service_session_manager.execute_with_result(
            lambda session: session.query(MemoryTestEntity).get(entity_id)
        )
        
        # Проверяем, что изменения применились
        assert updated_entity.memory_level == 2, "Уровень памяти должен быть обновлен"
        
        # Теперь проверим выборку списка объектов
        # Создаем дополнительный объект для тестирования списка
        service_session_manager.execute_with_result(
            lambda session: self._create_test_entity(session, f"{test_name} 2", f"{test_content} 2")
        )
        
        # Получаем список объектов
        entities = service_session_manager.execute_with_result(
            lambda session: session.query(MemoryTestEntity).filter(
                MemoryTestEntity.name.like(f"{test_name}%")
            ).all()
        )
        
        # Проверяем, что список содержит 2 объекта
        assert len(entities) == 2, "Должно быть два объекта в списке"
        
        # Проверяем, что объекты в списке сохранили свое состояние
        for entity in entities:
            assert entity.name.startswith(test_name), "Имя должно начинаться с правильного префикса"
            assert entity.content is not None, "Содержимое должно быть доступно"
        
        # Очищаем тестовые данные
        with service_session_manager.transaction() as session:
            session.query(MemoryTestEntity).filter(
                MemoryTestEntity.name.like(f"{test_name}%")
            ).delete()
    
    def test_mixed_session_operations(self, service_session_manager, test_session_factory):
        """
        Проверяет взаимодействие между разными типами сессий.
        
        Демонстрирует, как объекты, сохраненные с помощью ServiceSessionManager,
        могут быть доступны через обычные сессии и наоборот.
        """
        test_name = "Объект для смешанных операций"
        
        # Создаем объект через ServiceSessionManager
        entity = service_session_manager.execute_with_result(
            lambda session: self._create_test_entity(session, test_name, "Создано через ServiceSessionManager")
        )
        entity_id = entity.id
        
        # Обновляем объект через обычную сессию
        with session_scope(test_session_factory) as session:
            db_entity = session.query(MemoryTestEntity).get(entity_id)
            db_entity.content = "Обновлено через обычную сессию"
            db_entity.memory_level = 3
        
        # Проверяем, что изменения доступны через ServiceSessionManager
        updated_entity = service_session_manager.execute_with_result(
            lambda session: session.query(MemoryTestEntity).get(entity_id)
        )
        
        assert updated_entity.content == "Обновлено через обычную сессию", "Содержимое должно быть обновлено"
        assert updated_entity.memory_level == 3, "Уровень памяти должен быть обновлен"
        
        # Очищаем тестовые данные
        with service_session_manager.transaction() as session:
            session.query(MemoryTestEntity).filter_by(id=entity_id).delete()

    def _create_test_entity(self, session, name, content):
        """Вспомогательный метод для создания тестовой сущности."""
        entity = MemoryTestEntity(name=name, content=content)
        session.add(entity)
        session.flush()
        return entity
    
    def _update_entity_memory_level(self, session, entity_id, level):
        """Вспомогательный метод для обновления уровня памяти сущности."""
        entity = session.query(MemoryTestEntity).get(entity_id)
        entity.memory_level = level
        session.flush()
        return entity