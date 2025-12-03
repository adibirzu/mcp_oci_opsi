---
name: sql-performance
description: |
  Analyze SQL performance, identify problematic queries, and get tuning insights.
  Use this skill when the user asks about:
  - Top SQL queries by CPU, elapsed time, or I/O
  - SQL performance degradation or anomalies
  - SQL plan changes or execution plan analysis
  - SQL tuning recommendations
  - ADDM findings for SQL issues
  This skill provides advanced SQL analytics from Operations Insights.
allowed-tools:
  - summarize_sql_statistics
  - summarize_sql_insights
  - summarize_sql_plan_insights
  - get_sql_insight_details
  - get_top_sql_by_metric
  - list_sql_texts
  - summarize_addm_db_findings
---

# SQL Performance Analysis Skill

## Purpose
Identify SQL performance issues, analyze execution plans, and provide tuning insights.

## When to Use
- User asks about slow queries
- User wants to find top resource-consuming SQL
- User needs SQL plan analysis
- User wants ADDM SQL-related findings

## Recommended Approach

### For Top SQL Queries
Use `get_top_sql_by_metric()` with parameters:
- `metric`: CPU, ELAPSED_TIME, BUFFER_GETS, or DISK_READS
- `top_n`: Number of queries to return (default 10)
- Requires AWR database ID and snapshot range

### For SQL Anomaly Detection
Use `summarize_sql_insights()` with:
- `database_time_pct_greater_than`: Filter to high-impact SQL (e.g., 1.0 for >1%)
- Returns SQL with performance anomalies and trends

### For Plan Analysis
Use `summarize_sql_plan_insights()` with:
- `sql_identifier`: The specific SQL ID to analyze
- Returns plan changes, performance comparison across plans

### For Detailed Investigation
Use `get_sql_insight_details()` for comprehensive analysis of a specific SQL statement.

## Pre-Query Checklist
Before SQL analytics:
1. Verify SQL Watch is enabled: `get_sqlwatch_status(database_id)`
2. Get AWR snapshot range: `list_awr_snapshots(database_id, awr_db_id)`
3. Use recent time range (last 7 days recommended)

## Response Format Guidelines
- Present top SQL in ranked format with key metrics
- Highlight degrading SQL statements
- Include SQL_ID for reference
- Provide actionable insights, not raw numbers

## Example Interactions

**User**: "What are the top CPU consuming queries?"
**Approach**:
1. Get AWR snapshots to determine snapshot range
2. Call `get_top_sql_by_metric(metric="CPU", top_n=10)`
3. Format results showing SQL_ID, CPU time, executions

**User**: "Is any SQL degrading in performance?"
**Approach**:
1. Call `summarize_sql_insights()` with recent time range
2. Look for SQL with degrading trends
3. For degraded SQL, call `summarize_sql_plan_insights()` to check for plan changes

**User**: "Why is SQL xyz123 slow?"
**Approach**:
1. Call `get_sql_insight_details(sql_identifier="xyz123")`
2. Call `summarize_sql_plan_insights(sql_identifier="xyz123")`
3. Correlate execution time with plan changes

## Token Optimization
- Always specify time ranges to limit data volume
- Use `top_n` parameter to limit results
- Focus on actionable insights, not raw metrics
