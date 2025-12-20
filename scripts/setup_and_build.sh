#!/bin/bash
#
# Complete Setup and Cache Build Script for MCP OCI OPSI
#
# This script performs:
# 1. Virtual environment creation
# 2. Dependency installation
# 3. Tenancy review and cache build
#
# Usage:
#   ./setup_and_build.sh
#   ./setup_and_build.sh --profile emdemo
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
echo -e "${BLUE}   MCP OCI OPSI - Complete Setup${NC}"
echo -e "${BLUE}======================================================================${NC}"
echo ""

# Check if Python is available
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}ERROR: python3 not found${NC}"
    echo "Please install Python 3.10 or higher"
    exit 1
fi

PYTHON_VERSION=$(python3 --version | cut -d' ' -f2)
echo -e "${GREEN}✓ Python found: $PYTHON_VERSION${NC}"

# Check if OCI config exists
if [ ! -f "$HOME/.oci/config" ]; then
    echo -e "${RED}ERROR: OCI config not found${NC}"
    echo "Please configure OCI CLI first:"
    echo "  oci setup config"
    exit 1
fi

echo -e "${GREEN}✓ OCI config found${NC}"
echo ""

# Step 1: Create virtual environment if it doesn't exist
echo -e "${YELLOW}[Step 1/3] Setting up virtual environment...${NC}"
cd "$PROJECT_ROOT"

if [ -d ".venv" ]; then
    echo -e "${GREEN}✓ Virtual environment already exists${NC}"
else
    echo "Creating virtual environment..."
    python3 -m venv .venv
    echo -e "${GREEN}✓ Virtual environment created${NC}"
fi

# Activate virtual environment
source .venv/bin/activate
echo -e "${GREEN}✓ Virtual environment activated${NC}"
echo ""

# Step 2: Install dependencies
echo -e "${YELLOW}[Step 2/3] Installing dependencies...${NC}"

# Check if OCI SDK is already installed
if python3 -c "import oci" 2>/dev/null; then
    echo -e "${GREEN}✓ Dependencies already installed${NC}"
else
    echo "Installing MCP OCI OPSI package..."
    pip install -q -e .
    echo -e "${GREEN}✓ Dependencies installed successfully${NC}"
fi
echo ""

# Step 3: Run tenancy review
echo -e "${YELLOW}[Step 3/3] Running tenancy review...${NC}"
echo ""

# Parse arguments for profile
PROFILE_ARG=""
if [ "$1" == "--profile" ] && [ -n "$2" ]; then
    PROFILE_ARG="--profile $2"
    echo -e "${GREEN}Using OCI profile: $2${NC}"
    echo ""
fi

# Run the tenancy review
python3 scripts/tenancy_review.py $PROFILE_ARG

echo ""
echo -e "${GREEN}======================================================================${NC}"
echo -e "${GREEN}   ✅ SETUP COMPLETE${NC}"
echo -e "${GREEN}======================================================================${NC}"
echo ""
echo -e "${BLUE}What's next?${NC}"
echo ""
echo "1. Configure the MCP server in Claude Desktop or Claude Code"
echo ""
echo "2. Use these instant queries (powered by cache):"
echo "   • How many databases do I have?"
echo "   • Find database X"
echo "   • Show me databases in compartment X"
echo ""
echo "3. Use these detailed queries (real-time API):"
echo "   • Show me SQL statistics for the past week"
echo "   • Get ADDM findings for database X"
echo "   • Forecast storage capacity for the next 30 days"
echo ""
echo -e "${BLUE}Cache location:${NC} ~/.mcp-oci/cache/opsi_cache[_PROFILE].json"
echo -e "${BLUE}Review report:${NC} ~/.mcp-oci/cache/tenancy_review_*.json"
echo ""
echo -e "${YELLOW}Tip: To refresh the cache later, run:${NC}"
echo "  ./scripts/quick_cache_build.sh"
echo ""
