# DBA Skills Guide

This guide explains how to use the Skills feature in the MCP OCI OPSI server for enhanced DBA operations with minimal token usage and maximum accuracy.

## Two Types of Skills

The OPSI MCP server provides two complementary skill systems:

1. **Markdown Skills (v1)** - Declarative skill files that provide guidance and context
2. **Programmatic Skills (v2)** - Composable Python classes that provide intelligent analysis

### Quick Comparison

| Feature | Markdown Skills (v1) | Programmatic Skills (v2) |
|---------|---------------------|-------------------------|
| Format | SKILL.md files | Python classes |
| Purpose | Provide guidance | Perform analysis |
| Response | Skill context text | Structured data |
| Speed | Instant (file read) | Tiered (see below) |
| Use Case | Tool selection guidance | Direct database analysis |

---

## Programmatic Skills (v2) - NEW

The programmatic skills provide intelligent, composable analysis capabilities following the [skillz pattern](https://github.com/intellectronica/skillz).

### Available Programmatic Skills

| Skill | Tier | Response Time | Description |
|-------|------|---------------|-------------|
| `DatabaseDiscoverySkill` | 1 | < 100ms | Fast database fleet discovery using cached data |
| `PerformanceAnalysisSkill` | 2 | 1-30s | CPU, memory, I/O analysis with trends |
| `CostOptimizationSkill` | 2 | 1-5s | Identify cost-saving opportunities |

### Skill Tiers

- **Tier 1 (Cache-based)**: Uses local cache, instant response, zero API calls
- **Tier 2 (API-based)**: Makes OPSI API calls, 1-30 second response
- **Tier 3 (Database)**: Connects to database directly (future)

### Programmatic Skill Tools

#### Discovery Tools (Tier 1 - INSTANT)

```python
# Discover all databases with filters
skill_discover_databases(
    compartment_id="[Link to Secure Variable: OCI_COMPARTMENT_OCID]",  # optional
    region="us-ashburn-1",                   # optional
    db_type="adb",                           # optional: adb, base, exadata
    limit=50                                 # optional
)

# Get high-level fleet summary
skill_get_fleet_summary()
# Returns: total, by_type, by_state, by_region, total_cpu, total_storage

# Search databases by name or OCID
skill_search_databases(query="prod", limit=20)

# Get database by exact name
skill_get_database_by_name(name="PRODDB")
```

#### Performance Tools (Tier 2)

```python
# Analyze CPU usage with trend detection
skill_analyze_cpu_usage(
    database_id="[Link to Secure Variable: OCI_DATABASE_INSIGHT_OCID]",
    hours_back=24
)
# Returns: current_usage, average_usage, peak_usage, trend, recommendations

# Analyze memory usage
skill_analyze_memory_usage(database_id="...", hours_back=24)

# Analyze I/O performance
skill_analyze_io_performance(database_id="...", hours_back=24)

# Get comprehensive performance summary (all metrics)
skill_get_performance_summary(database_id="...", hours_back=24)
# Returns CPU, memory, and I/O analysis in one call
```

#### Cost Optimization Tools (Tier 2)

```python
# Find cost-saving opportunities
skill_find_cost_opportunities(
    compartment_id=None,        # optional filter
    min_savings_usd=50.0,       # minimum savings threshold
    limit=20
)
# Identifies: rightsizing, scheduling, storage, unused resources

# Get savings summary
skill_get_savings_summary(compartment_id=None)
# Returns: total_opportunities, total_monthly_savings, by_type, by_confidence
```

#### Skill Discovery

```python
# List all programmatic skills
list_programmatic_skills()

# Get skill recommendations for a query
get_skill_recommendations("What databases are over-provisioned?")
# Returns recommended skills and tools to use
```

### Usage Example

```python
# 1. Start with fleet discovery (Tier 1 - instant)
summary = skill_get_fleet_summary()
# → {"total": 42, "by_type": {"adb": 15, "base": 27}, ...}

# 2. Find a specific database
db = skill_get_database_by_name("PRODDB")
# → {"ocid": "[Link to Secure Variable: OCI_RESOURCE_OCID]", "name": "PRODDB", "db_type": "adb", ...}

# 3. Analyze its performance (Tier 2)
perf = skill_get_performance_summary(db["ocid"], hours_back=24)
# → {"cpu": {"current": 45, "peak": 78, "trend": "stable"}, ...}

# 4. Find cost opportunities across fleet
savings = skill_get_savings_summary()
# → {"total_monthly_savings": 1250.00, "top_opportunities": [...]}
```

---

## Markdown Skills (v1)

Markdown skills provide guidance and context for DBA workflows.

### What are Markdown Skills?

Skills are specialized instruction sets that teach Claude how to perform specific DBA tasks. They follow the [Anthropic Skills specification](https://github.com/anthropics/skills) and provide:

- **Focused Guidance**: Ta[Link to Secure Variable: OPENAI_API_KEY] instructions for common DBA workflows
- **Tool Recommendations**: Which MCP tools to use for each scenario
- **Best Practices**: Optimal approaches and examples
- **Token Optimization**: Guidance for minimal token consumption

## Available Skills

| Skill | Description | Key Tools |
|-------|-------------|-----------|
| `fleet-overview` | Instant database fleet statistics | get_fleet_summary, search_databases |
| `sql-performance` | SQL analysis and tuning | summarize_sql_insights, get_top_sql_by_metric |
| `capacity-planning` | Resource forecasting | get_resource_forecast_with_chart |
| `database-diagnostics` | ADDM, AWR, troubleshooting | get_addm_report, diagnose_opsi_permissions |
| `awr-analysis` | Deep AWR performance analysis | list_awr_snapshots, get_awr_report |
| `host-monitoring` | Host resource monitoring | get_host_resource_statistics |
| `storage-management` | Tablespace and storage | get_tablespace_usage, list_tablespaces |
| `security-audit` | Users, roles, privileges | list_users, list_roles |
| `sql-watch-management` | SQL Watch enablement | enable_sqlwatch, check_sqlwatch_status_bulk |
| `sql-plan-baselines` | SPM management | list_sql_plan_baselines |
| `multi-tenancy` | Multi-profile operations | list_oci_profiles_enhanced |
| `exadata-monitoring` | Exadata systems | list_exadata_insights |

## How to Use Skills

### For Clients Supporting Skills (Claude Code, Claude.ai)

Skills are automatically loaded from the `skills/` directory. The LLM can access skill context via:

```
list_available_skills()
get_skill_context("fleet-overview")
get_skill_for_query("How many databases do I have?")
```

### For Clients Not Supporting Skills

Use the skill tools to get context manually:

1. **Find the right skill**:
   ```
   get_skill_for_query("Show me slow queries")
   ```
   Returns: `{"matched_skill": "sql-performance", "context": "...", ...}`

2. **Get skill guidance**:
   ```
   get_skill_context("sql-performance")
   ```
   Returns full instructions, recommended tools, and examples.

3. **Follow the guidance** to complete the task with optimal tools.

## Quick Reference

Use `get_quick_reference()` for a condensed tool reference:

```python
get_quick_reference("sql")
# Returns SQL-related tools and their uses

get_quick_reference()
# Returns all categories: fleet, sql, capacity, diagnostics, storage, security
```

## Token Optimization

The MCP server is designed for minimal token usage:

### Token-Efficient Tools (Zero API Calls)
These tools use local cache - instant response, minimal tokens:
- `get_fleet_summary()` - Fleet overview
- `search_databases(name="...")` - Database search
- `get_databases_by_compartment("...")` - By compartment
- `get_cached_statistics()` - Detailed stats
- `list_cached_compartments()` - All compartments

### Best Practices
1. **Start with cache tools** before API-based tools
2. **Use limit parameters** to reduce result size
3. **Use summary tools** before detail tools
4. **Skip charts** unless visualization is needed
5. **Filter by time range** to limit data volume

Get tips with:
```python
get_token_optimization_tips()
```

## Skill File Format

Skills follow the Anthropic Skills specification. Each skill is a directory containing `SKILL.md`:

```markdown
---
name: skill-name
description: |
  Description of when to use this skill...
allowed-tools:
  - tool1
  - tool2
---

# Skill Title

## Purpose
What this skill helps accomplish...

## When to Use
Scenarios for using this skill...

## Recommended Approach
Step-by-step guidance...

## Example Interactions
User: "question"
Approach: How to handle it...
```

## Creating Custom Skills

1. Create a directory in `skills/`:
   ```bash
   mkdir skills/my-custom-skill
   ```

2. Create `SKILL.md` with YAML frontmatter and instructions

3. Restart the MCP server to load new skills

## Skills Directory Structure

```
skills/
├── fleet-overview/
│   └── SKILL.md
├── sql-performance/
│   └── SKILL.md
├── capacity-planning/
│   └── SKILL.md
├── database-diagnostics/
│   └── SKILL.md
├── awr-analysis/
│   └── SKILL.md
├── host-monitoring/
│   └── SKILL.md
├── storage-management/
│   └── SKILL.md
├── security-audit/
│   └── SKILL.md
├── sql-watch-management/
│   └── SKILL.md
├── sql-plan-baselines/
│   └── SKILL.md
├── multi-tenancy/
│   └── SKILL.md
└── exadata-monitoring/
    └── SKILL.md
```

## Integration with MCP Tools

Skills are integrated into the MCP server via 5 new tools:

1. **`list_available_skills()`** - List all skills
2. **`get_skill_context(skill_name)`** - Get skill details
3. **`get_skill_for_query(query)`** - Auto-detect skill for query
4. **`get_quick_reference(category)`** - Quick tool reference
5. **`get_token_optimization_tips()`** - Optimization guidance

## Example Workflow

### User asks: "What SQL statements are consuming the most CPU?"

1. **Auto-detect skill**:
   ```
   get_skill_for_query("What SQL statements are consuming the most CPU?")
   → matched_skill: "sql-performance"
   ```

2. **Skill recommends**:
   - Use `get_top_sql_by_metric(metric="CPU", top_n=10)`
   - Requires AWR database ID and snapshot range
   - First get snapshots with `list_awr_snapshots()`

3. **Execute tools** following skill guidance

4. **Result**: Efficient workflow with minimal token usage

## Benefits

- **Reduced Tokens**: Skills guide to the most efficient tools
- **Improved Accuracy**: Best practices built into guidance
- **Consistent Results**: Standardized approaches for common tasks
- **Self-Documenting**: Skills explain their own usage
- **Extensible**: Easy to add custom skills for specific needs
