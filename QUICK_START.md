# Quick Start Guide - Get Running in 5 Minutes

## Overview

This guide will get you up and running with the MCP OCI OPSI server in just 5 minutes, with optimized performance and minimal token usage.

## Step 1: Prerequisites (1 minute)

Check that you have:

```bash
# 1. Python 3.10 or higher
python3 --version

# 2. OCI CLI configured
ls ~/.oci/config

# 3. Git (to clone the repository)
git --version
```

If you don't have OCI CLI configured:
```bash
oci setup config
```

## Step 2: One-Command Setup (2 minutes) ⚡ EASIEST!

**The setup script does everything for you: install dependencies AND build cache!**

```bash
# Clone the repository
cd ~/dev  # or your preferred directory
git clone https://github.com/yourusername/mcp-oci-opsi.git
cd mcp-oci-opsi

# Run complete setup (creates venv, installs deps, builds cache)
./scripts/setup_and_build.sh
```

**Or with a specific profile:**
```bash
./scripts/setup_and_build.sh --profile emdemo
```

**Alternative: Manual Installation**

If you prefer to install manually:

```bash
# Create virtual environment and install
python3 -m venv .venv
source .venv/bin/activate
pip install -e .

# Optional: Install database features
pip install -e ".[database]"

# Build cache
./scripts/quick_cache_build.sh
```

Wait for it to complete. You'll see:
```
================================================================================
✅ TENANCY REVIEW COMPLETE
================================================================================

NEXT STEPS:
1. Use fast cache tools for instant database queries
2. Try: 'How many databases do I have?'
3. Try: 'Find database X'
4. Try: 'Show me databases in compartment X'
```

## Step 4: Configure MCP Server (30 seconds)

### For Claude Desktop

Add to your Claude Desktop config (`~/Library/Application Support/Claude/claude_desktop_config.json` on macOS):

```json
{
  "mcpServers": {
    "oci-opsi": {
      "command": "python",
      "args": [
        "-m",
        "mcp_oci_opsi.main"
      ],
      "cwd": "/Users/yourname/dev/mcp-oci-opsi",
      "env": {
        "OCI_CLI_PROFILE": "DEFAULT"
      }
    }
  }
}
```

### For Claude Code

Add to MCP settings in Claude Code:

```json
{
  "oci-opsi": {
    "command": "python",
    "args": ["-m", "mcp_oci_opsi.main"],
    "cwd": "/Users/yourname/dev/mcp-oci-opsi",
    "env": {
      "OCI_CLI_PROFILE": "DEFAULT"
    }
  }
}
```

**Restart Claude Desktop or Claude Code**

## Step 5: Test (30 seconds)

Try these instant queries in Claude:

```
1. "How many databases do I have?"
   → Should return instantly with your database count

2. "Find database ECREDITS" (or your database name)
   → Should find it instantly

3. "Show me all databases in the Production compartment" (or your compartment)
   → Should list them instantly
```

## 🎉 You're Done!

You now have:
- ✅ Fast cache with instant responses (< 50ms)
- ✅ 80% token usage reduction for inventory queries
- ✅ Zero API calls for database searches
- ✅ 58 MCP tools ready to use
- ✅ Comprehensive inventory of your OCI environment

## 🔒 Security Note

**IMPORTANT**: Cache files contain sensitive OCI data and are automatically protected:

- ✅ **Cache location**: `~/.mcp_oci_opsi_cache.json` (home directory, outside git)
- ✅ **Reports location**: `~/.mcp_oci_opsi/tenancy_review_*.json`
- ✅ **Protected by .gitignore**: Never accidentally committed
- ✅ **User-specific**: Isolated to your account

**Never commit**:
- Cache files (`*_cache.json`)
- Tenancy reports (`tenancy_review_*.json`)
- Credentials (`.env`, `*.pem`)
- Logs (`*.log`)

📖 **See [SECURITY.md](SECURITY.md) for complete security guidelines**

## What's Next?

### Try These Common Queries

#### Fleet Overview
```
"Show me fleet summary"
"What types of databases do I have?"
"How many databases are in each compartment?"
```

