# MCP OCI OPSI Demo Script

## 🎯 5-Minute Quick Demo

### 1. Fast Cache - The "Wow" Moment (1 minute)

```
👉 "How many databases do I have?"
   → Instant response: 177 databases, 31 hosts
   → Highlight: < 50ms, zero API calls

👉 "Find database ECREDITS"
   → Instant search result with details
   → Highlight: Instant discovery across 4 compartments

👉 "Show me all databases in the HR compartment"
   → Instant compartment inventory
   → Highlight: Token-efficient, grouped response
```

**Key Points:**
- ✅ Instant responses (< 50ms)
- ✅ 80% fewer tokens
- ✅ 177 databases pre-cached

---

### 2. Performance Diagnostics (2 minutes)

```
👉 "Show me SQL statistics for the past 7 days"
   → Detailed SQL performance metrics
   → Shows: Executions, CPU time, elapsed time

👉 "Get ADDM findings for database [pick from cache result]"
   → Specific performance recommendations
   → Shows: Impact, recommendations, priority

👉 "What are the top wait events?"
   → ASH wait event analysis
   → Shows: Wait classes, bottlenecks
```

**Key Points:**
- ✅ Identifies performance problems
- ✅ Specific recommendations
- ✅ Root cause analysis

---

### 3. Capacity Planning (1 minute)

```
👉 "Forecast storage usage for the next 30 days"
   → ML-based predictions
   → Shows: Trend analysis, predictions, alerts

👉 "Show me capacity trends for CPU over the past 90 days"
   → Historical trend analysis
   → Shows: Growth rate, patterns
```

**Key Points:**
- ✅ ML-based forecasting
- ✅ Proactive planning
- ✅ Budget preparation

---

### 4. Real-Time Monitoring (1 minute)

```
👉 "Show me CRITICAL alert logs from the past 24 hours"
   → Alert log analysis
   → Shows: Errors, warnings, issues

👉 "Show me fleet health metrics"
   → Organization-wide view
   → Shows: Health status, comparisons
```

**Key Points:**
- ✅ Real-time awareness
- ✅ Proactive monitoring
- ✅ Fleet-wide visibility

---

## 📊 15-Minute Full Demo

### Part 1: Fast Discovery & Inventory (3 min)

**Setup:** "Let's start with understanding what we have..."

```
1. "Show me fleet summary"
   Expected: 177 databases, 31 hosts, breakdown by compartment

2. "What types of databases do I have?"
   Expected: EXTERNAL-NONCDB: 104, ATP-D: 13, etc.

3. "How many databases in each compartment?"
   Expected: OperationsInsights: 57, Exadatas: 45, HR: 38, Finance: 37

4. "Find all ATP databases"
   Expected: List of 25 ATP databases (13 ATP-D, 12 ATP-S)

5. "Search for database ECREDITS"
   Expected: Instant result with compartment, type, version
```

**Talking Points:**
- All responses instant (< 50ms)
- Zero API calls
- 80% token savings
- Perfect for quick questions

---

### Part 2: Performance Problem Solving (5 min)

**Setup:** "Now let's diagnose a performance issue..."

```
6. "Show me SQL statistics for the past 7 days"
   Expected: Aggregated SQL performance data
   Point out: Top consumers, problem SQL

7. "What are the top 10 SQL statements by CPU usage?"
   Expected: Ranked list with metrics
   Show: SQL ID, CPU time, executions

8. "Get ADDM findings for database [X]"
   Expected: ADDM recommendations
   Point out: Specific findings, impact assessment, recommendations

9. "Show me ASH wait events for the past hour"
   Expected: Wait event analysis
   Show: Wait classes, time waited, frequency

10. "List alert logs with severity CRITICAL"
    Expected: Critical errors from logs
    Point out: Real-time problem detection
```

**Talking Points:**
- Identifies root causes
- Specific, actionable recommendations
- Multiple diagnostic tools
- Covers SQL, waits, alerts

---

### Part 3: Capacity Planning & Forecasting (4 min)

**Setup:** "Let's look at capacity planning..."

```
11. "Forecast storage usage for the next 30 days"
    Expected: ML-based storage forecast
    Show: Current trend, predicted usage, alerts

12. "Show me storage capacity trends for the past 90 days"
    Expected: Historical analysis
    Point out: Growth rate, patterns

13. "Will I run out of CPU in the next 30 days?"
    Expected: CPU forecast with predictions
    Show: Utilization trends, capacity limits

14. "What databases are growing fastest?"
    Expected: Growth rate analysis
    Point out: Databases needing attention
```

**Talking Points:**
- ML-based predictions
- Proactive capacity planning
- Budget preparation
- Prevents outages

---

### Part 4: Fleet Management & Monitoring (3 min)

**Setup:** "Finally, let's look at fleet-wide management..."

```
15. "Show me fleet health metrics"
    Expected: Organization-wide health status
    Show: Overall health, comparisons

16. "What databases need attention?"
    Expected: Prioritized list
    Point out: Health indicators, recommendations

17. "Show me database home availability metrics"
    Expected: Availability trends
    Show: Uptime, outages

18. "List all failed jobs from the past 24 hours"
    Expected: Job failures
    Point out: Operational awareness
```

**Talking Points:**
- Enterprise-wide visibility
- Proactive management
- Health tracking
- Operational excellence

---

## 🎬 Demo Scenarios

### Scenario 1: "I need to know what databases I have" (2 min)

