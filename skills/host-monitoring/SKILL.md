---
name: host-monitoring
description: |
  Monitor host infrastructure including CPU, memory, storage, and network.
  Use this skill when the user asks about:
  - Host resource utilization
  - Top processes consuming resources
  - Disk and I/O statistics
  - Network usage patterns
  - Host capacity planning
  This skill provides host-level observability for database servers.
allowed-tools:
  - list_host_insights
  - get_host_resource_statistics
  - get_host_resource_usage
  - get_host_resource_usage_trend
  - get_host_disk_statistics
  - get_host_io_usage_trend
  - get_host_network_usage_trend
  - get_host_storage_usage_trend
  - get_host_top_processes_usage
  - get_host_top_processes_usage_trend
---

# Host Monitoring Skill

## Purpose
Monitor and analyze host infrastructure supporting database workloads.

## When to Use
- User asks about server resource usage
- User needs to identify resource-hungry processes
- User wants disk or network analysis
- User investigates host-level performance

## Resource Metrics Available
- **CPU**: Processor utilization
- **MEMORY**: RAM usage (also LOGICAL_MEMORY for virtual)
- **STORAGE**: Disk space utilization
- **NETWORK**: Network I/O
- **IO**: Disk I/O operations

## Recommended Approach

### For Current Resource Status
Use `get_host_resource_statistics()`:
- Returns utilization for all hosts
- Includes capacity and usage values
- Shows utilization percentage

### For Historical Trends
Use trend tools:
- `get_host_resource_usage_trend()` - General resource trends
- `get_host_io_usage_trend()` - I/O patterns
- `get_host_network_usage_trend()` - Network traffic
- `get_host_storage_usage_trend()` - Storage growth

### For Process Analysis
Use `get_host_top_processes_usage()`:
- Shows top resource-consuming processes
- Supports CPU and MEMORY metrics
- Can filter by specific host

## Response Format Guidelines
- Present utilization as percentages
- Highlight hosts above 80% utilization
- Compare against capacity
- Identify trends (increasing/decreasing)

## Example Interactions

**User**: "Which hosts have high CPU usage?"
**Approach**:
1. Call `get_host_resource_statistics(resource_metric="CPU")`
2. Sort by utilization_percent descending
3. Highlight hosts above threshold

**User**: "What's consuming CPU on host X?"
**Approach**:
1. Call `get_host_top_processes_usage(resource_metric="CPU", host_id="...")`
2. List top 10 processes by CPU consumption
3. Identify any unusual processes

**User**: "Show disk I/O trends"
**Approach**:
1. Call `get_host_io_usage_trend()` for time range
2. Identify I/O patterns and peaks
3. Correlate with database activity

**User**: "Is storage growing too fast?"
**Approach**:
1. Call `get_host_storage_usage_trend()` for 30 days
2. Calculate growth rate
3. Project when capacity will be reached

## Token Optimization
- Filter by specific host_id when investigating single host
- Use statistics tools for point-in-time analysis
- Use trend tools only when historical context needed
- Limit time range to relevant period
