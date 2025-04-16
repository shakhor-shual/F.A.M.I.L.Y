-- ============================================================================
-- СОЗДАНИЕ БАЗЫ ДАННЫХ ДЛЯ ПРОЕКТА F.A.M.I.L.Y.
-- Дата создания: 12 апреля 2025 г.
-- ============================================================================

-- Проверка на существование базы данных и её создание при отсутствии
DO $$ 
BEGIN
    IF NOT EXISTS (SELECT FROM pg_database WHERE datname = 'family_memory_db') THEN
        CREATE DATABASE family_memory_db
        WITH 
        OWNER = postgres
        ENCODING = 'UTF8'
        TEMPLATE = template0
        LC_COLLATE = 'ru_RU.UTF-8'
        LC_CTYPE = 'ru_RU.UTF-8'
        TABLESPACE = pg_default
        CONNECTION LIMIT = -1;
        
        COMMENT ON DATABASE family_memory_db IS 'База данных для хранения воспоминаний АМИ (проект F.A.M.I.L.Y.)';
    END IF;
END $$;

-- Установка расширений для работы с векторами
\c family_memory_db

-- Проверка на существование расширения pgvector и его установка при отсутствии
CREATE EXTENSION IF NOT EXISTS vector;