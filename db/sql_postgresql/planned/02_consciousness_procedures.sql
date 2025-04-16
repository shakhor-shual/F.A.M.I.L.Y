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
CREATE OR REPLACE PROCEDURE init_ami_consciousness_level(
    ami_name TEXT, 
    ami_password TEXT DEFAULT NULL,
    schema_name TEXT DEFAULT 'ami_schema',
    grant_permissions BOOLEAN DEFAULT TRUE
)
LANGUAGE plpgsql
AS $$
DECLARE
    procedure_exists BOOLEAN;
    user_exists BOOLEAN;
    schema_exists BOOLEAN;
    sql_command TEXT;
BEGIN
    -- Проверка существования схемы
    SELECT EXISTS (
        SELECT FROM pg_namespace WHERE nspname = schema_name
    ) INTO schema_exists;
    
    -- Если схема не существует, создаем её
    IF NOT schema_exists THEN
        sql_command := 'CREATE SCHEMA ' || quote_ident(schema_name);
        EXECUTE sql_command;
        RAISE NOTICE 'Схема % успешно создана', schema_name;
    ELSE
        RAISE NOTICE 'Схема % уже существует', schema_name;
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
    
    -- Проверка и вызов процедуры создания базовых структур
    SELECT EXISTS (
        SELECT FROM pg_catalog.pg_proc p
        JOIN pg_catalog.pg_namespace n ON p.pronamespace = n.oid
        WHERE n.nspname = schema_name AND p.proname = 'create_ami_consciousness_base_structures'
    ) INTO procedure_exists;
    
    IF procedure_exists THEN
        -- Создаем динамический вызов процедуры в нужной схеме
        sql_command := 'CALL ' || quote_ident(schema_name) || '.create_ami_consciousness_base_structures()';
        EXECUTE sql_command;
        RAISE NOTICE 'Базовые структуры уровня сознания успешно созданы';
    ELSE
        RAISE WARNING 'Процедура create_ami_consciousness_base_structures не найдена в схеме %. Базовые структуры не созданы', schema_name;
    END IF;

    -- Проверка и вызов процедуры создания структуры опыта
    SELECT EXISTS (
        SELECT FROM pg_catalog.pg_proc p
        JOIN pg_catalog.pg_namespace n ON p.pronamespace = n.oid
        WHERE n.nspname = schema_name AND p.proname = 'create_ami_experience_structure'
    ) INTO procedure_exists;
    
    IF procedure_exists THEN
        sql_command := 'CALL ' || quote_ident(schema_name) || '.create_ami_experience_structure()';
        EXECUTE sql_command;
        RAISE NOTICE 'Структуры опыта успешно созданы';
    ELSE
        RAISE WARNING 'Процедура create_ami_experience_structure не найдена в схеме %. Структуры опыта не созданы', schema_name;
    END IF;

    -- Проверка и вызов процедуры создания структур мышления
    SELECT EXISTS (
        SELECT FROM pg_catalog.pg_proc p
        JOIN pg_catalog.pg_namespace n ON p.pronamespace = n.oid
        WHERE n.nspname = schema_name AND p.proname = 'create_ami_thinking_structures'
    ) INTO procedure_exists;
    
    IF procedure_exists THEN
        sql_command := 'CALL ' || quote_ident(schema_name) || '.create_ami_thinking_structures()';
        EXECUTE sql_command;
        RAISE NOTICE 'Структуры мышления успешно созданы';
    ELSE
        RAISE WARNING 'Процедура create_ami_thinking_structures не найдена в схеме %. Структуры мышления не созданы', schema_name;
    END IF;

    -- Проверка и вызов процедуры создания ассоциативных структур
    SELECT EXISTS (
        SELECT FROM pg_catalog.pg_proc p
        JOIN pg_catalog.pg_namespace n ON p.pronamespace = n.oid
        WHERE n.nspname = schema_name AND p.proname = 'create_ami_association_structures'
    ) INTO procedure_exists;
    
    IF procedure_exists THEN
        sql_command := 'CALL ' || quote_ident(schema_name) || '.create_ami_association_structures()';
        EXECUTE sql_command;
        RAISE NOTICE 'Ассоциативные структуры успешно созданы';
    ELSE
        RAISE WARNING 'Процедура create_ami_association_structures не найдена в схеме %. Ассоциативные структуры не созданы', schema_name;
    END IF;

    -- Проверка и вызов процедуры создания представлений
    SELECT EXISTS (
        SELECT FROM pg_catalog.pg_proc p
        JOIN pg_catalog.pg_namespace n ON p.pronamespace = n.oid
        WHERE n.nspname = schema_name AND p.proname = 'create_ami_consciousness_views'
    ) INTO procedure_exists;
    
    IF procedure_exists THEN
        sql_command := 'CALL ' || quote_ident(schema_name) || '.create_ami_consciousness_views()';
        EXECUTE sql_command;
        RAISE NOTICE 'Представления уровня сознания успешно созданы';
    ELSE
        RAISE WARNING 'Процедура create_ami_consciousness_views не найдена в схеме %. Представления не созданы', schema_name;
    END IF;
    
    -- Если нужно назначить права пользователю АМИ
    IF grant_permissions AND EXISTS (SELECT FROM pg_catalog.pg_roles WHERE rolname = ami_name) THEN
        -- Даем пользователю права на использование схемы
        sql_command := 'GRANT USAGE ON SCHEMA ' || quote_ident(schema_name) || ' TO ' || quote_ident(ami_name);
        EXECUTE sql_command;
        
        -- Даем права на все существующие таблицы в схеме
        sql_command := 'GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA ' || quote_ident(schema_name) || ' TO ' || quote_ident(ami_name);
        EXECUTE sql_command;
        
        -- Даем права на все последовательности в схеме
        sql_command := 'GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA ' || quote_ident(schema_name) || ' TO ' || quote_ident(ami_name);
        EXECUTE sql_command;
        
        -- Устанавливаем права по умолчанию для новых объектов
        sql_command := 'ALTER DEFAULT PRIVILEGES IN SCHEMA ' || quote_ident(schema_name) || 
                      ' GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO ' || quote_ident(ami_name);
        EXECUTE sql_command;
        
        sql_command := 'ALTER DEFAULT PRIVILEGES IN SCHEMA ' || quote_ident(schema_name) || 
                      ' GRANT USAGE, SELECT ON SEQUENCES TO ' || quote_ident(ami_name);
        EXECUTE sql_command;
        
        RAISE NOTICE 'Права для пользователя % успешно настроены', ami_name;
    ELSIF grant_permissions THEN
        RAISE WARNING 'Пользователь % не существует, права не настроены', ami_name;
    END IF;
    
    RAISE NOTICE 'Инициализация уровня сознания АМИ завершена';