#### Database Search
```
"Find all ATP databases"
"Search for databases with 'PROD' in the name"
"Show me External databases"
```

#### Performance Analysis
```
"Show me SQL statistics for the past 7 days"
"Get ADDM findings for database X"
"What are the top SQL statements by CPU?"
```

#### Capacity Planning
```
"Forecast storage for the next 30 days"
"Show me CPU capacity trends"
"Will I run out of resources?"
```

#### Real-Time Monitoring
```
"Show me CRITICAL alert logs"
"List failed database jobs"
"Get current session information"
```

### Explore the Documentation

- **[DBA_DEMO_QUESTIONS.md](DBA_DEMO_QUESTIONS.md)** - 141 example questions you can ask
- **[TENANCY_REVIEW_GUIDE.md](TENANCY_REVIEW_GUIDE.md)** - Complete guide to the tenancy review
- **[CACHE_SYSTEM.md](CACHE_SYSTEM.md)** - Deep dive into the cache system
- **[README.md](README.md)** - Full documentation and all 58 tools

## Troubleshooting

### "OCI config not found"
```bash
# Configure OCI CLI
oci setup config

# Verify it works
oci iam region list
```

### "No databases found"
```bash
# Check you're using the right profile
python3 scripts/tenancy_review.py --list-profiles

# Use the correct profile
./scripts/quick_cache_build.sh --profile your-profile
```

### "Cache is stale"
```bash
# Rebuild the cache
./scripts/quick_cache_build.sh
```

### MCP Server Not Connecting
1. Verify the `cwd` path in your MCP config
2. Check Python path is correct
3. Restart Claude Desktop/Code
4. Check logs in Claude Desktop/Code

## Pro Tips

### 1. Start with Cache Queries
For fast responses and low token usage:
```
Claude, how many databases?        (instant, ~150 tokens)
Claude, find database X             (instant, ~120 tokens)
Claude, show Production databases   (instant, ~200 tokens)
```

### 2. Then Use API for Details
For real-time data:
```
Claude, show SQL statistics         (2-3s, ~600 tokens)
Claude, get AWR report              (3-5s, ~800 tokens)
Claude, analyze wait events         (2-4s, ~500 tokens)
```

### 3. Combine for Best Results
```
Step 1: "Find database PRODDB"      (instant - from cache)
Step 2: "Show me its SQL stats"     (detailed - from API)
```

### 4. Keep Cache Fresh
```bash
# Set up daily cache refresh (optional)
# Add to crontab:
0 2 * * * cd /path/to/mcp-oci-opsi && ./scripts/quick_cache_build.sh
```

## Performance Comparison

### Inventory Query: "How many databases do I have?"

| Metric | Without Cache | With Cache | Improvement |
|--------|---------------|------------|-------------|
| Response Time | 3.2 seconds | **45ms** | **71x faster** |
| API Calls | 4 calls | **0 calls** | **100% reduction** |
| Tokens Used | 842 tokens | **156 tokens** | **81% savings** |

### Real-World Impact

For the **18 fast inventory questions** in DBA_DEMO_QUESTIONS.md:
- **Before**: ~14,400 tokens total
- **After**: ~2,700 tokens total
- **Savings**: **~11,700 tokens (81% reduction)**

## Summary

You've completed:
1. ✅ Installation (2 minutes)
2. ✅ Tenancy review (2 minutes)
3. ✅ MCP configuration (30 seconds)
4. ✅ Testing (30 seconds)

**Total time: ~5 minutes**

You now have:
- 🚀 Instant database inventory queries
- 💰 80% token usage reduction
- 📊 58 powerful MCP tools
- 🎯 Optimized for all 141 DBA demo questions

## Getting Help

- **Documentation**: Check the docs in this repository
- **Issues**: Report bugs at [GitHub Issues](https://github.com/yourusername/mcp-oci-opsi/issues)
- **Examples**: See [DBA_DEMO_QUESTIONS.md](DBA_DEMO_QUESTIONS.md) for 141 example queries

---

**Happy querying! 🎉**

Remember to rebuild your cache periodically:
```bash
./scripts/quick_cache_build.sh
```
