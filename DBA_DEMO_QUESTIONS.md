# DBA Demo Questions for MCP OCI OPSI

## Quick Inventory & Discovery (Fast Cache Tools - INSTANT)

### Fleet Overview
```
1. How many databases do I have in my environment?
2. Show me a fleet summary
3. What's the breakdown of databases by compartment?
4. How many databases are in the HR compartment?
5. What types of databases do I have? (ATP, ADW, External, etc.)
6. How many databases are ACTIVE vs other states?
7. Show me all host insights in my fleet
```

### Database Search & Discovery
```
8. Find the ECREDITS database
9. Search for all ATP databases
10. Show me all databases in the Finance compartment
11. Find databases with "PROD" in the name
12. List all External Non-CDB databases
13. What Autonomous databases do I have?
14. Search for MySQL databases
```

### Compartment & Organization
```
15. List all compartments with databases
16. Which compartment has the most databases?
17. Show me the compartment hierarchy
18. What databases are in the Exadatas compartment?
```

---

## Performance Issues & Diagnostics (API Tools)

### Top SQL Problems
```
19. Show me SQL statistics for the past 7 days
20. What are the top 10 SQL statements by CPU usage?
21. Which SQL statements are consuming the most I/O?
22. Show me SQL with the highest elapsed time
23. Find SQL statements with high buffer gets
24. What SQL is running most frequently?
```

### Database Performance
```
25. Show me database insights for the OperationsInsights compartment
26. What's the CPU utilization trend for database X over the past week?
27. Get me an AWR report for database X between snapshots Y and Z
28. Show me ADDM findings for database X
29. What are the performance recommendations from ADDM?
30. Analyze ASH wait events for the past hour
```

### Wait Event Analysis
```
31. What are the top wait events causing performance issues?
32. Show me User I/O wait events for database X
33. What SQL is waiting on locks?
34. Analyze CPU wait class for the past day
35. Show me network-related wait events
```

### Resource Bottlenecks
```
36. Which database is experiencing the highest CPU usage?
37. Show me memory utilization trends
38. What's the storage utilization for database X?
39. Are there any I/O bottlenecks?
40. Show me tablespace usage for database X
```

---

## Capacity Planning & Forecasting (API Tools)

### Storage Capacity
```
41. Will I run out of storage in the next 30 days?
42. Show me storage capacity trends for the past 90 days
43. Forecast storage usage for the next month
44. What's the storage growth rate?
45. Which databases are growing fastest?
46. Show me tablespace usage across all databases
```

### CPU Capacity
```
47. Forecast CPU usage for the next 30 days
48. Show me CPU capacity trends
49. Are we approaching CPU limits?
50. What's the peak CPU usage time?
51. Show me CPU utilization patterns by day of week
52. Which databases need more CPU allocation?
```

### Memory Planning
```
53. Show me memory utilization trends
54. Forecast memory usage for the next 30 days
55. Are there any databases with memory pressure?
56. What's the SGA/PGA usage pattern?
```

### Growth Analysis
```
57. What's my database growth rate over the past quarter?
58. Show me resource utilization trends for the past 6 months
59. When will I need to add capacity based on current trends?
60. What's the workload pattern - is it growing?
```

---

## Real-Time Monitoring (API Tools)

### Active Sessions
```
61. Show me current active sessions for database X
62. What's the current session count?
63. Get session information for database X
64. Are there any blocked sessions?
```

### Alert Logs
```
65. Show me CRITICAL alert log entries from the past 24 hours
66. List all alert logs with severity WARNING
67. What errors occurred in database X today?
68. Show me recent alert log messages for the Finance databases
69. Are there any ORA-00600 errors?
```

### Job Monitoring
```
70. List all scheduled database jobs for database X
71. Are there any failed jobs?
72. Show me job execution history
73. What jobs are currently running?
```

### Database Availability
```
74. Show me database home metrics for the past week
75. What's the uptime for database X?
76. Are all databases available?
77. Show me availability trends
```

---

## Database Management & Administration (API Tools)

### Configuration
```
78. Show me database parameters for database X
79. What's the value of parameter db_cache_size?
80. List all parameters with "memory" in the name
81. Show me initialization parameters that differ from defaults
```

### AWR Analysis
```
82. List AWR snapshots for database X
83. Generate an AWR report between snapshots 100 and 110
84. Show me AWR snapshots from the past week
85. What's the snapshot interval configured?
```

### System Statistics
```
86. Show me database system statistics from AWR
87. Get I/O statistics for database X
88. What's the database resource usage summary?
89. Show me CPU usage metrics over the past 24 hours
```

---

## Fleet-Level Analytics (API Tools)

### Fleet Health
```
90. Show me fleet health metrics
91. What's the overall health of my database fleet?
92. Which databases need attention?
93. Show me fleet-wide performance metrics
94. Compare performance across all databases
```

### Trend Analysis
```
95. Show me capacity trends across all databases
96. What's the fleet-wide CPU utilization?
97. Compare storage usage across compartments
98. Show me fleet-wide SQL statistics
```

---

## Database Registration & Setup (API Tools)

### Registration
```
99. Check if Operations Insights is enabled for database X
100. Register database X with Operations Insights
101. Show me database information for OCID X
102. What databases are registered with OPSI?
103. Disable Operations Insights for database X
```

### SQL Watch
```
104. Is SQL Watch enabled on database X?
105. Enable SQL Watch on database X
106. Check the status of SQL Watch operation
107. Disable SQL Watch on database X
```

---

## Direct Database Queries (API Tools - Optional)

### Schema Exploration
```
108. Query database X to show me all tables
109. Describe the structure of table EMPLOYEES
110. What's the database version and instance info?
111. Show me current session information
112. List all tablespaces in database X
```

