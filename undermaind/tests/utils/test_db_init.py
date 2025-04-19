"""
Тесты для модуля db_init.py, отвечающего за инициализацию базы данных F.A.M.I.L.Y.

Эти тесты проверяют работу класса DatabaseInitializer и его методов.
"""
import os
import pytest
import tempfile
from pathlib import Path
from unittest import mock

from undermaind.utils.db_init import DatabaseInitializer

class TestDatabaseInitializer:
    """Тесты для класса DatabaseInitializer"""

    def test_init_with_direct_params(self):
        """Тест инициализации с прямыми параметрами"""
        # Создание объекта с прямыми параметрами
        db_init = DatabaseInitializer(
            db_host="test_host",
            db_port=1234,
            db_name="test_db",
            admin_user="test_user",
            admin_password="test_password"
        )
        
        # Проверка правильности сохранения параметров
        assert db_init.db_host == "test_host"
        assert db_init.db_port == 1234
        assert db_init.db_name == "test_db"
        assert db_init.admin_user == "test_user"
        assert db_init.admin_password == "test_password"

    def test_init_with_config_path(self, tmp_path):
        """Тест инициализации с использованием конфигурационного файла"""
        # Создаем временный конфигурационный файл
        config_path = tmp_path / "test_config.env"
        with open(config_path, 'w') as f:
            f.write("""
FAMILY_DB_HOST="config_host"
FAMILY_DB_PORT=5678
FAMILY_DB_NAME="config_db"
FAMILY_ADMIN_USER="config_user"
FAMILY_ADMIN_PASSWORD="config_pass"
            """)
        
        # Создание объекта с путем к конфигурационному файлу
        db_init = DatabaseInitializer(config_path=str(config_path))
        
        # Проверка правильности параметров из конфигурации
        assert db_init.db_host == "config_host"
        assert db_init.db_port == 5678
        assert db_init.db_name == "config_db"
        assert db_init.admin_user == "config_user"
        assert db_init.admin_password == "config_pass"

    @mock.patch('undermaind.utils.db_init.psycopg2.connect')
    def test_check_connection_success(self, mock_connect):
        """Тест успешной проверки подключения"""
        # Настройка мока для успешного подключения
        mock_cursor = mock.MagicMock()
        mock_cursor.execute.return_value = None
        mock_connection = mock.MagicMock()
        mock_connection.__enter__.return_value = mock_connection
        mock_connection.cursor.return_value.__enter__.return_value = mock_cursor
        mock_connect.return_value = mock_connection
        
        db_init = DatabaseInitializer()
        
        # Проверка успешного подключения
        result = db_init.check_connection()
        assert result is True
        
        # Проверка вызовов функций
        mock_connect.assert_called_once()
        mock_cursor.execute.assert_called_once_with("SELECT 1")

    @mock.patch('undermaind.utils.db_init.psycopg2.connect')
    def test_check_connection_failure(self, mock_connect):
        """Тест неудачной проверки подключения"""
        # Настройка мока для неудачного подключения
        mock_connect.side_effect = Exception("Connection error")
        
        db_init = DatabaseInitializer()
        
        # Проверка неудачного подключения
        result = db_init.check_connection()
        assert result is False

    @mock.patch('undermaind.utils.db_init.psycopg2.connect')
    def test_database_exists_true(self, mock_connect):
        """Тест проверки существования базы данных - существует"""
        # Настройка мока для проверки существования базы данных
        mock_cursor = mock.MagicMock()
        mock_cursor.fetchone.return_value = (1,)
        mock_connection = mock.MagicMock()
        mock_connection.__enter__.return_value = mock_connection
        mock_connection.cursor.return_value.__enter__.return_value = mock_cursor
        mock_connect.return_value = mock_connection
        
        db_init = DatabaseInitializer(db_name="test_db")
        
        # Проверка существования базы данных
        result = db_init.database_exists()
        assert result is True
        
        # Проверка вызовов функций
        mock_connect.assert_called_once()
        mock_cursor.execute.assert_called_once_with(
            "SELECT 1 FROM pg_database WHERE datname = %s", 
            ("test_db",)
        )

    @mock.patch('undermaind.utils.db_init.psycopg2.connect')
    def test_database_exists_false(self, mock_connect):
        """Тест проверки существования базы данных - не существует"""
        # Настройка мока для проверки отсутствия базы данных
        mock_cursor = mock.MagicMock()
        mock_cursor.fetchone.return_value = None
        mock_connection = mock.MagicMock()
        mock_connection.__enter__.return_value = mock_connection
        mock_connection.cursor.return_value.__enter__.return_value = mock_cursor
        mock_connect.return_value = mock_connection
        
        db_init = DatabaseInitializer(db_name="test_db")
        
        # Проверка отсутствия базы данных
        result = db_init.database_exists()
        assert result is False

    @mock.patch('undermaind.utils.db_init.psycopg2.connect')
    def test_create_admin_user_exists(self, mock_connect):
        """Тест создания пользователя-администратора - уже существует"""
        # Настройка мока для проверки существования пользователя
        mock_cursor = mock.MagicMock()
        mock_cursor.fetchone.return_value = (1,)
        mock_connection = mock.MagicMock()
        mock_connection.__enter__.return_value = mock_connection
        mock_connection.cursor.return_value.__enter__.return_value = mock_cursor
        mock_connect.return_value = mock_connection
        
        db_init = DatabaseInitializer(admin_user="test_user")
        
        # Проверка создания существующего пользователя
        result = db_init.create_admin_user()
        assert result is True
        
        # Проверка вызовов функций
        mock_connect.assert_called_once()
        mock_cursor.execute.assert_called_once_with(
            "SELECT 1 FROM pg_roles WHERE rolname = %s", 
            ("test_user",)
        )

    @mock.patch('undermaind.utils.db_init.psycopg2.connect')
    def test_create_admin_user_new(self, mock_connect):
        """Тест создания нового пользователя-администратора"""
        # Настройка мока для создания нового пользователя
        mock_cursor = mock.MagicMock()
        mock_cursor.fetchone.return_value = None  # Пользователь не существует
        mock_connection = mock.MagicMock()
        mock_connection.__enter__.return_value = mock_connection
        mock_connection.cursor.return_value.__enter__.return_value = mock_cursor
        mock_connect.return_value = mock_connection
        
        db_init = DatabaseInitializer(admin_user="test_user", admin_password="test_password")
        
        # Проверка создания нового пользователя
        result = db_init.create_admin_user()
        assert result is True
        
        # Проверка вызовов функций
        assert mock_cursor.execute.call_count == 2
        # Первый вызов - проверка существования
        # Второй вызов - создание пользователя

    @mock.patch('undermaind.utils.db_init.DatabaseInitializer.database_exists')
    @mock.patch('undermaind.utils.db_init.psycopg2.connect')
    def test_create_database(self, mock_connect, mock_exists):
        """Тест создания базы данных"""
        # Настройка моков
        mock_exists.return_value = False  # База данных не существует
        mock_cursor = mock.MagicMock()
        mock_connection = mock.MagicMock()
        mock_connection.autocommit = False
        mock_connection.cursor.return_value = mock_cursor
        mock_connect.return_value = mock_connection
        
        db_init = DatabaseInitializer(db_name="test_db", admin_user="test_user")
        
        # Проверка создания базы данных
        result = db_init.create_database()
        assert result is True
        
        # Проверка вызовов функций
        mock_exists.assert_called_once()
        mock_connect.assert_called_once()
        mock_cursor.execute.assert_called_once_with('CREATE DATABASE test_db OWNER test_user')
        assert mock_connection.autocommit is True

    @mock.patch('undermaind.utils.db_init.DatabaseInitializer.database_exists')
    def test_create_database_already_exists(self, mock_exists):
        """Тест создания базы данных - уже существует"""
        # Настройка мока - база данных существует
        mock_exists.return_value = True
        
        db_init = DatabaseInitializer()
        
        # Проверка создания существующей базы данных
        result = db_init.create_database()
        assert result is True
        
        # Проверка вызовов функций
        mock_exists.assert_called_once()

    @mock.patch('undermaind.utils.db_init.Path.exists')
    def test_refresh_stored_procedures_success(self, mock_exists):
        """Тест успешного обновления хранимых процедур"""
        # Создаем временный файл для моков
        with tempfile.NamedTemporaryFile() as temp_file:
            # Настройка моков для симуляции успешного выполнения
            mock_exists.return_value = True
            
            # Подменяем методы, которые не нужно тестировать
            with mock.patch.object(DatabaseInitializer, 'database_exists', return_value=True) as mock_db_exists, \
                 mock.patch.object(DatabaseInitializer, '_get_database_connection') as mock_get_conn, \
                 mock.patch.object(DatabaseInitializer, 'filter_procedure_scripts', return_value=['test_proc.sql']) as mock_filter, \
                 mock.patch('builtins.open', mock.mock_open(read_data='CREATE OR REPLACE PROCEDURE test_proc() LANGUAGE SQL AS $$ SELECT 1; $$;')):
                
                # Настройка мока для подключения к БД
                mock_cursor = mock.MagicMock()
                mock_connection = mock.MagicMock()
                mock_connection.__enter__.return_value = mock_connection
                mock_connection.cursor.return_value.__enter__.return_value = mock_cursor
                mock_get_conn.return_value = mock_connection
                
                db_init = DatabaseInitializer()
                
                # Проверка обновления процедур
                result = db_init.refresh_stored_procedures()
                assert result is True
                
                # Проверка вызовов функций
                mock_db_exists.assert_called_once()
                assert mock_filter.called
                assert mock_cursor.execute.called
                assert mock_connection.commit.called
                
    @mock.patch('undermaind.utils.db_init.DatabaseInitializer.check_connection', return_value=True)
    @mock.patch('undermaind.utils.db_init.DatabaseInitializer.create_admin_user', return_value=True)
    @mock.patch('undermaind.utils.db_init.DatabaseInitializer.database_exists')
    @mock.patch('undermaind.utils.db_init.DatabaseInitializer.create_database', return_value=True)
    @mock.patch('undermaind.utils.db_init.Path.exists', return_value=True)
    @mock.patch('undermaind.utils.db_init.DatabaseInitializer.apply_sql_scripts', return_value=True)
    def test_initialize_database_new(self, mock_apply, mock_path_exists, mock_create_db, 
                                    mock_db_exists, mock_create_user, mock_check_conn):
        """Тест инициализации новой базы данных"""
        # Настройка моков
        mock_db_exists.return_value = False  # База данных не существует
        
        # Подготавливаем содержимое для имитации чтения init.conf
        with mock.patch('builtins.open', mock.mock_open(read_data='level1\nlevel2')):
            db_init = DatabaseInitializer()
            
            # Проверка инициализации
            result = db_init.initialize_database()
            assert result is True
            
            # Проверка вызовов функций
            mock_check_conn.assert_called_once()
            mock_create_user.assert_called_once()
            mock_db_exists.assert_called_once()
            mock_create_db.assert_called_once()
            assert mock_apply.call_count == 2  # По одному вызову на каждый уровень

    @mock.patch('undermaind.utils.db_init.DatabaseInitializer.check_connection', return_value=True)
    @mock.patch('undermaind.utils.db_init.DatabaseInitializer.create_admin_user', return_value=True)
    @mock.patch('undermaind.utils.db_init.DatabaseInitializer.database_exists')
    @mock.patch('undermaind.utils.db_init.DatabaseInitializer.drop_database', return_value=True)
    @mock.patch('undermaind.utils.db_init.DatabaseInitializer.create_database', return_value=True)
    @mock.patch('undermaind.utils.db_init.Path.exists', return_value=True)
    @mock.patch('undermaind.utils.db_init.DatabaseInitializer.apply_sql_scripts', return_value=True)
    def test_initialize_database_recreate(self, mock_apply, mock_path_exists, mock_create_db, 
                                         mock_drop_db, mock_db_exists, mock_create_user, mock_check_conn):
        """Тест пересоздания базы данных"""
        # Настройка моков
        mock_db_exists.return_value = True  # База данных существует
        
        # Подготавливаем содержимое для имитации чтения init.conf
        with mock.patch('builtins.open', mock.mock_open(read_data='level1\nlevel2')):
            db_init = DatabaseInitializer()
            
            # Проверка инициализации с пересозданием
            result = db_init.initialize_database(recreate=True)
            assert result is True
            
            # Проверка вызовов функций
            mock_check_conn.assert_called_once()
            mock_create_user.assert_called_once()
            mock_drop_db.assert_called_once_with(force=True)
            mock_db_exists.assert_called_once()
            mock_create_db.assert_called_once()
            assert mock_apply.call_count == 2  # По одному вызову на каждый уровень