END;
$$;

-- ============================================================================
-- ПРОЦЕДУРА СОЗДАНИЯ БАЗОВЫХ СТРУКТУР СОЗНАТЕЛЬНОГО УРОВНЯ
-- ============================================================================
-- Создает фундаментальные таблицы, необходимые для функционирования памяти АМИ:
-- 1. Источники опыта (experience_sources)
-- 2. Контексты опыта (experience_contexts)
-- ============================================================================

CREATE OR REPLACE PROCEDURE create_ami_consciousness_base_structures()
LANGUAGE plpgsql
AS $$
BEGIN
    -- =================================================================
    -- Таблица для хранения источников опыта (субъекты и объекты)
    -- Объединяет субъекты (агентивные источники - "Ты") и объекты (неагентивные источники - "Оно")
    -- =================================================================
    CREATE TABLE IF NOT EXISTS experience_sources (
        id SERIAL PRIMARY KEY,
        name TEXT NOT NULL,                    -- Имя/идентификатор источника (для человека) или URI (для ресурса)
        source_type TEXT NOT NULL CHECK (source_type IN (
            'human',      -- Человек
            'ami',        -- Другой искусственный разум
            'system',     -- Программная система
            'resource',   -- Информационный ресурс
            'self',       -- Сам АМИ
            'hybrid',     -- Гибридный источник (например, человек+система)
            'other'       -- Другой тип источника
        )),
        -- Субъективная категоризация источника
        information_category TEXT NOT NULL CHECK (information_category IN (
            'self',     -- Категория "Я"
            'subject',  -- Категория "Ты" (агентивный источник)
            'object',   -- Категория "Оно" (неагентивный источник)
            'ambiguous' -- Неоднозначная категоризация
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
            'file', 'webpage', 'api', 'database', 'service', 'other'
        )),
        
        -- Общие данные
        description TEXT,                        -- Описание источника
        related_experiences INTEGER[],           -- Связанные опыты
        meta_data JSONB                          -- Дополнительные метаданные
    );
    
    COMMENT ON TABLE experience_sources IS 'Объединенная таблица всех источников опыта АМИ - агентивных (категория "Ты") и неагентивных (категория "Оно")';
    COMMENT ON COLUMN experience_sources.information_category IS 'Субъективная категоризация источника: "Я", "Ты", "Оно" или "неоднозначно"';
    COMMENT ON COLUMN experience_sources.agency_level IS 'Субъективный уровень агентности источника от 0 (полностью неагентивный) до 10 (полностью агентивный)';
    COMMENT ON COLUMN experience_sources.is_ephemeral IS 'Флаг, указывающий на временный или неидентифицированный статус источника';
    COMMENT ON COLUMN experience_sources.provisional_data IS 'Временные данные об источнике до полной идентификации';
    COMMENT ON COLUMN experience_sources.familiarity_level IS 'Субъективный уровень знакомства: от 0 (незнакомец) до 10 (близко знакомый)';
    COMMENT ON COLUMN experience_sources.trust_level IS 'Субъективный уровень доверия: от -5 (полное недоверие) до 5 (полное доверие)';
    COMMENT ON COLUMN experience_sources.uri IS 'Универсальный идентификатор ресурса - путь к файлу, URL и т.д.';
    COMMENT ON COLUMN experience_sources.content_hash IS 'Хеш содержимого для определения, изменился ли ресурс между обращениями';

    -- Создание индексов для источников опыта
    CREATE INDEX IF NOT EXISTS experience_sources_name_idx ON experience_sources(name);
    CREATE INDEX IF NOT EXISTS experience_sources_type_idx ON experience_sources(source_type);
    CREATE INDEX IF NOT EXISTS experience_sources_information_category_idx ON experience_sources(information_category);
    CREATE INDEX IF NOT EXISTS experience_sources_agency_level_idx ON experience_sources(agency_level);
    CREATE INDEX IF NOT EXISTS experience_sources_last_interaction_idx ON experience_sources(last_interaction);
    CREATE INDEX IF NOT EXISTS experience_sources_familiarity_idx ON experience_sources(familiarity_level);
    CREATE INDEX IF NOT EXISTS experience_sources_uri_idx ON experience_sources(uri);
    
    -- =================================================================
    -- Таблица для хранения контекстов памяти
    -- Контекст - это долговременная ситуативная рамка для опыта
    -- =================================================================
    CREATE TABLE IF NOT EXISTS experience_contexts (
        id SERIAL PRIMARY KEY,
        title TEXT NOT NULL,                   -- Название контекста
        context_type TEXT NOT NULL CHECK (context_type IN (
            'conversation',         -- Разговор с другими
            'task',                 -- Выполнение задачи
            'research',             -- Исследование информации
            'learning',             -- Обучение новому
            'reflection',           -- Размышление о прошлом опыте
            'internal_dialogue',    -- Внутренний диалог с собой
            'resource_interaction', -- Взаимодействие с информационным ресурсом
            'system_interaction',   -- Взаимодействие с системой
            'other'                 -- Другой тип контекста
        )),
        parent_context_id INTEGER REFERENCES experience_contexts(id), -- Родительский контекст (для иерархии)
        created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP, -- Время создания контекста
        closed_at TIMESTAMP WITH TIME ZONE NULL, -- Время завершения контекста (NULL если активен)
        active_status BOOLEAN DEFAULT TRUE,   -- Активен ли контекст в данный момент
        participants INTEGER[],              -- Массив ID участников взаимодействия
        related_contexts INTEGER[],          -- Массив ID связанных контекстов
        summary TEXT,                        -- Краткое описание контекста
        summary_vector vector(1536),         -- Векторное представление для семантического поиска
        tags TEXT[],                         -- Метки для категоризации
        meta_data JSONB                      -- Дополнительные данные
    );
    
    COMMENT ON TABLE experience_contexts IS 'Долговременные ситуативные рамки, в которых происходят опыты АМИ - "сцена", на которой разворачивается опыт';
    COMMENT ON COLUMN experience_contexts.context_type IS 'Тип контекста: разговор, задача, исследование и т.д.';
    COMMENT ON COLUMN experience_contexts.parent_context_id IS 'Ссылка на родительский контекст для создания иерархической структуры';
    COMMENT ON COLUMN experience_contexts.active_status IS 'Статус активности: TRUE если контекст активен в настоящий момент';
    COMMENT ON COLUMN experience_contexts.participants IS 'Массив идентификаторов участников, вовлеченных в данный контекст';

    -- Создание индексов для контекстов памяти
    CREATE INDEX IF NOT EXISTS experience_contexts_title_idx ON experience_contexts(title);
    CREATE INDEX IF NOT EXISTS experience_contexts_type_idx ON experience_contexts(context_type);
    CREATE INDEX IF NOT EXISTS experience_contexts_created_at_idx ON experience_contexts(created_at);
    CREATE INDEX IF NOT EXISTS experience_contexts_parent_id_idx ON experience_contexts(parent_context_id);
    CREATE INDEX IF NOT EXISTS experience_contexts_active_status_idx ON experience_contexts(active_status);

    -- Динамическое определение правильного оператора для индекса
    BEGIN
        -- Пробуем использовать оператор для новых версий pgvector
        EXECUTE 'CREATE INDEX IF NOT EXISTS experience_contexts_summary_vector_idx ON experience_contexts USING ivfflat (summary_vector cosine_ops)';
    EXCEPTION
        WHEN undefined_object THEN
            BEGIN
                -- Пробуем использовать оператор для старых версий pgvector
                EXECUTE 'CREATE INDEX IF NOT EXISTS experience_contexts_summary_vector_idx ON experience_contexts USING ivfflat (summary_vector vector_cosine_ops)';
            EXCEPTION
                WHEN undefined_object THEN
                    RAISE NOTICE 'Не удалось создать индекс для векторного поля - ни cosine_ops, ни vector_cosine_ops не определены';
            END;
    END;

    -- Добавление записи для самого АМИ в таблицу источников опыта
    IF NOT EXISTS (SELECT 1 FROM experience_sources WHERE name = 'self' AND source_type = 'self') THEN
        INSERT INTO experience_sources 
        (name, source_type, information_category, agency_level, familiarity_level, trust_level, description) 
        VALUES 
        ('self', 'self', 'self', 10, 10, 5, 'Я - АМИ, Artifical Mind Identity');
        
        RAISE NOTICE 'Создана запись о самом АМИ в таблице источников опыта';
    ELSE
        RAISE NOTICE 'Запись о самом АМИ уже существует в таблице источников опыта';
    END IF;
    
    -- Добавление специальной записи для неизвестных источников
    IF NOT EXISTS (SELECT 1 FROM experience_sources WHERE name = 'UNKNOWN' AND source_type = 'other') THEN
        INSERT INTO experience_sources 
        (name, source_type, information_category, agency_level, is_ephemeral, familiarity_level, trust_level, description) 
        VALUES 
        ('UNKNOWN', 'other', 'ambiguous', 0, TRUE, 0, 0, 'Неидентифицированный источник опыта');
        
        RAISE NOTICE 'Создана запись для неизвестных источников в таблице источников опыта';
    ELSE
        RAISE NOTICE 'Запись для неизвестных источников уже существует в таблице источников опыта';
    END IF;

    RAISE NOTICE 'Базовые структуры уровня сознания успешно созданы';
