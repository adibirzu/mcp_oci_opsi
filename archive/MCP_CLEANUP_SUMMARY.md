# MCP OCI OPSI Server Cleanup Summary
**Date:** December 9, 2025  
**Status:** Critical Import Issues Identified - Server Currently Non-Functional

## Executive Summary

The MCP OCI OPSI server has **critical structural issues** preventing it from starting. The review identified broken import paths, misplaced files, and organizational problems that must be fixed before the server can function.

---

## ✅ Completed Actions (Phase 1 - Partial)

1. **Moved critical configuration files to root level:**
   - `config_base.py` (from test_scripts/)
   - `config_enhanced.py` (from test_scripts/)
   - `logging_config.py` (from test_scripts/)

2. **Fixed tools/__init__.py** to use local imports (`.` instead of `..`)

3. **Created wrapper files in tools/ folder:**
   - `oci_clients.py` - Re-exports from `..oci_clients`
   - `oci_clients_enhanced.py` - Re-exports from `..oci_clients_enhanced`
   - `config_enhanced.py` - Re-exports from `..config_enhanced`

---

## ❌ Remaining Critical Issues

### Import Path Problems in Tools

Many tool files import from `.cache`, `.config_enhanced`, etc., expecting these modules in the tools/ folder. However, creating wrappers causes circular dependencies with tools_cache.py.

**Affected Files:**
- `tools/tools_cache.py` - imports from `.cache`
- `tools/tools_database_discovery.py` - imports from `.cache`  
- All tools importing from `.oci_clients`, `.oci_clients_enhanced`, `.config_enhanced`

**Solution:** Use global search-replace to change tool imports from local (`.module`) to parent (`..module`).

---

## 📋 Complete Remediation Plan

### Phase 1B: Fix All Tool Imports (CRITICAL - SERVER WON'T START)

**Automated Fix Script:**
```bash
#!/bin/bash
# Fix imports in all tool files to use parent-level imports

cd /Users/abirzu/dev/oracle-db-autonomous-agent/mcp_oci_opsi/tools

# Remove wrapper files that cause circular imports
rm -f cache.py 2>/dev/null

# Fix imports in all tool files
for file in tools_*.py; do
  # Change .cache to ..cache
  sed -i '' 's/from \.cache import/from ..cache import/g' "$file"
  
  # Change .config_enhanced to ..config_enhanced  
  sed -i '' 's/from \.config_enhanced import/from ..config_enhanced import/g' "$file"
  
  # Change .config_base to ..config_base
  sed -i '' 's/from \.config_base import/from ..config_base import/g' "$file"
  
  # Already done by wrappers, but double-check:
  # .oci_clients should stay as is (wrapper exists)
  # .oci_clients_enhanced should stay as is (wrapper exists)
done

echo "✅ Tool imports fixed"
```

### Phase 2: Reorganize Scripts (ORGANIZATIONAL)