```
DBA: "I'm new here, can you show me what databases we have?"

You: "How many databases do I have?"
     → 177 databases instantly

You: "Show me fleet summary"
     → Breakdown by compartment and type

You: "What's in the HR compartment?"
     → 38 databases with details
```

**Win:** Instant inventory, no spreadsheets needed

---

### Scenario 2: "Database is slow, help!" (5 min)

```
DBA: "ECREDITS database is slow, what's wrong?"

You: "Find database ECREDITS"
     → Instant location

You: "Get ADDM findings for ECREDITS"
     → Specific performance recommendations

You: "Show me ASH wait events for ECREDITS"
     → Wait event analysis

You: "What are the top SQL statements by CPU for ECREDITS?"
     → Problem SQL identified
```

**Win:** Root cause identified in minutes

---

### Scenario 3: "Budget planning for next quarter" (4 min)

```
DBA: "Finance needs to know if we'll need more capacity"

You: "Forecast storage for the next 30 days"
     → ML prediction with trends

You: "Show me capacity trends for the past 90 days"
     → Historical growth analysis

You: "Forecast CPU usage for the next 30 days"
     → CPU capacity prediction

You: "What databases are growing fastest?"
     → Prioritized list
```

**Win:** Data-driven budget requests

---

### Scenario 4: "Morning health check" (3 min)

```
DBA: "Daily morning check - any issues?"

You: "Show me fleet health metrics"
     → Overall health status

You: "List CRITICAL alert logs from the past 24 hours"
     → Any critical issues

You: "Show me failed jobs from yesterday"
     → Operational issues

You: "Check if cache needs refresh"
     → Cache status
```

**Win:** Complete health check in minutes

---

## 💡 Demo Tips

### Do's ✅

1. **Start with cache tools** - Instant wow factor
2. **Show real data** - Use actual database names
3. **Highlight speed** - Point out instant responses
4. **Explain token savings** - 80% fewer tokens
5. **Show integration** - Mix cache and API tools
6. **Use scenarios** - Real DBA workflows
7. **Emphasize value** - Time savings, cost reduction

### Don'ts ❌

1. ~~Don't start with slow queries~~ - Start fast!
2. ~~Don't use made-up examples~~ - Use real fleet
3. ~~Don't skip cache demo~~ - It's the differentiator
4. ~~Don't go too technical~~ - Keep it business-focused
5. ~~Don't forget to highlight instant responses~~

---

## 📈 Value Proposition

### Time Savings

**Before MCP:**
- Manual queries: 10-15 minutes per question
- Multiple tools: OPSI Console, SQL Developer, OCI CLI
- Context switching: 5-10 minutes

**With MCP:**
- Instant answers: < 1 second for cache
- Single interface: Ask Claude in natural language
- No context switching: Everything in one place

**Result: 90% time savings**

### Cost Efficiency

**Token Savings:**
- Cache queries: 80% fewer tokens
- Efficient responses: Minimal data transfer
- Smart caching: 24-hour validity

**API Efficiency:**
- Fewer API calls: Cache handles inventory
- Targeted queries: Only when needed
- Batch operations: Multiple compartments at once

### Operational Excellence

**Proactive:**
- ML forecasting: Predict capacity needs
- Alert monitoring: Real-time awareness
- Trend analysis: Spot issues early

**Comprehensive:**
- 55 tools: Everything in one place
- 177 databases: Full fleet visibility
- Multiple clouds: OCI-wide coverage

---

## 🎤 Opening Lines

### Technical Audience
"Let me show you how Claude can become your AI DBA assistant with instant access to 177 databases across your OCI environment..."

### Executive Audience
"Imagine getting answers about your entire database fleet in under a second, with 80% less cost, and AI-powered capacity predictions..."

### Operations Team
"Let's see how you can go from 'database is slow' to root cause identified in under 5 minutes..."

---

## 📝 Demo Checklist

Before Demo:
- [ ] Restart Claude Desktop
- [ ] Verify cache is built (177 databases)
- [ ] Test: "Show me fleet summary"
- [ ] Identify 1-2 databases for detailed demos
- [ ] Have compartment OCIDs ready
- [ ] Check cache age (< 24 hours)

During Demo:
- [ ] Start with fast cache tools (wow factor)
- [ ] Show variety: inventory → diagnostics → forecasting
- [ ] Use real database names from fleet
- [ ] Point out response times
- [ ] Highlight token efficiency
- [ ] Show both cache and API tools

After Demo:
- [ ] Summarize: 55 tools, instant responses, token savings
- [ ] Provide documentation links
- [ ] Offer to answer questions
- [ ] Schedule follow-up if interested

---

## 🚀 Quick Commands Reference

### Fast (Cache)
```
- Show me fleet summary
- Find database X
- What's in HR compartment?
- How many databases?
- List compartments
```

### Diagnostics (API)
```
- Show SQL statistics
- Get ADDM findings
- Show ASH wait events
- List alert logs
- Show top SQL by CPU
```

### Capacity (API)
```
- Forecast storage
- Show capacity trends
- Predict CPU usage
- Show growth rate
```

### Management (API)
```
- Show fleet health
- Get AWR report
- List database jobs
- Show availability
```

---

**Total Tools: 55**
**Cache: 177 Databases + 31 Hosts**
**Response Time: < 50ms (cache), 2-5s (API)**
**Token Savings: 80% (cache queries)**

Ready to demo! 🎯