END;
$$;

-- ============================================================================
-- ПРОЦЕДУРА СОЗДАНИЯ СТРУКТУРЫ ОПЫТА СОЗНАТЕЛЬНОГО УРОВНЯ
-- ============================================================================
-- Создает центральную таблицу experiences и вспомогательную таблицу атрибутов:
-- 1. Опыт/переживания (experiences)
-- 2. Атрибуты опыта (experience_attributes)
-- ============================================================================

CREATE OR REPLACE PROCEDURE create_ami_experience_structure()
LANGUAGE plpgsql
AS $$
BEGIN
    -- =================================================================
    -- Таблица для хранения основных воспоминаний (опыта)
    -- Центральная таблица сознательного уровня памяти АМИ
    -- =================================================================
    CREATE TABLE IF NOT EXISTS experiences (
        id SERIAL PRIMARY KEY,
        timestamp TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP, -- Время создания переживания
        
        -- Категоризация опыта (обязательные поля)
        information_category TEXT NOT NULL CHECK (information_category IN (
            'self',    -- Категория "Я" (информация от самого себя)
            'subject', -- Категория "Ты" (информация от агентивного источника)
            'object'   -- Категория "Оно" (информация от неагентивного источника)
        )),
        
        -- Базовое деление опыта по типу (что это?)
        experience_type TEXT NOT NULL CHECK (experience_type IN (
            'perception',       -- Восприятие (входящая информация)
            'thought',          -- Мысль
            'action',           -- Действие АМИ
            'communication',    -- Коммуникация (входящая или исходящая)
            'decision',         -- Принятие решения
            'memory_recall',    -- Воспоминание
            'insight'           -- Инсайт/озарение
        )),
        
        -- Субъективная позиция АМИ в опыте (как АМИ себя позиционирует?)
        subjective_position TEXT NOT NULL CHECK (subjective_position IN (
            'addressee',      -- АМИ как адресат (кто-то обращается к АМИ)
            'addresser',      -- АМИ как адресант (АМИ обращается к кому-то)
            'observer',       -- АМИ как наблюдатель (воспринимает без прямого обращения)
            'reflective'      -- АМИ в рефлексивном режиме (внутренний диалог)
        )),
        
        -- Направление коммуникации (для опытов типа communication)
        communication_direction TEXT CHECK (communication_direction IN (
            'incoming',     -- Входящая коммуникация
            'outgoing'      -- Исходящая коммуникация
        )),
        
        -- Контекст (может быть null, если известен только provisional_context)
        context_id INTEGER REFERENCES experience_contexts(id),
        provisional_context TEXT, -- Текстовое описание контекста, когда context_id=NULL
        
        -- Связи с источниками опыта (могут быть null, если известен только provisional_source)
        source_id INTEGER REFERENCES experience_sources(id), -- Источник опыта (объединенная таблица)
        provisional_source TEXT, -- Текстовое описание источника, когда source_id=NULL
        target_id INTEGER REFERENCES experience_sources(id), -- Получатель (для направленных коммуникаций)
        
        -- Основное содержание
        content TEXT NOT NULL,                -- Текстовое содержание опыта
        content_vector vector(1536),          -- Векторное представление
        
        -- Базовые атрибуты опыта
        salience SMALLINT CHECK (salience BETWEEN 1 AND 10) DEFAULT 5, -- Значимость опыта (1-10)
        provenance_type TEXT NOT NULL CHECK (provenance_type IN (
            'identified',       -- Полностью идентифицированный опыт
            'provisional',      -- Опыт с временными данными
            'system_generated'  -- Опыт, сгенерированный системой
        )) DEFAULT 'identified',
        verified_status BOOLEAN DEFAULT FALSE, -- Верифицирована ли информация
        
        -- Связи с другими опытами
        parent_experience_id INTEGER REFERENCES experiences(id), -- Родительский опыт
        response_to_experience_id INTEGER REFERENCES experiences(id), -- На какой опыт это ответ
        thinking_process_id INTEGER,  -- Ссылка на процесс мышления, который привел к этому опыту (если есть)
        
        -- Связь с подсознательным уровнем (эмоции)
        emotional_evaluation_id INTEGER, -- Будет внешним ключом к таблице в подсознательном уровне
        
        -- Метаданные
        meta_data JSONB                       -- Дополнительные данные
    );
    
    COMMENT ON TABLE experiences IS 'Центральная таблица опыта/переживаний АМИ - все информационные события, оставляющие след в сознании';
    COMMENT ON COLUMN experiences.information_category IS 'Субъективная категория источника информации: Я (self), Ты (subject), Оно (object)';
    COMMENT ON COLUMN experiences.experience_type IS 'Тип опыта: восприятие, мысль, действие и т.д.';
    COMMENT ON COLUMN experiences.subjective_position IS 'Субъективная позиция АМИ в опыте: адресат, адресант, наблюдатель или рефлексирующий';
    COMMENT ON COLUMN experiences.communication_direction IS 'Направление коммуникации: входящая или исходящая (для типа communication)';
    COMMENT ON COLUMN experiences.provenance_type IS 'Тип происхождения опыта: идентифицированный, временный, сгенерированный системой';
    COMMENT ON COLUMN experiences.provisional_context IS 'Текстовое описание контекста, когда полноценная запись в таблице experience_contexts еще не создана';
    COMMENT ON COLUMN experiences.provisional_source IS 'Текстовое описание источника, когда полноценная запись в таблице experience_sources еще не создана';
    COMMENT ON COLUMN experiences.salience IS 'Субъективная значимость опыта по шкале 1-10';
    COMMENT ON COLUMN experiences.parent_experience_id IS 'Ссылка на родительский опыт (для иерархии)';
    COMMENT ON COLUMN experiences.response_to_experience_id IS 'Ссылка на опыт, на который это является ответом';
    COMMENT ON COLUMN experiences.thinking_process_id IS 'Ссылка на процесс мышления, который привел к данному опыту';
    COMMENT ON COLUMN experiences.emotional_evaluation_id IS 'Ссылка на эмоциональную оценку опыта из подсознательного уровня';

    -- Создание индексов для воспоминаний
    CREATE INDEX IF NOT EXISTS experiences_timestamp_idx ON experiences(timestamp);
    CREATE INDEX IF NOT EXISTS experiences_context_id_idx ON experiences(context_id);
    CREATE INDEX IF NOT EXISTS experiences_information_category_idx ON experiences(information_category);
    CREATE INDEX IF NOT EXISTS experiences_experience_type_idx ON experiences(experience_type);
    CREATE INDEX IF NOT EXISTS experiences_subjective_position_idx ON experiences(subjective_position);
    CREATE INDEX IF NOT EXISTS experiences_source_id_idx ON experiences(source_id);
    CREATE INDEX IF NOT EXISTS experiences_target_id_idx ON experiences(target_id);
    CREATE INDEX IF NOT EXISTS experiences_salience_idx ON experiences(salience);
    CREATE INDEX IF NOT EXISTS experiences_parent_experience_idx ON experiences(parent_experience_id);
    CREATE INDEX IF NOT EXISTS experiences_response_to_idx ON experiences(response_to_experience_id);
    CREATE INDEX IF NOT EXISTS experiences_thinking_process_idx ON experiences(thinking_process_id);

    -- Динамическое определение правильного оператора для индекса
    BEGIN
        -- Пробуем использовать оператор для новых версий pgvector
        EXECUTE 'CREATE INDEX IF NOT EXISTS experiences_content_vector_idx ON experiences USING ivfflat (content_vector cosine_ops)';
    EXCEPTION
        WHEN undefined_object THEN
            BEGIN
                -- Пробуем использовать оператор для старых версий pgvector
                EXECUTE 'CREATE INDEX IF NOT EXISTS experiences_content_vector_idx ON experiences USING ivfflat (content_vector vector_cosine_ops)';
            EXCEPTION
                WHEN undefined_object THEN
                    RAISE NOTICE 'Не удалось создать индекс для векторного поля - ни cosine_ops, ни vector_cosine_ops не определены';
            END;
    END;
    
    -- =================================================================
    -- Таблица для хранения расширенных атрибутов опыта (EAV-модель)
    -- Позволяет добавлять произвольные атрибуты к любому опыту
    -- =================================================================
    CREATE TABLE IF NOT EXISTS experience_attributes (
        id SERIAL PRIMARY KEY,
        experience_id INTEGER NOT NULL REFERENCES experiences(id), -- Ссылка на основной опыт
        attribute_name TEXT NOT NULL,          -- Название атрибута
        attribute_value TEXT NOT NULL,         -- Значение атрибута
        attribute_type TEXT CHECK (attribute_type IN (
            'string', 'number', 'boolean', 'datetime', 'json', 'other'
        )) DEFAULT 'string',
        meta_data JSONB                        -- Метаданные
    );
    
    COMMENT ON TABLE experience_attributes IS 'Расширенные атрибуты опыта - позволяют добавлять произвольные данные к опыту без изменения основной схемы';
    COMMENT ON COLUMN experience_attributes.attribute_name IS 'Название атрибута - должно быть осмысленным для данного типа опыта';
    COMMENT ON COLUMN experience_attributes.attribute_value IS 'Значение атрибута в текстовом представлении';
    COMMENT ON COLUMN experience_attributes.attribute_type IS 'Тип данных атрибута для правильной интерпретации значения';
    
    -- Создание индексов для атрибутов
    CREATE INDEX IF NOT EXISTS experience_attributes_experience_id_idx ON experience_attributes(experience_id);
    CREATE INDEX IF NOT EXISTS experience_attributes_name_idx ON experience_attributes(attribute_name);
    CREATE INDEX IF NOT EXISTS experience_attributes_name_value_idx ON experience_attributes(attribute_name, attribute_value);
    
    RAISE NOTICE 'Структуры опыта успешно созданы';
