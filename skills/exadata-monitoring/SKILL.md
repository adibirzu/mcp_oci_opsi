---
name: exadata-monitoring
description: |
  Monitor Oracle Exadata systems including rack topology and resource usage.
  Use this skill when the user asks about:
  - Exadata system inventory
  - Rack topology and configuration
  - Exadata resource utilization
  - Compute and storage server status
  This skill provides Exadata-specific monitoring capabilities.
allowed-tools:
  - list_exadata_insights
  - get_exadata_rack_visualization
---

# Exadata Monitoring Skill

## Purpose
Monitor Oracle Exadata infrastructure including rack topology, servers, and databases.

## What is Exadata?
- Oracle's engineered system for database
- Combines compute, storage, and networking
- Optimized for Oracle Database workloads
- Includes specialized hardware features

## When to Use
- User manages Exadata systems
- User needs rack topology view
- User monitors Exadata resources
- User investigates Exadata issues

## Exadata Components

### Compute Servers
- Run Oracle Database instances
- Host application workloads
- CPU and memory monitoring

### Storage Servers
- Exadata Storage Servers (cells)
- Smart scanning and offload
- Flash cache and disk storage

### Rack Configuration
- Multiple compute + storage servers
- InfiniBand networking
- Power and cooling redundancy

## Recommended Approach

### List Exadata Systems
```
list_exadata_insights(compartment_id)
```
Returns all Exadata systems in Operations Insights.

### View Rack Topology
```
get_exadata_rack_visualization(
    exadata_insight_id,
    compartment_id
)
```
Returns ASCII visualization of rack configuration.

## Response Format Guidelines
- Show system name and model
- Display rack configuration visually
- List compute and storage server counts
- Highlight any degraded components

## Example Interactions

**User**: "Show my Exadata systems"
**Approach**:
1. Call `list_exadata_insights(compartment_id)`
2. List system names, types, and status
3. Show location/compartment

**User**: "Show rack topology for Exadata X"
**Approach**:
1. Get exadata_insight_id from list
2. Call `get_exadata_rack_visualization()`
3. Display ASCII rack diagram
4. Show database placement

**User**: "How many servers in my Exadata?"
**Approach**:
1. Call `get_exadata_rack_visualization()`
2. Count compute servers
3. Count storage servers
4. Show configuration summary

**User**: "Is my Exadata healthy?"
**Approach**:
1. Call `list_exadata_insights()` to check status
2. Get rack visualization for topology
3. Note any degraded or failed components
4. Recommend checking cell health in OCI Console

## Token Optimization
- Use list first to identify systems
- Rack visualization is already compact
- Link to OCI Console for detailed metrics
