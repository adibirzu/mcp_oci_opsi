#!/bin/bash
set -e

echo "🔧 MCP OCI OPSI Import Fix Script"
echo "===================================="

BASE=/Users/abirzu/dev/oracle-db-autonomous-agent/mcp_oci_opsi

# Phase 1B: Fix tool imports
echo "Phase 1B: Fixing tool imports..."
cd "$BASE/tools"

for file in tools_*.py; do
  [ -f "$file" ] || continue
  echo "  Fixing $file..."
  sed -i '' 's/from \.cache import/from ..cache import/g' "$file"
  sed -i '' 's/from \.config_enhanced import/from ..config_enhanced import/g' "$file"
  sed -i '' 's/from \.config_base import/from ..config_base import/g' "$file"
done

echo "✅ Tool imports fixed"

# Test imports
echo ""
echo "Testing imports..."
cd "$BASE/.."
python3 -c "
import sys
sys.path.insert(0, '.')
from mcp_oci_opsi import __version__
from mcp_oci_opsi.config import get_oci_config  
from mcp_oci_opsi.tools import opsi
print(f'✅ Core imports working (v{__version__})')
" && echo "✅ Import test PASSED" || echo "❌ Import test failed - manual fixes may be needed"

echo ""
echo "✅ Phase 1B complete - Server should now be functional"
