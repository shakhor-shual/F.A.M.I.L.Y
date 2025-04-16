"""
Интеграционные тесты для базового класса Base и его взаимодействия со SchemaManager.

Эти тесты проверяют, что модели SQLAlchemy, наследующиеся от Base,
правильно привязываются к схеме БД, созданной через SchemaManager,
а также проверяют автоматическое создание схем и таблиц.
"""

import os
import pytest
import dotenv
from pathlib import Path
from sqlalchemy import Column, Integer, String, inspect, text
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import SQLAlchemyError

from undermaind.core.base import create_base, initialize_base_with_schema
from undermaind.core.schema_manager import SchemaManager, get_schema_manager
from undermaind.config import Config


@pytest.fixture(scope="module")
def test_config_path():
    """Путь к файлу конфигурации для тестовой среды."""
    # Используем файл конфигурации из директории tests
    base_dir = Path(__file__).parent.parent
    return base_dir / "test_config.env"


@pytest.fixture(scope="module")
def test_config(test_config_path):
    """Создает тестовую конфигурацию на основе файла test_config.env."""
    # Проверяем существование файла
    config_path = test_config_path
    if not config_path.exists():
        pytest.skip(f"Файл конфигурации не найден: {config_path}")
    
    # Загружаем переменные окружения из файла
    dotenv.load_dotenv(config_path)
    
    # Создаем конфигурацию из переменных окружения с префиксом FAMILY_
    return Config(
        DB_NAME=os.environ.get("FAMILY_DB_NAME", "family_db"),
        DB_HOST=os.environ.get("FAMILY_DB_HOST", "localhost"),
        DB_PORT=os.environ.get("FAMILY_DB_PORT", "5432"),
        DB_USERNAME=os.environ.get("FAMILY_ADMIN_USER", "family_admin"),
        DB_PASSWORD=os.environ.get("FAMILY_ADMIN_PASSWORD", ""),
        DB_SCHEMA=os.environ.get("FAMILY_DB_SCHEMA", "ami_memory")
    )


@pytest.fixture(scope="module")
def admin_credentials():
    """Получает учетные данные администратора PostgreSQL из переменных окружения."""
    # Используем FAMILY_ADMIN_* переменные из test_config.env
    admin_user = os.environ.get("FAMILY_ADMIN_USER")
    admin_password = os.environ.get("FAMILY_ADMIN_PASSWORD")
    
    # Пропускаем тесты, если учетные данные не предоставлены
    if not admin_user or not admin_password:
        pytest.skip("Не указаны учетные данные администратора (FAMILY_ADMIN_USER/FAMILY_ADMIN_PASSWORD)")
    
    return admin_user, admin_password


@pytest.fixture(scope="module")
def schema_manager(test_config, admin_credentials):
    """Создает экземпляр SchemaManager с установленными учетными данными администратора."""
    admin_user, admin_password = admin_credentials
    manager = SchemaManager(test_config)
    manager.set_admin_credentials(admin_user, admin_password)
    
    # Создаем базу данных, если она не существует
    if not manager.create_database():
        pytest.skip(f"Не удалось создать базу данных {test_config.DB_NAME}")
    
    return manager


