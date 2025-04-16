#!/bin/bash

# ============================================================================
# F.A.M.I.L.Y. DATABASE INITIALIZATION SCRIPT WITH MULTI-ENGINE SUPPORT
# Created: April 12, 2025
# Updated: April 16, 2025 - Added multi-engine support and modular structure
# ============================================================================

# Colors for information output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Output with highlighting and symbols
function echo_info() { echo -e "${BLUE}ℹ️ $1${NC}"; }
function echo_success() { echo -e "${GREEN}✅ $1${NC}"; }
function echo_warn() { echo -e "${YELLOW}⚠️ $1${NC}"; }
function echo_error() { echo -e "${RED}❌ $1${NC}"; }

# Display script usage information
function print_usage {
    echo "Usage: $0 [options]"
    echo "Options:"
    echo "  -c, --config [path]          Configuration file path (default: ./family_db.conf)"
    echo "  -f, --family-pass [password] Password for family_admin user (overrides config value)"
    echo "  -d, --db-host [host]         Database host (overrides config value)"
    echo "  -p, --db-port [port]         Database port (overrides config value)"
    echo "  -D, --drop                   Drop existing database (without creating a new one)"
    echo "  -R, --recreate               Recreate database (drop and create new)"
    echo "  --help                       Show this help message"
    echo ""
    echo "Example: $0 -c /path/to/family_db.conf -f your_secret_password"
    echo ""
}

# Parse command line parameters
CONFIG_FILE="$(dirname "$0")/family_db.conf"
FAMILY_ADMIN_PASS_CMD=""  # To store password from command line
DB_HOST=""
DB_PORT=""
DROP_DATABASE=false
RECREATE_DATABASE=false

while [[ $# -gt 0 ]]; do
    key="$1"
    case $key in
        -c|--config)
        CONFIG_FILE="$2"
        shift 2
        ;;
        -f|--family-pass)
        FAMILY_ADMIN_PASS_CMD="$2"  # Save password from command line
        shift 2
        ;;
        -d|--db-host)
        DB_HOST="$2"
        shift 2
        ;;
        -p|--db-port)
        DB_PORT="$2"
        shift 2
        ;;
        -D|--drop)
        DROP_DATABASE=true
        shift
        ;;
        -R|--recreate)
        RECREATE_DATABASE=true
        shift
        ;;
        --help)
        print_usage
        exit 0
        ;;
        *)
        echo_error "Unknown option: $1"
        print_usage
        exit 1
        ;;
    esac
done

# Check if configuration file exists
if [ ! -f "$CONFIG_FILE" ]; then
    echo_error "Configuration file not found: $CONFIG_FILE"
    exit 1
fi

# Load basic parameters from configuration file
echo_info "Loading parameters from configuration file: $CONFIG_FILE"
source "$CONFIG_FILE"

