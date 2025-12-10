#!/bin/bash
set -e

echo "🔧 Comprehensive OPSI MCP Import Fix"
echo "======================================"

BASE=/Users/abirzu/dev/oracle-db-autonomous-agent/mcp_oci_opsi

cd "$BASE/tools"

# Fix all relative imports to use parent-level references
echo "Fixing all tool imports..."

for file in tools_*.py; do
  [ -f "$file" ] || continue
  echo "  Processing $file..."
  
  # Change all local imports to parent imports
  sed -i '' 's/from \.cache import/from ..cache import/g' "$file"
  sed -i '' 's/from \.cache_enhanced import/from ..cache_enhanced import/g' "$file"
  sed -i '' 's/from \.config import/from ..config import/g' "$file"
  sed -i '' 's/from \.config_base import/from ..config_base import/g' "$file"
  sed -i '' 's/from \.config_enhanced import/from ..config_enhanced import/g' "$file"
  sed -i '' 's/from \.logging_config import/from ..logging_config import/g' "$file"
  
  # For visualization, import from scripts
  sed -i '' 's/from \.visualization import/from ..scripts.visualization import/g' "$file"
done

echo "✅ All tool imports fixed"
echo ""

# Test imports
echo "Testing Python imports..."
cd "$BASE/.."

python3 << 'PYEOF'
import sys
sys.path.insert(0, '.')

print("Testing core imports...")
try:
    from mcp_oci_opsi import __version__
    print(f"  ✓ Package version: {__version__}")
except Exception as e:
    print(f"  ✗ Package import failed: {e}")
    sys.exit(1)

try:
    from mcp_oci_opsi.config import get_oci_config
    print("  ✓ Config module OK")
except Exception as e:
    print(f"  ✗ Config import failed: {e}")
    sys.exit(1)

try:
    from mcp_oci_opsi.tools import opsi
    print("  ✓ OPSI tools OK")
except Exception as e:
    print(f"  ✗ OPSI tools import failed: {e}")
    sys.exit(1)

try:
    from mcp_oci_opsi.tools import cache
    print("  ✓ Cache tools OK")
except Exception as e:
    print(f"  ✗ Cache tools import failed: {e}")
    sys.exit(1)

try:
    from mcp_oci_opsi.tools import dbmanagement
    print("  ✓ DB Management tools OK")
except Exception as e:
    print(f"  ✗ DB Management import failed: {e}")
    sys.exit(1)

print("")
print("✅ All critical imports working!")
print("")
PYEOF

if [ $? -eq 0 ]; then
  echo "======================================"
  echo "✅ OPSI MCP Server is now functional!"
  echo "======================================"
  echo ""
  echo "To start the server:"
  echo "  cd $BASE"
  echo "  python -m mcp_oci_opsi"
  echo ""
else
  echo "❌ Import test failed - manual intervention needed"
  exit 1
fi
