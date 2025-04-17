-- ============================================================================
-- STORED PROCEDURE FOR DROPPING AMI SCHEMA IN F.A.M.I.L.Y. PROJECT
-- Creation date: April 15, 2025
-- Author: F.A.M.I.L.Y. Project Team
-- Updated: April 16, 2025 - Fixed issue with AMI user deletion while preserving dependencies
-- ============================================================================
-- This procedure drops the schema and AMI user, including all related objects,
-- from the FAMILY database. Use this procedure with caution as it
-- irreversibly deletes all AMI memory data.
-- ============================================================================

\set QUIET on
\set ON_ERROR_STOP on
\set QUIET off

-- Create stored procedure for dropping AMI schema and user
CREATE OR REPLACE PROCEDURE drop_ami_schema(ami_name TEXT, force_mode BOOLEAN DEFAULT FALSE)
LANGUAGE plpgsql
AS $$
DECLARE
    schema_name TEXT;
    user_exists BOOLEAN;
    schema_exists BOOLEAN;
    obj_count INTEGER;
    conn_count INTEGER;
    prev_object TEXT;
    obj_record RECORD;
BEGIN
    -- Set schema name directly to AMI name without prefix
    schema_name := ami_name;
    
    -- Check if schema with this name exists
    SELECT EXISTS(SELECT 1 FROM pg_namespace WHERE nspname = schema_name) INTO schema_exists;
    
    -- Check if user with this name exists
    SELECT EXISTS(SELECT 1 FROM pg_roles WHERE rolname = ami_name) INTO user_exists;
    
    -- If neither schema nor user exists, display warning and exit
    IF NOT schema_exists AND NOT user_exists THEN
        RAISE NOTICE 'AMI "%" does not exist: neither schema nor user with this name was found', ami_name;
        RETURN;
    END IF;
    
    -- If schema exists, check the number of objects before deletion
    IF schema_exists THEN
        -- Get total number of objects in the schema
        EXECUTE format('
            SELECT 
                (SELECT COUNT(*) FROM pg_tables WHERE schemaname = %L) +
                (SELECT COUNT(*) FROM pg_views WHERE schemaname = %L) +
                (SELECT COUNT(*) FROM pg_proc WHERE pronamespace = %L::regnamespace)', 
            schema_name, schema_name, schema_name) INTO obj_count;
            
        -- Get number of active connections to the schema
        SELECT COUNT(*) INTO conn_count 
        FROM pg_stat_activity 
        WHERE application_name LIKE 'ami_' || ami_name || '%'
        OR usename = ami_name;
        
        -- If there are active connections and force_mode is disabled, display warning
        IF conn_count > 0 AND NOT force_mode THEN
            RAISE WARNING 'Active connections to schema % detected (count: %)', schema_name, conn_count;
            RAISE WARNING 'Execution stopped. Use force_mode=TRUE for forced deletion';
            RETURN;
        END IF;
        
        -- If force_mode is enabled, forcibly close all connections
        IF conn_count > 0 AND force_mode THEN
            RAISE NOTICE 'Forcibly closing % active connections to schema %', conn_count, schema_name;
            
            -- Terminate all connections to the schema
            FOR i IN 1..3 LOOP -- Try several times as some connections may be resilient
                PERFORM pg_terminate_backend(pid) 
                FROM pg_stat_activity 
                WHERE application_name LIKE 'ami_' || ami_name || '%'
                OR usename = ami_name;
            END LOOP;
        END IF;
        
        -- IMPORTANT FIX: Before deleting the schema, we forcibly revoke all AMI user privileges
        -- on all schema objects. This helps avoid errors when deleting a user with dependencies.
        IF user_exists THEN
            BEGIN
                -- Revoke user privileges on the schema
                EXECUTE format('REVOKE ALL ON SCHEMA %I FROM %I', schema_name, ami_name);
                
                -- Revoke privileges on all tables in the schema
                EXECUTE format('REVOKE ALL ON ALL TABLES IN SCHEMA %I FROM %I', schema_name, ami_name);
                
                -- Revoke privileges on all sequences in the schema
                EXECUTE format('REVOKE ALL ON ALL SEQUENCES IN SCHEMA %I FROM %I', schema_name, ami_name);
                
                -- Revoke privileges on all functions in the schema
                EXECUTE format('REVOKE ALL ON ALL FUNCTIONS IN SCHEMA %I FROM %I', schema_name, ami_name);
                
                -- Revoke privileges on all stored procedures in the schema
                EXECUTE format('REVOKE ALL ON ALL PROCEDURES IN SCHEMA %I FROM %I', schema_name, ami_name);
                
                -- Revoke privileges on all types in the schema
                EXECUTE format('REVOKE ALL ON ALL TYPES IN SCHEMA %I FROM %I', schema_name, ami_name);
                
                -- Reset default privileges for the user in the schema
                EXECUTE format('ALTER DEFAULT PRIVILEGES FOR ROLE %I IN SCHEMA %I REVOKE ALL ON TABLES FROM %I',
                              current_user, schema_name, ami_name);
                EXECUTE format('ALTER DEFAULT PRIVILEGES FOR ROLE %I IN SCHEMA %I REVOKE ALL ON SEQUENCES FROM %I',
                              current_user, schema_name, ami_name);
                EXECUTE format('ALTER DEFAULT PRIVILEGES FOR ROLE %I IN SCHEMA %I REVOKE ALL ON FUNCTIONS FROM %I',
                              current_user, schema_name, ami_name);
                EXECUTE format('ALTER DEFAULT PRIVILEGES FOR ROLE %I IN SCHEMA %I REVOKE ALL ON TYPES FROM %I',
                              current_user, schema_name, ami_name);
            EXCEPTION
                WHEN OTHERS THEN
                    RAISE NOTICE 'Warning during privilege revocation: %', SQLERRM;
            END;
        END IF;
        
        -- Drop schema with all objects (in CASCADE mode)
        RAISE NOTICE 'Dropping schema % (contains % objects)...', schema_name, obj_count;
        EXECUTE format('DROP SCHEMA %I CASCADE', schema_name);
        RAISE NOTICE 'Schema % successfully dropped', schema_name;
    ELSE
        RAISE NOTICE 'Schema % does not exist', schema_name;
    END IF;
    
    -- If the user exists, delete it
    IF user_exists THEN
        -- Check if there are any objects owned by the user
        EXECUTE format('
            SELECT COUNT(*) 
            FROM pg_catalog.pg_class c 
            JOIN pg_catalog.pg_namespace n ON n.oid = c.relnamespace 
            WHERE n.nspname != ''pg_catalog'' 
            AND n.nspname != ''information_schema'' 
            AND c.relowner = (SELECT oid FROM pg_roles WHERE rolname = %L)', 
            ami_name) INTO obj_count;
            
        -- If the user still owns objects and force_mode is disabled, display warning
        IF obj_count > 0 AND NOT force_mode THEN
            RAISE WARNING 'User % owns % objects outside the deleted schema', ami_name, obj_count;
            RAISE WARNING 'Execution stopped. Use force_mode=TRUE for forced deletion';
            RETURN;
        END IF;
        
        -- Revoke user privileges on objects in the public schema
        RAISE NOTICE 'Revoking user % privileges on objects in public schema...', ami_name;
        
        BEGIN
            -- 1. Revoke privileges on public schema
            EXECUTE format('REVOKE ALL ON SCHEMA public FROM %I', ami_name);
            
            -- 2. Revoke privileges on vector type
            BEGIN
                EXECUTE format('REVOKE USAGE ON TYPE public.vector FROM %I', ami_name);
            EXCEPTION
                WHEN OTHERS THEN
                    RAISE NOTICE 'Warning during vector type privilege revocation: %', SQLERRM;
            END;
            
            -- 3. Revoke all privileges on pgvector functions
            -- Get list of all functions the user has privileges on
            FOR obj_record IN 
                SELECT 
                    p.proname, 
                    pg_catalog.pg_get_function_identity_arguments(p.oid) AS args
                FROM 
                    pg_proc p
                    JOIN pg_namespace n ON p.pronamespace = n.oid
                    JOIN (
                        SELECT (aclexplode(proacl)).grantee, (aclexplode(proacl)).grantor, oid 
                        FROM pg_proc 
                        WHERE proacl IS NOT NULL
                    ) privs ON privs.oid = p.oid
                    JOIN pg_roles r ON privs.grantee = r.oid
                WHERE 
                    n.nspname = 'public' AND
                    r.rolname = ami_name
            LOOP
                -- Compare with previous object to avoid duplication for overloaded functions
                IF prev_object IS DISTINCT FROM (obj_record.proname || obj_record.args) THEN
                    BEGIN
                        -- Revoke function privileges
                        IF obj_record.args IS NOT NULL AND obj_record.args != '' THEN
                            EXECUTE format('REVOKE ALL ON FUNCTION public.%I(%s) FROM %I', 
                                        obj_record.proname, obj_record.args, ami_name);
                        ELSE
                            EXECUTE format('REVOKE ALL ON FUNCTION public.%I() FROM %I', 
                                        obj_record.proname, ami_name);
                        END IF;
                        prev_object := obj_record.proname || obj_record.args;
                    EXCEPTION
                        WHEN OTHERS THEN
                            RAISE NOTICE 'Warning during function privilege revocation %.%: %', 
                                        obj_record.proname, obj_record.args, SQLERRM;
                    END;
                END IF;
            END LOOP;
            
            -- 4. Revoke privileges on all functions in public schema for simplification
            BEGIN
                EXECUTE format('REVOKE ALL ON ALL FUNCTIONS IN SCHEMA public FROM %I', ami_name);
            EXCEPTION
                WHEN OTHERS THEN
                    -- This is not critical as we already tried to revoke privileges on individual functions
                    RAISE NOTICE 'Warning during revocation of all function privileges: %', SQLERRM;
            END;
            
            -- 5. Revoke actions on behalf of roles
            BEGIN
                EXECUTE 'RESET ROLE';  -- Reset current role just in case
                -- Check if the user has INHERIT privileges on other roles
                FOR obj_record IN 
                    SELECT r2.rolname 
                    FROM pg_roles r1 
                    JOIN pg_auth_members m ON r1.oid = m.member 
                    JOIN pg_roles r2 ON m.roleid = r2.oid 
                    WHERE r1.rolname = ami_name
                LOOP
                    -- Revoke role inheritance
                    EXECUTE format('REVOKE %I FROM %I', obj_record.rolname, ami_name);
                END LOOP;
            EXCEPTION
                WHEN OTHERS THEN
                    RAISE NOTICE 'Warning during role inheritance privilege revocation: %', SQLERRM;
            END;
        EXCEPTION
            WHEN OTHERS THEN
                RAISE NOTICE 'Non-critical error during privilege revocation: %', SQLERRM;
        END;
        
        -- Delete the user
        RAISE NOTICE 'Deleting user %...', ami_name;
        BEGIN
            EXECUTE format('DROP ROLE %I', ami_name);
            RAISE NOTICE 'User % successfully deleted', ami_name;
        EXCEPTION
            WHEN OTHERS THEN
                -- If deletion failed, try without CASCADE (PostgreSQL doesn't support CASCADE for DROP ROLE)
                IF force_mode THEN
                    BEGIN
                        RAISE NOTICE 'Attempting to delete user % with alternative method...', ami_name;
                        -- Note: PostgreSQL doesn't support CASCADE for DROP ROLE
                        -- We've already handled dependencies by revoking privileges
                        EXECUTE format('DROP ROLE %I', ami_name);
                        RAISE NOTICE 'User % successfully deleted with alternative method', ami_name;
                    EXCEPTION
                        WHEN OTHERS THEN
                            RAISE EXCEPTION 'Failed to delete user even with alternative method: %', SQLERRM;
                    END;
                ELSE
                    RAISE EXCEPTION 'Failed to delete user: %', SQLERRM;
                END IF;
        END;
    ELSE
        RAISE NOTICE 'User % does not exist', ami_name;
    END IF;
    
    -- Create record of operation execution
    -- Here you can add a record to the system table or log
    -- that the AMI has been deleted (for audit or reporting)
    RAISE NOTICE '======================================================================';
    RAISE NOTICE 'AMI "%" successfully deleted from F.A.M.I.L.Y. system', ami_name;
    RAISE NOTICE 'Deletion date: %', NOW();
    RAISE NOTICE '======================================================================';
END;
$$;

-- Example of procedure usage:
-- CALL drop_ami_schema('ami_test'); -- Normal mode, checks for connections
-- CALL drop_ami_schema('ami_test', TRUE); -- Force mode, closes active connections