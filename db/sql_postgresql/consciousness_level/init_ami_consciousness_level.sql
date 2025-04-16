-- ============================================================================
-- ПРОЦЕДУРЫ ИНИЦИАЛИЗАЦИИ УРОВНЯ СОЗНАНИЯ ДЛЯ ПРОЕКТА F.A.M.I.L.Y.
-- Дата создания: 16 апреля 2025 г.
-- Автор: Команда проекта F.A.M.I.L.Y.
-- ============================================================================
-- Этот скрипт содержит процедуры для создания и инициализации компонентов
-- уровня сознания АМИ. Разбиение на процедуры обеспечивает модульность и гибкость
-- при развертывании и обновлении структуры базы данных.
-- ============================================================================

-- Главная процедура инициализации уровня сознания
-- Принимает параметры для создания пользователя АМИ и настройки прав
CREATE OR REPLACE PROCEDURE public.init_ami_consciousness_level(
    ami_name TEXT, 
    ami_password TEXT DEFAULT NULL,
    schema_name TEXT DEFAULT NULL,
    grant_permissions BOOLEAN DEFAULT TRUE
)
LANGUAGE plpgsql
AS $$
DECLARE
    v_schema_name TEXT;
    procedure_exists BOOLEAN;
    user_exists BOOLEAN;
    schema_exists BOOLEAN;
    sql_command TEXT;