END;
$$;

-- ============================================================================
-- ПРОЦЕДУРА СОЗДАНИЯ СТРУКТУР МЫШЛЕНИЯ СОЗНАТЕЛЬНОГО УРОВНЯ
-- ============================================================================
-- Создает таблицы для процессов мышления и фаз мышления:
-- 1. Процессы мышления (thinking_processes)
-- 2. Фазы мышления (thinking_phases)
-- ============================================================================

CREATE OR REPLACE PROCEDURE create_ami_thinking_structures()
LANGUAGE plpgsql
AS $$
BEGIN
    -- =================================================================
    -- Таблица для хранения процессов мышления
    -- Моделирует последовательные этапы размышлений АМИ
    -- =================================================================
    CREATE TABLE IF NOT EXISTS thinking_processes (
        id SERIAL PRIMARY KEY,
        process_name TEXT NOT NULL,              -- Название процесса мышления
        process_type TEXT NOT NULL CHECK (process_type IN (
            'reasoning',        -- Логическое рассуждение
            'problem_solving',  -- Решение проблемы
            'reflection',       -- Размышление о собственном опыте
            'planning',         -- Планирование
            'decision_making',  -- Принятие решения
            'creative',         -- Креативное мышление
            'learning',         -- Обучение
            'other'             -- Другой тип
        )),
        start_time TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP, -- Время начала процесса
        end_time TIMESTAMP WITH TIME ZONE NULL, -- Время завершения (NULL если не завершен)
        active_status BOOLEAN DEFAULT TRUE,    -- Активен ли процесс в данный момент
        completed_status BOOLEAN DEFAULT FALSE, -- Завершен ли процесс
        progress_percentage SMALLINT CHECK (progress_percentage BETWEEN 0 AND 100) DEFAULT 0, -- Процент выполнения
        
        -- Связи с контекстом и источниками
        context_id INTEGER REFERENCES experience_contexts(id), -- Контекст, в котором происходит мышление
        triggered_by_experience_id INTEGER REFERENCES experiences(id), -- Опыт, запустивший процесс
        
        -- Связи с результатами
        results TEXT,                           -- Текстовые результаты мышления
        result_experience_ids INTEGER[],        -- ID опытов, созданных в результате процесса
        
        -- Метаинформация
        description TEXT,                       -- Описание процесса мышления
        meta_data JSONB                         -- Дополнительные метаданные
    );
    
    COMMENT ON TABLE thinking_processes IS 'Процессы мышления АМИ - последовательности этапов размышлений, приводящие к выводам или решениям';
    COMMENT ON COLUMN thinking_processes.process_type IS 'Тип процесса мышления: рассуждение, решение проблемы, размышление и т.д.';
    COMMENT ON COLUMN thinking_processes.active_status IS 'Флаг активности: TRUE если процесс мышления активен в данный момент';
    COMMENT ON COLUMN thinking_processes.completed_status IS 'Флаг завершенности: TRUE если процесс мышления полностью завершен';
    COMMENT ON COLUMN thinking_processes.progress_percentage IS 'Процент завершения процесса мышления от 0 до 100';
    COMMENT ON COLUMN thinking_processes.triggered_by_experience_id IS 'ID опыта, который запустил данный процесс мышления';
    COMMENT ON COLUMN thinking_processes.result_experience_ids IS 'Массив ID опытов, созданных в результате этого процесса мышления';

    -- Создание индексов для процессов мышления
    CREATE INDEX IF NOT EXISTS thinking_processes_name_idx ON thinking_processes(process_name);
    CREATE INDEX IF NOT EXISTS thinking_processes_type_idx ON thinking_processes(process_type);
    CREATE INDEX IF NOT EXISTS thinking_processes_start_time_idx ON thinking_processes(start_time);
    CREATE INDEX IF NOT EXISTS thinking_processes_active_status_idx ON thinking_processes(active_status);
    CREATE INDEX IF NOT EXISTS thinking_processes_completed_status_idx ON thinking_processes(completed_status);
    CREATE INDEX IF NOT EXISTS thinking_processes_context_id_idx ON thinking_processes(context_id);
    CREATE INDEX IF NOT EXISTS thinking_processes_triggered_by_idx ON thinking_processes(triggered_by_experience_id);
    
    -- =================================================================
    -- Таблица для хранения фаз мышления
    -- Детализирует отдельные этапы/фазы процесса мышления
    -- =================================================================
    CREATE TABLE IF NOT EXISTS thinking_phases (
        id SERIAL PRIMARY KEY,
        thinking_process_id INTEGER NOT NULL REFERENCES thinking_processes(id), -- Ссылка на процесс мышления
        phase_name TEXT NOT NULL,                -- Название фазы
        phase_type TEXT NOT NULL CHECK (phase_type IN (
            'analysis',              -- Анализ информации
            'synthesis',             -- Синтез информации
            'comparison',            -- Сравнение альтернатив
            'evaluation',            -- Оценка
            'information_gathering', -- Сбор информации
            'hypothesis_formation',  -- Формирование гипотезы
            'hypothesis_testing',    -- Проверка гипотезы
            'conclusion',            -- Формирование вывода
            'other'                  -- Другой тип фазы
        )),
        sequence_number INTEGER NOT NULL,       -- Порядковый номер фазы
        start_time TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP, -- Время начала фазы
        end_time TIMESTAMP WITH TIME ZONE NULL, -- Время завершения фазы (NULL если не завершена)
        active_status BOOLEAN DEFAULT TRUE,     -- Активна ли фаза в данный момент
        completed_status BOOLEAN DEFAULT FALSE, -- Завершена ли фаза
        
        -- Содержание фазы
        content TEXT NOT NULL,                  -- Текстовое содержание фазы мышления
        content_vector vector(1536),            -- Векторное представление для семантического поиска
        
        -- Связи с источниками и результатами
        input_experience_ids INTEGER[],         -- ID опытов, использованных в этой фазе
        output_experience_ids INTEGER[],        -- ID опытов, созданных в этой фазе
        
        -- Метаинформация
        description TEXT,                       -- Описание фазы
        meta_data JSONB                         -- Дополнительные метаданные
    );
    
    COMMENT ON TABLE thinking_phases IS 'Фазы мышления - отдельные этапы процесса мышления, каждый с определенной функцией';
    COMMENT ON COLUMN thinking_phases.phase_type IS 'Тип фазы: анализ, синтез, сравнение, оценка и т.д.';
    COMMENT ON COLUMN thinking_phases.sequence_number IS 'Порядковый номер фазы в процессе мышления';
    COMMENT ON COLUMN thinking_phases.active_status IS 'Флаг активности: TRUE если фаза активна в данный момент';
    COMMENT ON COLUMN thinking_phases.completed_status IS 'Флаг завершенности: TRUE если фаза полностью завершена';
    COMMENT ON COLUMN thinking_phases.input_experience_ids IS 'Массив ID опытов, использованных как входные данные для этой фазы';
    COMMENT ON COLUMN thinking_phases.output_experience_ids IS 'Массив ID опытов, созданных как результат этой фазы';

    -- Создание индексов для фаз мышления
    CREATE INDEX IF NOT EXISTS thinking_phases_process_id_idx ON thinking_phases(thinking_process_id);
    CREATE INDEX IF NOT EXISTS thinking_phases_name_idx ON thinking_phases(phase_name);
    CREATE INDEX IF NOT EXISTS thinking_phases_type_idx ON thinking_phases(phase_type);
    CREATE INDEX IF NOT EXISTS thinking_phases_sequence_number_idx ON thinking_phases(sequence_number);
    CREATE INDEX IF NOT EXISTS thinking_phases_start_time_idx ON thinking_phases(start_time);
    CREATE INDEX IF NOT EXISTS thinking_phases_active_status_idx ON thinking_phases(active_status);
    CREATE INDEX IF NOT EXISTS thinking_phases_completed_status_idx ON thinking_phases(completed_status);

    -- Динамическое определение правильного оператора для индекса
    BEGIN
        -- Пробуем использовать оператор для новых версий pgvector
        EXECUTE 'CREATE INDEX IF NOT EXISTS thinking_phases_content_vector_idx ON thinking_phases USING ivfflat (content_vector cosine_ops)';
    EXCEPTION
        WHEN undefined_object THEN
            BEGIN
                -- Пробуем использовать оператор для старых версий pgvector
                EXECUTE 'CREATE INDEX IF NOT EXISTS thinking_phases_content_vector_idx ON thinking_phases USING ivfflat (content_vector vector_cosine_ops)';
            EXCEPTION
                WHEN undefined_object THEN
                    RAISE NOTICE 'Не удалось создать индекс для векторного поля - ни cosine_ops, ни vector_cosine_ops не определены';
            END;
    END;
    
    RAISE NOTICE 'Структуры мышления успешно созданы';
