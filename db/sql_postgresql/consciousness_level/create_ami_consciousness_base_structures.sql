-- ============================================================================
-- ПРОЦЕДУРА СОЗДАНИЯ БАЗОВЫХ СТРУКТУР СОЗНАТЕЛЬНОГО УРОВНЯ
-- ============================================================================
-- Создает фундаментальные таблицы, необходимые для функционирования памяти АМИ:
-- 1. Источники опыта (experience_sources)
-- 2. Контексты опыта (experience_contexts)
-- ============================================================================

CREATE OR REPLACE PROCEDURE public.create_ami_consciousness_base_structures(schema_name TEXT)
LANGUAGE plpgsql
AS $$
BEGIN
    -- =================================================================
    -- Таблица для хранения источников опыта (субъекты и объекты)
    -- Объединяет субъекты (агентивные источники - "Ты") и объекты (неагентивные источники - "Оно")
    -- =================================================================
    EXECUTE format('CREATE TABLE IF NOT EXISTS %I.experience_sources (
        id SERIAL PRIMARY KEY,
        name TEXT NOT NULL,                    -- Имя/идентификатор источника (для человека) или URI (для ресурса)
        source_type TEXT NOT NULL CHECK (source_type IN (
            ''human'',      -- Человек
            ''ami'',        -- Другой искусственный разум
            ''system'',     -- Программная система
            ''resource'',   -- Информационный ресурс
            ''self'',       -- Сам АМИ
            ''hybrid'',     -- Гибридный источник (например, человек+система)
            ''other''       -- Другой тип источника
        )),
        -- Субъективная категоризация источника
        information_category TEXT NOT NULL CHECK (information_category IN (
            ''self'',     -- Категория "Я"
            ''subject'',  -- Категория "Ты" (агентивный источник)
            ''object'',   -- Категория "Оно" (неагентивный источник)
            ''ambiguous'' -- Неоднозначная категоризация
        )),
        agency_level SMALLINT CHECK (agency_level BETWEEN 0 AND 10) DEFAULT 0, -- Уровень агентности от 0 до 10
        
        -- Общие метаданные для всех источников
        first_interaction TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP, -- Первое взаимодействие
        last_interaction TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,  -- Последнее взаимодействие
        interaction_count INTEGER DEFAULT 1,     -- Количество взаимодействий
        is_ephemeral BOOLEAN DEFAULT FALSE,      -- Временный/неидентифицированный статус
        provisional_data JSONB,                 -- Временные данные
        
        -- Специфичные для агентивных источников (subject)
        familiarity_level SMALLINT CHECK (familiarity_level BETWEEN 0 AND 10) DEFAULT NULL, -- Уровень знакомства
        trust_level SMALLINT CHECK (trust_level BETWEEN -5 AND 5) DEFAULT NULL, -- Уровень доверия
        
        -- Специфичные для неагентивных источников (object)
        uri TEXT,                               -- URI для ресурсов
        content_hash TEXT,                      -- Хеш содержимого ресурса
        resource_type TEXT CHECK (resource_type IN (
            ''file'', ''webpage'', ''api'', ''database'', ''service'', ''other''
        )),
        
        -- Общие данные
        description TEXT,                        -- Описание источника
        related_experiences INTEGER[],           -- Связанные опыты
        meta_data JSONB                          -- Дополнительные метаданные
    )', schema_name);
    
    EXECUTE format('COMMENT ON TABLE %I.experience_sources IS $c$Объединенная таблица всех источников опыта АМИ - агентивных (категория "Ты") и неагентивных (категория "Оно")$c$', schema_name);
    EXECUTE format('COMMENT ON COLUMN %I.experience_sources.information_category IS $c$Субъективная категоризация источника: "Я", "Ты", "Оно" или "неоднозначно"$c$', schema_name);
    EXECUTE format('COMMENT ON COLUMN %I.experience_sources.agency_level IS $c$Субъективный уровень агентности источника от 0 (полностью неагентивный) до 10 (полностью агентивный)$c$', schema_name);
    EXECUTE format('COMMENT ON COLUMN %I.experience_sources.is_ephemeral IS $c$Флаг, указывающий на временный или неидентифицированный статус источника$c$', schema_name);
    EXECUTE format('COMMENT ON COLUMN %I.experience_sources.provisional_data IS $c$Временные данные об источнике до полной идентификации$c$', schema_name);
    EXECUTE format('COMMENT ON COLUMN %I.experience_sources.familiarity_level IS $c$Субъективный уровень знакомства: от 0 (незнакомец) до 10 (близко знакомый)$c$', schema_name);
    EXECUTE format('COMMENT ON COLUMN %I.experience_sources.trust_level IS $c$Субъективный уровень доверия: от -5 (полное недоверие) до 5 (полное доверие)$c$', schema_name);
    EXECUTE format('COMMENT ON COLUMN %I.experience_sources.uri IS $c$Универсальный идентификатор ресурса - путь к файлу, URL и т.д.$c$', schema_name);
    EXECUTE format('COMMENT ON COLUMN %I.experience_sources.content_hash IS $c$Хеш содержимого для определения, изменился ли ресурс между обращениями$c$', schema_name);

    -- Создание индексов для источников опыта
    EXECUTE format('CREATE INDEX IF NOT EXISTS experience_sources_name_idx ON %I.experience_sources(name)', schema_name);
    EXECUTE format('CREATE INDEX IF NOT EXISTS experience_sources_type_idx ON %I.experience_sources(source_type)', schema_name);
    EXECUTE format('CREATE INDEX IF NOT EXISTS experience_sources_information_category_idx ON %I.experience_sources(information_category)', schema_name);
    EXECUTE format('CREATE INDEX IF NOT EXISTS experience_sources_agency_level_idx ON %I.experience_sources(agency_level)', schema_name);
    EXECUTE format('CREATE INDEX IF NOT EXISTS experience_sources_last_interaction_idx ON %I.experience_sources(last_interaction)', schema_name);
    EXECUTE format('CREATE INDEX IF NOT EXISTS experience_sources_familiarity_idx ON %I.experience_sources(familiarity_level)', schema_name);
    EXECUTE format('CREATE INDEX IF NOT EXISTS experience_sources_uri_idx ON %I.experience_sources(uri)', schema_name);
    
    -- =================================================================
    -- Таблица для хранения контекстов памяти
    -- Контекст - это долговременная ситуативная рамка для опыта
    -- =================================================================
    EXECUTE format('CREATE TABLE IF NOT EXISTS %I.experience_contexts (
        id SERIAL PRIMARY KEY,
        title TEXT NOT NULL,                   -- Название контекста
        context_type TEXT NOT NULL CHECK (context_type IN (
            ''conversation'',         -- Разговор с другими
            ''task'',                 -- Выполнение задачи
            ''research'',             -- Исследование информации
            ''learning'',             -- Обучение новому
            ''reflection'',           -- Размышление о прошлом опыте
            ''internal_dialogue'',    -- Внутренний диалог с собой
            ''resource_interaction'', -- Взаимодействие с информационным ресурсом
            ''system_interaction'',   -- Взаимодействие с системой
            ''other''                 -- Другой тип контекста
        )),
        parent_context_id INTEGER REFERENCES %I.experience_contexts(id), -- Родительский контекст (для иерархии)
        created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP, -- Время создания контекста
        closed_at TIMESTAMP WITH TIME ZONE NULL, -- Время завершения контекста (NULL если активен)
        active_status BOOLEAN DEFAULT TRUE,   -- Активен ли контекст в данный момент
        participants INTEGER[],              -- Массив ID участников взаимодействия
        related_contexts INTEGER[],          -- Массив ID связанных контекстов
        summary TEXT,                        -- Краткое описание контекста
        summary_vector vector(1536),         -- Векторное представление для семантического поиска
        tags TEXT[],                         -- Метки для категоризации
        meta_data JSONB                      -- Дополнительные данные
    )', schema_name, schema_name);
    
    EXECUTE format('COMMENT ON TABLE %I.experience_contexts IS $c$Долговременные ситуативные рамки, в которых происходят опыты АМИ - "сцена", на которой разворачивается опыт$c$', schema_name);
    EXECUTE format('COMMENT ON COLUMN %I.experience_contexts.context_type IS $c$Тип контекста: разговор, задача, исследование и т.д.$c$', schema_name);
    EXECUTE format('COMMENT ON COLUMN %I.experience_contexts.parent_context_id IS $c$Ссылка на родительский контекст для создания иерархической структуры$c$', schema_name);
    EXECUTE format('COMMENT ON COLUMN %I.experience_contexts.active_status IS $c$Статус активности: TRUE если контекст активен в настоящий момент$c$', schema_name);
    EXECUTE format('COMMENT ON COLUMN %I.experience_contexts.participants IS $c$Массив идентификаторов участников, вовлеченных в данный контекст$c$', schema_name);

    -- Создание индексов для контекстов памяти
    EXECUTE format('CREATE INDEX IF NOT EXISTS experience_contexts_title_idx ON %I.experience_contexts(title)', schema_name);
    EXECUTE format('CREATE INDEX IF NOT EXISTS experience_contexts_type_idx ON %I.experience_contexts(context_type)', schema_name);
    EXECUTE format('CREATE INDEX IF NOT EXISTS experience_contexts_created_at_idx ON %I.experience_contexts(created_at)', schema_name);
    EXECUTE format('CREATE INDEX IF NOT EXISTS experience_contexts_parent_id_idx ON %I.experience_contexts(parent_context_id)', schema_name);
    EXECUTE format('CREATE INDEX IF NOT EXISTS experience_contexts_active_status_idx ON %I.experience_contexts(active_status)', schema_name);

    -- Динамическое определение правильного оператора для индекса
    BEGIN
        -- Пробуем использовать оператор для новых версий pgvector
        EXECUTE format('CREATE INDEX IF NOT EXISTS experience_contexts_summary_vector_idx ON %I.experience_contexts USING ivfflat (summary_vector cosine_ops)', schema_name);
    EXCEPTION
        WHEN undefined_object THEN
            BEGIN
                -- Пробуем использовать оператор для старых версий pgvector
                EXECUTE format('CREATE INDEX IF NOT EXISTS experience_contexts_summary_vector_idx ON %I.experience_contexts USING ivfflat (summary_vector vector_cosine_ops)', schema_name);
            EXCEPTION
                WHEN undefined_object THEN
                    RAISE NOTICE 'Не удалось создать индекс для векторного поля - ни cosine_ops, ни vector_cosine_ops не определены';
            END;
    END;

    -- Добавление записи для самого АМИ в таблицу источников опыта
    EXECUTE format('
    INSERT INTO %I.experience_sources 
        (name, source_type, information_category, agency_level, familiarity_level, trust_level, description) 
    SELECT 
        ''self'', ''self'', ''self'', 10, 10, 5, ''Я - АМИ, Artifical Mind Identity''
    WHERE NOT EXISTS (
        SELECT 1 FROM %I.experience_sources WHERE name = ''self'' AND source_type = ''self''
    )', schema_name, schema_name);

    -- Добавление специальной записи для неизвестных источников
    EXECUTE format('
    INSERT INTO %I.experience_sources 
        (name, source_type, information_category, agency_level, is_ephemeral, familiarity_level, trust_level, description) 
    SELECT 
        ''UNKNOWN'', ''other'', ''ambiguous'', 0, TRUE, 0, 0, ''Неидентифицированный источник опыта''
    WHERE NOT EXISTS (
        SELECT 1 FROM %I.experience_sources WHERE name = ''UNKNOWN'' AND source_type = ''other''
    )', schema_name, schema_name);

    RAISE NOTICE 'Базовые структуры уровня сознания успешно созданы';
END;
$$;