# Remove quotes from password in configuration file if present
if [[ "$FAMILY_ADMIN_PASS" == \"*\" ]]; then
    FAMILY_ADMIN_PASS="${FAMILY_ADMIN_PASS//\"/}"
    echo_info "Removed surrounding quotes from password in configuration file"
fi

# Save password from config in case it's not specified in command line
CONFIG_ADMIN_PASS="$FAMILY_ADMIN_PASS"

# Apply command line parameters if specified (override)
if [ ! -z "$FAMILY_ADMIN_PASS_CMD" ]; then
    echo_info "Using password specified in command line parameters"
    # Remove quotes from password if present
    if [[ "$FAMILY_ADMIN_PASS_CMD" == \"*\" ]]; then
        FAMILY_ADMIN_PASS_CMD="${FAMILY_ADMIN_PASS_CMD//\"/}"
    fi
    FAMILY_ADMIN_PASS="$FAMILY_ADMIN_PASS_CMD"
else
    # FAMILY_ADMIN_PASS is already set from configuration file
    # and cleaned from quotes above
    FAMILY_ADMIN_PASS="$CONFIG_ADMIN_PASS"
fi

if [ ! -z "$DB_HOST" ]; then
    echo_info "Using database host specified in command line parameters"
else
    DB_HOST="$FAMILY_DB_HOST"
fi

if [ ! -z "$DB_PORT" ]; then
    echo_info "Using database port specified in command line parameters"
else
    DB_PORT="$FAMILY_DB_PORT"
fi

# Determine database engine
DB_ENGINE="${FAMILY_DB_ENGINE}"
if [ -z "$DB_ENGINE" ]; then
    echo_error "Database engine not specified (FAMILY_DB_ENGINE) in configuration file"
    exit 1
fi

# Define directory with SQL scripts for selected engine
case "$DB_ENGINE" in
    postgresql)
        SQL_SCRIPTS_DIR="$(dirname "$0")/sql_postgresql"
        # Debug PostgreSQL connection
        echo_info "Testing PostgreSQL connection..."
        echo_info "User: $FAMILY_ADMIN_USER"
        echo_info "Password: [hidden for security]"
        echo_info "Host: $DB_HOST"
        echo_info "Port: $DB_PORT"
        
        # Test connection to postgres database (system database)
        echo_info "Testing connection to postgres system database:"
        PGPASSWORD="$FAMILY_ADMIN_PASS" psql -h "$DB_HOST" -p "$DB_PORT" -U "$FAMILY_ADMIN_USER" -d "postgres" -c "SELECT 1 AS connection_test;" || {
            echo_error "Failed to connect to postgres system database. Check credentials."
            exit 1
        }
        ;;
    sqlite)
        SQL_SCRIPTS_DIR="$(dirname "$0")/sql_sqlite"
        ;;
    *)
        echo_error "Unsupported database engine: $DB_ENGINE"
        echo_info "Supported engines: postgresql, sqlite"
        exit 1
        ;;
esac

# Check if directory with SQL scripts exists
if [ ! -d "$SQL_SCRIPTS_DIR" ]; then
    echo_error "SQL scripts directory not found: $SQL_SCRIPTS_DIR"
    exit 1
fi

# Function to drop existing database
function drop_database {
    local create_new=$1  # Flag indicating whether to create a new database after deletion
    
    echo_warn "Starting to delete existing database '$FAMILY_DB_NAME'..."
    
    case "$DB_ENGINE" in
        postgresql)
            # Check if database exists
            if PGPASSWORD="$FAMILY_ADMIN_PASS" psql -h "$DB_HOST" -p "$DB_PORT" -U "$FAMILY_ADMIN_USER" -lqt | cut -d \| -f 1 | grep -qw "$FAMILY_DB_NAME"; then
                echo_info "Database '$FAMILY_DB_NAME' exists and will be deleted"
                # Disconnect active connections
                PGPASSWORD="$FAMILY_ADMIN_PASS" psql -h "$DB_HOST" -p "$DB_PORT" -U "$FAMILY_ADMIN_USER" postgres -c "SELECT pg_terminate_backend(pg_stat_activity.pid) FROM pg_stat_activity WHERE pg_stat_activity.datname = '$FAMILY_DB_NAME' AND pid <> pg_backend_pid();"
                # Drop database
                PGPASSWORD="$FAMILY_ADMIN_PASS" psql -h "$DB_HOST" -p "$DB_PORT" -U "$FAMILY_ADMIN_USER" postgres -c "DROP DATABASE $FAMILY_DB_NAME;"
                if [ $? -ne 0 ]; then
                    echo_error "Error when deleting database '$FAMILY_DB_NAME'"
                    return 1
                fi
                
                # Create database again only if create_new flag is set
                if [ "$create_new" = true ]; then
                    echo_info "Creating new database '$FAMILY_DB_NAME'"
                    PGPASSWORD="$FAMILY_ADMIN_PASS" psql -h "$DB_HOST" -p "$DB_PORT" -U "$FAMILY_ADMIN_USER" postgres -c "CREATE DATABASE $FAMILY_DB_NAME;"
                    if [ $? -ne 0 ]; then
                        echo_error "Error when creating new database '$FAMILY_DB_NAME'"
                        return 1
                    fi
                else
                    echo_info "Database deleted. New database creation skipped (create_new flag=$create_new)"
                fi
            else
                echo_info "Database '$FAMILY_DB_NAME' does not exist"
                
                # Create database only if create_new flag is set
                if [ "$create_new" = true ]; then
                    echo_info "Creating new database '$FAMILY_DB_NAME'"
                    PGPASSWORD="$FAMILY_ADMIN_PASS" psql -h "$DB_HOST" -p "$DB_PORT" -U "$FAMILY_ADMIN_USER" postgres -c "CREATE DATABASE $FAMILY_DB_NAME;"
                    if [ $? -ne 0 ]; then
                        echo_error "Error when creating database '$FAMILY_DB_NAME'"
                        return 1
                    fi
                fi
            fi
            ;;
        sqlite)
            # For SQLite just delete the database file if it exists
            if [ -f "$FAMILY_DB_NAME" ]; then
                echo_info "Deleting SQLite database file: $FAMILY_DB_NAME"
                rm -f "$FAMILY_DB_NAME"
                if [ $? -ne 0 ]; then
                    echo_error "Error when deleting SQLite database file: $FAMILY_DB_NAME"
                    return 1
                fi
            else
                echo_info "SQLite database file does not exist: $FAMILY_DB_NAME"
            fi
            # For SQLite we don't create database in advance, it will be created on first query
            ;;
    esac
    
    if [ "$create_new" = true ]; then
        echo_success "Database recreation completed successfully"
    else
        echo_success "Database deletion completed successfully"
    fi
    return 0
}

