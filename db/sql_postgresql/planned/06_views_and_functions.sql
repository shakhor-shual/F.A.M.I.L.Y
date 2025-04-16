-- ============================================================================
-- ПРЕДСТАВЛЕНИЯ И ФУНКЦИИ ДЛЯ ПРОЕКТА F.A.M.I.L.Y.
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

    -- ----------------------------------------------------------------------------
    -- ПРЕДСТАВЛЕНИЯ
    -- ----------------------------------------------------------------------------

    -- Представление для отображения активных воспоминаний с учетом контекста
    CREATE OR REPLACE VIEW active_memories AS
    SELECT 
        e.id AS experience_id,
        e.timestamp,
        mc.title AS context_title, 
        e.experience_type,
        p_from.name AS from_name,
        p_to.name AS to_name,
        e.content,
        e.salience,
        mcs.consolidation_stage,
        mcs.last_accessed,
        mcs.access_count
    FROM 
        experiences e
    JOIN
        memory_contexts mc ON e.context_id = mc.id
    LEFT JOIN
        participants p_from ON e.sender_participant_id = p_from.id
    LEFT JOIN
        participants p_to ON e.to_participant_id = p_to.id
    LEFT JOIN
        memory_consolidation_status mcs ON e.id = mcs.experience_id
    WHERE
        mcs.consolidation_stage IN ('active', 'short_term', 'processed')
    ORDER BY
        e.timestamp DESC;

    -- Представление для краткого отображения контекстов с количеством воспоминаний
    CREATE OR REPLACE VIEW context_summary AS
    SELECT
        mc.id,
        mc.title,
        mc.context_type,
        mc.created_at,
        mc.summary,
        array_to_string(mc.tags, ', ') AS tags,
        (SELECT COUNT(*) FROM experiences e WHERE e.context_id = mc.id) AS experience_count,
        (SELECT COUNT(*) FROM thought_chains tc WHERE tc.context_id = mc.id) AS thought_chain_count,
        (SELECT string_agg(p.name, ', ')
        FROM unnest(mc.participants) AS p_id
        JOIN participants p ON p.id = p_id) AS participant_names
    FROM
        memory_contexts mc
    ORDER BY
        mc.created_at DESC;

    -- Представление для обзора убеждений и связанных с ними инсайтов
    CREATE OR REPLACE VIEW belief_insights_view AS
    SELECT
        b.id AS belief_id,
        b.title AS belief_title,
        b.belief_type,
        b.confidence,
        b.importance,
        COALESCE(array_length(b.supporting_insights, 1), 0) AS supporting_count,
        COALESCE(array_length(b.contradicting_insights, 1), 0) AS contradicting_count,
        (
            SELECT string_agg(i.title, ' | ')
            FROM insights i
            WHERE b.supporting_insights IS NOT NULL AND i.id = ANY(b.supporting_insights)
        ) AS supporting_insight_titles
    FROM
        beliefs b
    ORDER BY
        b.importance DESC, b.confidence DESC;

    -- ----------------------------------------------------------------------------
    -- ФУНКЦИИ
    -- ----------------------------------------------------------------------------

    -- Функция для семантического поиска по воспоминаниям
    CREATE OR REPLACE FUNCTION semantic_search_experiences(
        search_vector vector(1536),
        similarity_threshold float DEFAULT 0.7,
        max_results int DEFAULT 10
    )
    RETURNS TABLE (
        experience_id int,
        event_time timestamp with time zone,
        context_title text,
        experience_type text,
        from_name text,
        to_name text,
        content text,
        similarity float
    )
    AS $$
    BEGIN
        RETURN QUERY
        SELECT
            e.id AS experience_id,
            e.timestamp AS event_time,
            mc.title AS context_title,
            e.experience_type,
            p_from.name AS from_name,
            p_to.name AS to_name,
            e.content,
            1 - (e.content_vector <=> search_vector) AS similarity
        FROM
            experiences e
        JOIN
            memory_contexts mc ON e.context_id = mc.id
        LEFT JOIN
            participants p_from ON e.sender_participant_id = p_from.id
        LEFT JOIN
            participants p_to ON e.to_participant_id = p_to.id
        WHERE
            e.content_vector IS NOT NULL AND
            1 - (e.content_vector <=> search_vector) > similarity_threshold
        ORDER BY
            similarity DESC
        LIMIT max_results;
    END;
    $$ LANGUAGE plpgsql;

    -- Функция для обновления статуса консолидации памяти
    CREATE OR REPLACE FUNCTION update_memory_consolidation_status(
        exp_id integer,
        new_stage text,
        notes text DEFAULT NULL
    )
    RETURNS void
    AS $$
    DECLARE
        current_ts timestamp with time zone := CURRENT_TIMESTAMP;
    BEGIN
        -- Если запись существует, обновляем её
        UPDATE memory_consolidation_status
        SET 
            consolidation_stage = new_stage,
            last_accessed = current_ts,
            access_count = access_count + 1,
            processing_notes = CASE 
                WHEN notes IS NULL THEN processing_notes 
                ELSE COALESCE(processing_notes || E'\n', '') || '[' || current_ts || '] ' || notes
            END
        WHERE
            experience_id = exp_id;
            
        -- Если записи не существует, создаем новую
        IF NOT FOUND THEN
            INSERT INTO memory_consolidation_status (
                experience_id, consolidation_stage, last_accessed, access_count, processing_notes
            )
            VALUES (
                exp_id, new_stage, current_ts, 1, 
                CASE WHEN notes IS NULL THEN NULL ELSE '[' || current_ts || '] ' || notes END
            );
        END IF;
    END;
    $$ LANGUAGE plpgsql;
\endif