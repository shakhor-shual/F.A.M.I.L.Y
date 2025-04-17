-- ============================================================================
-- CONSCIOUSNESS LEVEL INITIALIZATION PROCEDURES FOR F.A.M.I.L.Y. PROJECT
-- Creation date: April 16, 2025
-- Author: F.A.M.I.L.Y. Project Team
-- ============================================================================
-- This script contains procedures for creating and initializing components
-- of the AMI consciousness level. The division into procedures provides modularity 
-- and flexibility when deploying and updating the database structure.
-- ============================================================================

-- Main procedure for consciousness level initialization
-- Takes parameters for AMI user creation and permission setup
CREATE OR REPLACE PROCEDURE public.init_ami_consciousness_level(
    ami_name TEXT, 
    ami_password TEXT DEFAULT NULL,
    schema_name TEXT DEFAULT NULL,
    grant_permissions BOOLEAN DEFAULT TRUE
)
LANGUAGE plpgsql
AS $$
DECLARE
    v_schema_name TEXT;
    procedure_exists BOOLEAN;
    user_exists BOOLEAN;
    schema_exists BOOLEAN;
    sql_command TEXT;
BEGIN
    -- Define schema name if not specified
    v_schema_name := COALESCE(schema_name, ami_name);

    -- Create vector extension if it doesn't exist
    CREATE EXTENSION IF NOT EXISTS vector;

    -- Check if schema exists
    SELECT EXISTS (
        SELECT FROM pg_namespace WHERE nspname = v_schema_name
    ) INTO schema_exists;
    
    -- If schema doesn't exist, create it
    IF NOT schema_exists THEN
        sql_command := 'CREATE SCHEMA ' || quote_ident(v_schema_name);
        EXECUTE sql_command;
        RAISE NOTICE 'Schema % successfully created', v_schema_name;
    ELSE
        RAISE NOTICE 'Schema % already exists', v_schema_name;
    END IF;

    -- Check if AMI user exists
    SELECT EXISTS (
        SELECT FROM pg_catalog.pg_roles WHERE rolname = ami_name
    ) INTO user_exists;
    
    -- If user doesn't exist and password is specified, create user
    IF NOT user_exists AND ami_password IS NOT NULL THEN
        sql_command := 'CREATE USER ' || quote_ident(ami_name) || ' WITH PASSWORD ' || quote_literal(ami_password);
        EXECUTE sql_command;
        RAISE NOTICE 'User % successfully created', ami_name;
    ELSIF NOT user_exists AND ami_password IS NULL THEN
        RAISE WARNING 'User % does not exist, and password is not specified. User not created', ami_name;
    ELSE
        RAISE NOTICE 'User % already exists', ami_name;
    END IF;
    
    -- Call procedure to create base structures from public schema
    IF EXISTS (
        SELECT FROM pg_catalog.pg_proc p
        JOIN pg_catalog.pg_namespace n ON p.pronamespace = n.oid
        WHERE n.nspname = 'public' AND p.proname = 'create_ami_consciousness_base_structures'
    ) THEN
        EXECUTE format('CALL public.create_ami_consciousness_base_structures(%L)', v_schema_name);
        RAISE NOTICE 'Base consciousness level structures successfully created';
    ELSE
        RAISE WARNING 'Procedure create_ami_consciousness_base_structures not found in public schema. Base structures not created';
    END IF;

    -- Call procedure to create experience structure from public schema
    IF EXISTS (
        SELECT FROM pg_catalog.pg_proc p
        JOIN pg_catalog.pg_namespace n ON p.pronamespace = n.oid
        WHERE n.nspname = 'public' AND p.proname = 'create_ami_experience_structure'
    ) THEN
        EXECUTE format('CALL public.create_ami_experience_structure(%L)', v_schema_name);
        RAISE NOTICE 'Experience structures successfully created';
    ELSE
        RAISE WARNING 'Procedure create_ami_experience_structure not found in public schema. Experience structures not created';
    END IF;

    -- Call procedure to create thinking structures from public schema
    IF EXISTS (
        SELECT FROM pg_catalog.pg_proc p
        JOIN pg_catalog.pg_namespace n ON p.pronamespace = n.oid
        WHERE n.nspname = 'public' AND p.proname = 'create_ami_thinking_structures'
    ) THEN
        EXECUTE format('CALL public.create_ami_thinking_structures(%L)', v_schema_name);
        RAISE NOTICE 'Thinking structures successfully created';
    ELSE
        RAISE WARNING 'Procedure create_ami_thinking_structures not found in public schema. Thinking structures not created';
    END IF;

    -- Call procedure to create association structures from public schema
    IF EXISTS (
        SELECT FROM pg_catalog.pg_proc p
        JOIN pg_catalog.pg_namespace n ON p.pronamespace = n.oid
        WHERE n.nspname = 'public' AND p.proname = 'create_ami_association_structures'
    ) THEN
        EXECUTE format('CALL public.create_ami_association_structures(%L)', v_schema_name);
        RAISE NOTICE 'Association structures successfully created';
    ELSE
        RAISE WARNING 'Procedure create_ami_association_structures not found in public schema. Association structures not created';
    END IF;

    -- Call procedure to create views from public schema
    IF EXISTS (
        SELECT FROM pg_catalog.pg_proc p
        JOIN pg_catalog.pg_namespace n ON p.pronamespace = n.oid
        WHERE n.nspname = 'public' AND p.proname = 'create_ami_consciousness_views'
    ) THEN
        EXECUTE format('CALL public.create_ami_consciousness_views(%L)', v_schema_name);
        RAISE NOTICE 'Consciousness level views successfully created';
    ELSE
        RAISE WARNING 'Procedure create_ami_consciousness_views not found in public schema. Views not created';
    END IF;
    
    -- If permissions need to be granted to AMI user
    IF grant_permissions AND EXISTS (SELECT FROM pg_catalog.pg_roles WHERE rolname = ami_name) THEN
        -- Grant user schema usage rights
        sql_command := 'GRANT USAGE ON SCHEMA ' || quote_ident(v_schema_name) || ' TO ' || quote_ident(ami_name);
        EXECUTE sql_command;
        
        -- Grant rights to all existing tables in the schema
        sql_command := 'GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA ' || quote_ident(v_schema_name) || ' TO ' || quote_ident(ami_name);
        EXECUTE sql_command;
        
        -- Grant rights to all sequences in the schema
        sql_command := 'GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA ' || quote_ident(v_schema_name) || ' TO ' || quote_ident(ami_name);
        EXECUTE sql_command;
        
        -- Set default privileges for new objects
        sql_command := 'ALTER DEFAULT PRIVILEGES IN SCHEMA ' || quote_ident(v_schema_name) || 
                      ' GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO ' || quote_ident(ami_name);
        EXECUTE sql_command;
        
        sql_command := 'ALTER DEFAULT PRIVILEGES IN SCHEMA ' || quote_ident(v_schema_name) || 
                      ' GRANT USAGE, SELECT ON SEQUENCES TO ' || quote_ident(ami_name);
        EXECUTE sql_command;
        
        RAISE NOTICE 'Permissions for user % successfully configured', ami_name;
    ELSIF grant_permissions THEN
        RAISE WARNING 'User % does not exist, permissions not configured', ami_name;
    END IF;
    
    RAISE NOTICE 'AMI consciousness level initialization completed';
END;
$$;

-- Add comment to the procedure
COMMENT ON PROCEDURE public.init_ami_consciousness_level(TEXT, TEXT, TEXT, BOOLEAN) IS 
'AMI consciousness level initialization procedure.
Creates schema and AMI user, then calls all necessary procedures
to create consciousness level data structures.

Parameters:
- ami_name: AMI user name
- ami_password: AMI user password (optional)
- schema_name: schema name (defaults to ami_name)
- grant_permissions: whether to grant access permissions (defaults to true)';
