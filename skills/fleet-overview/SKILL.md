---
name: fleet-overview
description: |
  Get instant database fleet overview and statistics without API calls.
  Use this skill when the user asks about:
  - How many databases are in the fleet
  - Database inventory or fleet summary
  - Databases by compartment or type
  - Quick fleet statistics
  This skill uses cached data for instant responses with minimal token usage.
allowed-tools:
  - get_fleet_summary
  - search_databases
  - get_databases_by_compartment
  - get_cached_statistics
  - list_cached_compartments
---

# Fleet Overview Skill

## Purpose
Provide instant database fleet statistics and inventory from local cache.
Zero API calls required - responses are immediate.

## When to Use
- User asks "how many databases do I have?"
- User asks about fleet composition
- User asks about databases in specific compartments
- User needs a quick inventory check

## Recommended Approach

### Step 1: Get Fleet Summary First
Always start with `get_fleet_summary()` - it returns:
- Total database count
- Total host count
- Breakdown by compartment
- Breakdown by database type

### Step 2: Drill Down if Needed
If user needs more detail:
- Use `search_databases(name="partial_name")` for name search
- Use `get_databases_by_compartment(compartment_name="name")` for compartment drill-down
- Use `get_cached_statistics()` for detailed breakdowns

## Response Format Guidelines
Keep responses concise:
- Lead with the key number (e.g., "You have 57 databases")
- Provide breakdown only if requested
- Avoid verbose explanations

## Example Interactions

**User**: "How many databases do I have?"
**Approach**: Call `get_fleet_summary()` and respond with total count

**User**: "Show databases in Production compartment"
**Approach**: Call `get_databases_by_compartment(compartment_name="Production")`

**User**: "Find database named PayDB"
**Approach**: Call `search_databases(name="PayDB")`

## Token Optimization
- These tools return minimal JSON - ideal for token efficiency
- No need to format as tables unless specifically requested
- Single-line responses are preferred for simple queries
