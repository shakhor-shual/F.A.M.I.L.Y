#!/bin/bash

# ============================================================================
# F.A.M.I.L.Y. AMI USER INITIALIZATION SCRIPT
# Created: April 16, 2025
# Description: Creates or drops AMI user and schema in the F.A.M.I.L.Y database
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
    echo "  -c, --config [path]     Configuration file path (default: ./family_db.conf)"
    echo "  -u, --ami-user [name]   AMI user name to create"
    echo "  -p, --ami-pass [pass]   Password for AMI user"
    echo "  -D, --drop             Drop existing AMI user and schema"
    echo "  -f, --force            Force drop (with -D) even if there are active connections"
    echo "  --help                  Show this help message"
    echo ""
    echo "Example: $0 -u ami_user1 -p secret_pass"
    echo "         $0 -u ami_user1 -D -f"
    echo ""
}

# Parse command line parameters
CONFIG_FILE="$(dirname "$0")/family_db.conf"
AMI_USER=""
AMI_PASS=""
DROP_MODE=false
FORCE_MODE=false

while [[ $# -gt 0 ]]; do
    key="$1"
    case $key in
        -c|--config)
        CONFIG_FILE="$2"
        shift 2
        ;;
        -u|--ami-user)
        AMI_USER="$2"
        shift 2
        ;;
        -p|--ami-pass)
        AMI_PASS="$2"
        shift 2
        ;;
        -D|--drop)
        DROP_MODE=true
        shift
        ;;
        -f|--force)
        FORCE_MODE=true
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

# Check required parameters
if [ -z "$AMI_USER" ]; then
    echo_error "AMI user name is required (-u option)"
    print_usage
    exit 1
fi

if [ -z "$AMI_PASS" ] && [ "$DROP_MODE" = false ]; then
    echo_error "AMI user password is required (-p option) when creating AMI"
    print_usage
    exit 1
fi

# Load configuration
if [ ! -f "$CONFIG_FILE" ]; then
    echo_error "Configuration file not found: $CONFIG_FILE"
    exit 1
fi

source "$CONFIG_FILE"

# Function to initialize or drop AMI
function manage_ami {
    case "$FAMILY_DB_ENGINE" in
        postgresql)
            if [ "$DROP_MODE" = true ]; then
                echo_info "Dropping AMI user and schema: $AMI_USER..."
                sudo -u postgres psql -d "$FAMILY_DB_NAME" << EOF
                CALL public.drop_ami_schema('$AMI_USER', $FORCE_MODE);
EOF
            else
                echo_info "Creating AMI user and initializing consciousness level: $AMI_USER..."
                sudo -u postgres psql -d "$FAMILY_DB_NAME" << EOF
                CALL public.init_ami_consciousness_level(
                    ami_name := '$AMI_USER',
                    ami_password := '$AMI_PASS',
                    schema_name := 'ami_$AMI_USER',
                    grant_permissions := true
                );
EOF
            fi
            if [ $? -ne 0 ]; then
                [ "$DROP_MODE" = true ] && echo_error "Error dropping AMI" || echo_error "Error creating AMI"
                return 1
            fi
            [ "$DROP_MODE" = true ] && echo_success "AMI dropped successfully" || echo_success "AMI created successfully"
            ;;
            
        sqlite)
            echo_warn "SQLite does not support separate users and schemas"
            echo_info "Operations will be performed using table prefixes"
            ;;
    esac
    
    return 0
}

# Execute AMI management
manage_ami
if [ $? -eq 0 ]; then
    [ "$DROP_MODE" = true ] && echo_success "AMI deletion completed successfully" || echo_success "AMI initialization completed successfully"
    exit 0
else
    [ "$DROP_MODE" = true ] && echo_error "Error during AMI deletion" || echo_error "Error during AMI initialization"
    exit 1
fi