BEGIN
    -- Определяем имя схемы если не указано
    v_schema_name := COALESCE(schema_name, 'ami_' || ami_name);

    -- Создание расширения vector если оно не существует
    CREATE EXTENSION IF NOT EXISTS vector;

    -- Проверка существования схемы
    SELECT EXISTS (
        SELECT FROM pg_namespace WHERE nspname = v_schema_name
    ) INTO schema_exists;
    
    -- Если схема не существует, создаем её
    IF NOT schema_exists THEN
        sql_command := 'CREATE SCHEMA ' || quote_ident(v_schema_name);
        EXECUTE sql_command;
        RAISE NOTICE 'Схема % успешно создана', v_schema_name;
    ELSE
        RAISE NOTICE 'Схема % уже существует', v_schema_name;
    END IF;

    -- Проверка существования пользователя АМИ
    SELECT EXISTS (
        SELECT FROM pg_catalog.pg_roles WHERE rolname = ami_name
    ) INTO user_exists;
    
    -- Если пользователь не существует и указан пароль, создаем пользователя
    IF NOT user_exists AND ami_password IS NOT NULL THEN
        sql_command := 'CREATE USER ' || quote_ident(ami_name) || ' WITH PASSWORD ' || quote_literal(ami_password);
        EXECUTE sql_command;
        RAISE NOTICE 'Пользователь % успешно создан', ami_name;
    ELSIF NOT user_exists AND ami_password IS NULL THEN
        RAISE WARNING 'Пользователь % не существует, а пароль не указан. Пользователь не создан', ami_name;
    ELSE
        RAISE NOTICE 'Пользователь % уже существует', ami_name;
    END IF;
    
    -- Вызов процедуры создания базовых структур из схемы public
    IF EXISTS (
        SELECT FROM pg_catalog.pg_proc p
        JOIN pg_catalog.pg_namespace n ON p.pronamespace = n.oid
        WHERE n.nspname = 'public' AND p.proname = 'create_ami_consciousness_base_structures'
    ) THEN
        EXECUTE format('CALL public.create_ami_consciousness_base_structures(%L)', v_schema_name);
        RAISE NOTICE 'Базовые структуры уровня сознания успешно созданы';
    ELSE
        RAISE WARNING 'Процедура create_ami_consciousness_base_structures не найдена в схеме public. Базовые структуры не созданы';
    END IF;

    -- Вызов процедуры создания структуры опыта из схемы public
    IF EXISTS (
        SELECT FROM pg_catalog.pg_proc p
        JOIN pg_catalog.pg_namespace n ON p.pronamespace = n.oid
        WHERE n.nspname = 'public' AND p.proname = 'create_ami_experience_structure'
    ) THEN
        EXECUTE format('CALL public.create_ami_experience_structure(%L)', v_schema_name);
        RAISE NOTICE 'Структуры опыта успешно созданы';
    ELSE
        RAISE WARNING 'Процедура create_ami_experience_structure не найдена в схеме public. Структуры опыта не созданы';
    END IF;

    -- Вызов процедуры создания структур мышления из схемы public
    IF EXISTS (
        SELECT FROM pg_catalog.pg_proc p
        JOIN pg_catalog.pg_namespace n ON p.pronamespace = n.oid
        WHERE n.nspname = 'public' AND p.proname = 'create_ami_thinking_structures'
    ) THEN
        EXECUTE format('CALL public.create_ami_thinking_structures(%L)', v_schema_name);
        RAISE NOTICE 'Структуры мышления успешно созданы';
    ELSE
        RAISE WARNING 'Процедура create_ami_thinking_structures не найдена в схеме public. Структуры мышления не созданы';
    END IF;

    -- Вызов процедуры создания ассоциативных структур из схемы public
    IF EXISTS (
        SELECT FROM pg_catalog.pg_proc p
        JOIN pg_catalog.pg_namespace n ON p.pronamespace = n.oid
        WHERE n.nspname = 'public' AND p.proname = 'create_ami_association_structures'
    ) THEN
        EXECUTE format('CALL public.create_ami_association_structures(%L)', v_schema_name);
        RAISE NOTICE 'Ассоциативные структуры успешно созданы';
    ELSE
        RAISE WARNING 'Процедура create_ami_association_structures не найдена в схеме public. Ассоциативные структуры не созданы';
    END IF;

    -- Вызов процедуры создания представлений из схемы public
    IF EXISTS (
        SELECT FROM pg_catalog.pg_proc p
        JOIN pg_catalog.pg_namespace n ON p.pronamespace = n.oid
        WHERE n.nspname = 'public' AND p.proname = 'create_ami_consciousness_views'
    ) THEN
        EXECUTE format('CALL public.create_ami_consciousness_views(%L)', v_schema_name);
        RAISE NOTICE 'Представления уровня сознания успешно созданы';
    ELSE
        RAISE WARNING 'Процедура create_ami_consciousness_views не найдена в схеме public. Представления не созданы';
    END IF;
    
    -- Если нужно назначить права пользователю АМИ
    IF grant_permissions AND EXISTS (SELECT FROM pg_catalog.pg_roles WHERE rolname = ami_name) THEN
        -- Даем пользователю права на использование схемы
        sql_command := 'GRANT USAGE ON SCHEMA ' || quote_ident(v_schema_name) || ' TO ' || quote_ident(ami_name);
        EXECUTE sql_command;
        
        -- Даем права на все существующие таблицы в схеме
        sql_command := 'GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA ' || quote_ident(v_schema_name) || ' TO ' || quote_ident(ami_name);
        EXECUTE sql_command;
        
        -- Даем права на все последовательности в схеме
        sql_command := 'GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA ' || quote_ident(v_schema_name) || ' TO ' || quote_ident(ami_name);
        EXECUTE sql_command;
        
        -- Устанавливаем права по умолчанию для новых объектов
        sql_command := 'ALTER DEFAULT PRIVILEGES IN SCHEMA ' || quote_ident(v_schema_name) || 
                      ' GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO ' || quote_ident(ami_name);
        EXECUTE sql_command;
        
        sql_command := 'ALTER DEFAULT PRIVILEGES IN SCHEMA ' || quote_ident(v_schema_name) || 
                      ' GRANT USAGE, SELECT ON SEQUENCES TO ' || quote_ident(ami_name);
        EXECUTE sql_command;
        
        RAISE NOTICE 'Права для пользователя % успешно настроены', ami_name;
    ELSIF grant_permissions THEN
        RAISE WARNING 'Пользователь % не существует, права не настроены', ami_name;
    END IF;
    
    RAISE NOTICE 'Инициализация уровня сознания АМИ завершена';
END;
$$;

-- Добавляем комментарий к процедуре
COMMENT ON PROCEDURE public.init_ami_consciousness_level(TEXT, TEXT, TEXT, BOOLEAN) IS 
'Процедура инициализации уровня сознания АМИ.
Создает схему и пользователя АМИ, а затем вызывает все необходимые процедуры
для создания структур данных уровня сознания.

Параметры:
- ami_name: имя пользователя АМИ
- ami_password: пароль пользователя АМИ (опционально)
- schema_name: имя схемы (по умолчанию ami_{ami_name})
- grant_permissions: нужно ли назначать права доступа (по умолчанию true)';