### Custom SQL
```
113. Execute this query: SELECT table_name, num_rows FROM user_tables WHERE rownum <= 10
114. Show me the top 10 largest tables
115. Query database X for user count
```

---

## Troubleshooting Scenarios (Multi-Tool)

### Scenario 1: Performance Degradation
```
116. Database X is slow - show me ADDM findings
117. What SQL is consuming resources right now?
118. Check for any CRITICAL alerts in the past hour
119. Show me ASH wait events
120. Get AWR report for the problem period
```

### Scenario 2: Capacity Planning Request
```
121. We need to budget for next quarter - show me growth trends
122. Forecast storage needs for the next 90 days
123. What databases will need upgrades?
124. Show me resource utilization forecasts
```

### Scenario 3: Fleet Audit
```
125. How many databases do we have total?
126. What's the breakdown by type and compartment?
127. Are all databases registered with OPSI?
128. Show me databases that need attention
129. What's the overall fleet health status?
```

### Scenario 4: New Database Onboarding
```
130. Get information about database OCID X
131. Register this database with Operations Insights
132. Enable SQL Watch on this database
133. Verify the database is now visible in OPSI
```

---

## Profile & Configuration Management

### Profile Management
```
134. What OCI profile am I currently using?
135. List all available OCI profiles
136. Show me the configuration for profile emdemo
137. What compartment am I working in?
```

### Cache Management
```
138. Is my cache up to date?
139. When was the cache last refreshed?
140. Show me detailed cache statistics
141. Rebuild the cache for all compartments
```

---

## Demo Flow Recommendations

### 1. Start with Fast Cache (Impress with Speed)
```
"How many databases do I have?" → Instant response
"Find database ECREDITS" → Instant response
"Show me HR compartment databases" → Instant response
```

### 2. Show Performance Diagnostics (Real Value)
```
"Show me SQL statistics for the past week" → Detailed analysis
"Get ADDM findings for database X" → Specific recommendations
"What are the top wait events?" → Problem identification
```

### 3. Demonstrate Capacity Planning (Strategic Value)
```
"Forecast storage for the next 30 days" → ML-based prediction
"Show me capacity trends" → Historical analysis
"Will I run out of resources?" → Proactive planning
```

### 4. Real-Time Monitoring (Operational Value)
```
"Show me CRITICAL alert logs" → Immediate issues
"List failed jobs" → Operational awareness
"Show me ASH analytics" → Live diagnostics
```

### 5. Fleet Management (Enterprise Value)
```
"Show me fleet health metrics" → Organization-wide view
"Compare performance across databases" → Cross-database analysis
"What's my fleet composition?" → Inventory management
```

---

## Question Categories Summary

| Category | Count | Tools Used | Response Time |
|----------|-------|------------|---------------|
| **Fast Inventory** | 18 | Cache Tools | < 50ms |
| **Performance Issues** | 22 | API Tools | 2-5 seconds |
| **Capacity Planning** | 17 | API Tools | 2-5 seconds |
| **Real-Time Monitoring** | 16 | API Tools | 2-5 seconds |
| **Database Management** | 12 | API Tools | 2-5 seconds |
| **Fleet Analytics** | 8 | API Tools | 2-5 seconds |
| **Registration & Setup** | 9 | API Tools | 2-5 seconds |
| **Direct Queries** | 8 | API Tools | 2-5 seconds |
| **Troubleshooting** | 15 | Multi-Tool | Mixed |
| **Configuration** | 8 | Cache/API | Mixed |

**Total: 141 Demo Questions**

---

## Demo Script Examples

### Quick Demo (5 minutes)

```
1. "How many databases do I have?" [Cache - instant wow factor]
2. "Find database ECREDITS" [Cache - instant search]
3. "Show me SQL statistics for the past week" [API - detailed analysis]
4. "Get ADDM findings for database X" [API - specific recommendations]
5. "Forecast storage for the next 30 days" [API - ML prediction]
```

### Full Demo (15 minutes)

```
SECTION 1: Fast Inventory (2 min)
- "Show me fleet summary"
- "How many databases in each compartment?"
- "Find all ATP databases"

SECTION 2: Performance Diagnostics (5 min)
- "Show me SQL statistics"
- "What are top SQL by CPU?"
- "Get ADDM findings"
- "Show me ASH wait events"

SECTION 3: Capacity Planning (3 min)
- "Show me capacity trends"
- "Forecast storage for 30 days"
- "Will I run out of resources?"

SECTION 4: Real-Time Monitoring (3 min)
- "Show me CRITICAL alerts"
- "List failed jobs"
- "Get database availability metrics"

SECTION 5: Fleet Management (2 min)
- "Show me fleet health"
- "Compare performance across databases"
```

### Executive Demo (10 minutes)

```
1. Fleet Overview
   "How many databases do we have?" [INSTANT]
   "Show me fleet summary" [INSTANT]

2. Operational Efficiency
   "What databases need attention?" [Fleet health]
   "Show me performance trends" [Capacity planning]

3. Cost Optimization
   "Forecast resource needs" [ML predictions]
   "Show me underutilized databases" [Resource stats]

4. Risk Management
   "Show me CRITICAL alerts" [Alert logs]
   "What databases have performance issues?" [ADDM]

5. Strategic Planning
   "Show me growth trends" [Historical analysis]
   "When will we need more capacity?" [Forecasting]
```

---

**Total Tools: 55** (48 API + 7 Fast Cache)
**Questions Covered: 141**
**Demo Scenarios: 15**

This comprehensive list demonstrates all capabilities of the MCP OCI OPSI server from fast inventory queries to detailed performance diagnostics, capacity planning, and fleet management.
