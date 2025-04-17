-- ============================================================================
-- PROCEDURE FOR CREATING CONSCIOUSNESS LEVEL EXPERIENCE STRUCTURE
-- ============================================================================
-- Creates the central experiences table and auxiliary attributes table:
-- 1. Experiences (experiences)
-- 2. Experience attributes (experience_attributes)
-- ============================================================================

CREATE OR REPLACE PROCEDURE public.create_ami_experience_structure(schema_name TEXT)
LANGUAGE plpgsql
AS $$
BEGIN
    -- =================================================================
    -- Table for storing main memories (experiences)
    -- Central table of AMI's consciousness level memory
    -- =================================================================
    EXECUTE format('CREATE TABLE IF NOT EXISTS %I.experiences (
        id SERIAL PRIMARY KEY,
        timestamp TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
        
        -- Experience categorization (required fields)
        information_category TEXT NOT NULL CHECK (information_category IN (
            ''self'',    -- "Self" category (information from self)
            ''subject'', -- "You" category (information from agentive source)
            ''object''   -- "It" category (information from non-agentive source)
        )),
        
        -- Basic division of experience by type (what is it?)
        experience_type TEXT NOT NULL CHECK (experience_type IN (
            ''perception'',       -- Perception (incoming information)
            ''thought'',          -- Thought
            ''action'',           -- AMI action
            ''communication'',    -- Communication (incoming or outgoing)
            ''decision'',         -- Decision making
            ''memory_recall'',    -- Memory recall
            ''insight''           -- Insight/revelation
        )),
        
        -- Subjective position of AMI in the experience
        subjective_position TEXT NOT NULL CHECK (subjective_position IN (
            ''addressee'',      -- AMI as addressee
            ''addresser'',      -- AMI as addresser
            ''observer'',       -- AMI as observer
            ''reflective''      -- AMI in reflective mode
        )),
        
        -- Communication direction
        communication_direction TEXT CHECK (communication_direction IN (
            ''incoming'',     -- Incoming communication
            ''outgoing''      -- Outgoing communication
        )),
        
        -- Context
        context_id INTEGER REFERENCES %I.experience_contexts(id),
        provisional_context TEXT,
        
        -- Connections with experience sources
        source_id INTEGER REFERENCES %I.experience_sources(id),
        provisional_source TEXT,
        target_id INTEGER REFERENCES %I.experience_sources(id),
        
        -- Main content
        content TEXT NOT NULL,
        content_vector vector(1536),
        
        -- Basic experience attributes
        salience SMALLINT CHECK (salience BETWEEN 1 AND 10) DEFAULT 5,
        provenance_type TEXT NOT NULL CHECK (provenance_type IN (
            ''identified'',      -- Fully identified experience
            ''provisional'',     -- Experience with provisional data
            ''system_generated'' -- System-generated experience
        )) DEFAULT ''identified'',
        verified_status BOOLEAN DEFAULT FALSE,
        
        -- Connections with other experiences
        parent_experience_id INTEGER REFERENCES %I.experiences(id),
        response_to_experience_id INTEGER REFERENCES %I.experiences(id),
        thinking_process_id INTEGER,
        
        -- Connection with subconscious level
        emotional_evaluation_id INTEGER,
        
        -- Metadata
        meta_data JSONB
    )', schema_name, schema_name, schema_name, schema_name, schema_name, schema_name);
    
    -- Comments on experience table
    EXECUTE format('COMMENT ON TABLE %I.experiences IS $c$Central table of AMI experiences - all informational events that leave a trace in consciousness$c$', schema_name);
    EXECUTE format('COMMENT ON COLUMN %I.experiences.information_category IS $c$Subjective category of information source: Self (self), You (subject), It (object)$c$', schema_name);
    EXECUTE format('COMMENT ON COLUMN %I.experiences.experience_type IS $c$Experience type: perception, thought, action, etc.$c$', schema_name);
    EXECUTE format('COMMENT ON COLUMN %I.experiences.subjective_position IS $c$Subjective position of AMI in the experience: addressee, addresser, observer, or reflective$c$', schema_name);
    EXECUTE format('COMMENT ON COLUMN %I.experiences.communication_direction IS $c$Communication direction: incoming or outgoing (for communication type)$c$', schema_name);
    EXECUTE format('COMMENT ON COLUMN %I.experiences.provenance_type IS $c$Experience origin type: identified, provisional, system-generated$c$', schema_name);
    EXECUTE format('COMMENT ON COLUMN %I.experiences.provisional_context IS $c$Textual description of context when a full record in experience_contexts table has not yet been created$c$', schema_name);
    EXECUTE format('COMMENT ON COLUMN %I.experiences.provisional_source IS $c$Textual description of source when a full record in experience_sources table has not yet been created$c$', schema_name);
    EXECUTE format('COMMENT ON COLUMN %I.experiences.salience IS $c$Subjective significance of experience on a scale of 1-10$c$', schema_name);
    EXECUTE format('COMMENT ON COLUMN %I.experiences.parent_experience_id IS $c$Reference to parent experience (for hierarchy)$c$', schema_name);
    EXECUTE format('COMMENT ON COLUMN %I.experiences.response_to_experience_id IS $c$Reference to experience this is a response to$c$', schema_name);
    EXECUTE format('COMMENT ON COLUMN %I.experiences.thinking_process_id IS $c$Reference to thinking process that led to this experience$c$', schema_name);
    EXECUTE format('COMMENT ON COLUMN %I.experiences.emotional_evaluation_id IS $c$Reference to emotional evaluation of experience from subconscious level$c$', schema_name);

    -- Creating indexes for memories
    EXECUTE format('CREATE INDEX IF NOT EXISTS experiences_timestamp_idx ON %I.experiences(timestamp)', schema_name);
    EXECUTE format('CREATE INDEX IF NOT EXISTS experiences_context_id_idx ON %I.experiences(context_id)', schema_name);
    EXECUTE format('CREATE INDEX IF NOT EXISTS experiences_information_category_idx ON %I.experiences(information_category)', schema_name);
    EXECUTE format('CREATE INDEX IF NOT EXISTS experiences_experience_type_idx ON %I.experiences(experience_type)', schema_name);
    EXECUTE format('CREATE INDEX IF NOT EXISTS experiences_subjective_position_idx ON %I.experiences(subjective_position)', schema_name);
    EXECUTE format('CREATE INDEX IF NOT EXISTS experiences_source_id_idx ON %I.experiences(source_id)', schema_name);
    EXECUTE format('CREATE INDEX IF NOT EXISTS experiences_target_id_idx ON %I.experiences(target_id)', schema_name);
    EXECUTE format('CREATE INDEX IF NOT EXISTS experiences_salience_idx ON %I.experiences(salience)', schema_name);
    EXECUTE format('CREATE INDEX IF NOT EXISTS experiences_parent_experience_idx ON %I.experiences(parent_experience_id)', schema_name);
    EXECUTE format('CREATE INDEX IF NOT EXISTS experiences_response_to_idx ON %I.experiences(response_to_experience_id)', schema_name);
    EXECUTE format('CREATE INDEX IF NOT EXISTS experiences_thinking_process_idx ON %I.experiences(thinking_process_id)', schema_name);

    -- Dynamic determination of the correct operator for the index
    BEGIN
        -- Try using the operator for newer pgvector versions
        EXECUTE format('CREATE INDEX IF NOT EXISTS experiences_content_vector_idx ON %I.experiences USING ivfflat (content_vector cosine_ops)', schema_name);
    EXCEPTION
        WHEN undefined_object THEN
            BEGIN
                -- Try using the operator for older pgvector versions
                EXECUTE format('CREATE INDEX IF NOT EXISTS experiences_content_vector_idx ON %I.experiences USING ivfflat (content_vector vector_cosine_ops)', schema_name);
            EXCEPTION
                WHEN undefined_object THEN
                    RAISE NOTICE 'Failed to create index for vector field - neither cosine_ops nor vector_cosine_ops are defined';
            END;
    END;
    
    -- =================================================================
    -- Table for storing extended experience attributes (EAV model)
    -- Allows adding arbitrary attributes to any experience
    -- =================================================================
    EXECUTE format('CREATE TABLE IF NOT EXISTS %I.experience_attributes (
        id SERIAL PRIMARY KEY,
        experience_id INTEGER NOT NULL REFERENCES %I.experiences(id),
        attribute_name TEXT NOT NULL,
        attribute_value TEXT NOT NULL,
        attribute_type TEXT CHECK (attribute_type IN (
            ''string'', ''number'', ''boolean'', ''datetime'', ''json'', ''other''
        )) DEFAULT ''string'',
        meta_data JSONB
    )', schema_name, schema_name);
    
    -- Comments on experience_attributes table
    EXECUTE format('COMMENT ON TABLE %I.experience_attributes IS $c$Extended experience attributes - allows adding arbitrary data to experience without changing the main schema$c$', schema_name);
    EXECUTE format('COMMENT ON COLUMN %I.experience_attributes.attribute_name IS $c$Attribute name - should be meaningful for the given experience type$c$', schema_name);
    EXECUTE format('COMMENT ON COLUMN %I.experience_attributes.attribute_value IS $c$Attribute value in text representation$c$', schema_name);
    EXECUTE format('COMMENT ON COLUMN %I.experience_attributes.attribute_type IS $c$Attribute data type for correct interpretation of the value$c$', schema_name);
    
    -- Creating indexes for attributes
    EXECUTE format('CREATE INDEX IF NOT EXISTS experience_attributes_experience_id_idx ON %I.experience_attributes(experience_id)', schema_name);
    EXECUTE format('CREATE INDEX IF NOT EXISTS experience_attributes_name_idx ON %I.experience_attributes(attribute_name)', schema_name);
    EXECUTE format('CREATE INDEX IF NOT EXISTS experience_attributes_name_value_idx ON %I.experience_attributes(attribute_name, attribute_value)', schema_name);
    
    RAISE NOTICE 'Experience structures successfully created';
END;
$$;
