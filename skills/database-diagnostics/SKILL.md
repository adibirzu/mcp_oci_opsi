---
name: database-diagnostics
description: |
  Diagnose database issues, analyze ADDM findings, and troubleshoot performance.
  Use this skill when the user asks about:
  - Database performance problems
  - ADDM recommendations
  - AWR report analysis
  - Wait events and bottlenecks
  - Alert log issues
  - Permission or configuration problems
  This skill helps identify and resolve database issues.
allowed-tools:
  - get_addm_report
  - get_ash_analytics
  - get_awr_report
  - list_awr_snapshots
  - summarize_addm_db_findings
  - list_alert_logs
  - diagnose_opsi_permissions
  - get_comprehensive_diagnostics
  - check_database_insights_configuration
---

# Database Diagnostics Skill

## Purpose
Diagnose database issues using ADDM, AWR, ASH, and alert logs.

## When to Use
- User reports database performance problems
- User wants to understand bottlenecks
- User needs ADDM recommendations
- User asks about wait events
- User sees errors or alerts

## Diagnostic Workflow

### Step 1: Quick Assessment
Start with `summarize_addm_db_findings()` for fleet-wide findings, or `get_comprehensive_diagnostics()` for configuration issues.

### Step 2: AWR Analysis
1. Get snapshot range: `list_awr_snapshots(database_id, awr_db_id)`
2. Generate report: `get_awr_report(begin_snapshot_id, end_snapshot_id)`
3. Review key sections: Top Events, Top SQL, Instance Efficiency

### Step 3: Deep Dive
- For wait events: `get_ash_analytics(wait_class="User I/O")`
- For ADDM findings: `get_addm_report()`
- For recent errors: `list_alert_logs(log_level="CRITICAL")`

## Pre-Diagnostic Checklist
1. Identify the database OCID
2. Get AWR database ID (required for AWR/ADDM tools)
3. Determine time range of the issue
4. Check if Operations Insights is enabled

## Common Diagnostic Scenarios

### High CPU Usage
1. Get ASH data filtered by CPU wait class
2. Identify top SQL by CPU
3. Check ADDM for CPU-related findings

### Slow Queries
1. List AWR snapshots covering the slow period
2. Get ADDM report for the snapshot range
3. Analyze SQL-related ADDM findings

### Storage Issues
1. Check tablespace usage: `get_tablespace_usage()`
2. Review storage forecasts
3. Identify growth patterns

### Permission Issues
1. Run `diagnose_opsi_permissions(compartment_id)`
2. Review missing IAM policies
3. Follow remediation recommendations

## Response Format Guidelines
- Lead with the primary finding or issue
- Prioritize actionable recommendations
- Include ADDM finding IDs for reference
- Group related issues together

## Example Interactions

**User**: "My database is slow, what's wrong?"
**Approach**:
1. Call `summarize_addm_db_findings()` for quick assessment
2. Call `get_ash_analytics()` to identify top wait events
3. If CPU-related, get top SQL by CPU
4. Provide prioritized recommendations

**User**: "Show ADDM recommendations"
**Approach**:
1. Get snapshot range for desired period
2. Call `get_addm_report(begin_snapshot_id, end_snapshot_id)`
3. Format findings by impact and priority

**User**: "Why am I getting permission errors?"
**Approach**:
1. Call `diagnose_opsi_permissions(compartment_id)`
2. List specific missing permissions
3. Provide IAM policy statements to fix

## Token Optimization
- Use `summarize_addm_db_findings()` for fleet-wide view before drilling down
- Filter alert logs by severity level
- Specify narrow time ranges when possible
