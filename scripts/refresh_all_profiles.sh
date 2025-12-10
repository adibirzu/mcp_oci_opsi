#!/bin/bash
# Refresh caches for all profiles found in ~/.oci/config
# Usage: ./refresh_all_profiles.sh

set -e
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
cd "$PROJECT_ROOT"

# Ensure venv exists
if [ ! -d ".venv" ]; then
    echo "Virtual environment not found. Please run setup_and_build.sh first."
    exit 1
fi

# Activate venv to ensure environment is correct
source "$PROJECT_ROOT/.venv/bin/activate"
VENV_PYTHON="python3"

# Ensure dependencies are installed (in case pip install -e . wasn't run)
echo "Ensuring package is installed..."
pip install -q -e . || echo "Warning: pip install failed"

# Add PARENT directory to PYTHONPATH so we can import mcp_oci_opsi as a module
PARENT_DIR="$(dirname "$PROJECT_ROOT")"
export PYTHONPATH="$PARENT_DIR:$PYTHONPATH"

echo "Debug: PROJECT_ROOT=$PROJECT_ROOT"
echo "Debug: PARENT_DIR=$PARENT_DIR"
echo "Debug: PYTHONPATH=$PYTHONPATH"
# Verify we can see the package directory
ls -d "$PARENT_DIR/mcp_oci_opsi"

echo "Detecting OCI profiles from ~/.oci/config..."
if [ ! -f "$HOME/.oci/config" ]; then
    echo "Error: ~/.oci/config not found."
    exit 1
fi

# Read profiles using awk to extract [SECTION] lines
profiles=$(awk -F'[][]' '/^\[.*\]/ {print $2}' ~/.oci/config)

# Set IFS to newline to handle profiles correctly
SAVEIFS=$IFS
IFS=$'\n'

for profile in $profiles; do
    # Trim whitespace
    profile=$(echo "$profile" | tr -d '\r' | xargs)
    if [ -z "$profile" ]; then continue; fi

    echo ""
    echo "========================================================"
    echo "Processing profile: '$profile'"
    echo "========================================================"
    
    # Run enhanced discovery (builds enhanced cache)
    echo "-> Building Enhanced Cache (v2)..."
    "$VENV_PYTHON" -m mcp_oci_opsi.scripts.enhanced_database_discovery --profile "$profile" || echo "Warning: Enhanced discovery failed for $profile"

    # Run tenancy review (builds basic cache) - usually redundant if using enhanced, but good for backup
    echo "-> Building Basic Cache (v1)..."
    "$VENV_PYTHON" -m mcp_oci_opsi.scripts.tenancy_review --profile "$profile" || echo "Warning: Tenancy review failed for $profile"

    echo "Done with $profile"
done

IFS=$SAVEIFS
echo ""
echo "All profiles processed."
