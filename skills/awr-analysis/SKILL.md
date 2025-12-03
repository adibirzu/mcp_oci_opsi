---
name: awr-analysis
description: |
  Deep AWR (Automatic Workload Repository) analysis for performance tuning.
  Use this skill when the user asks about:
  - AWR reports and metrics
  - Database wait events over time
  - System statistics and trends
  - CPU usage patterns
  - Parameter changes
  This skill provides detailed AWR-based performance analysis.
allowed-tools:
  - list_awr_snapshots
  - get_awr_report
  - summarize_awr_db_metrics
  - summarize_awr_db_cpu_usages
  - summarize_awr_db_wait_event_buckets
  - summarize_awr_db_sysstats
  - summarize_awr_db_parameter_changes
  - get_database_system_statistics
  - get_database_io_statistics
---

# AWR Analysis Skill

## Purpose
Provide detailed AWR-based database performance analysis.

## When to Use
- User needs historical performance data
- User wants to analyze specific time periods
- User needs detailed wait event analysis
- User wants to track parameter changes
- User needs system statistics trends

## AWR Analysis Workflow

### Step 1: Identify Snapshot Range
Always start by listing available snapshots:
```
list_awr_snapshots(database_id, awr_db_id, time_greater_than, time_less_than)
```

### Step 2: Choose Analysis Type
Select the appropriate tool based on user's question:
- **General Report**: `get_awr_report()`
- **Wait Events**: `summarize_awr_db_wait_event_buckets()`
- **CPU Analysis**: `summarize_awr_db_cpu_usages()`
- **System Stats**: `summarize_awr_db_sysstats()`
- **Parameter Changes**: `summarize_awr_db_parameter_changes()`

### Step 3: Correlate Findings
Cross-reference multiple AWR data points for root cause analysis.

## Getting AWR Database ID
The AWR database ID (awr_db_id) is required for AWR operations:
1. Get managed database details: `get_managed_database_details(database_id)`
2. The AWR DB ID is typically the DBID from the database

## Response Format Guidelines
- Summarize key metrics first
- Highlight anomalies and changes
- Compare with baseline periods when available
- Focus on actionable insights

## Example Interactions

**User**: "Show me AWR snapshots for last 24 hours"
**Approach**:
1. Calculate time range (now - 24 hours)
2. Call `list_awr_snapshots()` with time filters
3. Return snapshot IDs and timestamps

**User**: "What wait events are affecting performance?"
**Approach**:
1. Get snapshot range
2. Call `summarize_awr_db_wait_event_buckets()`
3. Rank wait events by time waited
4. Identify top bottlenecks

**User**: "Were any parameters changed recently?"
**Approach**:
1. Call `summarize_awr_db_parameter_changes()` for recent snapshots
2. List changed parameters with old/new values
3. Correlate with any performance changes

**User**: "Analyze CPU usage over time"
**Approach**:
1. Call `summarize_awr_db_cpu_usages()` for time range
2. Show CPU consumption trends
3. Identify peak usage periods

## Token Optimization
- Request HTML format for AWR reports (more structured)
- Use specific AWR summary tools instead of full reports when possible
- Filter by time range to limit data volume
- Focus on top 5-10 items in rankings
