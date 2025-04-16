-- ============================================================================
-- ПРОЦЕДУРА СОЗДАНИЯ СТРУКТУР МЫШЛЕНИЯ СОЗНАТЕЛЬНОГО УРОВНЯ
-- ============================================================================
-- Создает таблицы для процессов мышления и фаз мышления:
-- 1. Процессы мышления (thinking_processes)
-- 2. Фазы мышления (thinking_phases)
-- ============================================================================

CREATE OR REPLACE PROCEDURE public.create_ami_thinking_structures(schema_name TEXT)
LANGUAGE plpgsql
AS $$
BEGIN
    -- =================================================================
    -- Таблица для хранения процессов мышления
    -- Моделирует последовательные этапы размышлений АМИ
    -- =================================================================
    EXECUTE format('CREATE TABLE IF NOT EXISTS %I.thinking_processes (
        id SERIAL PRIMARY KEY,
        process_name TEXT NOT NULL,              -- Название процесса мышления
        process_type TEXT NOT NULL CHECK (process_type IN (
            ''reasoning'',        -- Логическое рассуждение
            ''problem_solving'',  -- Решение проблемы
            ''reflection'',       -- Размышление о собственном опыте
            ''planning'',         -- Планирование
            ''decision_making'',  -- Принятие решения
            ''creative'',         -- Креативное мышление
            ''learning'',         -- Обучение
            ''other''             -- Другой тип
        )),
        start_time TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
        end_time TIMESTAMP WITH TIME ZONE NULL,
        active_status BOOLEAN DEFAULT TRUE,
        completed_status BOOLEAN DEFAULT FALSE,
        progress_percentage SMALLINT CHECK (progress_percentage BETWEEN 0 AND 100) DEFAULT 0,
        
        -- Связи с контекстом и источниками
        context_id INTEGER REFERENCES %I.experience_contexts(id),
        triggered_by_experience_id INTEGER REFERENCES %I.experiences(id),
        
        -- Связи с результатами
        results TEXT,
        result_experience_ids INTEGER[],
        
        -- Метаинформация
        description TEXT,
        meta_data JSONB
    )', schema_name, schema_name, schema_name);
    
    -- Комментарии к таблице thinking_processes
    EXECUTE format('COMMENT ON TABLE %I.thinking_processes IS $c$Процессы мышления АМИ - последовательности этапов размышлений, приводящие к выводам или решениям$c$', schema_name);
    EXECUTE format('COMMENT ON COLUMN %I.thinking_processes.process_type IS $c$Тип процесса мышления: рассуждение, решение проблемы, размышление и т.д.$c$', schema_name);
    EXECUTE format('COMMENT ON COLUMN %I.thinking_processes.active_status IS $c$Флаг активности: TRUE если процесс мышления активен в данный момент$c$', schema_name);
    EXECUTE format('COMMENT ON COLUMN %I.thinking_processes.completed_status IS $c$Флаг завершенности: TRUE если процесс мышления полностью завершен$c$', schema_name);
    EXECUTE format('COMMENT ON COLUMN %I.thinking_processes.progress_percentage IS $c$Процент завершения процесса мышления от 0 до 100$c$', schema_name);
    EXECUTE format('COMMENT ON COLUMN %I.thinking_processes.triggered_by_experience_id IS $c$ID опыта, который запустил данный процесс мышления$c$', schema_name);
    EXECUTE format('COMMENT ON COLUMN %I.thinking_processes.result_experience_ids IS $c$Массив ID опытов, созданных в результате этого процесса мышления$c$', schema_name);

    -- Создание индексов для процессов мышления
    EXECUTE format('CREATE INDEX IF NOT EXISTS thinking_processes_name_idx ON %I.thinking_processes(process_name)', schema_name);
    EXECUTE format('CREATE INDEX IF NOT EXISTS thinking_processes_type_idx ON %I.thinking_processes(process_type)', schema_name);
    EXECUTE format('CREATE INDEX IF NOT EXISTS thinking_processes_start_time_idx ON %I.thinking_processes(start_time)', schema_name);
    EXECUTE format('CREATE INDEX IF NOT EXISTS thinking_processes_active_status_idx ON %I.thinking_processes(active_status)', schema_name);
    EXECUTE format('CREATE INDEX IF NOT EXISTS thinking_processes_completed_status_idx ON %I.thinking_processes(completed_status)', schema_name);
    EXECUTE format('CREATE INDEX IF NOT EXISTS thinking_processes_context_id_idx ON %I.thinking_processes(context_id)', schema_name);
    EXECUTE format('CREATE INDEX IF NOT EXISTS thinking_processes_triggered_by_idx ON %I.thinking_processes(triggered_by_experience_id)', schema_name);
    
    -- =================================================================
    -- Таблица для хранения фаз мышления
    -- Детализирует отдельные этапы/фазы процесса мышления
    -- =================================================================
    EXECUTE format('CREATE TABLE IF NOT EXISTS %I.thinking_phases (
        id SERIAL PRIMARY KEY,
        thinking_process_id INTEGER NOT NULL REFERENCES %I.thinking_processes(id),
        phase_name TEXT NOT NULL,
        phase_type TEXT NOT NULL CHECK (phase_type IN (
            ''analysis'',              -- Анализ информации
            ''synthesis'',             -- Синтез информации
            ''comparison'',            -- Сравнение альтернатив
            ''evaluation'',            -- Оценка
            ''information_gathering'', -- Сбор информации
            ''hypothesis_formation'',  -- Формирование гипотезы
            ''hypothesis_testing'',    -- Проверка гипотезы
            ''conclusion'',            -- Формирование вывода
            ''other''                  -- Другой тип фазы
        )),
        sequence_number INTEGER NOT NULL,
        start_time TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
        end_time TIMESTAMP WITH TIME ZONE NULL,
        active_status BOOLEAN DEFAULT TRUE,
        completed_status BOOLEAN DEFAULT FALSE,
        
        -- Содержание фазы
        content TEXT NOT NULL,
        content_vector vector(1536),
        
        -- Связи с источниками и результатами
        input_experience_ids INTEGER[],
        output_experience_ids INTEGER[],
        
        -- Метаинформация
        description TEXT,
        meta_data JSONB
    )', schema_name, schema_name);
    
    -- Комментарии к таблице thinking_phases
    EXECUTE format('COMMENT ON TABLE %I.thinking_phases IS $c$Фазы мышления - отдельные этапы процесса мышления, каждый с определенной функцией$c$', schema_name);
    EXECUTE format('COMMENT ON COLUMN %I.thinking_phases.phase_type IS $c$Тип фазы: анализ, синтез, сравнение, оценка и т.д.$c$', schema_name);
    EXECUTE format('COMMENT ON COLUMN %I.thinking_phases.sequence_number IS $c$Порядковый номер фазы в процессе мышления$c$', schema_name);
    EXECUTE format('COMMENT ON COLUMN %I.thinking_phases.active_status IS $c$Флаг активности: TRUE если фаза активна в данный момент$c$', schema_name);
    EXECUTE format('COMMENT ON COLUMN %I.thinking_phases.completed_status IS $c$Флаг завершенности: TRUE если фаза полностью завершена$c$', schema_name);
    EXECUTE format('COMMENT ON COLUMN %I.thinking_phases.input_experience_ids IS $c$Массив ID опытов, использованных как входные данные для этой фазы$c$', schema_name);
    EXECUTE format('COMMENT ON COLUMN %I.thinking_phases.output_experience_ids IS $c$Массив ID опытов, созданных как результат этой фазы$c$', schema_name);

    -- Создание индексов для фаз мышления
    EXECUTE format('CREATE INDEX IF NOT EXISTS thinking_phases_process_id_idx ON %I.thinking_phases(thinking_process_id)', schema_name);
    EXECUTE format('CREATE INDEX IF NOT EXISTS thinking_phases_name_idx ON %I.thinking_phases(phase_name)', schema_name);
    EXECUTE format('CREATE INDEX IF NOT EXISTS thinking_phases_type_idx ON %I.thinking_phases(phase_type)', schema_name);
    EXECUTE format('CREATE INDEX IF NOT EXISTS thinking_phases_sequence_number_idx ON %I.thinking_phases(sequence_number)', schema_name);
    EXECUTE format('CREATE INDEX IF NOT EXISTS thinking_phases_start_time_idx ON %I.thinking_phases(start_time)', schema_name);
    EXECUTE format('CREATE INDEX IF NOT EXISTS thinking_phases_active_status_idx ON %I.thinking_phases(active_status)', schema_name);
    EXECUTE format('CREATE INDEX IF NOT EXISTS thinking_phases_completed_status_idx ON %I.thinking_phases(completed_status)', schema_name);

    -- Динамическое определение правильного оператора для индекса
    BEGIN
        EXECUTE format('CREATE INDEX IF NOT EXISTS thinking_phases_content_vector_idx ON %I.thinking_phases USING ivfflat (content_vector cosine_ops)', schema_name);
    EXCEPTION
        WHEN undefined_object THEN
            BEGIN
                EXECUTE format('CREATE INDEX IF NOT EXISTS thinking_phases_content_vector_idx ON %I.thinking_phases USING ivfflat (content_vector vector_cosine_ops)', schema_name);
            EXCEPTION
                WHEN undefined_object THEN
                    RAISE NOTICE 'Не удалось создать индекс для векторного поля - ни cosine_ops, ни vector_cosine_ops не определены';
            END;
    END;
    
    RAISE NOTICE 'Структуры мышления успешно созданы';
END;
$$;
