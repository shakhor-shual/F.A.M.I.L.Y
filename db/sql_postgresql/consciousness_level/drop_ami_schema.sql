-- ============================================================================
-- ХРАНИМАЯ ПРОЦЕДУРА ДЛЯ УДАЛЕНИЯ СХЕМЫ АМИ В ПРОЕКТЕ F.A.M.I.L.Y.
-- Дата создания: 15 апреля 2025 г.
-- Автор: Команда проекта F.A.M.I.L.Y.
-- Обновлено: 16 апреля 2025 г. - исправление проблемы с удалением пользователя АМИ с сохранением зависимостей
-- ============================================================================
-- Эта процедура удаляет схему и пользователя АМИ, включая все связанные объекты,
-- из базы данных FAMILY. Используйте эту процедуру с осторожностью, так как
-- она необратимо удаляет все данные памяти АМИ.
-- ============================================================================

\set QUIET on
\set ON_ERROR_STOP on
\set QUIET off

-- Создаем хранимую процедуру для удаления схемы и пользователя АМИ
CREATE OR REPLACE PROCEDURE drop_ami_schema(ami_name TEXT, force_mode BOOLEAN DEFAULT FALSE)
LANGUAGE plpgsql
AS $$
DECLARE
    schema_name TEXT;
    user_exists BOOLEAN;
    schema_exists BOOLEAN;
    obj_count INTEGER;
    conn_count INTEGER;
    prev_object TEXT;
    obj_record RECORD;