@pytest.mark.integration
class TestBaseIntegration:
    """
    Интеграционные тесты для базового класса Base.
    
    Проверяет взаимодействие Base с SchemaManager и правильное создание моделей
    в указанной схеме PostgreSQL.
    """
    
    # Тестовые данные, используем имя из конфигурации для уникальности
    TEST_SCHEMA = os.environ.get("FAMILY_AMI_SCHEMA", "ami_test_user") + "_base_test"
    TEST_PASSWORD = os.environ.get("FAMILY_AMI_PASSWORD", "ami_secure_password")
    
    def test_create_base_with_schema(self, schema_manager, test_config):
        """Проверяет создание базового класса с указанной схемой."""
        try:
            # Удаляем схему, если она осталась от предыдущих тестов
            schema_manager.drop_schema(self.TEST_SCHEMA, cascade=True, drop_user=True)
            
            # Создаем схему с пользователем для теста
            schema_manager.create_schema(self.TEST_SCHEMA, self.TEST_PASSWORD, create_user=True)
            
            # Создаем базовый класс с указанной схемой
            TestBase = create_base(schema_name=self.TEST_SCHEMA, auto_create_schema=False, config=test_config)
            
            # Проверяем привязку к схеме
            assert TestBase.metadata.schema == self.TEST_SCHEMA
            
            # Проверяем метод получения имени схемы
            assert TestBase.get_schema_name() == self.TEST_SCHEMA
            
        finally:
            # Гарантированная очистка после теста
            schema_manager.drop_schema(self.TEST_SCHEMA, cascade=True, drop_user=True)
    
    def test_base_models_with_tables(self, schema_manager, test_config, admin_credentials):
        """Проверяет создание моделей и таблиц на основе Base в указанной схеме."""
        try:
            # Создаем схему для теста
            schema_manager.create_schema(self.TEST_SCHEMA, self.TEST_PASSWORD, create_user=True)
            
            # Создаем базовый класс с указанной схемой
            TestBase = create_base(
                schema_name=self.TEST_SCHEMA, 
                auto_create_schema=True, 
                config=test_config,
                admin_credentials=admin_credentials
            )
            
            # Определяем тестовую модель
            class TestModel(TestBase):
                __tablename__ = 'test_table'
                
                id = Column(Integer, primary_key=True)
                name = Column(String, nullable=False)
                description = Column(String)
            
            # Создаем движок для работы с этой схемой
            engine = TestBase.create_engine(
                use_admin=True, 
                config=test_config,
                admin_credentials=admin_credentials
            )
            
            # Создаем таблицы
            TestBase.metadata.create_all(engine)
            
            # Проверяем, что таблица создана в правильной схеме
            inspector = inspect(engine)
            assert 'test_table' in inspector.get_table_names(schema=self.TEST_SCHEMA)
            
            # Создаем сессию и добавляем тестовые данные
            Session = sessionmaker(bind=engine)
            session = Session()
            
            try:
                # Добавляем тестовую запись
                test_record = TestModel(name="Test Name", description="Test Description")
                session.add(test_record)
                session.commit()
                
                # Проверяем, что запись добавлена
                result = session.query(TestModel).filter_by(name="Test Name").first()
                assert result is not None
                assert result.name == "Test Name"
                assert result.description == "Test Description"
                
            finally:
                # Закрываем сессию
                session.close()
            
        finally:
            # Гарантированная очистка после теста
            schema_manager.drop_schema(self.TEST_SCHEMA, cascade=True, drop_user=True)
    
    def test_auto_create_schema(self, test_config, admin_credentials):
        """Проверяет автоматическое создание схемы при инициализации Base."""
        admin_user, admin_password = admin_credentials
        test_schema = f"{self.TEST_SCHEMA}_auto"
        
        try:
            # Создаем базовый класс с автоматическим созданием схемы, передавая учетные данные
            TestBase = initialize_base_with_schema(
                schema_name=test_schema,
                auto_create_schema=True,
                config=test_config,
                admin_credentials=admin_credentials  # Передаем учетные данные
            )
            
            # Определяем тестовую модель
            class AutoTestModel(TestBase):
                __tablename__ = 'auto_test_table'
                
                id = Column(Integer, primary_key=True)
                value = Column(String, nullable=False)
            
            # Получаем менеджер схем для проверки
            schema_manager = get_schema_manager(
                config=test_config,
                admin_user=admin_user,
                admin_password=admin_password
            )
            
            # Проверяем, что схема создана автоматически
            assert schema_manager.schema_exists(test_schema) is True
            
            # Создаем движок и таблицы, передавая учетные данные
            engine = TestBase.create_engine(
                use_admin=True, 
                config=test_config,
                admin_credentials=admin_credentials  # Передаем учетные данные
            )
            TestBase.metadata.create_all(engine)
            
            # Проверяем, что таблица создана
            inspector = inspect(engine)
            assert 'auto_test_table' in inspector.get_table_names(schema=test_schema)
            
        finally:
            # Гарантированная очистка после теста
            schema_manager = get_schema_manager(
                config=test_config,
                admin_user=admin_user,
                admin_password=admin_password
            )
            schema_manager.drop_schema(test_schema, cascade=True, drop_user=True)
    
    def test_multiple_base_classes(self, schema_manager, test_config, admin_credentials):
        """Проверяет работу с несколькими базовыми классами для разных схем."""
        schema1 = f"{self.TEST_SCHEMA}_1"
        schema2 = f"{self.TEST_SCHEMA}_2"
        
        try:
            # Создаем две схемы
            schema_manager.create_schema(schema1, self.TEST_PASSWORD, create_user=True)
            schema_manager.create_schema(schema2, self.TEST_PASSWORD, create_user=True)
            
            # Создаем два базовых класса с разными схемами, передаем учетные данные
            Base1 = create_base(
                schema_name=schema1, 
                auto_create_schema=False, 
                config=test_config,
                admin_credentials=admin_credentials
            )
            Base2 = create_base(
                schema_name=schema2, 
                auto_create_schema=False, 
                config=test_config,
                admin_credentials=admin_credentials
            )
            
            # Определяем модели для разных схем
            class Model1(Base1):
                __tablename__ = 'model1'
                id = Column(Integer, primary_key=True)
                value = Column(String)
            
            class Model2(Base2):
                __tablename__ = 'model2'
                id = Column(Integer, primary_key=True)
                value = Column(String)
            
            # Создаем движки и таблицы, передаем учетные данные
            engine1 = Base1.create_engine(
                use_admin=True, 
                config=test_config,
                admin_credentials=admin_credentials
            )
            engine2 = Base2.create_engine(
                use_admin=True, 
                config=test_config,
                admin_credentials=admin_credentials
            )
            
            Base1.metadata.create_all(engine1)
            Base2.metadata.create_all(engine2)
            
            # Проверяем, что таблицы созданы в правильных схемах
            inspector1 = inspect(engine1)
            inspector2 = inspect(engine2)
            
            assert 'model1' in inspector1.get_table_names(schema=schema1)
            assert 'model2' in inspector2.get_table_names(schema=schema2)
            
            # Проверяем, что таблицы не смешиваются между схемами
            assert 'model1' not in inspector2.get_table_names(schema=schema2)
            assert 'model2' not in inspector1.get_table_names(schema=schema1)
            
        finally:
            # Гарантированная очистка после теста
            schema_manager.drop_schema(schema1, cascade=True, drop_user=True)
            schema_manager.drop_schema(schema2, cascade=True, drop_user=True)