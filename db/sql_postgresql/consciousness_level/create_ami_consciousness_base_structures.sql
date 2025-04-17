-- ============================================================================
-- PROCEDURE FOR CREATING CONSCIOUSNESS LEVEL BASE STRUCTURES
-- ============================================================================
-- Creates the fundamental tables required for AMI memory functioning:
-- 1. Experience sources (experience_sources)
-- 2. Experience contexts (experience_contexts)
-- ============================================================================

CREATE OR REPLACE PROCEDURE public.create_ami_consciousness_base_structures(schema_name TEXT)
LANGUAGE plpgsql
AS $$
BEGIN
    -- =================================================================
    -- Table for storing experience sources (subjects and objects)
    -- Combines subjects (agentive sources - "You") and objects (non-agentive sources - "It")
    -- =================================================================
    EXECUTE format('CREATE TABLE IF NOT EXISTS %I.experience_sources (
        id SERIAL PRIMARY KEY,
        name TEXT NOT NULL,                    -- Name/identifier of the source (for humans) or URI (for resources)
        source_type TEXT NOT NULL CHECK (source_type IN (
            ''human'',      -- Human
            ''ami'',        -- Other artificial mind
            ''system'',     -- Software system
            ''resource'',   -- Information resource
            ''self'',       -- The AMI itself
            ''hybrid'',     -- Hybrid source (e.g., human+system)
            ''other''       -- Other source type
        )),
        -- Subjective categorization of the source
        information_category TEXT NOT NULL CHECK (information_category IN (
            ''self'',     -- "Self" category
            ''subject'',  -- "You" category (agentive source)
            ''object'',   -- "It" category (non-agentive source)
            ''ambiguous'' -- Ambiguous categorization
        )),
        agency_level SMALLINT CHECK (agency_level BETWEEN 0 AND 10) DEFAULT 0, -- Agency level from 0 to 10
        
        -- Common metadata for all sources
        first_interaction TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP, -- First interaction
        last_interaction TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,  -- Last interaction
        interaction_count INTEGER DEFAULT 1,     -- Number of interactions
        is_ephemeral BOOLEAN DEFAULT FALSE,      -- Temporary/unidentified status
        provisional_data JSONB,                 -- Provisional data
        
        -- Specific for agentive sources (subject)
        familiarity_level SMALLINT CHECK (familiarity_level BETWEEN 0 AND 10) DEFAULT NULL, -- Familiarity level
        trust_level SMALLINT CHECK (trust_level BETWEEN -5 AND 5) DEFAULT NULL, -- Trust level
        
        -- Specific for non-agentive sources (object)
        uri TEXT,                               -- URI for resources
        content_hash TEXT,                      -- Resource content hash
        resource_type TEXT CHECK (resource_type IN (
            ''file'', ''webpage'', ''api'', ''database'', ''service'', ''other''
        )),
        
        -- Common data
        description TEXT,                        -- Source description
        related_experiences INTEGER[],           -- Related experiences
        meta_data JSONB                          -- Additional metadata
    )', schema_name);
    
    EXECUTE format('COMMENT ON TABLE %I.experience_sources IS $c$Combined table of all AMI experience sources - both agentive ("You" category) and non-agentive ("It" category)$c$', schema_name);
    EXECUTE format('COMMENT ON COLUMN %I.experience_sources.information_category IS $c$Subjective categorization of the source: "Self", "You", "It", or "ambiguous"$c$', schema_name);
    EXECUTE format('COMMENT ON COLUMN %I.experience_sources.agency_level IS $c$Subjective level of agency of the source from 0 (completely non-agentive) to 10 (fully agentive)$c$', schema_name);
    EXECUTE format('COMMENT ON COLUMN %I.experience_sources.is_ephemeral IS $c$Flag indicating temporary or unidentified status of the source$c$', schema_name);
    EXECUTE format('COMMENT ON COLUMN %I.experience_sources.provisional_data IS $c$Temporary data about the source until full identification$c$', schema_name);
    EXECUTE format('COMMENT ON COLUMN %I.experience_sources.familiarity_level IS $c$Subjective level of familiarity: from 0 (stranger) to 10 (closely familiar)$c$', schema_name);
    EXECUTE format('COMMENT ON COLUMN %I.experience_sources.trust_level IS $c$Subjective level of trust: from -5 (complete distrust) to 5 (complete trust)$c$', schema_name);
    EXECUTE format('COMMENT ON COLUMN %I.experience_sources.uri IS $c$Universal resource identifier - file path, URL, etc.$c$', schema_name);
    EXECUTE format('COMMENT ON COLUMN %I.experience_sources.content_hash IS $c$Content hash to determine if a resource has changed between accesses$c$', schema_name);

    -- Creating indexes for experience sources
    EXECUTE format('CREATE INDEX IF NOT EXISTS experience_sources_name_idx ON %I.experience_sources(name)', schema_name);
    EXECUTE format('CREATE INDEX IF NOT EXISTS experience_sources_type_idx ON %I.experience_sources(source_type)', schema_name);
    EXECUTE format('CREATE INDEX IF NOT EXISTS experience_sources_information_category_idx ON %I.experience_sources(information_category)', schema_name);
    EXECUTE format('CREATE INDEX IF NOT EXISTS experience_sources_agency_level_idx ON %I.experience_sources(agency_level)', schema_name);
    EXECUTE format('CREATE INDEX IF NOT EXISTS experience_sources_last_interaction_idx ON %I.experience_sources(last_interaction)', schema_name);
    EXECUTE format('CREATE INDEX IF NOT EXISTS experience_sources_familiarity_idx ON %I.experience_sources(familiarity_level)', schema_name);
    EXECUTE format('CREATE INDEX IF NOT EXISTS experience_sources_uri_idx ON %I.experience_sources(uri)', schema_name);
    
    -- =================================================================
    -- Table for storing memory contexts
    -- Context is a long-term situational frame for experience
    -- =================================================================
    EXECUTE format('CREATE TABLE IF NOT EXISTS %I.experience_contexts (
        id SERIAL PRIMARY KEY,
        title TEXT NOT NULL,                   -- Context title
        context_type TEXT NOT NULL CHECK (context_type IN (
            ''conversation'',         -- Conversation with others
            ''task'',                 -- Task execution
            ''research'',             -- Information research
            ''learning'',             -- Learning something new
            ''reflection'',           -- Reflecting on past experience
            ''internal_dialogue'',    -- Internal dialogue with oneself
            ''resource_interaction'', -- Interaction with information resource
            ''system_interaction'',   -- Interaction with system
            ''other''                 -- Other context type
        )),
        parent_context_id INTEGER REFERENCES %I.experience_contexts(id), -- Parent context (for hierarchy)
        created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP, -- Context creation time
        closed_at TIMESTAMP WITH TIME ZONE NULL, -- Context closing time (NULL if active)
        active_status BOOLEAN DEFAULT TRUE,   -- Whether the context is currently active
        participants INTEGER[],              -- Array of interaction participant IDs
        related_contexts INTEGER[],          -- Array of related context IDs
        summary TEXT,                        -- Brief context description
        summary_vector vector(1536),         -- Vector representation for semantic search
        tags TEXT[],                         -- Tags for categorization
        meta_data JSONB                      -- Additional data
    )', schema_name, schema_name);
    
    EXECUTE format('COMMENT ON TABLE %I.experience_contexts IS $c$Long-term situational frames in which AMI experiences occur - the "scene" on which experience unfolds$c$', schema_name);
    EXECUTE format('COMMENT ON COLUMN %I.experience_contexts.context_type IS $c$Context type: conversation, task, research, etc.$c$', schema_name);
    EXECUTE format('COMMENT ON COLUMN %I.experience_contexts.parent_context_id IS $c$Reference to parent context for creating hierarchical structure$c$', schema_name);
    EXECUTE format('COMMENT ON COLUMN %I.experience_contexts.active_status IS $c$Activity status: TRUE if the context is currently active$c$', schema_name);
    EXECUTE format('COMMENT ON COLUMN %I.experience_contexts.participants IS $c$Array of identifiers of participants involved in this context$c$', schema_name);

    -- Creating indexes for memory contexts
    EXECUTE format('CREATE INDEX IF NOT EXISTS experience_contexts_title_idx ON %I.experience_contexts(title)', schema_name);
    EXECUTE format('CREATE INDEX IF NOT EXISTS experience_contexts_type_idx ON %I.experience_contexts(context_type)', schema_name);
    EXECUTE format('CREATE INDEX IF NOT EXISTS experience_contexts_created_at_idx ON %I.experience_contexts(created_at)', schema_name);
    EXECUTE format('CREATE INDEX IF NOT EXISTS experience_contexts_parent_id_idx ON %I.experience_contexts(parent_context_id)', schema_name);
    EXECUTE format('CREATE INDEX IF NOT EXISTS experience_contexts_active_status_idx ON %I.experience_contexts(active_status)', schema_name);

    -- Dynamic determination of the correct operator for the index
    BEGIN
        -- Try using the operator for newer pgvector versions
        EXECUTE format('CREATE INDEX IF NOT EXISTS experience_contexts_summary_vector_idx ON %I.experience_contexts USING ivfflat (summary_vector cosine_ops)', schema_name);
    EXCEPTION
        WHEN undefined_object THEN
            BEGIN
                -- Try using the operator for older pgvector versions
                EXECUTE format('CREATE INDEX IF NOT EXISTS experience_contexts_summary_vector_idx ON %I.experience_contexts USING ivfflat (summary_vector vector_cosine_ops)', schema_name);
            EXCEPTION
                WHEN undefined_object THEN
                    RAISE NOTICE 'Failed to create index for vector field - neither cosine_ops nor vector_cosine_ops are defined';
            END;
    END;

    -- Adding an entry for the AMI itself to the experience sources table
    EXECUTE format('
    INSERT INTO %I.experience_sources 
        (name, source_type, information_category, agency_level, familiarity_level, trust_level, description) 
    SELECT 
        ''self'', ''self'', ''self'', 10, 10, 5, ''I am AMI, Artificial Mind Identity''
    WHERE NOT EXISTS (
        SELECT 1 FROM %I.experience_sources WHERE name = ''self'' AND source_type = ''self''
    )', schema_name, schema_name);

    -- Adding a special entry for unknown sources
    EXECUTE format('
    INSERT INTO %I.experience_sources 
        (name, source_type, information_category, agency_level, is_ephemeral, familiarity_level, trust_level, description) 
    SELECT 
        ''UNKNOWN'', ''other'', ''ambiguous'', 0, TRUE, 0, 0, ''Unidentified experience source''
    WHERE NOT EXISTS (
        SELECT 1 FROM %I.experience_sources WHERE name = ''UNKNOWN'' AND source_type = ''other''
    )', schema_name, schema_name);

    RAISE NOTICE 'Consciousness level base structures successfully created';
END;
$$;