# Function to create database and family_admin user
function create_family_admin_and_db {
    echo_info "Creating admin user $FAMILY_ADMIN_USER and database $FAMILY_DB_NAME..."
    
    case "$DB_ENGINE" in
        postgresql)
            # First create admin user with parameterized SQL
            sudo -u postgres psql \
                -c "CREATE TEMP TABLE IF NOT EXISTS params (param_name text PRIMARY KEY, param_value text);" \
                -c "INSERT INTO params VALUES ('user_name', '$FAMILY_ADMIN_USER') ON CONFLICT (param_name) DO UPDATE SET param_value = EXCLUDED.param_value;" \
                -c "INSERT INTO params VALUES ('user_password', '$FAMILY_ADMIN_PASS') ON CONFLICT (param_name) DO UPDATE SET param_value = EXCLUDED.param_value;" \
                -f "$SQL_SCRIPTS_DIR/utils/admin_operations.sql"
            if [ $? -ne 0 ]; then
                echo_error "Error executing admin user creation SQL script"
                return 1
            fi

            # Create database if it doesn't exist
            echo_info "Creating database $FAMILY_DB_NAME if not exists..."
            if ! sudo -u postgres psql -lqt | cut -d \| -f 1 | grep -qw "$FAMILY_DB_NAME"; then
                sudo -u postgres createdb -O "$FAMILY_ADMIN_USER" "$FAMILY_DB_NAME"
                if [ $? -ne 0 ]; then
                    echo_error "Error creating database $FAMILY_DB_NAME"
                    return 1
                fi
                echo_success "Database $FAMILY_DB_NAME created successfully"
            else
                echo_info "Database $FAMILY_DB_NAME already exists"
            fi

            echo_success "Admin user $FAMILY_ADMIN_USER and database $FAMILY_DB_NAME successfully configured"
            ;;
            
        sqlite)
            # For SQLite just create database file if it doesn't exist
            echo_info "SQLite: Creating database file $FAMILY_DB_NAME if not exists..."
            if [ ! -f "$FAMILY_DB_NAME" ]; then
                echo "PRAGMA foreign_keys=ON;" | sqlite3 "$FAMILY_DB_NAME"
                if [ $? -ne 0 ]; then
                    echo_error "Error when creating SQLite database file: $FAMILY_DB_NAME"
                    return 1
                fi
                echo_success "SQLite database file successfully created: $FAMILY_DB_NAME"
            else
                echo_info "SQLite database file already exists: $FAMILY_DB_NAME"
            fi
            ;;
    esac
    
    return 0
}

