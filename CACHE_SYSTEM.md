# Fast Cache System - Instant Database Inventory

## Overview

The MCP OCI OPSI server now includes a high-performance caching system that provides **instant responses with zero API calls** for database inventory queries. This dramatically reduces token usage and response times.

## Key Benefits

✅ **Instant Responses** - No API calls, sub-millisecond lookups
✅ **Token Efficient** - Minimal data transfer, concise responses
✅ **Hierarchical Scanning** - Includes all child compartments
✅ **Comprehensive** - All databases, hosts, and compartments
✅ **Smart Caching** - 24-hour validity with easy refresh

## Cache Statistics

**Example Cache:**
- **N Databases** across your compartments
- **N Hosts**
- **Compartments:** Your compartment names
- **Location:** `~/.mcp-oci/cache/opsi_cache.json`
- **Shared cache (optional):** set `MCP_CACHE_BACKEND=redis` + `MCP_REDIS_URL` to reuse cache across agents/servers

**Example Database Types:**
- EXTERNAL-NONCDB: X
- EXTERNAL-PDB: X
- ATP-D: X
- ATP-S: X
- ADW-S: X
- ADW-D: X
- MDS-MYSQL: X
- EXTERNAL-MYSQL: X

## Fast Cache Tools (7 new tools)

### 1. get_fleet_summary()
**Ultra-fast fleet overview - ZERO API calls**

```
Claude, show me fleet summary
Claude, how many databases do I have?
Claude, what's in my fleet?
```

Response:
```json
{
  "databases": 150,
  "hosts": 25,
  "by_compartment": {
    "Compartment-A": 60,
    "Compartment-B": 50,
    "Compartment-C": 40
  },
  "by_type": {
    "EXTERNAL-NONCDB": 80,
    "ATP-D": 20,
    ...
  }
}
```

### 2. search_databases(name?, compartment?, limit=20)
**Instant database search**

```
Claude, search for databases named "MYDB"
Claude, find all databases in Production compartment
Claude, search for ATP databases
```

### 3. get_databases_by_compartment(compartment_name)
**Get all databases in a compartment**

```
Claude, show me all databases in Production compartment
Claude, list Development databases
Claude, what databases are in Test?
```

Response (token-efficient):
```json
{
  "compartments": {
    "Production": [
      {"name": "PRODDB01", "type": "EXTERNAL-NONCDB", "version": "19.0.0.0.0", "status": "ACTIVE"},
      {"name": "PRODATP01", "type": "ATP-D", "version": "19c", "status": "ACTIVE"}
    ]
  }
}
```

### 4. get_cached_statistics()
**Detailed statistics**

```
Claude, show me detailed cache statistics
Claude, give me cache metadata
```

### 5. list_cached_compartments()
**List all compartments**

```
Claude, list all compartments
Claude, show me compartment hierarchy
```

### 6. build_database_cache(compartment_ids)
**Build/rebuild cache**

```
Claude, build cache for these compartments: [list of OCIDs]
Claude, rebuild the database cache
```

### 7. refresh_cache_if_needed(max_age_hours=24)
**Check cache validity**

```
Claude, check if cache needs refresh
Claude, is my cache up to date?
```

## Setup Instructions

### Initial Cache Build

**Option 1: Using the build script**
```bash
cd /path/to/mcp_oci_opsi
python3 build_cache.py
```

**Option 2: Via Claude (after MCP server is running)**
```
Claude, build cache for these compartments:
- [Link to Secure Variable: OCI_COMPARTMENT_OCID]
- [Link to Secure Variable: OCI_COMPARTMENT_OCID]
- [Link to Secure Variable: OCI_COMPARTMENT_OCID]
- [Link to Secure Variable: OCI_COMPARTMENT_OCID]
```

### Example Compartments

Configure the cache for your compartments:

1. **Production**
   - OCID: `[Link to Secure Variable: OCI_COMPARTMENT_OCID]`
   - Databases: X

2. **Development**
   - OCID: `[Link to Secure Variable: OCI_COMPARTMENT_OCID]`
   - Databases: X

3. **Test**
   - OCID: `[Link to Secure Variable: OCI_COMPARTMENT_OCID]`
   - Databases: X

4. **Staging**
   - OCID: `[Link to Secure Variable: OCI_COMPARTMENT_OCID]`
   - Databases: X

## Usage Patterns

### Pattern 1: Quick Fleet Overview
```
User: "How many databases do I have?"
Claude: [Calls get_fleet_summary() - instant response]
"You have N databases and N hosts across X compartments."
```

