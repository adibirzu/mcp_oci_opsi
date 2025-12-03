---
name: storage-management
description: |
  Manage and monitor database storage including tablespaces and data files.
  Use this skill when the user asks about:
  - Tablespace usage and availability
  - Storage alerts and warnings
  - Data file management
  - Storage growth and trends
  - Database resource utilization
  This skill helps DBAs manage storage proactively.
allowed-tools:
  - get_tablespace_usage
  - list_tablespaces
  - get_tablespace
  - list_table_statistics
  - get_database_resource_usage
---

# Storage Management Skill

## Purpose
Monitor and manage database storage including tablespaces and data files.

## When to Use
- User asks about tablespace usage
- User needs storage alerts
- User wants table statistics
- User investigates storage issues

## Key Concepts

### Tablespaces
- Logical storage containers in Oracle
- Critical metrics: size, used, free, auto-extend status
- Warning threshold: 80% used
- Critical threshold: 90% used

### Data Files
- Physical files backing tablespaces
- Can be auto-extensible or fixed size
- Location and size matter for I/O performance

## Recommended Approach

### For Quick Storage Check
Use `get_tablespace_usage(database_id)`:
- Returns all tablespaces with usage metrics
- Shows percentage used
- Identifies tablespaces needing attention

### For Detailed Analysis
Use `list_tablespaces()` and `get_tablespace()`:
- Returns detailed tablespace configuration
- Shows auto-extend settings
- Lists constituent data files

### For Table-Level Analysis
Use `list_table_statistics()`:
- Shows table sizes
- Identifies large tables
- Helps with space reclamation planning

## Response Format Guidelines
- Lead with tablespaces above 80% usage
- Sort by criticality (highest used first)
- Include auto-extend status
- Provide growth rate if available

## Example Interactions

**User**: "How much storage is left?"
**Approach**:
1. Call `get_tablespace_usage(database_id)`
2. Calculate total free space
3. Highlight any tablespaces above threshold

**User**: "Which tablespaces are running out of space?"
**Approach**:
1. Call `get_tablespace_usage(database_id)`
2. Filter for usage > 80%
3. Check auto-extend status
4. Recommend actions (extend or add datafile)

**User**: "Show largest tables in schema X"
**Approach**:
1. Call `list_table_statistics()` with schema filter
2. Sort by size descending
3. Identify candidates for cleanup or archival

**User**: "Is SYSTEM tablespace healthy?"
**Approach**:
1. Call `get_tablespace(tablespace_name="SYSTEM")`
2. Check usage percentage
3. Verify auto-extend settings
4. Review recent growth

## Token Optimization
- Use `get_tablespace_usage()` for overview
- Use `get_tablespace()` only for specific tablespace details
- Filter table statistics by schema when possible
