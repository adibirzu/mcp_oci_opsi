# Scripts Directory

This directory contains setup and maintenance scripts for the MCP OCI OPSI server.

## Scripts Overview

### 1. setup_and_build.sh (RECOMMENDED FOR FIRST-TIME SETUP)

**Purpose**: Complete automated setup from scratch

**What it does**:
- Creates Python virtual environment (if not exists)
- Installs all dependencies (OCI SDK, MCP framework, etc.)
- Runs tenancy review and builds cache

**When to use**:
- First-time setup
- After cloning the repository
- When dependencies are not installed

**Usage**:
```bash
# Default profile
./scripts/setup_and_build.sh

# Specific profile
./scripts/setup_and_build.sh --profile emdemo
```

**Time**: ~3-5 minutes (depending on fleet size)

---

### 2. quick_cache_build.sh (FOR CACHE REFRESH)

**Purpose**: Quick cache rebuild (assumes dependencies already installed)

**What it does**:
- Activates existing virtual environment
- Verifies dependencies are installed
- Runs tenancy review and rebuilds cache

**When to use**:
- Dependencies already installed
- Cache needs refresh (> 24 hours old)
- After adding/removing databases
- After compartment changes

**Usage**:
```bash
# Default profile
./scripts/quick_cache_build.sh

# Specific profile
./scripts/quick_cache_build.sh --profile emdemo
```

**Time**: ~1-2 minutes (depending on fleet size)

---

### 3. tenancy_review.py (CORE PYTHON SCRIPT)

**Purpose**: Core tenancy scanning and cache building logic

**What it does**:
- Scans all compartments recursively
- Discovers databases, hosts, and Exadata systems
- Builds optimized cache
- Generates inventory reports
- Provides recommendations

**When to use**:
- Called by other scripts
- Direct use with Python for advanced options
- Debugging or custom scans

**Usage**:
```bash
# Activate venv first
source .venv/bin/activate

# Scan entire tenancy
python3 scripts/tenancy_review.py

# Specific profile
python3 scripts/tenancy_review.py --profile emdemo

# Single compartment only
python3 scripts/tenancy_review.py --compartment ocid1.compartment.oc1..aaa...

# List available profiles
python3 scripts/tenancy_review.py --list-profiles
```

---

## Decision Tree: Which Script to Use?

```
START
  |
  ├─ First time setup?
  │  └─ YES → Use setup_and_build.sh
  │         (Creates venv, installs deps, builds cache)
  │
  └─ NO → Dependencies already installed?
         |
         ├─ YES → Use quick_cache_build.sh
         │        (Just rebuilds cache quickly)
         │
         └─ NO → Use setup_and_build.sh
                 (Installs deps, then builds cache)
```

## Quick Reference

| Scenario | Script | Command |
|----------|--------|---------|
| **Fresh install** | setup_and_build.sh | `./scripts/setup_and_build.sh` |
| **Cache refresh** | quick_cache_build.sh | `./scripts/quick_cache_build.sh` |
| **Custom scan** | tenancy_review.py | `python3 scripts/tenancy_review.py --compartment X` |
| **Different profile** | Any | Add `--profile emdemo` |

## Output Files

All scripts generate these outputs:

1. **Cache File**: `~/.mcp_oci_opsi_cache.json`
   - Optimized for instant queries
   - Valid for 24 hours
   - ~100-500 KB depending on fleet size

2. **Review Report**: `~/.mcp_oci_opsi/tenancy_review_TIMESTAMP.json`
   - Comprehensive inventory report
   - Includes recommendations
   - Useful for audits and documentation

## Common Issues

### "Virtual environment not found"

**Solution**: Use `setup_and_build.sh` instead of `quick_cache_build.sh`

### "OCI SDK not installed"

**Solution**: Use `setup_and_build.sh` to install dependencies

### "No databases found"

**Possible causes**:
1. Operations Insights not enabled in compartments
2. Wrong OCI profile
3. Insufficient permissions

**Solution**:
```bash
# Check available profiles
python3 scripts/tenancy_review.py --list-profiles

# Use correct profile
./scripts/setup_and_build.sh --profile your-profile
```

### "Permission denied"

**Solution**:
```bash
# Make scripts executable
chmod +x scripts/*.sh
```

## Scheduling Automatic Cache Refresh

For production environments, schedule daily cache refresh:

```bash
# Add to crontab (runs daily at 2 AM)
0 2 * * * cd /path/to/mcp-oci-opsi && ./scripts/quick_cache_build.sh --profile production >> /tmp/cache_build.log 2>&1
```

## Environment Variables

Scripts respect these environment variables:

- `OCI_CLI_PROFILE`: OCI profile to use (can be overridden with --profile)
- `OCI_REGION`: OCI region (optional override)
- `OCI_COMPARTMENT_ID`: Default compartment (optional)

## Exit Codes

All scripts use standard exit codes:

- `0`: Success
- `1`: Error (check output for details)

## Logging

Scripts output to stdout/stderr. For logging:

```bash
# Log to file
./scripts/setup_and_build.sh 2>&1 | tee setup.log

# Background with logging
nohup ./scripts/quick_cache_build.sh > cache_build.log 2>&1 &
```

---

**Need help?** See the main [TENANCY_REVIEW_GUIDE.md](../TENANCY_REVIEW_GUIDE.md) for detailed documentation.