# Function to apply SQL scripts from level configuration file
function apply_sql_scripts_from_config {
    local level_dir="$1"
    local level_config="$level_dir/init.conf"
    
    if [ ! -f "$level_config" ];then
        echo_error "Level configuration file not found: $level_config"
        return 1
    fi
    
    echo_info "Applying SQL scripts from level: $(basename "$level_dir")"
    
    # Read list of scripts from level configuration file
    while IFS= read -r script_file || [ -n "$script_file" ]; do
        # Skip empty lines and comments
        if [[ -z "$script_file" || "$script_file" =~ ^# ]]; then
            continue
        fi
        
        local script_path="$level_dir/$script_file"
        
        if [ ! -f "$script_path" ]; then
            echo_error "SQL script not found: $script_path"
            return 1
        fi
        
        echo_info "Executing SQL script: $script_file"
        
        # Execute SQL script depending on engine type
        case "$DB_ENGINE" in
            postgresql)
                PGPASSWORD="$FAMILY_ADMIN_PASS" psql -h "$DB_HOST" -p "$DB_PORT" -U "$FAMILY_ADMIN_USER" -d "$FAMILY_DB_NAME" -f "$script_path"
                if [ $? -ne 0 ]; then
                    echo_error "Error executing SQL script: $script_path"
                    return 1
                fi
                ;;
            sqlite)
                sqlite3 "$FAMILY_DB_NAME" < "$script_path"
                if [ $? -ne 0 ]; then
                    echo_error "Error executing SQL script: $script_path"
                    return 1
                fi
                ;;
        esac
        
        echo_success "SQL script executed successfully: $script_file"
    done < "$level_config"
    
    return 0
}

# Main function for sequential level application
function apply_levels {
    local engine_root_config="$SQL_SCRIPTS_DIR/init.conf"
    
    if [ ! -f "$engine_root_config" ]; then
        echo_error "Engine root configuration file not found: $engine_root_config"
        return 1
    fi
    
    echo_info "Reading level list from engine root configuration file: $engine_root_config"
    
    # Read level list from root configuration file
    while IFS= read -r level_name || [ -n "$level_name" ]; do
        # Skip empty lines and comments
        if [[ -z "$level_name" || "$level_name" =~ ^# ]]; then
            continue
        fi
        
        local level_dir="$SQL_SCRIPTS_DIR/$level_name"
        
        if [ ! -d "$level_dir" ]; then
            echo_error "Level directory not found: $level_dir"
            return 1
        fi
        
        echo_info "Processing level: $level_name"
        
        # Apply SQL scripts from level
        apply_sql_scripts_from_config "$level_dir"
        if [ $? -ne 0 ]; then
            echo_error "Error applying SQL scripts from level: $level_name"
            return 1
        fi
        
        echo_success "Level successfully applied: $level_name"
    done < "$engine_root_config"
    
    return 0
}

# Check for required utilities
case "$DB_ENGINE" in
    postgresql)
        if ! command -v psql &> /dev/null; then
            echo_error "psql utility not found. Install PostgreSQL client."
            exit 1
        fi
        ;;
    sqlite)
        if ! command -v sqlite3 &> /dev/null; then
            echo_error "sqlite3 utility not found. Install SQLite."
            exit 1
        fi
        ;;
esac

echo_info "Initializing F.A.M.I.L.Y. database"
echo_info "Database engine: $DB_ENGINE"
echo_info "Host: $DB_HOST"
echo_info "Port: $DB_PORT"
echo_info "Database name: $FAMILY_DB_NAME"
echo_info "User: $FAMILY_ADMIN_USER"

