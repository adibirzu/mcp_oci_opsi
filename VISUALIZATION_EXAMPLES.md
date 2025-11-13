# Visualization & Charting Examples

This document provides comprehensive examples of using the new visualization and charting features in the MCP OCI OPSI Server.

## Overview

The MCP server now includes three enhanced visualization tools that provide:
- **ASCII line charts** for viewing trends directly in Claude
- **Capacity planning recommendations** based on ML forecasting
- **OCI Console URLs** for accessing full graphical dashboards
- **Exadata rack topology** visualizations

## Table of Contents

1. [Capacity Trend Visualization](#capacity-trend-visualization)
2. [Resource Forecast with Charts](#resource-forecast-with-charts)
3. [Exadata Rack Visualization](#exadata-rack-visualization)
4. [Common Use Cases](#common-use-cases)
5. [Understanding the Output](#understanding-the-output)

---

## Capacity Trend Visualization

### Tool: `get_capacity_trend_with_chart()`

This tool shows historical capacity utilization with an ASCII line chart.

### Example 1: CPU Capacity Trend

**Query:**
```
Claude, show me the CPU capacity trend for the OperationsInsights compartment over the past 90 days
```

**What Claude Does:**
1. Identifies the compartment OCID
2. Calculates the date range (90 days ago to today)
3. Calls `get_capacity_trend_with_chart()` with resource_metric="CPU"
4. Returns ASCII chart + data + OCI Console link

**Expected Output:**
```
CPU Capacity Trend: Database_Name
================================================================================

   100.0 │                                     ●
    90.0 │                               ●───●   ●
    80.0 │                         ●───●             ●
    70.0 │                   ●───●                     ●
    60.0 │             ●───●                             ●───●
    50.0 │       ●───●                                         ●
    40.0 │ ●───●
    30.0 │
         └────────────────────────────────────────────────────────────────────
           08/15          09/15          10/15          11/13

Summary:
- Current Utilization: 72.5%
- Average Utilization: 65.3%
- Peak Utilization: 95.2%
- Trend: Increasing

📊 For graphical charts, open: https://cloud.oracle.com/operations-insights/...
```

### Example 2: Storage Capacity Trend for Specific Database

**Query:**
```
Claude, show me storage capacity trend for database PRODDB01 for the past 30 days
```

**Parameters:**
- resource_metric: "STORAGE"
- time_interval: Past 30 days
- database_id: OCID of PRODDB01
- database_name: "PRODDB01"

---

## Resource Forecast with Charts

### Tool: `get_resource_forecast_with_chart()`

This tool combines historical data with ML-based forecasts in a single chart.

### Example 3: CPU Forecast with Recommendations

**Query:**
```
Claude, forecast CPU usage for the next 30 days and show me if we need to scale
```

**Expected Output:**
```
CPU Forecast (Historical + 30d Prediction): Database_Name
================================================================================

   100.0 │                                              ◆
    90.0 │                                        ◆┈┈◆
    80.0 │                                  ◆┈┈◆
    70.0 │                            ●───●
    60.0 │                      ●───●
    50.0 │                ●───●
    40.0 │          ●───●
    30.0 │    ●───●
         └────────────────────────────────────────────────────────────────────
           10/01    10/15    11/01    11/15    12/01    12/15

  ● Historical    ◆ Forecast

Summary:
- Current Utilization: 68.5%
- Forecast End (30d): 92.3%
- Forecast High Confidence: 95.8%
- Forecast Low Confidence: 88.1%

Recommendations:
🟡 WARNING: Forecasted capacity will exceed 80% - plan for scaling
   → Recommendation: Schedule capacity increase for CPU in next 2-4 weeks
   📈 Trend: CPU usage growing at 35.2% over forecast period

📊 For interactive forecast with confidence bands:
https://cloud.oracle.com/operations-insights/.../forecast
```

### Example 4: Storage Forecast for Multiple Databases

**Query:**
```
Claude, forecast storage for all databases in HR compartment for next 60 days
```

**Parameters:**
- resource_metric: "STORAGE"
- forecast_days: 60
- compartment_id: HR compartment OCID

**Result:** Claude will iterate through databases and show forecasts for each.

---

## Exadata Rack Visualization

### Tool: `get_exadata_rack_visualization()`

Shows Exadata system topology with databases and hardware components.

### Example 5: Exadata Rack Topology

**Query:**
```
Claude, show me the Exadata rack visualization for system X5-2_Qtr_DBM01
```

**Expected Output:**
```
================================================================================
  Exadata System: X5-2_Qtr_DBM01
================================================================================

System ID: ocid1.exadatainsight.oc1...a7xrxq

Hardware Configuration:
  ├─ Compute Servers:  2
  ├─ Storage Servers:  3
  └─ Databases:        8

Databases on System:
  ├─ DBM01adm01-c.us.oracle.com (DATABASE) - Status: Active
  ├─ DBM01adm02-c.us.oracle.com (DATABASE) - Status: Active
  ├─ DBM01eth-sw.oraclecloud.internal (DATABASE) - Status: Active
  ├─ DBM01sw-ib1.us.oracle.com (DATABASE) - Status: Active
  ├─ DBM01sw-ib2.us.oracle.com (DATABASE) - Status: Active
  ├─ DBM01sw-ib3.us.oracle.com (DATABASE) - Status: Active
  ├─ DBM01cei01.us.oracle.com (DATABASE) - Status: Active
  └─ DBM01cei02.us.oracle.com (DATABASE) - Status: Active

================================================================================

🖼️  For graphical rack visualization with interactive components:
https://cloud.oracle.com/operations-insights/exadata-insights/...
```

---

## Common Use Cases

### Use Case 1: Morning Capacity Check

**Workflow:**
```
1. "Show me fleet summary" (cache - instant)
2. "Show CPU capacity trends for past 7 days" (trend with chart)
3. "Forecast CPU for next 30 days" (forecast with recommendations)
```

**Benefits:**
- Quick overview of fleet status
- Visual trend identification
- Proactive capacity planning

### Use Case 2: Budget Planning

**Workflow:**
```
1. "List all databases in Production compartment"
2. "For each database, forecast storage for next 90 days"
3. "Show me which databases need scaling"
```

**Output:** Comprehensive forecast report with cost implications.

### Use Case 3: Performance Investigation

**Workflow:**
```
1. "Show CPU trend for database X" (identify spike timing)
2. "Show SQL statistics during spike period"
3. "Get ADDM findings for that time range"
```

**Benefits:** Correlate capacity usage with SQL activity.

### Use Case 4: Exadata Health Check

**Workflow:**
```
1. "List all Exadata systems in compartment Y"
2. "Show rack visualization for Exadata Z"
3. "Show capacity trends for all databases on that system"
```

**Benefits:** Complete Exadata system health assessment.

---

## Understanding the Output

### ASCII Chart Components

**Symbols:**
- `●` = Historical data point
- `─` = Line connecting historical points
- `◆` = Forecast data point
- `┈` = Dashed line for forecast
- `│` = Y-axis
- `└─` = X-axis

**Chart Features:**
- **Width**: 80 characters (fits standard terminal)
- **Height**: 20 lines
- **Scale**: Automatic scaling based on min/max values
- **Time Axis**: Shows first, middle, and last timestamps

### Capacity Recommendations

**Color Indicators:**
- 🔴 **CRITICAL** (>90%): Immediate action required
- 🟡 **WARNING** (>80%): Plan for scaling
- 🟢 **MONITOR** (>70%): Continue monitoring
- ✅ **OK** (<70%): Healthy capacity

**Trend Indicators:**
- ↑ **Increasing**: Usage growing
- ↓ **Decreasing**: Usage declining
- → **Stable**: No significant change

### OCI Console URLs

The OCI Console links provide access to:
- **Interactive charts** with zoom and pan
- **Confidence bands** for forecasts
- **Detailed metrics** and breakdowns
- **Export capabilities** (CSV, PDF)
- **Alert configuration** for thresholds

Simply click the URL to open the full graphical interface.

---

## Advanced Examples

### Example 6: Compare Multiple Resources

**Query:**
```
Claude, for database X, show me:
1. CPU trend for past 90 days
2. Memory trend for past 90 days
3. Storage trend for past 90 days
4. Forecasts for all three for next 30 days
```

**Result:** Four separate charts showing comprehensive resource analysis.

### Example 7: Fleet-Wide Forecast

**Query:**
```
Claude, forecast CPU for all databases in Production compartment.
Show me which ones will exceed 80% in the next 30 days.
```

**Result:** List of databases with forecasts, filtered by those needing attention.

### Example 8: Historical Analysis

**Query:**
```
Claude, show me CPU capacity trend for the past 12 months.
What were the peak usage periods?
```

**Result:** Long-term trend chart with peak analysis.

---

## Tips & Best Practices

### 1. Date Range Selection

**Short-term trends (7-30 days):**
- More granular data points
- Better for immediate decisions
- Faster response time

**Long-term trends (90-365 days):**
- Shows seasonal patterns
- Better for strategic planning
- May have aggregated data points

### 2. Forecast Duration

**Recommended forecast periods:**
- **7-14 days**: Operational planning
- **30 days**: Budget planning
- **60-90 days**: Strategic capacity planning

**Note:** Longer forecasts have wider confidence intervals.

### 3. Using Charts Effectively

**For Quick Checks:**
- Use ASCII charts in Claude
- Get immediate visual insight
- No need to open browser

**For Detailed Analysis:**
- Click OCI Console link
- Use interactive features
- Export data for reports

**For Presentations:**
- Take screenshots of OCI Console
- Include ASCII charts in documentation
- Use recommendations in planning docs

### 4. Combining with Other Tools

**Effective combinations:**
```
1. Cache: "Find database X" (instant)
2. Trend: "Show capacity trend" (visualization)
3. Forecast: "Predict usage" (planning)
4. SQL Stats: "Show top SQL" (root cause)
5. ADDM: "Get recommendations" (optimization)
```

---

## Troubleshooting

### Issue: Chart looks distorted

**Solution:** Ensure your terminal/display is at least 80 characters wide.

### Issue: No forecast data returned

**Possible causes:**
- Database not enabled for Operations Insights
- Insufficient historical data (need 7+ days)
- Database ID incorrect

**Solution:** Verify database is registered with OPSI and has been collecting data.

### Issue: OCI Console link doesn't work

**Possible causes:**
- Not logged into OCI Console
- Incorrect region
- Insufficient permissions

**Solution:** Log into OCI Console first, then click the link.

### Issue: Forecast recommendations unclear

**Solution:** Ask Claude to explain: "What does this recommendation mean? What should I do?"

---

## Next Steps

1. **Try the examples** above with your own databases
2. **Explore forecasts** for different resource types (CPU, STORAGE, MEMORY, IO)
3. **Compare historical vs forecast** to validate predictions
4. **Use recommendations** for capacity planning decisions
5. **Share OCI Console links** with team members for collaboration

---

## Additional Resources

- **CACHE_SYSTEM.md**: Fast cache for database inventory
- **DBA_DEMO_QUESTIONS.md**: More query examples
- **DEMO_SCRIPT.md**: Complete demo workflows
- **README.md**: All available tools

---

**Questions?**

Ask Claude for help:
- "How do I forecast storage for database X?"
- "Show me an example capacity trend query"
- "What resources can I forecast?"
- "Explain this chart to me"

The visualization tools are designed to make capacity planning intuitive and actionable!
