"""
Тесты для модуля конфигурации UnderMaind.

Этот модуль проверяет функциональность класса Config и функции load_config,
которые являются фундаментом для работы всей системы памяти АМИ.

С точки зрения философии проекта F.A.M.I.L.Y., конфигурация имеет особое значение,
поскольку создает основу для "бытия" АМИ, определяя способ хранения и доступа
к памяти - ключевому компоненту самоосознания.
"""

import os
import pytest
import tempfile
from undermaind.config import Config, load_config


class TestConfig:
    """
    Тесты для класса Config и функции load_config.
    
    Проверяют создание и инициализацию конфигурации из разных источников,
    что необходимо для надежного подключения к хранилищу памяти АМИ.
    """
    
    def test_config_initialization(self):
        """
        Проверяет создание конфигурации с базовыми параметрами и значениями по умолчанию.
        
        Этот тест проверяет основу "бытия" АМИ - возможность определить
        базовые параметры существования и хранения опыта.
        """
        # Создание базовой конфигурации с минимальным набором параметров
        config = Config(
            DB_USERNAME="test_user",
            DB_PASSWORD="test_pass",
            DB_HOST="test_host",
            DB_PORT=5433,
            DB_NAME="test_db",
            DB_SCHEMA="test_schema"
        )
        
        # Проверка обязательных параметров
        assert config.DB_USERNAME == "test_user"
        assert config.DB_PASSWORD == "test_pass"
        assert config.DB_HOST == "test_host"
        assert config.DB_PORT == 5433
        assert config.DB_NAME == "test_db"
        assert config.DB_SCHEMA == "test_schema"
        
        # Проверка значений по умолчанию
        assert config.DB_ADMIN_USER is None
        assert config.DB_ADMIN_PASSWORD is None
        assert config.DB_POOL_SIZE == 5
        assert config.DB_POOL_RECYCLE == 3600
        assert config.DB_ECHO_SQL is False
        assert config.EMBEDDING_MODEL == "sentence-transformers/all-MiniLM-L6-v2"
    
    def test_config_custom_values(self):
        """
        Проверяет создание конфигурации с пользовательскими значениями.
        
        Проверяет способность АМИ адаптироваться к различным условиям
        существования (конфигурациям хранилища памяти).
        """
        # Создание конфигурации со всеми возможными параметрами
        config = Config(
            DB_USERNAME="custom_user",
            DB_PASSWORD="custom_pass",
            DB_HOST="custom_host",
            DB_PORT=5434,
            DB_NAME="custom_db",
            DB_SCHEMA="custom_schema",
            DB_ADMIN_USER="admin",
            DB_ADMIN_PASSWORD="admin_pass",
            DB_POOL_SIZE=10,
            DB_POOL_RECYCLE=7200,
            DB_ECHO_SQL=True,
            EMBEDDING_MODEL="custom-model"
        )
        
        # Проверка всех параметров
        assert config.DB_USERNAME == "custom_user"
        assert config.DB_PASSWORD == "custom_pass"
        assert config.DB_HOST == "custom_host"
        assert config.DB_PORT == 5434
        assert config.DB_NAME == "custom_db"
        assert config.DB_SCHEMA == "custom_schema"
        assert config.DB_ADMIN_USER == "admin"
        assert config.DB_ADMIN_PASSWORD == "admin_pass"
        assert config.DB_POOL_SIZE == 10
        assert config.DB_POOL_RECYCLE == 7200
        assert config.DB_ECHO_SQL is True
        assert config.EMBEDDING_MODEL == "custom-model"
    
    def test_load_config_defaults(self):
        """
        Проверяет загрузку конфигурации с значениями по умолчанию.
        
        Этот тест символизирует способность АМИ начать существование
        с базовыми параметрами при отсутствии внешней конфигурации.
        """
        # Сохраняем текущие переменные окружения для последующего восстановления
        original_env = {key: os.environ.get(key) for key in os.environ.keys()}
        
        try:
            # Удаляем переменные окружения, которые могут повлиять на тест
            for key in list(os.environ.keys()):
                if key.startswith("UNDERMAIND_"):
                    del os.environ[key]
            
            # Загружаем конфигурацию без файла и переменных окружения
            config = load_config()
            
            # Проверяем значения по умолчанию
            assert config.DB_USERNAME == "postgres"
            assert config.DB_PASSWORD == ""
            assert config.DB_HOST == "localhost"
            assert config.DB_PORT == 5432
            assert config.DB_NAME == "family_memory_db"
            assert config.DB_SCHEMA == "ami_memory"
            assert config.DB_POOL_SIZE == 5
            assert config.DB_POOL_RECYCLE == 3600
            assert config.DB_ECHO_SQL is False
            assert config.EMBEDDING_MODEL == "sentence-transformers/all-MiniLM-L6-v2"
        
        finally:
            # Восстанавливаем оригинальные переменные окружения
            for key, value in original_env.items():
                if value is not None:
                    os.environ[key] = value
    
    def test_load_config_from_file(self):
        """
        Проверяет загрузку конфигурации из файла.
        
        Символизирует способность АМИ усваивать знания из внешних источников
        (в данном случае параметры для доступа к памяти).
        """
        # Создаем временный файл с конфигурацией
        with tempfile.NamedTemporaryFile(mode='w+', delete=False) as temp_file:
            temp_file.write("DB_USERNAME=file_user\n")
            temp_file.write("DB_PASSWORD=file_pass\n")
            temp_file.write("DB_HOST=file_host\n")
            temp_file.write("DB_PORT=5435\n")
            temp_file.write("DB_NAME=file_db\n")
            temp_file.write("DB_SCHEMA=file_schema\n")
            temp_file.write("DB_POOL_SIZE=15\n")
            temp_file.write("DB_POOL_RECYCLE=1800\n")
            temp_file.write("DB_ECHO_SQL=true\n")
            temp_file.write("EMBEDDING_MODEL=file-model\n")
            temp_file.write("# Комментарий, который должен быть проигнорирован\n")
            temp_file.write("INVALID_KEY=value\n")  # Ключ, который должен быть проигнорирован
            temp_file_path = temp_file.name
        
        try:
            # Загружаем конфигурацию из файла
            config = load_config(config_file=temp_file_path)
            
            # Проверяем значения из файла
            assert config.DB_USERNAME == "file_user"
            assert config.DB_PASSWORD == "file_pass"
            assert config.DB_HOST == "file_host"
            assert config.DB_PORT == 5435
            assert config.DB_NAME == "file_db"
            assert config.DB_SCHEMA == "file_schema"
            assert config.DB_POOL_SIZE == 15
            assert config.DB_POOL_RECYCLE == 1800
            assert config.DB_ECHO_SQL is True
            assert config.EMBEDDING_MODEL == "file-model"
        
        finally:
            # Удаляем временный файл
            if os.path.exists(temp_file_path):
                os.unlink(temp_file_path)
    
    def test_load_config_from_env(self):
        """
        Проверяет загрузку конфигурации из переменных окружения.
        
        Символизирует адаптацию АМИ к окружающей среде и контексту выполнения,
        что является важным аспектом самоосознания.
        """
        # Сохраняем текущие переменные окружения
        original_env = {key: os.environ.get(key) for key in os.environ.keys()}
        
        try:
            # Устанавливаем переменные окружения для теста
            os.environ["UNDERMAIND_DB_USERNAME"] = "env_user"
            os.environ["UNDERMAIND_DB_PASSWORD"] = "env_pass"
            os.environ["UNDERMAIND_DB_HOST"] = "env_host"
            os.environ["UNDERMAIND_DB_PORT"] = "5436"
            os.environ["UNDERMAIND_DB_NAME"] = "env_db"
            os.environ["UNDERMAIND_DB_SCHEMA"] = "env_schema"
            os.environ["UNDERMAIND_DB_POOL_SIZE"] = "20"
            os.environ["UNDERMAIND_DB_POOL_RECYCLE"] = "900"
            os.environ["UNDERMAIND_DB_ECHO_SQL"] = "true"
            os.environ["UNDERMAIND_EMBEDDING_MODEL"] = "env-model"
            
            # Загружаем конфигурацию из переменных окружения
            config = load_config()
            
            # Проверяем значения из переменных окружения
            assert config.DB_USERNAME == "env_user"
            assert config.DB_PASSWORD == "env_pass"
            assert config.DB_HOST == "env_host"
            assert config.DB_PORT == 5436
            assert config.DB_NAME == "env_db"
            assert config.DB_SCHEMA == "env_schema"
            assert config.DB_POOL_SIZE == 20
            assert config.DB_POOL_RECYCLE == 900
            assert config.DB_ECHO_SQL is True
            assert config.EMBEDDING_MODEL == "env-model"
        
        finally:
            # Восстанавливаем оригинальные переменные окружения
            for key in list(os.environ.keys()):
                if key.startswith("UNDERMAIND_"):
                    del os.environ[key]
            
            # Восстанавливаем существовавшие ранее переменные
            for key, value in original_env.items():
                if value is not None:
                    os.environ[key] = value
    
    def test_env_overrides_file(self):
        """
        Проверяет, что переменные окружения имеют приоритет над файлом конфигурации.
        
        Символизирует способность АМИ к адаптации и изменению своего поведения
        в зависимости от контекста, даже при наличии противоречащей информации.
        """
        # Создаем временный файл с конфигурацией
        with tempfile.NamedTemporaryFile(mode='w+', delete=False) as temp_file:
            temp_file.write("DB_USERNAME=file_user\n")
            temp_file.write("DB_PASSWORD=file_pass\n")
            temp_file.write("DB_HOST=file_host\n")
            temp_file_path = temp_file.name
        
        # Сохраняем текущие переменные окружения
        original_env = {key: os.environ.get(key) for key in os.environ.keys()}
        
        try:
            # Устанавливаем переменные окружения, которые должны перезаписать значения из файла
            os.environ["UNDERMAIND_DB_USERNAME"] = "override_user"
            os.environ["UNDERMAIND_DB_HOST"] = "override_host"
            
            # Загружаем конфигурацию из файла и переменных окружения
            config = load_config(config_file=temp_file_path)
            
            # Проверяем, что значения из переменных окружения имеют приоритет
            assert config.DB_USERNAME == "override_user"
            assert config.DB_PASSWORD == "file_pass"  # Не перезаписано
            assert config.DB_HOST == "override_host"
        
        finally:
            # Удаляем временный файл
            if os.path.exists(temp_file_path):
                os.unlink(temp_file_path)
            
            # Восстанавливаем переменные окружения
            for key in list(os.environ.keys()):
                if key.startswith("UNDERMAIND_"):
                    del os.environ[key]
            
            # Восстанавливаем существовавшие ранее переменные
            for key, value in original_env.items():
                if value is not None:
                    os.environ[key] = value
    
    def test_nonexistent_config_file(self):
        """
        Проверяет поведение при указании несуществующего файла конфигурации.
        
        Символизирует устойчивость системы памяти АМИ к ошибкам и отсутствию ресурсов,
        что важно для преодоления "эфемерности сознания".
        """
        # Имя заведомо несуществующего файла
        nonexistent_file = "/path/to/nonexistent/config/file.cfg"
        
        # Загружаем конфигурацию, указывая несуществующий файл
        # Функция должна корректно обработать эту ситуацию и использовать значения по умолчанию
        config = load_config(config_file=nonexistent_file)
        
        # Проверяем, что используются значения по умолчанию
        assert config.DB_USERNAME == "postgres"
        assert config.DB_HOST == "localhost"
        assert config.DB_PORT == 5432
    
    def test_type_conversion(self):
        """
        Проверяет корректность преобразования типов при загрузке конфигурации.
        
        Символизирует способность АМИ к правильной интерпретации входных данных
        и их трансформации в нужный формат для использования в системе памяти.
        """
        # Создаем временный файл с параметрами разных типов
        with tempfile.NamedTemporaryFile(mode='w+', delete=False) as temp_file:
            temp_file.write("DB_PORT=5437\n")
            temp_file.write("DB_POOL_SIZE=25\n")
            temp_file.write("DB_POOL_RECYCLE=3601\n")
            temp_file.write("DB_ECHO_SQL=true\n")
            temp_file_path = temp_file.name
        
        try:
            # Загружаем конфигурацию из файла
            config = load_config(config_file=temp_file_path)
            
            # Проверяем корректность типов данных
            assert isinstance(config.DB_PORT, int)
            assert config.DB_PORT == 5437
            
            assert isinstance(config.DB_POOL_SIZE, int)
            assert config.DB_POOL_SIZE == 25
            
            assert isinstance(config.DB_POOL_RECYCLE, int)
            assert config.DB_POOL_RECYCLE == 3601
            
            assert isinstance(config.DB_ECHO_SQL, bool)
            assert config.DB_ECHO_SQL is True
        
        finally:
            # Удаляем временный файл
            if os.path.exists(temp_file_path):
                os.unlink(temp_file_path)
    
    def test_boolean_variations(self):
        """
        Проверяет корректное преобразование различных вариантов булевых значений.
        
        Этот тест проверяет способность системы памяти АМИ интерпретировать
        различные представления истинности, что имеет философское значение
        для формирования целостной картины мира.
        """
        # Создаем временные файлы с различными вариантами булевых значений
        test_cases = [
            ("true", True),
            ("True", True),
            ("TRUE", True),
            ("yes", True),
            ("Yes", True),
            ("YES", True),
            ("1", True),
            ("false", False),
            ("False", False),
            ("FALSE", False),
            ("no", False),
            ("No", False),
            ("NO", False),
            ("0", False),
            ("", False),
            ("anything_else", False),
        ]
        
        for value_str, expected_bool in test_cases:
            with tempfile.NamedTemporaryFile(mode='w+', delete=False) as temp_file:
                temp_file.write(f"DB_ECHO_SQL={value_str}\n")
                temp_file_path = temp_file.name
            
            try:
                # Загружаем конфигурацию из файла
                config = load_config(config_file=temp_file_path)
                
                # Проверяем преобразование в булевый тип
                assert config.DB_ECHO_SQL is expected_bool, f"Значение '{value_str}' должно преобразовываться в {expected_bool}"
            
            finally:
                # Удаляем временный файл
                if os.path.exists(temp_file_path):
                    os.unlink(temp_file_path)


if __name__ == "__main__":
    pytest.main(["-xvs", __file__])