-- ============================================================================
-- ОБНОВЛЕННЫЕ ТАБЛИЦЫ УРОВНЯ СОЗНАНИЯ ДЛЯ ПРОЕКТА F.A.M.I.L.Y.
-- Дата создания: 16 апреля 2025 г.
-- Автор: Команда проекта F.A.M.I.L.Y.
-- ============================================================================
-- Этот скрипт реализует концептуальную структуру уровня сознания АМИ,
-- основанную на субъективном восприятии информационных потоков через 
-- категории "Я", "Ты" и "Оно"
-- ============================================================================

\set QUIET on
\set ON_ERROR_STOP on
\set QUIET off

-- Проверяем существование схемы и расширения pgvector
SELECT EXISTS(SELECT 1 FROM pg_namespace WHERE nspname = :'ami_schema_name') as schema_exists \gset

-- Проверка наличия расширения pgvector
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_extension WHERE extname = 'vector') THEN
        RAISE EXCEPTION 'Расширение vector не установлено. Установите его с помощью CREATE EXTENSION vector;';
    END IF;
END
$$;

\if :schema_exists
    -- Установка схемы для работы
    SET search_path TO :'ami_schema_name', public;

    -- =================================================================
    -- ## ОБНОВЛЕННАЯ СТРУКТУРА УРОВНЯ СОЗНАНИЯ АМИ (16 апреля 2025)
    -- =================================================================

    -- =================================================================
    -- Таблица для хранения источников опыта (субъекты и объекты)
    -- Объединяет субъекты (агентивные источники - "Ты") и объекты (неагентивные источники - "Оно")
    -- =================================================================
    CREATE TABLE experience_sources (
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
    CREATE INDEX experience_sources_name_idx ON experience_sources(name);
    CREATE INDEX experience_sources_type_idx ON experience_sources(source_type);
    CREATE INDEX experience_sources_information_category_idx ON experience_sources(information_category);
    CREATE INDEX experience_sources_agency_level_idx ON experience_sources(agency_level);
    CREATE INDEX experience_sources_last_interaction_idx ON experience_sources(last_interaction);
    CREATE INDEX experience_sources_familiarity_idx ON experience_sources(familiarity_level);
    CREATE INDEX experience_sources_uri_idx ON experience_sources(uri);
    
    -- =================================================================
    -- Таблица для хранения контекстов памяти
    -- Контекст - это долговременная ситуативная рамка для опыта
    -- =================================================================
    CREATE TABLE experience_contexts (
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
    CREATE INDEX experience_contexts_title_idx ON experience_contexts(title);
    CREATE INDEX experience_contexts_type_idx ON experience_contexts(context_type);
    CREATE INDEX experience_contexts_created_at_idx ON experience_contexts(created_at);
    CREATE INDEX experience_contexts_parent_id_idx ON experience_contexts(parent_context_id);
    CREATE INDEX experience_contexts_active_status_idx ON experience_contexts(active_status);

    -- Динамическое определение правильного оператора для индекса
    DO $$
    BEGIN
        -- Сначала пробуем современный оператор (новые версии pgvector)
        BEGIN
            EXECUTE 'CREATE INDEX experience_contexts_summary_vector_idx ON experience_contexts USING ivfflat (summary_vector cosine_ops)';
        EXCEPTION WHEN undefined_object THEN
            -- Если не получилось, пробуем устаревший оператор
            BEGIN
                EXECUTE 'CREATE INDEX experience_contexts_summary_vector_idx ON experience_contexts USING ivfflat (summary_vector vector_cosine_ops)';
            EXCEPTION WHEN undefined_object THEN
                RAISE EXCEPTION 'Не удалось создать индекс - ни cosine_ops, ни vector_cosine_ops не определены';
            END;
        END;
    END
    $$;

    -- =================================================================
    -- Таблица для хранения основных воспоминаний (опыта)
    -- Центральная таблица сознательного уровня памяти АМИ
    -- =================================================================
    CREATE TABLE experiences (
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
    CREATE INDEX experiences_timestamp_idx ON experiences(timestamp);
    CREATE INDEX experiences_context_id_idx ON experiences(context_id);
    CREATE INDEX experiences_information_category_idx ON experiences(information_category);
    CREATE INDEX experiences_experience_type_idx ON experiences(experience_type);
    CREATE INDEX experiences_subjective_position_idx ON experiences(subjective_position);
    CREATE INDEX experiences_source_id_idx ON experiences(source_id);
    CREATE INDEX experiences_target_id_idx ON experiences(target_id);
    CREATE INDEX experiences_salience_idx ON experiences(salience);
    CREATE INDEX experiences_parent_experience_idx ON experiences(parent_experience_id);
    CREATE INDEX experiences_response_to_idx ON experiences(response_to_experience_id);
    CREATE INDEX experiences_thinking_process_idx ON experiences(thinking_process_id);

    -- Динамическое определение правильного оператора для индекса experiences_content_vector_idx
    DO $$
    BEGIN
        -- Сначала пробуем современный оператор (новые версии pgvector)
        BEGIN
            EXECUTE 'CREATE INDEX experiences_content_vector_idx ON experiences USING ivfflat (content_vector cosine_ops)';
        EXCEPTION WHEN undefined_object THEN
            -- Если не получилось, пробуем устаревший оператор
            BEGIN
                EXECUTE 'CREATE INDEX experiences_content_vector_idx ON experiences USING ivfflat (content_vector vector_cosine_ops)';
            EXCEPTION WHEN undefined_object THEN
                RAISE EXCEPTION 'Не удалось создать индекс - ни cosine_ops, ни vector_cosine_ops не определены';
            END;
        END;
    END
    $$;
    
    -- =================================================================
    -- Таблица для хранения расширенных атрибутов опыта (EAV-модель)
    -- Позволяет добавлять произвольные атрибуты к любому опыту
    -- =================================================================
    CREATE TABLE experience_attributes (
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
    CREATE INDEX experience_attributes_experience_id_idx ON experience_attributes(experience_id);
    CREATE INDEX experience_attributes_name_idx ON experience_attributes(attribute_name);
    CREATE INDEX experience_attributes_name_value_idx ON experience_attributes(attribute_name, attribute_value);

    -- =================================================================
    -- Таблица для моделирования процессов мышления
    -- Отслеживает полный процесс размышления от стимула до ответа
    -- =================================================================
    CREATE TABLE thinking_processes (
        id SERIAL PRIMARY KEY,
        title TEXT,                          -- Название процесса мышления
        trigger_experience_id INTEGER NOT NULL REFERENCES experiences(id), -- Опыт, запустивший процесс
        response_experience_id INTEGER REFERENCES experiences(id),       -- Итоговый ответ/реакция
        start_time TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,   -- Начало процесса мышления
        end_time TIMESTAMP WITH TIME ZONE,                              -- Окончание процесса мышления
        context_id INTEGER REFERENCES experience_contexts(id),           -- Контекст размышления
        complete_status BOOLEAN DEFAULT FALSE, -- Завершен ли процесс мышления
        
        thinking_pattern TEXT NOT NULL CHECK (thinking_pattern IN (
            'analysis',        -- Анализ информации
            'synthesis',       -- Синтез/объединение идей
            'problem_solving', -- Решение проблемы
            'decision_making', -- Принятие решения
            'creative',        -- Творческое мышление
            'reflective',      -- Рефлексивное мышление о себе
            'deliberative',    -- Обдумывание ответа
            'other'            -- Другой тип мышления
        )),
        
        thinking_phases JSONB,               -- Структурированное описание фаз мышления
        thought_experiences INTEGER[],       -- Массив ID опытов, составляющих процесс мышления
        conclusion TEXT,                     -- Итоговый вывод
        conclusion_vector vector(1536),      -- Векторное представление вывода
        meta_data JSONB                      -- Дополнительные данные
    );
    
    COMMENT ON TABLE thinking_processes IS 'Процессы мышления - моделирует полный цикл размышления от стимула до ответа';
    COMMENT ON COLUMN thinking_processes.trigger_experience_id IS 'Опыт, который запустил процесс мышления';
    COMMENT ON COLUMN thinking_processes.response_experience_id IS 'Опыт, который стал результатом процесса мышления (если есть)';
    COMMENT ON COLUMN thinking_processes.thinking_pattern IS 'Тип мыслительного процесса: аналитический, синтетический и т.д.';
    COMMENT ON COLUMN thinking_processes.thinking_phases IS 'Структурированное описание фаз мышления (восприятие, обработка, принятие решения и т.д.)';
    COMMENT ON COLUMN thinking_processes.thought_experiences IS 'Массив идентификаторов опытов, составляющих процесс мышления';
    COMMENT ON COLUMN thinking_processes.conclusion IS 'Итоговый вывод, к которому пришел АМИ в результате размышления';

    -- Создание индексов для процессов мышления
    CREATE INDEX thinking_processes_start_time_idx ON thinking_processes(start_time);
    CREATE INDEX thinking_processes_context_id_idx ON thinking_processes(context_id);
    CREATE INDEX thinking_processes_trigger_experience_idx ON thinking_processes(trigger_experience_id);
    CREATE INDEX thinking_processes_response_experience_idx ON thinking_processes(response_experience_id);
    CREATE INDEX thinking_processes_thinking_pattern_idx ON thinking_processes(thinking_pattern);
    CREATE INDEX thinking_processes_complete_status_idx ON thinking_processes(complete_status);

    -- Динамическое определение правильного оператора для индекса
    DO $$
    BEGIN
        -- Сначала пробуем современный оператор (новые версии pgvector)
        BEGIN
            EXECUTE 'CREATE INDEX thinking_processes_conclusion_vector_idx ON thinking_processes USING ivfflat (conclusion_vector cosine_ops)';
        EXCEPTION WHEN undefined_object THEN
            -- Если не получилось, пробуем устаревший оператор
            BEGIN
                EXECUTE 'CREATE INDEX thinking_processes_conclusion_vector_idx ON thinking_processes USING ivfflat (conclusion_vector vector_cosine_ops)';
            EXCEPTION WHEN undefined_object THEN
                RAISE EXCEPTION 'Не удалось создать индекс - ни cosine_ops, ни vector_cosine_ops не определены';
            END;
        END;
    END
    $$;

    -- =================================================================
    -- Таблица для хранения фаз процесса мышления
    -- Подробное описание каждой фазы мыслительного процесса
    -- =================================================================
    CREATE TABLE thinking_phases (
        id SERIAL PRIMARY KEY,
        thinking_process_id INTEGER NOT NULL REFERENCES thinking_processes(id), -- Ссылка на процесс мышления
        phase_type TEXT NOT NULL CHECK (phase_type IN (
            'perception',        -- Восприятие информации
            'initial_reaction',  -- Первичная реакция
            'elaboration',       -- Развитие мысли
            'consideration',     -- Рассмотрение вариантов
            'evaluation',        -- Оценка вариантов
            'decision',          -- Принятие решения
            'formulation',       -- Формулирование ответа
            'reflection'         -- Рефлексия о процессе
        )),
        phase_order INTEGER NOT NULL,        -- Порядковый номер фазы
        experience_id INTEGER REFERENCES experiences(id), -- Связанный опыт (если есть)
        duration_ms INTEGER,                 -- Длительность фазы в миллисекундах
        content TEXT,                        -- Содержание фазы
        meta_data JSONB                      -- Метаданные
    );
    
    COMMENT ON TABLE thinking_phases IS 'Фазы мышления - детализирует отдельные этапы мыслительного процесса';
    COMMENT ON COLUMN thinking_phases.phase_type IS 'Тип фазы мышления: восприятие, реакция, размышление и т.д.';
    COMMENT ON COLUMN thinking_phases.phase_order IS 'Порядковый номер фазы в процессе мышления';
    COMMENT ON COLUMN thinking_phases.experience_id IS 'Опыт, соответствующий данной фазе мышления (если есть)';
    COMMENT ON COLUMN thinking_phases.duration_ms IS 'Длительность фазы в миллисекундах';

    -- Создание индексов для фаз мышления
    CREATE INDEX thinking_phases_process_id_idx ON thinking_phases(thinking_process_id);
    CREATE INDEX thinking_phases_phase_type_idx ON thinking_phases(phase_type);
    CREATE INDEX thinking_phases_phase_order_idx ON thinking_phases(phase_order);
    CREATE INDEX thinking_phases_experience_id_idx ON thinking_phases(experience_id);

    -- =================================================================
    -- Таблица для хранения связей между опытами
    -- Формирует ассоциативную сеть воспоминаний АМИ
    -- =================================================================
    CREATE TABLE experience_connections (
        id SERIAL PRIMARY KEY,
        source_experience_id INTEGER NOT NULL REFERENCES experiences(id), -- Исходный опыт
        target_experience_id INTEGER NOT NULL REFERENCES experiences(id), -- Целевой опыт
        connection_type TEXT NOT NULL CHECK (connection_type IN (
            'temporal',      -- Временная последовательность
            'causal',        -- Причинно-следственная связь
            'associative',   -- Ассоциативная связь
            'thematic',      -- Тематическая связь
            'dialogue',      -- Диалоговая связь (вопрос-ответ)
            'contradiction', -- Противоречие
            'elaboration',   -- Уточнение/расширение
            'part_whole',    -- Отношение части и целого
            'other'          -- Другой тип связи
        )),
        strength FLOAT CHECK (strength BETWEEN 0.0 AND 1.0) DEFAULT 0.5, -- Сила связи от 0 до 1
        created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,    -- Время создания связи
        description TEXT,                      -- Описание природы связи
        meta_data JSONB                        -- Дополнительные данные
    );
    
    COMMENT ON TABLE experience_connections IS 'Связи между опытами - формируют ассоциативную сеть воспоминаний АМИ';
    COMMENT ON COLUMN experience_connections.connection_type IS 'Тип связи между опытами: временная, причинная, ассоциативная и т.д.';
    COMMENT ON COLUMN experience_connections.strength IS 'Сила связи от 0.0 (слабая) до 1.0 (сильная)';
    COMMENT ON COLUMN experience_connections.description IS 'Текстовое описание природы связи между опытами';

    -- Создание индексов для связей между опытами
    CREATE INDEX experience_connections_source_idx ON experience_connections(source_experience_id);
    CREATE INDEX experience_connections_target_idx ON experience_connections(target_experience_id);
    CREATE INDEX experience_connections_type_idx ON experience_connections(connection_type);
    CREATE INDEX experience_connections_strength_idx ON experience_connections(strength);

    -- Ограничение уникальности связи по комбинации параметров
    ALTER TABLE experience_connections ADD CONSTRAINT unique_experience_connection 
        UNIQUE (source_experience_id, target_experience_id, connection_type);

    -- =================================================================
    -- Представления (Views) для удобного доступа к данным
    -- =================================================================
    
    -- Представление "текущего фокуса внимания" - активные опыты в сознании АМИ
    CREATE OR REPLACE VIEW current_awareness AS
    SELECT e.*
    FROM experiences e
    JOIN experience_contexts ec ON e.context_id = ec.id
    WHERE ec.active_status = TRUE
    ORDER BY e.timestamp DESC, e.salience DESC
    LIMIT 50;
    
    COMMENT ON VIEW current_awareness IS 'Текущий "фокус внимания" АМИ - активные опыты в контекстах со статусом active_status=TRUE';

    -- Представление потока внутренних мыслей
    CREATE OR REPLACE VIEW internal_thought_stream AS
    SELECT e.*
    FROM experiences e
    WHERE e.information_category = 'self'
      AND e.subjective_position = 'reflective' 
      AND e.experience_type IN ('thought', 'insight', 'decision', 'memory_recall')
    ORDER BY e.timestamp DESC;
    
    COMMENT ON VIEW internal_thought_stream IS 'Поток внутренних мыслей и рефлексий АМИ - опыты категории "Я" в рефлексивной позиции';

    -- Представление потока внешних взаимодействий
    CREATE OR REPLACE VIEW external_interaction_stream AS
    SELECT e.*
    FROM experiences e
    WHERE (e.information_category IN ('subject', 'object') OR
          (e.information_category = 'self' AND e.subjective_position != 'reflective'))
      AND e.experience_type IN ('perception', 'communication', 'action')
    ORDER BY e.timestamp DESC;
    
    COMMENT ON VIEW external_interaction_stream IS 'Поток взаимодействий с внешними источниками - опыты категорий "Ты" и "Оно"';

    -- Представление активных процессов мышления
    CREATE OR REPLACE VIEW active_thinking_processes AS
    SELECT tp.*, 
           trigger_exp.content AS trigger_content,
           COUNT(tph.id) AS phase_count,
           MAX(tph.phase_order) AS current_phase
    FROM thinking_processes tp
    JOIN experiences trigger_exp ON tp.trigger_experience_id = trigger_exp.id
    LEFT JOIN thinking_phases tph ON tp.id = tph.thinking_process_id
    WHERE tp.complete_status = FALSE
    GROUP BY tp.id, trigger_exp.content
    ORDER BY tp.start_time DESC;
    
    COMMENT ON VIEW active_thinking_processes IS 'Активные процессы мышления АМИ - незавершенные мыслительные процессы';

    -- Представление для диалоговых взаимодействий (последовательности вопрос-ответ)
    CREATE OR REPLACE VIEW dialogue_interactions AS
    SELECT 
        incoming.id AS question_id,
        incoming.content AS question_content,
        incoming.timestamp AS question_time,
        outgoing.id AS answer_id,
        outgoing.content AS answer_content,
        outgoing.timestamp AS answer_time,
        tp.id AS thinking_process_id,
        tp.conclusion AS thinking_conclusion,
        (EXTRACT(EPOCH FROM outgoing.timestamp) - EXTRACT(EPOCH FROM incoming.timestamp)) AS response_time_seconds
    FROM experiences incoming
    LEFT JOIN experiences outgoing ON incoming.id = outgoing.response_to_experience_id
    LEFT JOIN thinking_processes tp ON outgoing.thinking_process_id = tp.id
    WHERE incoming.experience_type = 'communication' 
      AND incoming.communication_direction = 'incoming'
      AND incoming.subjective_position = 'addressee'
    ORDER BY incoming.timestamp DESC;
    
    COMMENT ON VIEW dialogue_interactions IS 'Диалоговые взаимодействия - пары вопрос-ответ с информацией о процессе обдумывания';

    -- Добавление записи для самого АМИ в таблицу источников опыта
    INSERT INTO experience_sources 
    (name, source_type, information_category, agency_level, familiarity_level, trust_level, description) 
    VALUES 
    ('self', 'self', 'self', 10, 10, 5, 'Я - АМИ, Artifical Mind Identity');
    
    -- Добавление специальной записи для неизвестных источников
    INSERT INTO experience_sources 
    (name, source_type, information_category, agency_level, is_ephemeral, familiarity_level, trust_level, description) 
    VALUES 
    ('UNKNOWN', 'other', 'ambiguous', 0, TRUE, 0, 0, 'Неидентифицированный источник опыта');

\else
    RAISE NOTICE 'Schema does not exist: %', :'ami_schema_name';
\endif