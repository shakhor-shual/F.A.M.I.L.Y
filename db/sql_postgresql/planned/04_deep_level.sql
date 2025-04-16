-- ============================================================================
-- ТАБЛИЦЫ ГЛУБИННОГО УРОВНЯ ДЛЯ ПРОЕКТА F.A.M.I.L.Y.
-- Дата создания: 12 апреля 2025 г.
-- Обновлено: 13 апреля 2025 г. - адаптация имен полей для SQLAlchemy ORM
-- ============================================================================

\set QUIET on
\set ON_ERROR_STOP on
\set QUIET off

-- Проверяем существование схемы
SELECT EXISTS(SELECT 1 FROM pg_namespace WHERE nspname = :'ami_schema_name') as schema_exists \gset

\if :schema_exists
    -- Установка схемы для работы
    SET search_path TO :'ami_schema_name', public;

    -- Таблица для хранения фундаментальных принципов
    CREATE TABLE core_principles (
        id SERIAL PRIMARY KEY,
        established_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
        title TEXT NOT NULL,
        description TEXT NOT NULL,
        principle_type TEXT NOT NULL CHECK (principle_type IN (
            'ethical', 'epistemological', 'operational', 'identity', 'safety', 'developmental'
        )),
        priority SMALLINT CHECK (priority > 0) DEFAULT 5,
        origin TEXT,
        supporting_beliefs INTEGER[],
        immutability FLOAT CHECK (immutability BETWEEN 0 AND 1) DEFAULT 0.8,
        active BOOLEAN DEFAULT TRUE
    );

    -- Создание индексов для фундаментальных принципов
    CREATE INDEX core_principles_established_at_idx ON core_principles(established_at);
    CREATE INDEX core_principles_type_idx ON core_principles(principle_type);
    CREATE INDEX core_principles_priority_idx ON core_principles(priority);

    -- Таблица для хранения поведенческих эвристик
    CREATE TABLE behavioral_heuristics (
        id SERIAL PRIMARY KEY,
        created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
        name TEXT NOT NULL,
        description TEXT NOT NULL,
        trigger_pattern TEXT NOT NULL,
        response_pattern TEXT NOT NULL,
        heuristic_type TEXT NOT NULL CHECK (heuristic_type IN (
            'safety', 'communication', 'cognitive', 'emotional', 'goal_oriented', 'social'
        )),
        priority SMALLINT CHECK (priority > 0) DEFAULT 5,
        override_threshold FLOAT CHECK (override_threshold BETWEEN 0 AND 1) DEFAULT 0.7,
        success_rate FLOAT CHECK (success_rate BETWEEN 0 AND 1) DEFAULT 0.5,
        application_count INTEGER DEFAULT 0,
        last_applied TIMESTAMP WITH TIME ZONE,
        active BOOLEAN DEFAULT TRUE
    );

    -- Создание индексов для поведенческих эвристик
    CREATE INDEX behavioral_heuristics_created_at_idx ON behavioral_heuristics(created_at);
    CREATE INDEX behavioral_heuristics_type_idx ON behavioral_heuristics(heuristic_type);
    CREATE INDEX behavioral_heuristics_priority_idx ON behavioral_heuristics(priority);

    -- Таблица для отслеживания когнитивных искажений
    CREATE TABLE cognitive_biases (
        id SERIAL PRIMARY KEY,
        identified_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
        name TEXT NOT NULL,
        description TEXT NOT NULL,
        bias_type TEXT NOT NULL CHECK (bias_type IN (
            'confirmation', 'availability', 'anchoring', 'representativeness', 
            'overconfidence', 'self_serving', 'other'
        )),
        detection_conditions TEXT,
        correction_strategy TEXT,
        occurrence_count INTEGER DEFAULT 0,
        last_occurrence TIMESTAMP WITH TIME ZONE,
        correction_success_rate FLOAT CHECK (correction_success_rate BETWEEN 0 AND 1) DEFAULT 0.5
    );

    -- Создание индексов для когнитивных искажений
    CREATE INDEX cognitive_biases_identified_at_idx ON cognitive_biases(identified_at);
    CREATE INDEX cognitive_biases_type_idx ON cognitive_biases(bias_type);

    -- Таблица для хранения убеждений АМИ
    CREATE TABLE beliefs (
        id SERIAL PRIMARY KEY,
        title TEXT NOT NULL,
        belief_type TEXT NOT NULL CHECK (belief_type IN (
            'core', 'derived', 'provisional', 'adopted', 'questioned'
        )),
        created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
        content TEXT NOT NULL,
        content_vector vector(1536),
        source_insights INTEGER[],
        supporting_insights INTEGER[],
        contradicting_insights INTEGER[],
        confidence FLOAT CHECK (confidence BETWEEN 0.0 AND 1.0) DEFAULT 0.5,
        importance SMALLINT CHECK (importance BETWEEN 1 AND 10) DEFAULT 5,
        meta_data JSONB  -- Переименовано из metadata для совместимости с SQLAlchemy
    );

    -- Создание индексов для убеждений
    CREATE INDEX beliefs_title_idx ON beliefs(title);
    CREATE INDEX beliefs_type_idx ON beliefs(belief_type);
    CREATE INDEX beliefs_confidence_idx ON beliefs(confidence);
    CREATE INDEX beliefs_importance_idx ON beliefs(importance);
    CREATE INDEX beliefs_content_vector_idx ON beliefs USING ivfflat (content_vector vector_cosine_ops);

    -- Таблица для хранения принципов АМИ
    CREATE TABLE principles (
        id SERIAL PRIMARY KEY,
        title TEXT NOT NULL,
        principle_type TEXT NOT NULL CHECK (principle_type IN (
            'ethical', 'operational', 'personal', 'relational', 'systemic'
        )),
        created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
        content TEXT NOT NULL,
        content_vector vector(1536),
        related_beliefs INTEGER[],
        priority SMALLINT CHECK (priority BETWEEN 1 AND 10) DEFAULT 5,
        is_active BOOLEAN DEFAULT TRUE,
        meta_data JSONB  -- Переименовано из metadata для совместимости с SQLAlchemy
    );

    -- Создание индексов для принципов
    CREATE INDEX principles_title_idx ON principles(title);
    CREATE INDEX principles_type_idx ON principles(principle_type);
    CREATE INDEX principles_priority_idx ON principles(priority);
    CREATE INDEX principles_content_vector_idx ON principles USING ivfflat (content_vector vector_cosine_ops);

    -- Таблица для хранения ценностей АМИ (переименовано из values во избежание конфликта с ключевым словом Python)
    CREATE TABLE ami_values (  -- Переименовано из values для совместимости с Python
        id SERIAL PRIMARY KEY,
        title TEXT NOT NULL,
        value_type TEXT NOT NULL CHECK (value_type IN (
            'intrinsic', 'instrumental', 'moral', 'aesthetic', 'social', 'personal'
        )),
        created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
        content TEXT NOT NULL,
        content_vector vector(1536),
        related_principles INTEGER[],
        importance SMALLINT CHECK (importance BETWEEN 1 AND 10) DEFAULT 5,
        meta_data JSONB  -- Переименовано из metadata для совместимости с SQLAlchemy
    );

    -- Создание индексов для ценностей (обновлены имена индексов)
    CREATE INDEX ami_values_title_idx ON ami_values(title);  -- Обновлено имя индекса
    CREATE INDEX ami_values_type_idx ON ami_values(value_type);  -- Обновлено имя индекса
    CREATE INDEX ami_values_importance_idx ON ami_values(importance);  -- Обновлено имя индекса
    CREATE INDEX ami_values_content_vector_idx ON ami_values USING ivfflat (content_vector vector_cosine_ops);  -- Обновлено имя индекса

\else
    RAISE NOTICE 'Schema does not exist: %', :'ami_schema_name';
\endif