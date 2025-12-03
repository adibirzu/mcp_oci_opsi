---
name: capacity-planning
description: |
  Forecast resource utilization and plan capacity for databases and hosts.
  Use this skill when the user asks about:
  - CPU, memory, storage, or I/O forecasts
  - Capacity trends and predictions
  - When resources will run out
  - Right-sizing recommendations
  - Historical utilization trends
  This skill uses OCI's ML-based forecasting for accurate predictions.
allowed-tools:
  - get_database_capacity_trend
  - get_database_resource_forecast
  - get_capacity_trend_with_chart
  - get_resource_forecast_with_chart
  - get_host_resource_forecast_trend
  - get_host_resource_capacity_trend
  - get_host_resource_utilization_insight
  - get_host_recommendations
---

# Capacity Planning Skill

## Purpose
Provide ML-based resource forecasting and capacity planning insights.

## When to Use
- User asks about future resource usage
- User wants to know when capacity will be exhausted
- User needs utilization trends
- User asks for right-sizing recommendations

## Recommended Approach

### For Database Forecasts
Use `get_resource_forecast_with_chart()`:
- Returns both historical trend and forecast
- Includes ASCII visualization
- Provides OCI Console link for graphical view

### For Host Forecasts
Use `get_host_resource_forecast_trend()`:
- Supports CPU, MEMORY, STORAGE, NETWORK
- Returns ML-based predictions

### For Recommendations
Use `get_host_recommendations()`:
- Returns AI-driven sizing recommendations
- Based on actual utilization patterns

## Parameters Guide

### Resource Metrics
- **CPU**: Processor utilization
- **MEMORY**: Memory consumption
- **STORAGE**: Disk space usage
- **IO**: I/O operations

### Forecast Period
- Default: 30 days
- Recommended: 30-90 days for capacity planning
- Maximum: 365 days

### Time Range for Historical Data
- Use at least 7 days of historical data
- 30 days recommended for accurate forecasting
- Recent data weights more heavily in predictions

## Response Format Guidelines
- Lead with the key finding (e.g., "Storage will reach 80% in 45 days")
- Include current utilization percentage
- Provide forecast trend direction
- Only show ASCII chart if specifically requested

## Example Interactions

**User**: "When will my database run out of storage?"
**Approach**:
1. Call `get_resource_forecast_with_chart(resource_metric="STORAGE", forecast_days=90)`
2. Look for when utilization crosses 80% threshold
3. Respond with predicted date and current usage

**User**: "Show CPU forecast for next month"
**Approach**:
1. Call `get_resource_forecast_with_chart(resource_metric="CPU", forecast_days=30)`
2. Include the ASCII chart in response
3. Highlight any concerning trends

**User**: "Do I need to scale up my hosts?"
**Approach**:
1. Call `get_host_recommendations()` for recommendations
2. Call `get_host_resource_utilization_insight()` for current state
3. Provide actionable scaling advice

## Token Optimization
- Use `get_database_resource_forecast()` without chart for minimal response
- Only include ASCII charts when visualization adds value
- Focus on actionable timeline predictions