### Pattern 2: Find Specific Database
```
User: "Find the MYDB database"
Claude: [Calls search_databases(name="MYDB") - instant]
"Found MYDB database: EXTERNAL-PDB, 19.0.0.0.0, in Production compartment"
```

### Pattern 3: Compartment Inventory
```
User: "What databases are in the Production compartment?"
Claude: [Calls get_databases_by_compartment("Production") - instant]
"Production compartment has X databases: N EXTERNAL-NONCDB, N ATP-D, N ADW-S"
```

### Pattern 4: Database Search
```
User: "Show me all ATP databases"
Claude: [Calls search_databases(name="ATP") - instant]
"Found N ATP databases: X ATP-D, X ATP-S across your compartments"
```

## Cache Management

### Cache Validity

Cache is valid for **24 hours** by default. After that:

```
Claude, check if cache needs refresh
```

If refresh needed:
```
Claude, rebuild the cache
```

### Manual Refresh

```
Claude, build cache for these compartments: [OCIDs]
```

### Cache Location

**File:** `~/.mcp-oci/cache/opsi_cache.json`

**View cache:**
```bash
cat ~/.mcp-oci/cache/opsi_cache.json | jq '.statistics'
```

## Performance Comparison

### Without Cache (API calls)
- **Response Time:** 2-5 seconds
- **Tokens Used:** ~500-1000 tokens
- **API Calls:** 1-4 calls per query

### With Cache (instant)
- **Response Time:** <50ms
- **Tokens Used:** ~100-200 tokens
- **API Calls:** 0

**Result: 40x faster, 5x fewer tokens**

## Token Efficiency Examples

### Question: "How many databases?"

**Without cache:**
- API call to list_database_insights()
- Returns full response with all metadata
- ~800 tokens

**With cache:**
- Read from local file
- Returns concise summary
- ~150 tokens

**Savings: 81% fewer tokens**

### Question: "Find database X"

**Without cache:**
- API call with filters
- Multiple fields returned
- ~600 tokens

**With cache:**
- Instant lookup
- Essential fields only
- ~120 tokens

**Savings: 80% fewer tokens**

## Architecture

```
┌─────────────┐
│   Claude    │
│   Desktop   │
└──────┬──────┘
       │
       ├─ Fast Cache Tools (7 tools) ──────> Local Cache File
       │  • get_fleet_summary()              (~/.mcp-oci/cache/opsi_cache.json)
       │  • search_databases()
       │  • get_databases_by_compartment()   • Your databases
       │  • get_cached_statistics()          • Your hosts
       │  • list_cached_compartments()       • Your compartments
       │  • refresh_cache_if_needed()        • Updated every 24h
       │  • build_database_cache()
       │
       └─ Standard API Tools (48 tools) ───> OCI API
          • Real-time data                   • Live queries
          • Performance metrics              • AWR reports
          • ADDM/ASH analytics              • Direct DB access
```

## Best Practices

### For Quick Questions
**Use cache tools** - Instant, token-efficient

```
Claude, how many databases?              → get_fleet_summary()
Claude, find database X                   → search_databases()
Claude, show Production databases         → get_databases_by_compartment()
```

### For Real-Time Data
**Use API tools** - Live metrics, performance data

```
Claude, show SQL performance        → API calls
Claude, get AWR report              → API calls
Claude, analyze wait events         → API calls
```

### For Hybrid Queries
**Start with cache, then API for details**

```
1. Claude, find database X          → Cache (instant)
2. Claude, show X's performance     → API (detailed metrics)
```

## Troubleshooting

### Cache Not Found

```
Claude, build cache for compartments: [OCIDs]
```

### Cache Expired

```
Claude, check cache validity
Claude, rebuild cache
```

### Wrong Compartments

Edit `build_cache.py` and rebuild:
```python
DEMO_COMPARTMENTS = [
    "[Link to Secure Variable: OCI_COMPARTMENT_OCID]",
    "[Link to Secure Variable: OCI_COMPARTMENT_OCID]",
]
```

Then:
```bash
python3 build_cache.py
```

## Summary

The cache system provides:

✅ **55 Total Tools** (48 API + 7 Cache)
✅ **Your Databases** instantly accessible
✅ **Your Hosts** instantly accessible
✅ **Zero latency** for inventory queries
✅ **80% token savings** for common questions
✅ **24-hour validity** with easy refresh
✅ **Hierarchical scanning** of all child compartments

**Perfect for:**
- Fleet overviews
- Database discovery
- Quick inventories
- Compartment queries
- Database searches

**Use API tools for:**
- Real-time metrics
- Performance analysis
- AWR/ADDM reports
- Live monitoring
- Diagnostic data

---

**Status: ✅ CACHE READY**

Build the cache with your databases and compartments to get started.
