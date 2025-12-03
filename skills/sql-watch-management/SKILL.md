---
name: sql-watch-management
description: |
  Enable, disable, and manage SQL Watch for detailed SQL monitoring.
  Use this skill when the user asks about:
  - Enabling SQL Watch on databases
  - Checking SQL Watch status
  - Bulk SQL Watch operations
  - SQL monitoring configuration
  SQL Watch is required for SQL-level insights in Operations Insights.
allowed-tools:
  - get_sqlwatch_status
  - enable_sqlwatch
  - disable_sqlwatch
  - get_sqlwatch_work_request
  - enable_sqlwatch_bulk
  - disable_sqlwatch_bulk
  - check_sqlwatch_work_requests
  - check_sqlwatch_status_bulk
---

# SQL Watch Management Skill

## Purpose
Manage SQL Watch feature for detailed SQL-level monitoring in Operations Insights.

## What is SQL Watch?
SQL Watch is a Database Management feature that:
- Captures SQL execution statistics
- Enables SQL-level insights in Operations Insights
- Required for SQL performance analysis tools
- Minimal overhead on database performance

## When to Use
- User wants to enable SQL monitoring
- User needs to check SQL Watch status
- User wants to enable across multiple databases
- User troubleshoots SQL insights availability

## Recommended Approach

### Check Status First
Always verify current status before changes:
```
get_sqlwatch_status(database_id)
```

### Enable on Single Database
```
enable_sqlwatch(database_id)
```
Returns work request ID for tracking.

### Enable Across Fleet
For bulk operations:
```
enable_sqlwatch_bulk(compartment_id, dry_run=True)
```
Always use `dry_run=True` first to preview changes.

### Track Operations
Async operations return work request IDs:
```
get_sqlwatch_work_request(work_request_id)
```

## Pre-Enablement Checklist
Before enabling SQL Watch:
1. Verify Database Management is enabled
2. Check database type compatibility
3. Review any licensing requirements
4. Consider impact during peak hours

## Response Format Guidelines
- Report current status clearly
- Show work request status for async operations
- Indicate estimated completion time
- Warn about any prerequisites

## Example Interactions

**User**: "Is SQL Watch enabled on my databases?"
**Approach**:
1. Call `check_sqlwatch_status_bulk(compartment_id)`
2. Summarize enabled vs disabled counts
3. List databases without SQL Watch

**User**: "Enable SQL Watch on all databases"
**Approach**:
1. Call `enable_sqlwatch_bulk(compartment_id, dry_run=True)` first
2. Show preview of changes
3. If confirmed, call with `dry_run=False`
4. Return work request IDs for tracking

**User**: "Enable SQL Watch on database X"
**Approach**:
1. Call `get_sqlwatch_status(database_id)` to verify current state
2. If not enabled, call `enable_sqlwatch(database_id)`
3. Return work request ID
4. Explain it may take a few minutes

**User**: "Check status of SQL Watch enablement"
**Approach**:
1. Call `check_sqlwatch_work_requests(compartment_id, hours_back=1)`
2. Show status of recent operations
3. Identify any failures

## Token Optimization
- Use bulk status check instead of individual calls
- Always dry_run first for bulk operations
- Track work requests only when needed
