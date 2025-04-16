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

CREATE OR REPLACE PROCEDURE public.create_ami_consciousness_views(schema_name TEXT)
LANGUAGE plpgsql
AS $$
BEGIN
    -- =================================================================
    -- Представление "текущего фокуса внимания"
    -- Показывает наиболее актуальные опыты из разных источников
    -- =================================================================
    EXECUTE format('CREATE OR REPLACE VIEW %I.current_awareness AS
    WITH recent_experiences AS (
        -- Недавние значимые опыты
        SELECT *
        FROM %I.experiences
        WHERE timestamp > (CURRENT_TIMESTAMP - interval ''24 hours'')
        ORDER BY timestamp DESC, salience DESC
        LIMIT 50
    ),
    recent_thinking AS (
        -- Активные процессы мышления
        SELECT tp.*, ph.id as last_phase_id, ph.content as last_phase_content
        FROM %I.thinking_processes tp
        LEFT JOIN %I.thinking_phases ph ON tp.id = ph.thinking_process_id
        WHERE tp.active_status = TRUE
        AND (ph.id IS NULL OR ph.id = (
            SELECT id FROM %I.thinking_phases 
            WHERE thinking_process_id = tp.id 
            ORDER BY sequence_number DESC 
            LIMIT 1
        ))
        ORDER BY tp.start_time DESC
        LIMIT 10
    )
    SELECT ''experience'' as element_type, id, timestamp, content, salience, NULL::INTEGER as process_id
    FROM recent_experiences
    UNION ALL
    SELECT ''thinking_process'' as element_type, id, start_time as timestamp, 
           CASE WHEN last_phase_content IS NOT NULL 
                THEN process_name || '': '' || last_phase_content 
                ELSE process_name 
           END as content,
           CASE WHEN active_status THEN 10 ELSE 5 END as salience,
           id as process_id
    FROM recent_thinking
    ORDER BY timestamp DESC, salience DESC
    LIMIT 20', schema_name, schema_name, schema_name, schema_name, schema_name);
    
    EXECUTE format('COMMENT ON VIEW %I.current_awareness IS $c$Представление текущего фокуса внимания АМИ - наиболее актуальные опыты и процессы мышления$c$', schema_name);
    
    -- =================================================================
    -- Представление внутреннего потока мыслей
    -- Включает опыты типа "мысль", "воспоминание", "инсайт"
    -- =================================================================
    EXECUTE format('CREATE OR REPLACE VIEW %I.internal_thought_stream AS
    SELECT e.*,
           ec.title as context_title,
           tp.process_name as thinking_process_name,
           tp.process_type as thinking_process_type,
           tp.active_status as thinking_process_active
    FROM %I.experiences e
    LEFT JOIN %I.experience_contexts ec ON e.context_id = ec.id
    LEFT JOIN %I.thinking_processes tp ON e.thinking_process_id = tp.id
    WHERE e.information_category = ''self''
      AND e.experience_type IN (''thought'', ''memory_recall'', ''insight'', ''decision'')
      AND e.timestamp > (CURRENT_TIMESTAMP - interval ''7 days'')
    ORDER BY e.timestamp DESC', schema_name, schema_name, schema_name, schema_name);
    
    EXECUTE format('COMMENT ON VIEW %I.internal_thought_stream IS $c$Внутренний поток мыслей АМИ - последовательность внутренних размышлений, воспоминаний и инсайтов$c$', schema_name);
    
    -- =================================================================
    -- Представление внешних взаимодействий
    -- Включает опыты, связанные с внешними источниками
    -- =================================================================
    EXECUTE format('CREATE OR REPLACE VIEW %I.external_interaction_stream AS
    SELECT e.*,
           s.name as source_name,
           s.source_type,
           t.name as target_name,
           ec.title as context_title
    FROM %I.experiences e
    LEFT JOIN %I.experience_sources s ON e.source_id = s.id
    LEFT JOIN %I.experience_sources t ON e.target_id = t.id
    LEFT JOIN %I.experience_contexts ec ON e.context_id = ec.id
    WHERE (e.information_category = ''subject'' OR e.information_category = ''object'')
      AND e.timestamp > (CURRENT_TIMESTAMP - interval ''7 days'')
    ORDER BY e.timestamp DESC', schema_name, schema_name, schema_name, schema_name, schema_name);
    
    EXECUTE format('COMMENT ON VIEW %I.external_interaction_stream IS $c$Поток внешних взаимодействий АМИ - последовательность опытов, связанных с внешними источниками$c$', schema_name);
    
    -- =================================================================
    -- Представление диалоговых взаимодействий
    -- Группирует опыты коммуникации по контекстам и участникам
    -- =================================================================
    EXECUTE format('CREATE OR REPLACE VIEW %I.dialogue_interactions AS
    SELECT 
        ec.id as context_id,
        ec.title as context_title,
        ec.context_type,
        (SELECT string_agg(DISTINCT es.name, '', '') 
         FROM %I.experience_sources es 
         WHERE es.id = ANY(ec.participants)) as participants,
        ec.created_at as started_at,
        ec.closed_at as ended_at,
        ec.active_status as is_active,
        (SELECT COUNT(*) FROM %I.experiences 
         WHERE context_id = ec.id AND experience_type = ''communication'') as message_count,
        (SELECT MAX(timestamp) FROM %I.experiences 
         WHERE context_id = ec.id AND experience_type = ''communication'') as last_message_at
    FROM %I.experience_contexts ec
    WHERE ec.context_type = ''conversation''
      AND ec.created_at > (CURRENT_TIMESTAMP - interval ''30 days'')
    ORDER BY 
        ec.active_status DESC,
        last_message_at DESC', schema_name, schema_name, schema_name, schema_name, schema_name);
    
    EXECUTE format('COMMENT ON VIEW %I.dialogue_interactions IS $c$Представление диалоговых взаимодействий АМИ - разговоры с внешними источниками, сгруппированные по контекстам$c$', schema_name);
    
    -- =================================================================
    -- Представление активных процессов мышления
    -- Показывает текущие процессы размышления с их фазами
    -- =================================================================
    EXECUTE format('CREATE OR REPLACE VIEW %I.active_thinking_processes AS
    WITH process_stats AS (
        SELECT 
            thinking_process_id,
            COUNT(*) as total_phases,
            SUM(CASE WHEN completed_status THEN 1 ELSE 0 END) as completed_phases,
            string_agg(
                CASE WHEN active_status THEN 
                    ''['' || sequence_number::text || ''] '' || phase_name 
                ELSE 
                    sequence_number::text || ''. '' || phase_name 
                END, 
                '' → '' ORDER BY sequence_number
            ) as phase_sequence
        FROM %I.thinking_phases
        GROUP BY thinking_process_id
    )
    SELECT 
        tp.id,
        tp.process_name,
        tp.process_type,
        tp.start_time,
        tp.end_time,
        tp.active_status,
        tp.completed_status,
        tp.progress_percentage,
        tp.context_id,
        tp.triggered_by_experience_id,
        tp.results,
        tp.result_experience_ids,
        tp.description,
        tp.meta_data,
        ps.total_phases,
        ps.completed_phases,
        (ps.completed_phases * 100.0 / ps.total_phases)::integer as actual_progress,
        ps.phase_sequence,
        ec.title as context_title,
        CASE 
            WHEN trig_exp.id IS NOT NULL THEN trig_exp.content 
            ELSE NULL 
        END as trigger_content
    FROM %I.thinking_processes tp
    LEFT JOIN process_stats ps ON tp.id = ps.thinking_process_id
    LEFT JOIN %I.experience_contexts ec ON tp.context_id = ec.id
    LEFT JOIN %I.experiences trig_exp ON tp.triggered_by_experience_id = trig_exp.id
    WHERE tp.active_status = TRUE OR (tp.completed_status = TRUE AND tp.end_time > (CURRENT_TIMESTAMP - interval ''24 hours''))
    ORDER BY 
        tp.active_status DESC,
        tp.start_time DESC', schema_name, schema_name, schema_name, schema_name, schema_name);
    
    EXECUTE format('COMMENT ON VIEW %I.active_thinking_processes IS $c$Представление активных процессов мышления АМИ - текущие размышления с детализацией по фазам$c$', schema_name);
    
    RAISE NOTICE 'Представления уровня сознания успешно созданы';
END;
$$;