BEGIN
    -- Устанавливаем имя схемы с правильным префиксом ami_
    schema_name := 'ami_' || ami_name;
    
    -- Проверяем, существует ли схема с таким именем
    SELECT EXISTS(SELECT 1 FROM pg_namespace WHERE nspname = schema_name) INTO schema_exists;
    
    -- Проверяем, существует ли пользователь с таким именем
    SELECT EXISTS(SELECT 1 FROM pg_roles WHERE rolname = ami_name) INTO user_exists;
    
    -- Если ни схемы, ни пользователя не существует, выводим предупреждение и завершаем
    IF NOT schema_exists AND NOT user_exists THEN
        RAISE NOTICE 'АМИ "%" не существует: ни схемы, ни пользователя с таким именем не найдено', ami_name;
        RETURN;
    END IF;
    
    -- Если схема существует, проверяем количество объектов перед удалением
    IF schema_exists THEN
        -- Получаем общее количество объектов в схеме
        EXECUTE format('
            SELECT 
                (SELECT COUNT(*) FROM pg_tables WHERE schemaname = %L) +
                (SELECT COUNT(*) FROM pg_views WHERE schemaname = %L) +
                (SELECT COUNT(*) FROM pg_proc WHERE pronamespace = %L::regnamespace)', 
            schema_name, schema_name, schema_name) INTO obj_count;
            
        -- Получаем количество активных подключений к схеме
        SELECT COUNT(*) INTO conn_count 
        FROM pg_stat_activity 
        WHERE application_name LIKE 'ami_' || ami_name || '%'
        OR usename = ami_name;
        
        -- Если есть активные подключения и force_mode отключен, выводим предупреждение
        IF conn_count > 0 AND NOT force_mode THEN
            RAISE WARNING 'Обнаружены активные подключения к схеме % (количество: %)', schema_name, conn_count;
            RAISE WARNING 'Выполнение остановлено. Для принудительного удаления используйте force_mode=TRUE';
            RETURN;
        END IF;
        
        -- Если force_mode включен, принудительно закрываем все подключения
        IF conn_count > 0 AND force_mode THEN
            RAISE NOTICE 'Принудительное закрытие % активных подключений к схеме %', conn_count, schema_name;
            
            -- Завершаем все подключения к схеме
            FOR i IN 1..3 LOOP -- Пробуем несколько раз, так как некоторые подключения могут быть устойчивыми
                PERFORM pg_terminate_backend(pid) 
                FROM pg_stat_activity 
                WHERE application_name LIKE 'ami_' || ami_name || '%'
                OR usename = ami_name;
            END LOOP;
        END IF;
        
        -- ВАЖНОЕ ИСПРАВЛЕНИЕ: Перед удалением схемы, мы принудительно отзываем все привилегии пользователя АМИ
        -- на всех объектах схемы. Это позволяет избежать ошибки при удалении пользователя с зависимостями.
        IF user_exists THEN
            BEGIN
                -- Отзываем привилегии пользователя на схему
                EXECUTE format('REVOKE ALL ON SCHEMA %I FROM %I', schema_name, ami_name);
                
                -- Отзываем привилегии на все таблицы в схеме
                EXECUTE format('REVOKE ALL ON ALL TABLES IN SCHEMA %I FROM %I', schema_name, ami_name);
                
                -- Отзываем привилегии на все последовательности в схеме
                EXECUTE format('REVOKE ALL ON ALL SEQUENCES IN SCHEMA %I FROM %I', schema_name, ami_name);
                
                -- Отзываем привилегии на все функции в схеме
                EXECUTE format('REVOKE ALL ON ALL FUNCTIONS IN SCHEMA %I FROM %I', schema_name, ami_name);
                
                -- Отзываем привилегии на все хранимые процедуры в схеме
                EXECUTE format('REVOKE ALL ON ALL PROCEDURES IN SCHEMA %I FROM %I', schema_name, ami_name);
                
                -- Отзываем привилегии на все типы в схеме
                EXECUTE format('REVOKE ALL ON ALL TYPES IN SCHEMA %I FROM %I', schema_name, ami_name);
                
                -- Сбрасываем стандартные привилегии для пользователя в схеме
                EXECUTE format('ALTER DEFAULT PRIVILEGES FOR ROLE %I IN SCHEMA %I REVOKE ALL ON TABLES FROM %I',
                              current_user, schema_name, ami_name);
                EXECUTE format('ALTER DEFAULT PRIVILEGES FOR ROLE %I IN SCHEMA %I REVOKE ALL ON SEQUENCES FROM %I',
                              current_user, schema_name, ami_name);
                EXECUTE format('ALTER DEFAULT PRIVILEGES FOR ROLE %I IN SCHEMA %I REVOKE ALL ON FUNCTIONS FROM %I',
                              current_user, schema_name, ami_name);
                EXECUTE format('ALTER DEFAULT PRIVILEGES FOR ROLE %I IN SCHEMA %I REVOKE ALL ON TYPES FROM %I',
                              current_user, schema_name, ami_name);
            EXCEPTION
                WHEN OTHERS THEN
                    RAISE NOTICE 'Предупреждение при отзыве привилегий: %', SQLERRM;
            END;
        END IF;
        
        -- Удаляем схему со всеми объектами (в режиме CASCADE)
        RAISE NOTICE 'Удаление схемы % (содержит % объектов)...', schema_name, obj_count;
        EXECUTE format('DROP SCHEMA %I CASCADE', schema_name);
        RAISE NOTICE 'Схема % успешно удалена', schema_name;
    ELSE
        RAISE NOTICE 'Схема % не существует', schema_name;
    END IF;
    
    -- Если пользователь существует, удаляем его
    IF user_exists THEN
        -- Проверяем, остались ли объекты, принадлежащие пользователю
        EXECUTE format('
            SELECT COUNT(*) 
            FROM pg_catalog.pg_class c 
            JOIN pg_catalog.pg_namespace n ON n.oid = c.relnamespace 
            WHERE n.nspname != ''pg_catalog'' 
            AND n.nspname != ''information_schema'' 
            AND c.relowner = (SELECT oid FROM pg_roles WHERE rolname = %L)', 
            ami_name) INTO obj_count;
            
        -- Если у пользователя остались объекты и force_mode отключен, выводим предупреждение
        IF obj_count > 0 AND NOT force_mode THEN
            RAISE WARNING 'Пользователь % владеет % объектами за пределами удаленной схемы', ami_name, obj_count;
            RAISE WARNING 'Выполнение остановлено. Для принудительного удаления используйте force_mode=TRUE';
            RETURN;
        END IF;
        
        -- Отзыв привилегий пользователя на объекты в схеме public
        RAISE NOTICE 'Отзыв привилегий пользователя % на объекты в схеме public...', ami_name;
        
        BEGIN
            -- 1. Отзыв привилегий на схему public
            EXECUTE format('REVOKE ALL ON SCHEMA public FROM %I', ami_name);
            
            -- 2. Отзыв привилегий на тип vector
            BEGIN
                EXECUTE format('REVOKE USAGE ON TYPE public.vector FROM %I', ami_name);
            EXCEPTION
                WHEN OTHERS THEN
                    RAISE NOTICE 'Предупреждение при отзыве привилегий на тип vector: %', SQLERRM;
            END;
            
            -- 3. Отзыв всех привилегий на функции pgvector
            -- Получаем список всех функций, на которые пользователь имеет привилегии
            FOR obj_record IN 
                SELECT 
                    p.proname, 
                    pg_catalog.pg_get_function_identity_arguments(p.oid) AS args
                FROM 
                    pg_proc p
                    JOIN pg_namespace n ON p.pronamespace = n.oid
                    JOIN (
                        SELECT (aclexplode(proacl)).grantee, (aclexplode(proacl)).grantor, oid 
                        FROM pg_proc 
                        WHERE proacl IS NOT NULL
                    ) privs ON privs.oid = p.oid
                    JOIN pg_roles r ON privs.grantee = r.oid
                WHERE 
                    n.nspname = 'public' AND
                    r.rolname = ami_name
            LOOP
                -- Сравниваем с предыдущим объектом, чтобы избежать дублирования для перегруженных функций
                IF prev_object IS DISTINCT FROM (obj_record.proname || obj_record.args) THEN
                    BEGIN
                        -- Отзыв привилегий на функцию
                        IF obj_record.args IS NOT NULL AND obj_record.args != '' THEN
                            EXECUTE format('REVOKE ALL ON FUNCTION public.%I(%s) FROM %I', 
                                        obj_record.proname, obj_record.args, ami_name);
                        ELSE
                            EXECUTE format('REVOKE ALL ON FUNCTION public.%I() FROM %I', 
                                        obj_record.proname, ami_name);
                        END IF;
                        prev_object := obj_record.proname || obj_record.args;
                    EXCEPTION
                        WHEN OTHERS THEN
                            RAISE NOTICE 'Предупреждение при отзыве привилегий на функцию %.%: %', 
                                        obj_record.proname, obj_record.args, SQLERRM;
                    END;
                END IF;
            END LOOP;
            
            -- 4. Отзыв привилегий на все функции в схеме public для упрощения
            BEGIN
                EXECUTE format('REVOKE ALL ON ALL FUNCTIONS IN SCHEMA public FROM %I', ami_name);
            EXCEPTION
                WHEN OTHERS THEN
                    -- Это не критично, так как мы уже попытались отозвать привилегии на отдельные функции
                    RAISE NOTICE 'Предупреждение при отзыве всех привилегий на функции: %', SQLERRM;
            END;
            
            -- 5. Отзыв действия от имени роли
            BEGIN
                EXECUTE 'RESET ROLE';  -- Сбрасываем текущую роль на всякий случай
                -- Проверяем, имеет ли пользователь привилегии INHERIT на другие роли
                FOR obj_record IN 
                    SELECT r2.rolname 
                    FROM pg_roles r1 
                    JOIN pg_auth_members m ON r1.oid = m.member 
                    JOIN pg_roles r2 ON m.roleid = r2.oid 
                    WHERE r1.rolname = ami_name
                LOOP
                    -- Отзыв наследования роли
                    EXECUTE format('REVOKE %I FROM %I', obj_record.rolname, ami_name);
                END LOOP;
            EXCEPTION
                WHEN OTHERS THEN
                    RAISE NOTICE 'Предупреждение при отзыве привилегий наследования ролей: %', SQLERRM;
            END;
        EXCEPTION
            WHEN OTHERS THEN
                RAISE NOTICE 'Некритичная ошибка при отзыве привилегий: %', SQLERRM;
        END;
        
        -- Удаляем пользователя
        RAISE NOTICE 'Удаление пользователя %...', ami_name;
        BEGIN
            EXECUTE format('DROP ROLE %I', ami_name);
            RAISE NOTICE 'Пользователь % успешно удален', ami_name;
        EXCEPTION
            WHEN OTHERS THEN
                -- Если удаление не удалось, пробуем с CASCADE
                IF force_mode THEN
                    BEGIN
                        RAISE NOTICE 'Попытка удаления пользователя % с CASCADE...', ami_name;
                        EXECUTE format('DROP ROLE %I CASCADE', ami_name);
                        RAISE NOTICE 'Пользователь % успешно удален с CASCADE', ami_name;
                    EXCEPTION
                        WHEN OTHERS THEN
                            RAISE EXCEPTION 'Не удалось удалить пользователя даже с CASCADE: %', SQLERRM;
                    END;
                ELSE
                    RAISE EXCEPTION 'Не удалось удалить пользователя: %', SQLERRM;
                END IF;
        END;
    ELSE
        RAISE NOTICE 'Пользователь % не существует', ami_name;
    END IF;
    
    -- Создание записи о выполнении операции
    -- Здесь можно добавить запись в системную таблицу или лог
    -- о том, что АМИ был удален (для аудита или отчетности)
    RAISE NOTICE '======================================================================';
    RAISE NOTICE 'АМИ "%" успешно удален из системы F.A.M.I.L.Y.', ami_name;
    RAISE NOTICE 'Дата удаления: %', NOW();
    RAISE NOTICE '======================================================================';
END;
$$;

-- Пример использования процедуры:
-- CALL drop_ami_schema('ami_test'); -- Обычный режим, проверяет наличие подключений
-- CALL drop_ami_schema('ami_test', TRUE); -- Принудительный режим, закрывает активные подключения