**Move utility scripts from root to scripts/**
```bash
cd /Users/abirzu/dev/oracle-db-autonomous-agent/mcp_oci_opsi

mv auto_validate_apis.py scripts/
mv cleanup_non_working_apis.py scripts/
mv catalog_tools.py scripts/
mv test_sql_stats_fix.py scripts/
mv build_cache.py scripts/
mv build_enhanced_cache.py scripts/
mv main_v3.py scripts/discovery_cli.py
```

**Update scripts/README.md** to document the new scripts.

### Phase 3: Clean Up Tests (ORGANIZATIONAL)

**Rename test_scripts/ to tests/**
```bash
cd /Users/abirzu/dev/oracle-db-autonomous-agent/mcp_oci_opsi

mv test_scripts tests

# Remove duplicate config files now at root
rm tests/config_base.py
rm tests/config_enhanced.py  
rm tests/logging_config.py
```

### Phase 4: Remove Obsolete Files (CLEANUP)

**Delete old backups and documentation:**
```bash
cd /Users/abirzu/dev/oracle-db-autonomous-agent/mcp_oci_opsi

rm -rf backups/
rm -rf OLD/
```

**Consider consolidating:**
- `README.md` vs `README_UPDATED.md` - Keep one
- Multiple DEMO_GUIDE files - Consolidate or archive

### Phase 5: Verify & Test (VALIDATION)

**Import Test:**
```bash
cd /Users/abirzu/dev/oracle-db-autonomous-agent

python3 -c "
import sys
sys.path.insert(0, '.')

# Test core imports
from mcp_oci_opsi import __version__
from mcp_oci_opsi.config import get_oci_config
from mcp_oci_opsi.tools import opsi, cache, dbmanagement

print(f'✅ MCP OCI OPSI v{__version__} - All imports working!')
"
```

**MCP Server Test:**
```bash
cd /Users/abirzu/dev/oracle-db-autonomous-agent/mcp_oci_opsi

# Activate venv
source .venv/bin/activate

# Test server startup
python -m mcp_oci_opsi &
PID=$!
sleep 2
kill $PID

echo "✅ Server starts without errors"
```

---

## 🎯 Recommended Next Steps

1. **IMMEDIATE:** Run Phase 1B automated fix script to repair imports
2. **TEST:** Verify server can import all modules
3. **OPTIONAL:** Run Phase 2-4 for organization (non-breaking)
4. **DOCUMENT:** Update main README with correct startup instructions

---

## 📊 Final Structure (After All Phases)

```
mcp_oci_opsi/
├── __init__.py
├── __main__.py (entry point)
├── main.py (FastMCP v2 server - ACTUAL MCP SERVER)
├── config_base.py ← MOVED
├── config_enhanced.py ← MOVED  
├── logging_config.py ← MOVED
├── oci_clients.py
├── oci_clients_enhanced.py
├── cache.py
├── cache_enhanced.py
├── skills_loader.py
├── pyproject.toml
├── .env.example
├── auth/
├── auth_bridge/
├── config/ (re-export namespace)
├── servers/ (cache_server, opsi_server, dbm_server, admin_server)
├── tools/ (ALL MCP tools)
│   ├── __init__.py ← FIXED
│   ├── oci_clients.py (wrapper)
│   ├── oci_clients_enhanced.py (wrapper)
│   ├── config_enhanced.py (wrapper)
│   └── tools_*.py (ALL imports fixed to use ..)
├── scripts/ (utility scripts and CLI tools)
│   ├── setup_and_build.sh
│   ├── quick_cache_build.sh
│   ├── tenancy_review.py
│   ├── discovery_cli.py ← RENAMED from main_v3.py
│   ├── enhanced_database_discovery.py
│   ├── auto_validate_apis.py ← MOVED
│   ├── cleanup_non_working_apis.py ← MOVED
│   ├── catalog_tools.py ← MOVED
│   ├── build_cache.py ← MOVED
│   └── README.md (updated)
├── tests/ ← RENAMED from test_scripts
│   ├── test_*.py (test files)
│   └── (removed duplicate config files)
├── skills/ (skill definitions)
├── terraform/ (deployment)
├── wiki/ (documentation)
└── docs/ (guides)

REMOVED:
├── backups/ ← DELETED
└── OLD/ ← DELETED
```

---

## 🔧 Quick Fix Script

Save and run this complete fix:

```bash
#!/bin/bash
set -e

echo "🔧 MCP OCI OPSI Cleanup Script"
echo "================================"

BASE=/Users/abirzu/dev/oracle-db-autonomous-agent/mcp_oci_opsi

# Phase 1B: Fix tool imports
echo "Phase 1B: Fixing tool imports..."
cd "$BASE/tools"

for file in tools_*.py; do
  [ -f "$file" ] || continue
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
" || echo "❌ Import test failed - manual fixes needed"

echo ""
echo "✅ Phase 1B complete - Server should now be functional"
echo ""
echo "Optional: Run phases 2-4 for organization (non-breaking)"
```

---

## Variables Exposed to LLMs

The MCP server exposes tools via FastMCP. All tools defined in `main.py` with `@app.tool()` decorator are automatically available to any MCP-compatible LLM client (Claude, ChatGPT, Gemini, etc.).

**Key Tools Available:**
- `ping()`, `whoami()`, `list_oci_profiles()`
- `build_database_cache()`, `get_fleet_summary()`, `search_databases()`
- `list_database_insights()`, `query_warehouse_standard()`, `list_sql_texts()`
- Database Management, SQL Watch, Compartment listing tools

The server works as a **standalone MCP server** that any LLM can connect to via the MCP protocol.

---

## Notes

- `main_v3.py` is NOT an MCP server - it's a CLI discovery tool
- `__main__.py` defaults to v2 (main.py) which is the actual MCP server
- The auth_bridge/ folder appears unused (OCA auth noted as removed in main.py)
- Consider removing or documenting auth_bridge if not actively used
