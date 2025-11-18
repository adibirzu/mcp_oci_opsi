# Operations Insights Demo Script Guide

## Overview

The `demo_opsi_features.py` script demonstrates **15 key Operations Insights capabilities** with real data from your OCI environment.

## What It Demonstrates

### Database Insights (2 prompts)
1. **List Database Insights** - All databases with Operations Insights enabled
2. **SQL Performance Statistics** - Most resource-intensive SQL statements

### Host Insights (13 prompts)
3. **List Host Insights** - All monitored hosts
4. **CPU Forecast (30 days)** - ML-based CPU capacity predictions
5. **Memory Forecast (15 days)** - Memory capacity predictions
6. **CPU Capacity Trends** - Historical CPU usage patterns
7. **Current Resource Usage** - Real-time CPU usage across hosts
8. **Memory Statistics** - Memory utilization metrics
9. **Disk I/O Statistics** - Disk read/write performance
10. **Network Usage Trends** - Network throughput over time
11. **Top CPU Processes** - Most resource-intensive processes
12. **Storage Forecast** - Storage capacity predictions
13. **High CPU Utilization** - Hosts with high CPU usage
14. **SQL Performance Issues** - SQL statements with degrading performance
15. **Overall Health Summary** - Complete infrastructure health overview

## Running the Demo

### Quick Start

```bash
cd /Users/abirzu/dev/mcp_oci_opsi
source .venv/bin/activate
python3 demo_opsi_features.py
```

### What You'll See

The script will:
- ✅ Make 15 different API calls to Operations Insights
- ✅ Display results in a formatted, readable way
- ✅ Show metrics like CPU usage, memory, disk I/O, network traffic
- ✅ Identify performance issues and degrading SQL statements
- ✅ Provide forecasts and capacity planning data

### Sample Output

```
================================================================================
OCI OPERATIONS INSIGHTS MCP SERVER - FEATURE DEMO
================================================================================

Compartment: ocid1.compartment.oc1..aaaa...
Time Range: 2025-11-11T00:00:00Z to 2025-11-18T00:00:00Z
Duration: 7 days

================================================================================
1. List Database Insights in Compartment
================================================================================
PROMPT: Show me all databases with Operations Insights enabled

✅ Success! Found 5 items

  Item 1:
    database_display_name: SALES-XA-WD_6
    database_type: EXTERNAL-PDB
    status: ENABLED

================================================================================
2. SQL Performance Statistics (Last 7 Days)
================================================================================
PROMPT: What are the most resource-intensive SQL statements in the last week?

✅ Success! Found 11 items

  Item 1:
    sql_identifier: 02bhunw0vgg2j
    database_display_name: SALES-XA-WD_6
    executions_count: 2,399,310
    cpu_time_in_sec: 4,455,083,828.00
    database_time_pct: 26.0
    category: ['CHANGING_PLANS', 'DEGRADING']

... (and so on for 15 prompts)
```

## Configuration

The script uses these default settings:

```python
COMPARTMENT_ID = "ocid1.compartment.oc1..aaaa..."  # Your compartment
TIME_RANGE = 7 days (from now)
FORECAST_DAYS = 30 days
```

To customize, edit the top of `demo_opsi_features.py`:

```python
# Configuration
COMPARTMENT_ID = "your-compartment-ocid"
TIME_END = datetime.now()
TIME_START = TIME_END - timedelta(days=30)  # Change to 30 days
```

## Features Showcased

### 🔍 New Host Insights APIs (Implemented Today!)
- ✅ `summarize_host_insight_resource_forecast_trend()` - **Critical feature from OCI Console**
- ✅ `summarize_host_insight_resource_capacity_trend()`
- ✅ `summarize_host_insight_resource_usage()`
- ✅ `summarize_host_insight_resource_statistics()`
- ✅ `summarize_host_insight_disk_statistics()`
- ✅ `summarize_host_insight_network_usage_trend()`
- ✅ `summarize_host_insight_top_processes_usage()`

### 🔧 Fixed APIs
- ✅ `list_database_insights()` - No longer throws "not iterable" error
- ✅ `summarize_sql_statistics()` - Now returns actual metrics (not nulls)

## Use Cases

### 1. Capacity Planning
Prompts 4, 5, 6, 12 show capacity forecasts and trends:
- CPU forecast for next 30 days
- Memory forecast for next 15 days
- Storage capacity predictions

### 2. Performance Monitoring
Prompts 2, 7, 8, 11, 14 identify performance issues:
- Resource-intensive SQL statements
- Current CPU/memory usage
- Top processes consuming resources
- Degrading SQL statements

### 3. Infrastructure Overview
Prompts 1, 3, 15 provide inventory and health:
- All monitored databases and hosts
- Overall system health summary

### 4. Detailed Analysis
Prompts 9, 10, 13 give deep insights:
- Disk I/O patterns
- Network usage trends
- High-utilization hosts

## Troubleshooting

### No Data Returned

If you get empty results:

1. **Check Operations Insights is enabled**
   ```bash
   oci opsi database-insights list --compartment-id <your-compartment>
   ```

2. **Verify time range has data**
   - Default is last 7 days
   - Try extending to 30 days if needed

3. **Check IAM permissions**
   ```
   Allow group YourGroup to read opsi-database-insights in compartment
   Allow group YourGroup to read opsi-host-insights in compartment
   ```

### Error: Not Iterable

If you get this error, **restart your MCP server** - the fix has been applied but needs a restart.

### Error: Null Values

If metrics show as `null`, **restart your MCP server** - the SQL statistics fix requires a restart.

## For LLM Integration

This demo script serves as a template for how an LLM can query Operations Insights data. Each prompt demonstrates:

1. **What question to ask** (the PROMPT line)
2. **Which API to call** (the function name)
3. **What parameters to use** (compartment, time range, metrics)
4. **How to interpret results** (key fields to display)

### Example LLM Workflow

```
User: "Show me hosts with high CPU usage"
LLM: Calls summarize_host_insight_resource_capacity_trend()
     with utilization_level="HIGH_UTILIZATION"
LLM: Formats results showing host names, usage %, and timestamps
```

## Next Steps

1. **Run the demo** to see all features in action
2. **Review the output** to understand available data
3. **Customize prompts** for your specific use cases
4. **Integrate with LLM** using these patterns

## Summary

This demo showcases:
- ✅ 15 different Operations Insights queries
- ✅ All newly implemented host insight APIs
- ✅ Fixed database and SQL statistics functions
- ✅ Real data from your OCI environment
- ✅ Ready-to-use patterns for LLM integration

**Total API Coverage**: 75+ Operations Insights tools now available!
