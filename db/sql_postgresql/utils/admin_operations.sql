-- Administrative operations for F.A.M.I.L.Y Database
-- This file contains parameterized SQL queries for database administration

-- Create temporary table for parameters if it doesn't exist
CREATE TEMP TABLE IF NOT EXISTS params (
    param_name text PRIMARY KEY,
    param_value text
);

-- Create admin user if not exists
DO $$
DECLARE
    v_user_name text;
    v_user_password text;
BEGIN
    -- Get parameters from temp table
    SELECT param_value INTO v_user_name FROM params WHERE param_name = 'user_name';
    SELECT param_value INTO v_user_password FROM params WHERE param_name = 'user_password';

    -- Create admin user if not exists
    IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = v_user_name) THEN
        EXECUTE format('CREATE USER %I WITH PASSWORD %L SUPERUSER CREATEDB CREATEROLE INHERIT LOGIN', 
            v_user_name, 
            v_user_password
        );
        RAISE NOTICE 'Created admin user: %', v_user_name;
    ELSE
        RAISE NOTICE 'Admin user % already exists', v_user_name;
    END IF;
END
$$;

-- Создание базы данных и настройка пользователя
DO $$ 
BEGIN
    -- Создание пользователя с параметрами
    IF NOT EXISTS (
        SELECT FROM pg_roles WHERE rolname = (SELECT param_value FROM params WHERE param_name = 'user_name')
    ) THEN
        EXECUTE format('CREATE USER %I WITH PASSWORD %L', 
            (SELECT param_value FROM params WHERE param_name = 'user_name'),
            (SELECT param_value FROM params WHERE param_name = 'user_password')
        );
    END IF;

    -- Установка расширения vector если не установлено
    CREATE EXTENSION IF NOT EXISTS vector;
END $$;