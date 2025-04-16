-- ============================================================================
-- ПРОЦЕДУРА СОЗДАНИЯ АССОЦИАТИВНЫХ СТРУКТУР СОЗНАТЕЛЬНОГО УРОВНЯ
-- ============================================================================
-- Создает таблицу для хранения связей между опытами:
-- 1. Связи между опытами (experience_connections)
-- ============================================================================

CREATE OR REPLACE PROCEDURE public.create_ami_association_structures(schema_name TEXT)
LANGUAGE plpgsql
AS $$
BEGIN
    -- =================================================================
    -- Таблица для хранения связей между опытами
    -- Моделирует различные типы ассоциативных связей между воспоминаниями
    -- =================================================================
    EXECUTE format('CREATE TABLE IF NOT EXISTS %I.experience_connections (
        id SERIAL PRIMARY KEY,
        source_experience_id INTEGER NOT NULL REFERENCES %I.experiences(id),
        target_experience_id INTEGER NOT NULL REFERENCES %I.experiences(id),
        connection_type TEXT NOT NULL CHECK (connection_type IN (
            ''temporal'',         -- Временная связь (последовательность)
            ''causal'',           -- Причинно-следственная связь
            ''semantic'',         -- Семантическая (смысловая) связь
            ''contextual'',       -- Контекстуальная связь (одинаковый контекст)
            ''thematic'',         -- Тематическая связь
            ''emotional'',        -- Эмоциональная связь
            ''analogy'',          -- Аналогия
            ''contrast'',         -- Контраст (противопоставление)
            ''elaboration'',      -- Детализация (расширение) 
            ''reference'',        -- Явная ссылка одного опыта на другой
            ''association'',      -- Свободная ассоциация без явной категории
            ''other''             -- Другой тип связи
        )),
        strength SMALLINT CHECK (strength BETWEEN 1 AND 10) DEFAULT 5,
        created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
        last_activated TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
        activation_count INTEGER DEFAULT 1,
        direction TEXT CHECK (direction IN (
            ''unidirectional'',   -- Однонаправленная связь
            ''bidirectional''     -- Двунаправленная связь
        )) DEFAULT ''bidirectional'',
        conscious_status BOOLEAN DEFAULT TRUE,
        description TEXT,
        meta_data JSONB
    )', schema_name, schema_name, schema_name);
    
    -- Комментарии к таблице experience_connections
    EXECUTE format('COMMENT ON TABLE %I.experience_connections IS $c$Связи между опытами - моделирует различные типы ассоциативных связей между воспоминаниями$c$', schema_name);
    EXECUTE format('COMMENT ON COLUMN %I.experience_connections.connection_type IS $c$Тип связи: временная, причинно-следственная, семантическая и т.д.$c$', schema_name);
    EXECUTE format('COMMENT ON COLUMN %I.experience_connections.strength IS $c$Сила ассоциативной связи по шкале 1-10$c$', schema_name);
    EXECUTE format('COMMENT ON COLUMN %I.experience_connections.activation_count IS $c$Количество активаций этой связи - отражает частоту использования$c$', schema_name);
    EXECUTE format('COMMENT ON COLUMN %I.experience_connections.direction IS $c$Направление связи: однонаправленная или двунаправленная$c$', schema_name);
    EXECUTE format('COMMENT ON COLUMN %I.experience_connections.conscious_status IS $c$Осознаёт ли АМИ эту связь (TRUE) или она существует на подсознательном уровне (FALSE)$c$', schema_name);

    -- Создание индексов для связей между опытами
    EXECUTE format('CREATE INDEX IF NOT EXISTS experience_connections_source_idx ON %I.experience_connections(source_experience_id)', schema_name);
    EXECUTE format('CREATE INDEX IF NOT EXISTS experience_connections_target_idx ON %I.experience_connections(target_experience_id)', schema_name);
    EXECUTE format('CREATE INDEX IF NOT EXISTS experience_connections_type_idx ON %I.experience_connections(connection_type)', schema_name);
    EXECUTE format('CREATE INDEX IF NOT EXISTS experience_connections_strength_idx ON %I.experience_connections(strength)', schema_name);
    EXECUTE format('CREATE INDEX IF NOT EXISTS experience_connections_last_activated_idx ON %I.experience_connections(last_activated)', schema_name);
    EXECUTE format('CREATE INDEX IF NOT EXISTS experience_connections_activation_count_idx ON %I.experience_connections(activation_count)', schema_name);
    EXECUTE format('CREATE INDEX IF NOT EXISTS experience_connections_direction_idx ON %I.experience_connections(direction)', schema_name);
    EXECUTE format('CREATE INDEX IF NOT EXISTS experience_connections_conscious_status_idx ON %I.experience_connections(conscious_status)', schema_name);
    
    -- Ограничение уникальности для предотвращения дублирования ассоциаций
    EXECUTE format('CREATE UNIQUE INDEX IF NOT EXISTS experience_connections_unique_idx 
    ON %I.experience_connections(source_experience_id, target_experience_id, connection_type)', schema_name);
    
    RAISE NOTICE 'Ассоциативные структуры успешно созданы';
END;
$$;
