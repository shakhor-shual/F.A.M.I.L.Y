#!/bin/bash

# Скрипт для запуска тестов SchemaManager с подключением к реальной БД PostgreSQL
# Этот скрипт настраивает переменные окружения и запускает тесты для SchemaManager

# Функция для вывода сообщений об ошибках и выхода
error_exit() {
    echo "ОШИБКА: $1" >&2
    exit 1
}

# Активируем виртуальное окружение, если оно существует
if [ -d ".venv" ]; then
    echo "Активация виртуального окружения..."
    source .venv/bin/activate || error_exit "Не удалось активировать виртуальное окружение"
fi

# Запрос учетных данных администратора PostgreSQL
read -p "Введите имя пользователя PostgreSQL с правами администратора [family_admin]: " DB_ADMIN_USER
DB_ADMIN_USER=${DB_ADMIN_USER:-family_admin}

read -s -p "Введите пароль для пользователя $DB_ADMIN_USER: " DB_ADMIN_PASSWORD
echo ""

# Запрос информации о подключении
read -p "Введите хост БД [localhost]: " DB_HOST
DB_HOST=${DB_HOST:-localhost}

read -p "Введите порт БД [5432]: " DB_PORT
DB_PORT=${DB_PORT:-5432}

read -p "Введите имя тестовой базы данных [family_db]: " DB_NAME
DB_NAME=${DB_NAME:-family_db}

# Экспорт переменных окружения для тестов - устанавливаем все необходимые переменные
export TEST_DB_USER=$DB_ADMIN_USER
export TEST_DB_PASSWORD=$DB_ADMIN_PASSWORD
export TEST_DB_HOST=$DB_HOST
export TEST_DB_PORT=$DB_PORT
export TEST_DB_NAME=$DB_NAME

# Дополнительно устанавливаем переменные, используемые в SchemaManager
export DB_ADMIN_USER=$DB_ADMIN_USER
export DB_ADMIN_PASSWORD=$DB_ADMIN_PASSWORD

# Устанавливаем переменную окружения, указывающую что запускаются тесты
export FAMILY_TEST_MODE=1

# Проверяем доступность базы данных
echo "Проверка подключения к базе данных..."
PGPASSWORD=$DB_ADMIN_PASSWORD psql -U $DB_ADMIN_USER -h $DB_HOST -p $DB_PORT -c '\conninfo' postgres &> /dev/null

if [ $? -ne 0 ]; then
    error_exit "Не удалось подключиться к PostgreSQL. Проверьте учетные данные и доступность сервера."
fi

# Создаем тестовую базу данных, если она не существует
echo "Проверка существования тестовой базы данных..."
DB_EXISTS=$(PGPASSWORD=$DB_ADMIN_PASSWORD psql -U $DB_ADMIN_USER -h $DB_HOST -p $DB_PORT -tAc "SELECT 1 FROM pg_database WHERE datname='$DB_NAME'" postgres)

if [ -z "$DB_EXISTS" ]; then
    echo "Создание тестовой базы данных $DB_NAME..."
    PGPASSWORD=$DB_ADMIN_PASSWORD psql -U $DB_ADMIN_USER -h $DB_HOST -p $DB_PORT -c "CREATE DATABASE $DB_NAME" postgres
    
    if [ $? -ne 0 ]; then
        error_exit "Не удалось создать тестовую базу данных $DB_NAME"
    fi
fi

# Запускаем тесты
echo "Запуск тестов SchemaManager с реальной БД..."
pytest -xvs undermaind/tests/core/test_schema_manager.py

# Очистка после тестов
echo "Тесты завершены. Хотите удалить тестовую базу данных $DB_NAME? (y/N)"
read DELETE_DB

if [ "$DELETE_DB" == "y" ] || [ "$DELETE_DB" == "Y" ]; then
    echo "Удаление тестовой базы данных $DB_NAME..."
    PGPASSWORD=$DB_ADMIN_PASSWORD psql -U $DB_ADMIN_USER -h $DB_HOST -p $DB_PORT -c "DROP DATABASE IF EXISTS $DB_NAME" postgres
    echo "База данных удалена."
fi

echo "Готово!"