-- ============================================================================
-- ТАБЛИЦЫ МЕТАСИСТЕМНОГО УРОВНЯ ДЛЯ ПРОЕКТА F.A.M.I.L.Y.
-- Дата создания: 12 апреля 2025 г.
-- ============================================================================

\set QUIET on
\set ON_ERROR_STOP on
\set QUIET off

-- Проверяем существование схемы
SELECT EXISTS(SELECT 1 FROM pg_namespace WHERE nspname = :'ami_schema_name') as schema_exists \gset

\if :schema_exists
    -- Установка схемы для работы
    SET search_path TO :'ami_schema_name', public;

    -- Таблица для операций по управлению памятью
    CREATE TABLE memory_management_operations (
        id SERIAL PRIMARY KEY,
        timestamp TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
        operation_type TEXT CHECK (operation_type IN (
            'consolidation', 'generalization', 'reactivation', 'pruning', 'reorganization', 'audit'
        )),
        target_entities JSONB,
        operation_description TEXT,
        triggered_by TEXT,
        success_status BOOLEAN,
        performance_metrics JSONB,
        notes TEXT
    );

    -- Создание индексов для операций по управлению памятью
    CREATE INDEX memory_management_operations_timestamp_idx ON memory_management_operations(timestamp);
    CREATE INDEX memory_management_operations_type_idx ON memory_management_operations(operation_type);

    -- Таблица для управления временным "окном внимания"
    CREATE TABLE temporal_memory_window (
        id SERIAL PRIMARY KEY,
        window_start TIMESTAMP WITH TIME ZONE,
        window_end TIMESTAMP WITH TIME ZONE,
        focus_intensity JSONB,
        primary_context_ids INTEGER[],
        primary_experience_ids INTEGER[],
        active_thought_chains INTEGER[],
        relevant_insights INTEGER[],
        relevant_beliefs INTEGER[],
        active_principles INTEGER[],
        window_summary TEXT,
        created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
        is_current BOOLEAN DEFAULT FALSE
    );

    -- Создание индекса для текущего окна внимания
    CREATE INDEX temporal_memory_window_is_current_idx ON temporal_memory_window(is_current);
    CREATE INDEX temporal_memory_window_time_range_idx ON temporal_memory_window(window_start, window_end);

    -- Таблица для отслеживания баланса внимания
    CREATE TABLE attention_balance_metrics (
        id SERIAL PRIMARY KEY,
        timestamp TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
        time_window INTERVAL,
        internal_attention_percent FLOAT,
        external_attention_percent FLOAT,
        thought_count INTEGER,
        external_interaction_count INTEGER,
        balance_assessment TEXT,
        potential_concerns TEXT,
        adjustment_actions TEXT
    );

    -- Создание индексов для метрик баланса внимания
    CREATE INDEX attention_balance_metrics_timestamp_idx ON attention_balance_metrics(timestamp);

    -- Таблица для сегментации потока сознания
    CREATE TABLE consciousness_stream_segments (
        id SERIAL PRIMARY KEY,
        start_timestamp TIMESTAMP WITH TIME ZONE,
        end_timestamp TIMESTAMP WITH TIME ZONE,
        segment_type TEXT CHECK (segment_type IN (
            'focused_task', 'conversation', 'exploration', 'reflection', 'transition', 'integration'
        )),
        subjective_duration FLOAT,
        primary_focus TEXT,
        experiences_count INTEGER,
        internal_external_ratio FLOAT,
        segment_summary TEXT,
        continuity_markers JSONB
    );

    -- Создание индексов для сегментов потока сознания
    CREATE INDEX consciousness_stream_segments_time_range_idx ON consciousness_stream_segments(start_timestamp, end_timestamp);
    CREATE INDEX consciousness_stream_segments_type_idx ON consciousness_stream_segments(segment_type);

    -- Таблица для управления вниманием
    CREATE TABLE attention_management (
        id SERIAL PRIMARY KEY,
        timestamp TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
        context_id INTEGER,
        focus_object TEXT,
        focus_type TEXT CHECK (focus_type IN ('internal', 'external', 'mixed')),
        priority INTEGER CHECK (priority BETWEEN 1 AND 10),
        duration INTERVAL,
        interruption_count INTEGER DEFAULT 0,
        effectiveness_score FLOAT,
        notes TEXT
    );

    -- Создание индексов для управления вниманием
    CREATE INDEX attention_context_idx ON attention_management(context_id);
    CREATE INDEX attention_focus_idx ON attention_management(focus_type);
    CREATE INDEX attention_priority_idx ON attention_management(priority);

    -- Таблица для метаданных памяти
    CREATE TABLE memory_metadata (
        id SERIAL PRIMARY KEY,
        timestamp TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
        metadata_type TEXT CHECK (metadata_type IN ('system_state', 'health_check', 'statistics', 'consistency')),
        summary TEXT,
        detailed_data JSONB,
        health_score FLOAT CHECK (health_score BETWEEN 0 AND 1),
        recommendations TEXT,
        action_taken TEXT
    );

    -- Создание индексов для метаданных памяти
    CREATE INDEX memory_metadata_type_idx ON memory_metadata(metadata_type);
    CREATE INDEX memory_metadata_health_idx ON memory_metadata(health_score);

    -- Таблица для отслеживания происхождения воспоминаний
    CREATE TABLE memory_provenance (
        id SERIAL PRIMARY KEY,
        memory_id INTEGER,
        memory_type TEXT CHECK (memory_type IN ('experience', 'insight', 'belief', 'principle')),
        source_description TEXT,
        source_reliability FLOAT CHECK (source_reliability BETWEEN 0 AND 1),
        verification_status TEXT CHECK (verification_status IN ('unverified', 'partially_verified', 'verified', 'disputed')),
        verification_method TEXT,
        timestamp TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
    );

    -- Создание индексов для происхождения воспоминаний
    CREATE INDEX memory_provenance_memory_idx ON memory_provenance(memory_id, memory_type);
    CREATE INDEX memory_provenance_source_idx ON memory_provenance(source_reliability, verification_status);

    -- Таблица для хранения целей АМИ
    CREATE TABLE goals (
        id SERIAL PRIMARY KEY, 
        title TEXT NOT NULL,
        description TEXT,
        created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
        target_completion_date TIMESTAMP WITH TIME ZONE,
        priority INTEGER CHECK (priority BETWEEN 1 AND 10),
        progress FLOAT CHECK (progress BETWEEN 0 AND 1) DEFAULT 0,
        status TEXT CHECK (status IN ('active', 'completed', 'abandoned', 'postponed')),
        parent_goal_id INTEGER REFERENCES goals(id),
        related_experiences INTEGER[],
        related_insights INTEGER[],
        success_criteria TEXT,
        reflection_notes TEXT
    );

    -- Создание индекса для целей
    CREATE INDEX goals_progress_idx ON goals(progress);
\else
    RAISE EXCEPTION 'Schema does not exist';
\endif