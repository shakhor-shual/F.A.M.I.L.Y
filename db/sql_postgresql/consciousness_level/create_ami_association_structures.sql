-- ============================================================================
-- PROCEDURE FOR CREATING CONSCIOUSNESS LEVEL ASSOCIATION STRUCTURES
-- ============================================================================
-- Creates table for storing connections between experiences:
-- 1. Experience connections (experience_connections)
-- ============================================================================

CREATE OR REPLACE PROCEDURE public.create_ami_association_structures(schema_name TEXT)
LANGUAGE plpgsql
AS $$
BEGIN
    -- =================================================================
    -- Table for storing connections between experiences
    -- Models various types of associative connections between memories
    -- =================================================================
    EXECUTE format('CREATE TABLE IF NOT EXISTS %I.experience_connections (
        id SERIAL PRIMARY KEY,
        source_experience_id INTEGER NOT NULL REFERENCES %I.experiences(id),
        target_experience_id INTEGER NOT NULL REFERENCES %I.experiences(id),
        connection_type TEXT NOT NULL CHECK (connection_type IN (
            ''temporal'',         -- Temporal connection (sequence)
            ''causal'',           -- Causal connection
            ''semantic'',         -- Semantic (meaning) connection
            ''contextual'',       -- Contextual connection (same context)
            ''thematic'',         -- Thematic connection
            ''emotional'',        -- Emotional connection
            ''analogy'',          -- Analogy
            ''contrast'',         -- Contrast (opposition)
            ''elaboration'',      -- Elaboration (expansion)
            ''reference'',        -- Explicit reference of one experience to another
            ''association'',      -- Free association without explicit category
            ''other''             -- Other connection type
        )),
        strength SMALLINT CHECK (strength BETWEEN 1 AND 10) DEFAULT 5,
        created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
        last_activated TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
        activation_count INTEGER DEFAULT 1,
        direction TEXT CHECK (direction IN (
            ''unidirectional'',   -- Unidirectional connection
            ''bidirectional''     -- Bidirectional connection
        )) DEFAULT ''bidirectional'',
        conscious_status BOOLEAN DEFAULT TRUE,
        description TEXT,
        meta_data JSONB
    )', schema_name, schema_name, schema_name);
    
    -- Comments on experience_connections table
    EXECUTE format('COMMENT ON TABLE %I.experience_connections IS $c$Connections between experiences - models various types of associative connections between memories$c$', schema_name);
    EXECUTE format('COMMENT ON COLUMN %I.experience_connections.connection_type IS $c$Connection type: temporal, causal, semantic, etc.$c$', schema_name);
    EXECUTE format('COMMENT ON COLUMN %I.experience_connections.strength IS $c$Strength of associative connection on a scale of 1-10$c$', schema_name);
    EXECUTE format('COMMENT ON COLUMN %I.experience_connections.activation_count IS $c$Number of activations of this connection - reflects frequency of use$c$', schema_name);
    EXECUTE format('COMMENT ON COLUMN %I.experience_connections.direction IS $c$Connection direction: unidirectional or bidirectional$c$', schema_name);
    EXECUTE format('COMMENT ON COLUMN %I.experience_connections.conscious_status IS $c$Whether AMI is aware of this connection (TRUE) or it exists at the subconscious level (FALSE)$c$', schema_name);

    -- Creating indexes for connections between experiences
    EXECUTE format('CREATE INDEX IF NOT EXISTS experience_connections_source_idx ON %I.experience_connections(source_experience_id)', schema_name);
    EXECUTE format('CREATE INDEX IF NOT EXISTS experience_connections_target_idx ON %I.experience_connections(target_experience_id)', schema_name);
    EXECUTE format('CREATE INDEX IF NOT EXISTS experience_connections_type_idx ON %I.experience_connections(connection_type)', schema_name);
    EXECUTE format('CREATE INDEX IF NOT EXISTS experience_connections_strength_idx ON %I.experience_connections(strength)', schema_name);
    EXECUTE format('CREATE INDEX IF NOT EXISTS experience_connections_last_activated_idx ON %I.experience_connections(last_activated)', schema_name);
    EXECUTE format('CREATE INDEX IF NOT EXISTS experience_connections_activation_count_idx ON %I.experience_connections(activation_count)', schema_name);
    EXECUTE format('CREATE INDEX IF NOT EXISTS experience_connections_direction_idx ON %I.experience_connections(direction)', schema_name);
    EXECUTE format('CREATE INDEX IF NOT EXISTS experience_connections_conscious_status_idx ON %I.experience_connections(conscious_status)', schema_name);
    
    -- Uniqueness constraint to prevent duplicate associations
    EXECUTE format('CREATE UNIQUE INDEX IF NOT EXISTS experience_connections_unique_idx 
    ON %I.experience_connections(source_experience_id, target_experience_id, connection_type)', schema_name);
    
    RAISE NOTICE 'Association structures successfully created';
END;
$$;
