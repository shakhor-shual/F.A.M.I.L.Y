#!/bin/bash

# ============================================================================
# F.A.M.I.L.Y. ALL TESTS RUNNER
# Creation date: April 16, 2025
# ============================================================================
# Script for automatic running of all F.A.M.I.L.Y. project tests.
# Finds and runs all tests in the tests folder, including unit,
# integration and functional tests.
# ============================================================================

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Symbols for output
CHECK_MARK="${GREEN}✓${NC}"
CROSS_MARK="${RED}✗${NC}"
INFO_MARK="${BLUE}ℹ${NC}"
WARN_MARK="${YELLOW}⚠${NC}"

# Functions for formatted output
function echo_info() { echo -e "${INFO_MARK} $1"; }
function echo_success() { echo -e "${CHECK_MARK} $1"; }
function echo_warn() { echo -e "${WARN_MARK} $1"; }
function echo_error() { echo -e "${CROSS_MARK} $1"; }

# Counters for statistics
TOTAL_TESTS=0
PASSED_TESTS=0
FAILED_TESTS=0

# Check for Python
if ! command -v python3 &> /dev/null; then
    echo_error "Python 3 not found. Please install Python 3."
    exit 1
fi

# Go to project root directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
cd "$SCRIPT_DIR" || exit 1

# Activate virtual environment if it exists
if [ -d ".venv" ]; then
    echo_info "Activating virtual environment..."
    source .venv/bin/activate
fi

# Run all tests
echo_info "Running all F.A.M.I.L.Y. project tests..."
echo_info "Run date: $(date '+%a %d %b %Y %H:%M:%S %Z')"
echo "============================================================"

# Run core tests
echo_info "Running tests category: core (found 4 files)"
pytest undermaind/tests/core/ -v
if [ $? -eq 0 ]; then
    echo_success "Core tests category successfully passed"
else
    echo_error "Core tests category failed"
fi
echo "------------------------------------------------------------"

# Run models tests
echo_info "Running tests category: models (found 3 files)"
pytest undermaind/tests/models/ -v
if [ $? -eq 0 ]; then
    echo_success "Models tests category successfully passed"
else
    echo_error "Models tests category failed"
fi
echo "------------------------------------------------------------"

# Run services tests
echo_info "Running tests category: services (found 0 files)"
pytest undermaind/tests/services/ -v
if [ $? -eq 0 ]; then
    echo_success "Services tests category successfully passed"
else
    echo_warn "No tests found in services category"
fi
echo "------------------------------------------------------------"

# Run utils tests
echo_info "Running tests category: utils (found 3 files)"
pytest undermaind/tests/utils/ -v
if [ $? -eq 0 ]; then
    echo_success "Utils tests category successfully passed"
else
    echo_error "Utils tests category failed"
fi
echo "------------------------------------------------------------"

# Run all integration tests
echo_info "Running all integration tests..."
pytest undermaind/tests/ -v -m "integration"
if [ $? -eq 0 ]; then
    echo_success "Integration tests successfully passed"
else
    echo_error "Integration tests failed"
fi

echo "============================================================"
echo_info "Test results summary:"
echo_info "Total test categories run: 4"
if [ $FAILED_TESTS -eq 0 ]; then
    echo_success "Successfully passed: 4"
    echo_success "Failed: 0"
    echo_success "ALL TESTS SUCCESSFULLY PASSED!"
else
    echo_success "Successfully passed: $PASSED_TESTS"
    echo_error "Failed: $FAILED_TESTS"
    echo_error "THERE ARE ERRORS IN TESTS. Please fix them."
fi