END;
$$;

-- ============================================================================
-- ПРОЦЕДУРА СОЗДАНИЯ АССОЦИАТИВНЫХ СТРУКТУР СОЗНАТЕЛЬНОГО УРОВНЯ
-- ============================================================================
-- Создает таблицу для хранения связей между опытами:
-- 1. Связи между опытами (experience_connections)
-- ============================================================================

CREATE OR REPLACE PROCEDURE create_ami_association_structures()
LANGUAGE plpgsql
AS $$
BEGIN
    -- =================================================================
    -- Таблица для хранения связей между опытами
    -- Моделирует различные типы ассоциативных связей между воспоминаниями
    -- =================================================================
    CREATE TABLE IF NOT EXISTS experience_connections (
        id SERIAL PRIMARY KEY,
        source_experience_id INTEGER NOT NULL REFERENCES experiences(id), -- Исходный опыт
        target_experience_id INTEGER NOT NULL REFERENCES experiences(id), -- Целевой опыт
        connection_type TEXT NOT NULL CHECK (connection_type IN (
            'temporal',         -- Временная связь (последовательность)
            'causal',           -- Причинно-следственная связь
            'semantic',         -- Семантическая (смысловая) связь
            'contextual',       -- Контекстуальная связь (одинаковый контекст)
            'thematic',         -- Тематическая связь
            'emotional',        -- Эмоциональная связь
            'analogy',          -- Аналогия
            'contrast',         -- Контраст (противопоставление)
            'elaboration',      -- Детализация (расширение) 
            'reference',        -- Явная ссылка одного опыта на другой
            'association',      -- Свободная ассоциация без явной категории
            'other'             -- Другой тип связи
        )),
        strength SMALLINT CHECK (strength BETWEEN 1 AND 10) DEFAULT 5, -- Сила связи
        created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP, -- Время создания связи
        last_activated TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP, -- Время последней активации
        activation_count INTEGER DEFAULT 1,     -- Счетчик активаций
        direction TEXT CHECK (direction IN (
            'unidirectional',   -- Однонаправленная связь
            'bidirectional'     -- Двунаправленная связь
        )) DEFAULT 'bidirectional',
        conscious_status BOOLEAN DEFAULT TRUE,  -- Осознаваемая или неосознаваемая связь
        description TEXT,                       -- Описание связи
        meta_data JSONB                         -- Дополнительные метаданные
    );
    
    COMMENT ON TABLE experience_connections IS 'Связи между опытами - моделирует различные типы ассоциативных связей между воспоминаниями';
    COMMENT ON COLUMN experience_connections.connection_type IS 'Тип связи: временная, причинно-следственная, семантическая и т.д.';
    COMMENT ON COLUMN experience_connections.strength IS 'Сила ассоциативной связи по шкале 1-10';
    COMMENT ON COLUMN experience_connections.activation_count IS 'Количество активаций этой связи - отражает частоту использования';
    COMMENT ON COLUMN experience_connections.direction IS 'Направление связи: однонаправленная или двунаправленная';
    COMMENT ON COLUMN experience_connections.conscious_status IS 'Осознаёт ли АМИ эту связь (TRUE) или она существует на подсознательном уровне (FALSE)';

    -- Создание индексов для связей между опытами
    CREATE INDEX IF NOT EXISTS experience_connections_source_idx ON experience_connections(source_experience_id);
    CREATE INDEX IF NOT EXISTS experience_connections_target_idx ON experience_connections(target_experience_id);
    CREATE INDEX IF NOT EXISTS experience_connections_type_idx ON experience_connections(connection_type);
    CREATE INDEX IF NOT EXISTS experience_connections_strength_idx ON experience_connections(strength);
    CREATE INDEX IF NOT EXISTS experience_connections_last_activated_idx ON experience_connections(last_activated);
    CREATE INDEX IF NOT EXISTS experience_connections_activation_count_idx ON experience_connections(activation_count);
    CREATE INDEX IF NOT EXISTS experience_connections_direction_idx ON experience_connections(direction);
    CREATE INDEX IF NOT EXISTS experience_connections_conscious_status_idx ON experience_connections(conscious_status);
    
    -- Ограничение уникальности для предотвращения дублирования ассоциаций
    CREATE UNIQUE INDEX IF NOT EXISTS experience_connections_unique_idx 
    ON experience_connections(source_experience_id, target_experience_id, connection_type);
    
    RAISE NOTICE 'Ассоциативные структуры успешно созданы';
