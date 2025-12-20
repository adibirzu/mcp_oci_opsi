#!/bin/bash
#
# Quick Cache Build Script for MCP OCI OPSI
#
# This script performs a quick tenancy review and builds the database cache
# for fast instant responses.
#
# Usage:
#   ./quick_cache_build.sh
#   ./quick_cache_build.sh --profile emdemo
#

set -e

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Get script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

echo -e "${BLUE}======================================================================${NC}"
echo -e "${BLUE}   MCP OCI OPSI - Quick Cache Build${NC}"
echo -e "${BLUE}======================================================================${NC}"
echo ""

# Check if Python is available
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}ERROR: python3 not found${NC}"
    echo "Please install Python 3.10 or higher"
    exit 1
fi

# Check if OCI config exists
if [ ! -f "$HOME/.oci/config" ]; then
    echo -e "${RED}ERROR: OCI config not found${NC}"
    echo "Please configure OCI CLI first:"
    echo "  oci setup config"
    exit 1
fi

# Check if virtual environment exists and activate it
if [ -d "$PROJECT_ROOT/.venv" ]; then
    echo -e "${YELLOW}Activating virtual environment...${NC}"
    source "$PROJECT_ROOT/.venv/bin/activate"
elif [ -d "$PROJECT_ROOT/venv" ]; then
    echo -e "${YELLOW}Activating virtual environment...${NC}"
    source "$PROJECT_ROOT/venv/bin/activate"
else
    echo -e "${RED}ERROR: Virtual environment not found${NC}"
    echo "Please create a virtual environment and install dependencies first:"
    echo ""
    echo "  cd $PROJECT_ROOT"
    echo "  python3 -m venv .venv"
    echo "  source .venv/bin/activate"
    echo "  pip install -e ."
    echo ""
    exit 1
fi

# Verify OCI SDK is installed
if ! python3 -c "import oci" 2>/dev/null; then
    echo -e "${RED}ERROR: OCI SDK not installed${NC}"
    echo "Please install dependencies first:"
    echo ""
    echo "  cd $PROJECT_ROOT"
    echo "  source .venv/bin/activate"
    echo "  pip install -e ."
    echo ""
    exit 1
fi

echo -e "${GREEN}✓ Virtual environment activated${NC}"
echo -e "${GREEN}✓ Dependencies verified${NC}"
echo ""

# Parse arguments
PROFILE_ARG=""
if [ "$1" == "--profile" ] && [ -n "$2" ]; then
    PROFILE_ARG="--profile $2"
    echo -e "${GREEN}Using OCI profile: $2${NC}"
    echo ""
fi

# Run the tenancy review script
echo -e "${YELLOW}Running tenancy review...${NC}"
echo ""

cd "$PROJECT_ROOT"
python3 scripts/tenancy_review.py $PROFILE_ARG

echo ""
echo -e "${GREEN}======================================================================${NC}"
echo -e "${GREEN}   ✅ CACHE BUILD COMPLETE${NC}"
echo -e "${GREEN}======================================================================${NC}"
echo ""
echo -e "${BLUE}Next steps:${NC}"
echo "1. Start using the MCP server with Claude Desktop or Claude Code"
echo "2. Try these fast queries (instant responses):"
echo "   • How many databases do I have?"
echo "   • Find database X"
echo "   • Show me databases in compartment X"
echo ""
echo -e "${BLUE}Cache location:${NC} ~/.mcp-oci/cache/opsi_cache[_PROFILE].json"
echo -e "${BLUE}Review report:${NC} ~/.mcp-oci/cache/tenancy_review_*.json"
echo ""
