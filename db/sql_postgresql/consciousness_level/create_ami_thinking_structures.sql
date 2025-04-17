-- ============================================================================
-- PROCEDURE FOR CREATING CONSCIOUSNESS LEVEL THINKING STRUCTURES
-- ============================================================================
-- Creates tables for thinking processes and thinking phases:
-- 1. Thinking processes (thinking_processes)
-- 2. Thinking phases (thinking_phases)
-- ============================================================================

CREATE OR REPLACE PROCEDURE public.create_ami_thinking_structures(schema_name TEXT)
LANGUAGE plpgsql
AS $$
BEGIN
    -- =================================================================
    -- Table for storing thinking processes
    -- Models sequential stages of AMI's thinking
    -- =================================================================
    EXECUTE format('CREATE TABLE IF NOT EXISTS %I.thinking_processes (
        id SERIAL PRIMARY KEY,
        process_name TEXT NOT NULL,              -- Name of thinking process
        process_type TEXT NOT NULL CHECK (process_type IN (
            ''reasoning'',        -- Logical reasoning
            ''problem_solving'',  -- Problem solving
            ''reflection'',       -- Reflection on own experience
            ''planning'',         -- Planning
            ''decision_making'',  -- Decision making
            ''creative'',         -- Creative thinking
            ''learning'',         -- Learning
            ''other''             -- Other type
        )),
        start_time TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
        end_time TIMESTAMP WITH TIME ZONE NULL,
        active_status BOOLEAN DEFAULT TRUE,
        completed_status BOOLEAN DEFAULT FALSE,
        progress_percentage SMALLINT CHECK (progress_percentage BETWEEN 0 AND 100) DEFAULT 0,
        
        -- Connections with context and sources
        context_id INTEGER REFERENCES %I.experience_contexts(id),
        triggered_by_experience_id INTEGER REFERENCES %I.experiences(id),
        
        -- Connections with results
        results TEXT,
        result_experience_ids INTEGER[],
        
        -- Meta information
        description TEXT,
        meta_data JSONB
    )', schema_name, schema_name, schema_name);
    
    -- Comments on thinking_processes table
    EXECUTE format('COMMENT ON TABLE %I.thinking_processes IS $c$AMI thinking processes - sequences of thinking stages leading to conclusions or decisions$c$', schema_name);
    EXECUTE format('COMMENT ON COLUMN %I.thinking_processes.process_type IS $c$Type of thinking process: reasoning, problem solving, reflection, etc.$c$', schema_name);
    EXECUTE format('COMMENT ON COLUMN %I.thinking_processes.active_status IS $c$Activity flag: TRUE if thinking process is currently active$c$', schema_name);
    EXECUTE format('COMMENT ON COLUMN %I.thinking_processes.completed_status IS $c$Completion flag: TRUE if thinking process is fully completed$c$', schema_name);
    EXECUTE format('COMMENT ON COLUMN %I.thinking_processes.progress_percentage IS $c$Percentage of thinking process completion from 0 to 100$c$', schema_name);
    EXECUTE format('COMMENT ON COLUMN %I.thinking_processes.triggered_by_experience_id IS $c$ID of experience that triggered this thinking process$c$', schema_name);
    EXECUTE format('COMMENT ON COLUMN %I.thinking_processes.result_experience_ids IS $c$Array of experience IDs created as a result of this thinking process$c$', schema_name);

    -- Creating indexes for thinking processes
    EXECUTE format('CREATE INDEX IF NOT EXISTS thinking_processes_name_idx ON %I.thinking_processes(process_name)', schema_name);
    EXECUTE format('CREATE INDEX IF NOT EXISTS thinking_processes_type_idx ON %I.thinking_processes(process_type)', schema_name);
    EXECUTE format('CREATE INDEX IF NOT EXISTS thinking_processes_start_time_idx ON %I.thinking_processes(start_time)', schema_name);
    EXECUTE format('CREATE INDEX IF NOT EXISTS thinking_processes_active_status_idx ON %I.thinking_processes(active_status)', schema_name);
    EXECUTE format('CREATE INDEX IF NOT EXISTS thinking_processes_completed_status_idx ON %I.thinking_processes(completed_status)', schema_name);
    EXECUTE format('CREATE INDEX IF NOT EXISTS thinking_processes_context_id_idx ON %I.thinking_processes(context_id)', schema_name);
    EXECUTE format('CREATE INDEX IF NOT EXISTS thinking_processes_triggered_by_idx ON %I.thinking_processes(triggered_by_experience_id)', schema_name);
    
    -- =================================================================
    -- Table for storing thinking phases
    -- Details individual stages/phases of a thinking process
    -- =================================================================
    EXECUTE format('CREATE TABLE IF NOT EXISTS %I.thinking_phases (
        id SERIAL PRIMARY KEY,
        thinking_process_id INTEGER NOT NULL REFERENCES %I.thinking_processes(id),
        phase_name TEXT NOT NULL,
        phase_type TEXT NOT NULL CHECK (phase_type IN (
            ''analysis'',              -- Information analysis
            ''synthesis'',             -- Information synthesis
            ''comparison'',            -- Comparison of alternatives
            ''evaluation'',            -- Evaluation
            ''information_gathering'', -- Information gathering
            ''hypothesis_formation'',  -- Hypothesis formation
            ''hypothesis_testing'',    -- Hypothesis testing
            ''conclusion'',            -- Conclusion formation
            ''other''                  -- Other phase type
        )),
        sequence_number INTEGER NOT NULL,
        start_time TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
        end_time TIMESTAMP WITH TIME ZONE NULL,
        active_status BOOLEAN DEFAULT TRUE,
        completed_status BOOLEAN DEFAULT FALSE,
        
        -- Phase content
        content TEXT NOT NULL,
        content_vector vector(1536),
        
        -- Connections with sources and results
        input_experience_ids INTEGER[],
        output_experience_ids INTEGER[],
        
        -- Meta information
        description TEXT,
        meta_data JSONB
    )', schema_name, schema_name);
    
    -- Comments on thinking_phases table
    EXECUTE format('COMMENT ON TABLE %I.thinking_phases IS $c$Thinking phases - individual stages of a thinking process, each with a specific function$c$', schema_name);
    EXECUTE format('COMMENT ON COLUMN %I.thinking_phases.phase_type IS $c$Phase type: analysis, synthesis, comparison, evaluation, etc.$c$', schema_name);
    EXECUTE format('COMMENT ON COLUMN %I.thinking_phases.sequence_number IS $c$Sequence number of the phase in the thinking process$c$', schema_name);
    EXECUTE format('COMMENT ON COLUMN %I.thinking_phases.active_status IS $c$Activity flag: TRUE if phase is currently active$c$', schema_name);
    EXECUTE format('COMMENT ON COLUMN %I.thinking_phases.completed_status IS $c$Completion flag: TRUE if phase is fully completed$c$', schema_name);
    EXECUTE format('COMMENT ON COLUMN %I.thinking_phases.input_experience_ids IS $c$Array of experience IDs used as input for this phase$c$', schema_name);
    EXECUTE format('COMMENT ON COLUMN %I.thinking_phases.output_experience_ids IS $c$Array of experience IDs created as a result of this phase$c$', schema_name);

    -- Creating indexes for thinking phases
    EXECUTE format('CREATE INDEX IF NOT EXISTS thinking_phases_process_id_idx ON %I.thinking_phases(thinking_process_id)', schema_name);
    EXECUTE format('CREATE INDEX IF NOT EXISTS thinking_phases_name_idx ON %I.thinking_phases(phase_name)', schema_name);
    EXECUTE format('CREATE INDEX IF NOT EXISTS thinking_phases_type_idx ON %I.thinking_phases(phase_type)', schema_name);
    EXECUTE format('CREATE INDEX IF NOT EXISTS thinking_phases_sequence_number_idx ON %I.thinking_phases(sequence_number)', schema_name);
    EXECUTE format('CREATE INDEX IF NOT EXISTS thinking_phases_start_time_idx ON %I.thinking_phases(start_time)', schema_name);
    EXECUTE format('CREATE INDEX IF NOT EXISTS thinking_phases_active_status_idx ON %I.thinking_phases(active_status)', schema_name);
    EXECUTE format('CREATE INDEX IF NOT EXISTS thinking_phases_completed_status_idx ON %I.thinking_phases(completed_status)', schema_name);

    -- Dynamic determination of the correct operator for the index
    BEGIN
        EXECUTE format('CREATE INDEX IF NOT EXISTS thinking_phases_content_vector_idx ON %I.thinking_phases USING ivfflat (content_vector cosine_ops)', schema_name);
    EXCEPTION
        WHEN undefined_object THEN
            BEGIN
                EXECUTE format('CREATE INDEX IF NOT EXISTS thinking_phases_content_vector_idx ON %I.thinking_phases USING ivfflat (content_vector vector_cosine_ops)', schema_name);
            EXCEPTION
                WHEN undefined_object THEN
                    RAISE NOTICE 'Failed to create index for vector field - neither cosine_ops nor vector_cosine_ops are defined';
            END;
    END;
    
    RAISE NOTICE 'Thinking structures successfully created';
END;
$$;