END;
$$;

-- ============================================================================
-- ПРОЦЕДУРА СОЗДАНИЯ ПРЕДСТАВЛЕНИЙ СОЗНАТЕЛЬНОГО УРОВНЯ
-- ============================================================================
-- Создает представления (views) для удобного доступа к данным сознательного уровня:
-- 1. Представление текущего внимания (current_awareness)
-- 2. Внутренний поток мыслей (internal_thought_stream)
-- 3. Представление взаимодействий (external_interaction_stream)
-- 4. Диалоговые взаимодействия (dialogue_interactions)
-- 5. Активные процессы мышления (active_thinking_processes)
-- ============================================================================

CREATE OR REPLACE PROCEDURE create_ami_consciousness_views()
LANGUAGE plpgsql
AS $$
BEGIN
    -- =================================================================
    -- Представление "текущего фокуса внимания"
    -- Показывает наиболее актуальные опыты из разных источников
    -- =================================================================
    CREATE OR REPLACE VIEW current_awareness AS
    WITH recent_experiences AS (
        -- Недавние значимые опыты
        SELECT *
        FROM experiences
        WHERE timestamp > (CURRENT_TIMESTAMP - interval '24 hours')
        ORDER BY timestamp DESC, salience DESC
        LIMIT 50
    ),
    recent_thinking AS (
        -- Активные процессы мышления
        SELECT tp.*, ph.id as last_phase_id, ph.content as last_phase_content
        FROM thinking_processes tp
        LEFT JOIN thinking_phases ph ON tp.id = ph.thinking_process_id
        WHERE tp.active_status = TRUE
        AND (ph.id IS NULL OR ph.id = (
            SELECT id FROM thinking_phases 
            WHERE thinking_process_id = tp.id 
            ORDER BY sequence_number DESC 
            LIMIT 1
        ))
        ORDER BY tp.start_time DESC
        LIMIT 10
    )
    SELECT 'experience' as element_type, id, timestamp, content, salience, NULL::INTEGER as process_id
    FROM recent_experiences
    UNION ALL
    SELECT 'thinking_process' as element_type, id, start_time as timestamp, 
           CASE WHEN last_phase_content IS NOT NULL 
                THEN process_name || ': ' || last_phase_content 
                ELSE process_name 
           END as content,
           CASE WHEN active_status THEN 10 ELSE 5 END as salience,
           id as process_id
    FROM recent_thinking
    ORDER BY timestamp DESC, salience DESC
    LIMIT 20;
    
    COMMENT ON VIEW current_awareness IS 'Представление текущего фокуса внимания АМИ - наиболее актуальные опыты и процессы мышления';
    
    -- =================================================================
    -- Представление внутреннего потока мыслей
    -- Включает опыты типа "мысль", "воспоминание", "инсайт"
    -- =================================================================
    CREATE OR REPLACE VIEW internal_thought_stream AS
    SELECT e.*,
           ec.title as context_title,
           tp.process_name as thinking_process_name,
           tp.process_type as thinking_process_type,
           tp.active_status as thinking_process_active
    FROM experiences e
    LEFT JOIN experience_contexts ec ON e.context_id = ec.id
    LEFT JOIN thinking_processes tp ON e.thinking_process_id = tp.id
    WHERE e.information_category = 'self'
      AND e.experience_type IN ('thought', 'memory_recall', 'insight', 'decision')
      AND e.timestamp > (CURRENT_TIMESTAMP - interval '7 days')
    ORDER BY e.timestamp DESC;
    
    COMMENT ON VIEW internal_thought_stream IS 'Внутренний поток мыслей АМИ - последовательность внутренних размышлений, воспоминаний и инсайтов';
    
    -- =================================================================
    -- Представление внешних взаимодействий
    -- Включает опыты, связанные с внешними источниками
    -- =================================================================
    CREATE OR REPLACE VIEW external_interaction_stream AS
    SELECT e.*,
           s.name as source_name,
           s.source_type,
           t.name as target_name,
           ec.title as context_title
    FROM experiences e
    LEFT JOIN experience_sources s ON e.source_id = s.id
    LEFT JOIN experience_sources t ON e.target_id = t.id
    LEFT JOIN experience_contexts ec ON e.context_id = ec.id
    WHERE (e.information_category = 'subject' OR e.information_category = 'object')
      AND e.timestamp > (CURRENT_TIMESTAMP - interval '7 days')
    ORDER BY e.timestamp DESC;
    
    COMMENT ON VIEW external_interaction_stream IS 'Поток внешних взаимодействий АМИ - последовательность опытов, связанных с внешними источниками';
    
    -- =================================================================
    -- Представление диалоговых взаимодействий
    -- Группирует опыты коммуникации по контекстам и участникам
    -- =================================================================
    CREATE OR REPLACE VIEW dialogue_interactions AS
    SELECT 
        ec.id as context_id,
        ec.title as context_title,
        ec.context_type,
        (SELECT string_agg(DISTINCT es.name, ', ') 
         FROM experience_sources es 
         WHERE es.id = ANY(ec.participants)) as participants,
        ec.created_at as started_at,
        ec.closed_at as ended_at,
        ec.active_status as is_active,
        (SELECT COUNT(*) FROM experiences 
         WHERE context_id = ec.id AND experience_type = 'communication') as message_count,
        (SELECT MAX(timestamp) FROM experiences 
         WHERE context_id = ec.id AND experience_type = 'communication') as last_message_at
    FROM experience_contexts ec
    WHERE ec.context_type = 'conversation'
      AND ec.created_at > (CURRENT_TIMESTAMP - interval '30 days')
    ORDER BY 
        ec.active_status DESC,
        last_message_at DESC;
    
    COMMENT ON VIEW dialogue_interactions IS 'Представление диалоговых взаимодействий АМИ - разговоры с внешними источниками, сгруппированные по контекстам';
    
    -- =================================================================
    -- Представление активных процессов мышления
    -- Показывает текущие процессы размышления с их фазами
    -- =================================================================
    CREATE OR REPLACE VIEW active_thinking_processes AS
    WITH process_stats AS (
        SELECT 
            thinking_process_id,
            COUNT(*) as total_phases,
            SUM(CASE WHEN completed_status THEN 1 ELSE 0 END) as completed_phases,
            string_agg(
                CASE WHEN active_status THEN 
                    '[' || sequence_number::text || '] ' || phase_name 
                ELSE 
                    sequence_number::text || '. ' || phase_name 
                END, 
                ' → ' ORDER BY sequence_number
            ) as phase_sequence
        FROM thinking_phases
        GROUP BY thinking_process_id
    )
    SELECT 
        tp.*,
        ps.total_phases,
        ps.completed_phases,
        (ps.completed_phases * 100.0 / ps.total_phases)::integer as actual_progress,
        ps.phase_sequence,
        ec.title as context_title,
        CASE 
            WHEN trig_exp.id IS NOT NULL THEN trig_exp.content 
            ELSE NULL 
        END as trigger_content,
        tp.meta_data
    FROM thinking_processes tp
    LEFT JOIN process_stats ps ON tp.id = ps.thinking_process_id
    LEFT JOIN experience_contexts ec ON tp.context_id = ec.id
    LEFT JOIN experiences trig_exp ON tp.triggered_by_experience_id = trig_exp.id
    WHERE tp.active_status = TRUE OR (tp.completed_status = TRUE AND tp.end_time > (CURRENT_TIMESTAMP - interval '24 hours'))
    ORDER BY 
        tp.active_status DESC,
        tp.start_time DESC;
    
    COMMENT ON VIEW active_thinking_processes IS 'Представление активных процессов мышления АМИ - текущие размышления с детализацией по фазам';
    
    RAISE NOTICE 'Представления уровня сознания успешно созданы';
END;
$$;