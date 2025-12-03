---
name: sql-plan-baselines
description: |
  Manage SQL Plan Baselines for execution plan stability and performance.
  Use this skill when the user asks about:
  - SQL plan baseline management
  - Execution plan stability
  - Plan regression prevention
  - Automatic plan capture
  - SPM (SQL Plan Management) configuration
  This skill helps DBAs maintain consistent SQL performance.
allowed-tools:
  - list_sql_plan_baselines
  - get_sql_plan_baseline
  - load_sql_plan_baselines_from_awr
  - drop_sql_plan_baselines
  - enable_automatic_spm_evolve_task
  - configure_automatic_spm_capture
---

# SQL Plan Baselines Skill

## Purpose
Manage SQL Plan Management (SPM) to ensure execution plan stability and prevent plan regression.

## What are SQL Plan Baselines?
- Stored execution plans for SQL statements
- Prevent optimizer from choosing worse plans
- Enable consistent query performance
- Part of Oracle's SQL Plan Management (SPM)

## When to Use
- User wants to prevent plan regressions
- User needs to capture good plans
- User investigates plan changes
- User configures SPM automation

## Key Concepts

### Plan States
- **ENABLED**: Plan can be used by optimizer
- **ACCEPTED**: Plan verified to perform well
- **FIXED**: Plan always used, ignores cost

### SPM Operations
- **Capture**: Store plans in baseline
- **Evolve**: Test and accept new plans
- **Drop**: Remove unwanted plans

## Recommended Approach

### List Existing Baselines
```
list_sql_plan_baselines(database_id)
```
Filter by `is_enabled` or `is_accepted` status.

### Load Plans from AWR
For critical SQL, capture plans from AWR history:
```
load_sql_plan_baselines_from_awr(
    database_id,
    sql_handle="...",
    begin_snapshot=100,
    end_snapshot=150
)
```

### Enable Automatic Capture
For proactive plan management:
```
configure_automatic_spm_capture(database_id, enabled=True)
```

### Enable Plan Evolution
Let Oracle automatically test new plans:
```
enable_automatic_spm_evolve_task(database_id)
```

## Response Format Guidelines
- Show plan name and SQL handle
- Indicate enabled/accepted status
- Note fixed plans (they override optimization)
- Highlight recently created baselines

## Example Interactions

**User**: "Show all SQL plan baselines"
**Approach**:
1. Call `list_sql_plan_baselines(database_id)`
2. Group by SQL handle
3. Show enabled/accepted status

**User**: "Capture plan for slow SQL"
**Approach**:
1. Identify SQL handle from AWR or SQL ID
2. Get snapshot range covering good execution
3. Call `load_sql_plan_baselines_from_awr()` with parameters
4. Verify plan was captured

**User**: "Enable automatic plan capture"
**Approach**:
1. Explain implications (more storage, maintenance)
2. Call `configure_automatic_spm_capture(enabled=True)`
3. Recommend also enabling evolve task
4. Provide monitoring guidance

**User**: "Remove baseline for SQL X"
**Approach**:
1. Call `list_sql_plan_baselines()` to find exact plan
2. Confirm deletion with user
3. Call `drop_sql_plan_baselines(plan_name="...")`
4. Verify removal

**User**: "Why is my query using a different plan?"
**Approach**:
1. Check if baseline exists: `list_sql_plan_baselines()`
2. Verify baseline is enabled and accepted
3. If fixed=False, optimizer may choose different plan
4. Recommend fixing the baseline if stability needed

## Token Optimization
- Filter baselines by SQL handle when investigating specific SQL
- Use status filters to reduce result size
- Capture plans only for critical SQL statements