# First check if we just need to drop the database
if [ "$DROP_DATABASE" = true ]; then
    echo_info "Drop database mode detected (-D option)"
    
    case "$DB_ENGINE" in
        postgresql)
            # Check if database exists before attempting to drop it
            if PGPASSWORD="$FAMILY_ADMIN_PASS" psql -h "$DB_HOST" -p "$DB_PORT" -U "$FAMILY_ADMIN_USER" -lqt | cut -d \| -f 1 | grep -qw "$FAMILY_DB_NAME"; then
                echo_info "Database '$FAMILY_DB_NAME' exists and will be deleted"
                # Disconnect active connections
                PGPASSWORD="$FAMILY_ADMIN_PASS" psql -h "$DB_HOST" -p "$DB_PORT" -U "$FAMILY_ADMIN_USER" postgres -c "SELECT pg_terminate_backend(pg_stat_activity.pid) FROM pg_stat_activity WHERE pg_stat_activity.datname = '$FAMILY_DB_NAME' AND pid <> pg_backend_pid();"
                # Drop database
                PGPASSWORD="$FAMILY_ADMIN_PASS" psql -h "$DB_HOST" -p "$DB_PORT" -U "$FAMILY_ADMIN_USER" postgres -c "DROP DATABASE $FAMILY_DB_NAME;"
                if [ $? -ne 0 ]; then
                    echo_error "Error when deleting database '$FAMILY_DB_NAME'"
                    exit 1
                fi
                echo_success "Database '$FAMILY_DB_NAME' successfully deleted"
            else
                echo_info "Database '$FAMILY_DB_NAME' does not exist, nothing to drop"
            fi
            ;;
        sqlite)
            # For SQLite just delete the database file if it exists
            if [ -f "$FAMILY_DB_NAME" ]; then
                echo_info "Deleting SQLite database file: $FAMILY_DB_NAME"
                rm -f "$FAMILY_DB_NAME"
                if [ $? -ne 0 ]; then
                    echo_error "Error when deleting SQLite database file: $FAMILY_DB_NAME"
                    exit 1
                fi
                echo_success "SQLite database file successfully deleted: $FAMILY_DB_NAME"
            else
                echo_info "SQLite database file does not exist: $FAMILY_DB_NAME, nothing to drop"
            fi
            ;;
    esac
    echo_info "Database drop operation completed. Exiting script."
    exit 0
fi

# Recreate database if specified
if [ "$RECREATE_DATABASE" = true ]; then
    echo_info "Recreate database mode detected (-R option)"
    # For recreate option we first need to make sure the admin user exists
    # This is needed only for the admin user, not for the database itself
    case "$DB_ENGINE" in
        postgresql)
            # Connect as postgres (PostgreSQL superuser) to check/create admin user
            echo_info "Checking if user $FAMILY_ADMIN_USER exists..."
            if sudo -u postgres psql -tAc "SELECT 1 FROM pg_roles WHERE rolname='$FAMILY_ADMIN_USER'" | grep -q 1; then
                echo_info "User $FAMILY_ADMIN_USER already exists"
            else
                echo_info "Creating user $FAMILY_ADMIN_USER with superuser privileges..."
                sudo -u postgres psql -c "CREATE USER $FAMILY_ADMIN_USER WITH PASSWORD '$FAMILY_ADMIN_PASS' SUPERUSER CREATEDB CREATEROLE INHERIT LOGIN;"
                if [ $? -ne 0 ]; then
                    echo_error "Error when creating user $FAMILY_ADMIN_USER"
                    exit 1
                fi
                echo_success "User $FAMILY_ADMIN_USER successfully created with superuser privileges"
            fi
            ;;
    esac
    
    # Now proceed with drop_database which will recreate if needed
    drop_database true
    if [ $? -ne 0 ]; then
        echo_error "Error recreating database"
        exit 1
    fi
fi

# Now we can initialize user and database for normal operation mode
if [ "$DROP_DATABASE" = false ] && [ "$RECREATE_DATABASE" = false ]; then
    create_family_admin_and_db
    if [ $? -ne 0 ]; then
        echo_error "Error creating user and database"
        exit 1
    fi
fi

# Start database initialization process
apply_levels
if [ $? -eq 0 ]; then
    echo_success "F.A.M.I.L.Y. database initialization completed successfully"
else
    echo_error "Error initializing F.A.M.I.L.Y. database"
    exit 1
fi

exit 0