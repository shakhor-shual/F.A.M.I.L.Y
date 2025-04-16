-- ============================================================================
-- СОЗДАНИЕ СХЕМЫ ДЛЯ ПАМЯТИ АМИ В ПРОЕКТЕ F.A.M.I.L.Y.
-- Дата создания: 12 апреля 2025 г.
-- ============================================================================

\set QUIET on
\set ON_ERROR_STOP on
\set QUIET off

-- Проверяем существование схемы
SELECT EXISTS(SELECT 1 FROM pg_namespace WHERE nspname = :'ami_schema_name') as schema_exists \gset

-- Создаем схему с именем, если она не существует
\if :schema_exists
    \echo 'NOTICE: Схема' :ami_schema_name 'уже существует'
\else
    CREATE SCHEMA :"ami_schema_name";
    \echo 'NOTICE: Создана схема' :ami_schema_name
\endif

-- Установка созданной схемы как текущей для последующих операций
SET search_path TO :"ami_schema_name", public;