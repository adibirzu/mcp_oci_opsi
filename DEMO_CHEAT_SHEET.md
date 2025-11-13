# MCP OCI OPSI Demo Cheat Sheet

## 🎯 5-Minute Demo Flow

### 1️⃣ Fast Cache (1 min)
```
✅ "How many databases do I have?"
✅ "Find database ECREDITS"
✅ "Show me HR compartment databases"
```
**Point: < 50ms, zero API calls, 80% token savings**

### 2️⃣ Performance (2 min)
```
✅ "Show me SQL statistics for the past 7 days"
✅ "Get ADDM findings for database X"
✅ "What are the top wait events?"
```
**Point: Root cause analysis, specific recommendations**

### 3️⃣ Capacity (1 min)
```
✅ "Forecast storage for the next 30 days"
✅ "Show me CPU capacity trends"
```
**Point: ML-based predictions, proactive planning**

### 4️⃣ Monitoring (1 min)
```
✅ "Show me CRITICAL alert logs from past 24 hours"
✅ "Show me fleet health metrics"
```
**Point: Real-time awareness, fleet-wide visibility**

---

## 📊 Key Numbers

- **55 Total Tools** (48 API + 7 Cache)
- **177 Databases** cached
- **31 Hosts** cached
- **4 Compartments** (OperationsInsights, Exadatas, HR, Finance)
- **< 50ms** response time (cache)
- **80%** token savings (cache)
- **60-100x** faster (cache vs API)

---

## 🚀 Fast Commands (Cache - INSTANT)

| Question | Tool | Response Time |
|----------|------|---------------|
| "Show me fleet summary" | get_fleet_summary() | < 50ms |
| "Find database X" | search_databases() | < 30ms |
| "What's in HR?" | get_databases_by_compartment() | < 40ms |
| "List compartments" | list_cached_compartments() | < 20ms |
| "How many databases?" | get_fleet_summary() | < 50ms |

---

## 🔧 Diagnostic Commands (API - LIVE DATA)

| Question | Tool | Use Case |
|----------|------|----------|
| "Show SQL statistics" | summarize_sql_statistics() | Performance analysis |
| "Get ADDM findings" | get_addm_report() | Recommendations |
| "Show ASH wait events" | get_ash_analytics() | Wait analysis |
| "Top SQL by CPU" | get_top_sql_by_metric() | Resource hogs |
| "List CRITICAL alerts" | list_alert_logs() | Issues |

---

## 📈 Capacity Commands (API - PREDICTIONS)

| Question | Tool | Use Case |
|----------|------|----------|
| "Forecast storage 30 days" | get_database_resource_forecast() | Planning |
| "Show capacity trends" | get_database_capacity_trend() | Analysis |
| "Show growth rate" | get_database_capacity_trend() | Trending |

---

## 🎭 Demo Scenarios

### Scenario A: New DBA
```
1. "How many databases?"          [Fast]
2. "Show fleet summary"            [Fast]
3. "What's in each compartment?"   [Fast]
```

### Scenario B: Performance Issue
```
1. "Find database ECREDITS"        [Fast]
2. "Get ADDM findings"             [Diagnostic]
3. "Show ASH wait events"          [Diagnostic]
4. "Top SQL by CPU"                [Diagnostic]
```

### Scenario C: Budget Planning
```
1. "Forecast storage 30 days"      [Capacity]
2. "Show capacity trends 90 days"  [Capacity]
3. "What databases growing fast?"  [Fast search]
```

### Scenario D: Morning Check
```
1. "Show fleet health"             [Monitoring]
2. "CRITICAL alerts past 24h"      [Monitoring]
3. "Failed jobs"                   [Monitoring]
```

---

## 💡 Value Propositions

### For DBAs
- **90% time savings** - No more manual queries
- **Single interface** - Everything in Claude
- **Natural language** - No SQL needed
- **Instant inventory** - 177 databases < 50ms

### For Management
- **Proactive** - ML predictions prevent issues
- **Cost efficient** - 80% token savings
- **Comprehensive** - 55 tools, full visibility
- **Data-driven** - Capacity planning with ML

### For Operations
- **Real-time** - Alert monitoring
- **Automated** - AI-powered diagnostics
- **Fast** - 60-100x faster responses
- **Accurate** - Direct from OPSI

---

## 🎤 Demo Opening Lines

**Technical:**
"Watch Claude become your AI DBA with instant access to 177 databases..."

**Executive:**
"Get answers about your database fleet in under a second with 80% cost savings..."

**Operations:**
"Go from 'database is slow' to root cause in under 5 minutes..."

---

## ⚡ Quick Wins to Highlight

1. **Speed** - Instant responses (< 50ms)
2. **Efficiency** - 80% fewer tokens
3. **Intelligence** - ML-based forecasting
4. **Comprehensive** - 177 databases cached
5. **Proactive** - Capacity predictions
6. **Simple** - Natural language queries
7. **Powerful** - 55 specialized tools
8. **Complete** - Inventory → Diagnostics → Planning

---

## 📋 Pre-Demo Checklist

✅ Restart Claude Desktop
✅ Test: "Show me fleet summary"
✅ Verify: 177 databases in cache
✅ Identify: 1-2 databases for detailed demo
✅ Note: Real database names (ECREDITS, etc.)
✅ Ready: Compartment names (HR, Finance, etc.)

---

## 🎯 Demo Flow Template

```
1. FAST START (wow factor)
   → "How many databases do I have?"
   → Point out: < 50ms response

2. SHOW VARIETY (capability)
   → Cache: Fast inventory
   → API: Detailed diagnostics
   → ML: Predictions

3. TELL STORY (scenario)
   → Pick: Performance issue
   → Show: Fast diagnosis
   → Prove: Value delivered

4. SUMMARIZE (value)
   → Speed: 60-100x faster
   → Savings: 80% tokens
   → Tools: 55 available

5. CLOSE (action)
   → Questions?
   → Documentation?
   → Follow-up?
```

---

## 🔥 Power Combos

### Combo 1: Fast Discovery → Deep Dive
```
"Find database X"              [Cache - instant]
"Get ADDM findings for X"      [API - detailed]
```

### Combo 2: Fleet View → Specific Action
```
"Show fleet health"            [API - overview]
"What databases need attention?" [Analysis]
"Get details for database Y"   [Deep dive]
```

### Combo 3: Historical → Prediction
```
"Show capacity trends 90 days" [API - historical]
"Forecast storage 30 days"     [API - prediction]
```

---

## 📞 Common Questions & Answers

**Q: How current is the cache?**
A: Last updated [check time], refreshes every 24 hours automatically.

**Q: Can I get real-time data?**
A: Yes! We have 48 API tools for live metrics, diagnostics, and reports.

**Q: How many databases can it handle?**
A: Currently 177 cached, scales to thousands. No performance impact.

**Q: What about security?**
A: Uses OCI IAM, no passwords stored, read-only access by default.

**Q: Can it predict capacity needs?**
A: Yes! ML-based forecasting for storage, CPU, memory up to 30+ days.

**Q: Does it work with other clouds?**
A: This is OCI-specific. Can be extended to other cloud providers.

---

## 🎬 Closing Statements

**Summary:**
"In just 5 minutes, we've shown how Claude can instantly inventory 177 databases, diagnose performance issues, and predict capacity needs - all through simple natural language questions."

**Value:**
"This means 90% time savings for DBAs, 80% cost reduction in tokens, and proactive capacity management with ML predictions."

**Call to Action:**
"Ready to transform your database operations with AI? Let's discuss next steps."

---

**Print This Sheet!** 🖨️
Keep it visible during demos for quick reference.
