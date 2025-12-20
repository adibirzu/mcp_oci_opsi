# MCP OCI OPSI Server v2.0 - Demo Guide

## Overview

The v2.0 demo scripts demonstrate **117 tools** including 18 new APIs with enhanced capabilities for agent detection, multi-tenancy, user management, and performance monitoring.

---

## 🎉 What's New in v2.0

### Quick Stats
- **Total Tools**: 117 (up from 99)
- **New APIs**: +18
- **New Features**: 5 major enhancements
- **Documentation**: 85% complete

### Major Features Demonstrated
1. 🤖 **Agent Detection & Prioritization**
2. 👥 **Multi-Tenancy Support**
3. 📊 **Resource Statistics**
4. 🔐 **User Management**
5. ⚡ **AWR Performance Metrics**

---

## 📂 Demo Scripts

### 1. v2.0 New Features Demo (`demo_v2_features.py`)

**Focus**: Showcases all new v2.0 capabilities

**Sections**:
1. Agent Detection & Prioritization (2 demos)
2. Multi-Tenancy & Profile Management (2 demos)
3. Resource Statistics & Monitoring (2 demos)
4. User & Privilege Management (requires managed DB)
5. AWR Performance Metrics (requires managed DB)

**Run It**:
```bash
cd /Users/abirzu/dev/mcp_oci_opsi
source .venv/bin/activate
python3 demo_v2_features.py
```

### 2. Original Features Demo (`demo_opsi_features.py`)

**Focus**: Host insights and SQL analytics (15 demos)

**Covers**: Database insights, host monitoring, capacity planning, SQL statistics

**Run It**:
```bash
python3 demo_opsi_features.py
```

---

## 🤖 Section 1: Agent Detection

### Demo 1.1: Fleet Classification
**Question**: *"Classify all databases by agent type"*

**Shows**:
```
Fleet Summary:
  Total Databases: 57
  Agent-Based: 8 (14.0%)
  Non-Agent: 49

Breakdown by Agent Type:
  🤖 [Priority 1] Management Agent (MACS): 5
  🤖 [Priority 1] Autonomous Database: 3
  📋 [Priority 3] EM-Managed: 49
```

**Key Insights**:
- Agent adoption percentage
- Priority classification (1-3)
- Migration recommendations

### Demo 1.2: API Compatibility Check
**Question**: *"Which APIs work with this database?"*

**Shows**:
```
Database: PRODDB
Entity Source: MACS_MANAGED_EXTERNAL_DATABASE
Priority: 1

API Compatibility:
  ✅ list_database_insights
  ✅ summarize_sql_statistics
  ✅ summarize_database_insight_resource_statistics
  ✅ get_sql_plan

Recommendations:
  • Full API support available
  • All 117 tools compatible
```

---

## 👥 Section 2: Multi-Tenancy

### Demo 2.1: Profile Management
**Question**: *"List all OCI profiles and validate them"*

**Shows**:
```
Profile Summary:
  Total Profiles: 3
  Valid: 2
  Invalid: 1

Available Profiles:
  ✅ DEFAULT
     Region: us-phoenix-1
     Tenancy: CompanyA

  ✅ production
     Region: us-ashburn-1
     Tenancy: CompanyB

  ❌ sandbox
     Error: Invalid API key fingerprint
```

### Demo 2.2: Profile Comparison
**Question**: *"Compare production and development profiles"*

**Shows**:
```
Comparing: production vs development

Profile 1 (production):
  Tenancy: CompanyB
  Region: us-ashburn-1

Profile 2 (development):
  Tenancy: CompanyC
  Region: eu-frankfurt-1

Comparison:
  Same Tenancy: ❌
  Same Region: ❌
  Same User: ❌

ℹ️ These profiles access different tenancies
```

---

## 📊 Section 3: Resource Statistics

### Demo 3.1: CPU Utilization
**Question**: *"Show CPU utilization across all databases"*

**Shows**:
```
Database 1: PROD-DB-01
  Type: EXTERNAL-PDB
  Utilization: 67.3%
  Usage: 2.4 cores
  Capacity: 3.6 cores

Database 2: TEST-DB-01
  Type: AUTONOMOUS
  Utilization: 23.1%
  Usage: 1.1 cores
  Capacity: 4.8 cores
```

**Use Case**: Real-time capacity monitoring

### Demo 3.2: Tablespace Trends
**Question**: *"Show tablespace growth for capacity planning"*

**Shows**:
```
Tablespace 1: USERS
  Database: PROD-DB-01
  Size (GB): 500.00
  Used (GB): 425.50
  Usage %: 85.1%

Tablespace 2: SYSTEM
  Database: PROD-DB-01
  Size (GB): 100.00
  Used (GB): 42.30
  Usage %: 42.3%
```

**Use Case**: Storage capacity planning

---

## 🔐 Section 4: User Management

### Demo 4.1: User Audit
**Question**: *"List all database users for security audit"*

**Shows**:
```
Total users: 127

Item 1:
  name: ADMIN
  status: OPEN
  profile: DEFAULT
  authentication_type: PASSWORD

Item 2:
  name: APP_USER
  status: OPEN
  profile: APP_PROFILE
  authentication_type: PASSWORD
```

**Use Case**: Security compliance, privilege review

### Demo 4.2: Role Management
**Question**: *"Show all database roles"*

**Shows**:
```
Total roles: 45

Item 1:
  name: DBA
  common: YES
  oracle_maintained: YES

Item 2:
  name: APP_ADMIN_ROLE
  common: NO
  oracle_maintained: NO
```

**Use Case**: Role-based access control

---

## ⚡ Section 5: AWR Metrics

### Demo 5.1: CPU Usage Analysis
**Question**: *"Show CPU usage trends from AWR"*

**Shows**:
```
Item 1:
  timestamp: 2025-11-18T10:00:00Z
  usage_pct: 65.3
  load: 2.8

Item 2:
  timestamp: 2025-11-18T11:00:00Z
  usage_pct: 72.1
  load: 3.2
```

**Use Case**: Performance trending

### Demo 5.2: Wait Event Analysis
**Question**: *"Identify top wait events"*

**Shows**:
```
Item 1:
  name: db file sequential read
  total_time_waited: 125,430 ms
  total_waits: 45,230

Item 2:
  name: log file sync
  total_time_waited: 98,120 ms
  total_waits: 23,450
```

**Use Case**: Performance troubleshooting

---

## 🚀 Running the Demos

### Prerequisites

1. **OCI CLI configured**:
   ```bash
   oci setup config
   ```

2. **Virtual environment activated**:
   ```bash
   cd /Users/abirzu/dev/mcp_oci_opsi
   source .venv/bin/activate
   ```

3. **Compartment ID**:
   - Update `COMPARTMENT_ID` in demo scripts
   - Get from OCI Console or: `oci iam compartment list --all`

### Quick Start

```bash
# Run v2.0 feature demo
python3 demo_v2_features.py

# Run original host insights demo
python3 demo_opsi_features.py
```

### Expected Runtime
- **v2.0 Demo**: 1-2 minutes (10 API calls)
- **Original Demo**: 2-3 minutes (15 API calls)

---

## 📋 Demo Checklist

Before running demos, verify:

- ✅ OCI CLI installed and configured
- ✅ Virtual environment activated
- ✅ Compartment ID configured
- ✅ Operations Insights enabled in compartment
- ✅ At least one database with OPSI enabled
- ✅ IAM permissions configured

### Required IAM Permissions

```
Allow group demo-users to read opsi-namespace in compartment Demo
Allow group demo-users to read database-family in compartment Demo
Allow group demo-users to read database-management-family in compartment Demo
```

---

## 🎯 Use Cases by Role

### For Database Administrators
**Run**: v2.0 Demo (Sections 1, 3, 4, 5)
**Focus**: Agent detection, resource monitoring, user auditing, performance

### For Capacity Planners
**Run**: Original Demo + v2.0 Section 3
**Focus**: CPU forecasts, memory trends, tablespace growth

### For Security Teams
**Run**: v2.0 Section 4
**Focus**: User management, privilege auditing, role review

### For Performance Engineers
**Run**: v2.0 Section 5 + Original Demo (SQL stats)
**Focus**: AWR metrics, wait events, SQL performance

---

## 🔧 Customization

### Change Time Range

```python
# In demo script
TIME_START = TIME_END - timedelta(days=30)  # Change to 30 days
```

### Change Compartment

```python
# In demo script
COMPARTMENT_ID = "[Link to Secure Variable: OCI_COMPARTMENT_OCID]"
```

### Add Managed Database

```python
# For user/AWR demos
MANAGED_DATABASE_ID = "[Link to Secure Variable: OCI_MANAGED_DATABASE_OCID]"
```

---

## 🐛 Troubleshooting

### No Data Returned

**Issue**: Empty results from API calls

**Solutions**:
1. Check Operations Insights is enabled
2. Verify time range has data (try 30 days)
3. Check IAM permissions
4. Verify compartment has databases

### Connection Timeout

**Issue**: API calls timing out

**Solutions**:
1. Check network connectivity to OCI
2. Verify OCI CLI can connect: `oci iam region list`
3. Check firewall/proxy settings

### Profile Not Found

**Issue**: "ProfileNotFound" error

**Solutions**:
1. List available profiles: `cat ~/.oci/config | grep "^\["`
2. Use correct profile name
3. Run `oci setup config` if needed

---

## 📊 Sample Output

### Successful Run

```
================================================================================
MCP OCI OPSI SERVER v2.0 - NEW FEATURES DEMO
================================================================================

🎉 What's New in v2.0:
  ✨ 18 new APIs
  🤖 Agent detection & prioritization
  👥 Multi-tenancy support
  📊 Resource statistics
  🔐 User management
  💾 Tablespace monitoring
  ⚡ AWR performance metrics

Compartment: [Link to Secure Variable: OCI_COMPARTMENT_OCID]
Time Range: 2025-11-11T00:00:00Z to 2025-11-18T00:00:00Z
Duration: 7 days

🤖 🤖 🤖 🤖 🤖 🤖 🤖 🤖 🤖 🤖 🤖 🤖 🤖 🤖 🤖 🤖 🤖 🤖 🤖 🤖
SECTION 1: AGENT DETECTION & PRIORITIZATION
🤖 🤖 🤖 🤖 🤖 🤖 🤖 🤖 🤖 🤖 🤖 🤖 🤖 🤖 🤖 🤖 🤖 🤖 🤖 🤖

================================================================================
1. Agent Detection - Database Fleet Classification
================================================================================
PROMPT: Classify all databases by agent type and show adoption rate

📊 Fleet Summary:
   Total Databases: 57
   Agent-Based: 8 (14.0%)
   Non-Agent: 49

💡 ⚠️ Consider migrating non-agent databases to MACS for full API support

📋 Breakdown by Agent Type:
   🤖 [Priority 1] Management Agent (MACS): 5
   🤖 [Priority 1] Autonomous Database: 3
   📋 [Priority 3] EM-Managed: 49

... (continues for all sections)
```

---

## 📚 Additional Resources

### Documentation
- [README_UPDATED.md](./README_UPDATED.md) - Complete v2.0 docs
- [V2.0_RELEASE_SUMMARY.md](./V2.0_RELEASE_SUMMARY.md) - Full release notes
- [ROADMAP_STATUS.md](./ROADMAP_STATUS.md) - Roadmap progress

### Wiki Guides
- [Installation](./wiki/Installation.md) - Setup guide
- [Quick Start](./wiki/Quick-Start.md) - Getting started
- [Agent Detection](./wiki/Agent-Detection.md) - Agent features
- [Multi-Tenancy](./wiki/Multi-Tenancy.md) - Profile management
- [Troubleshooting](./wiki/Troubleshooting.md) - Common issues

### API Reference
- [API Coverage](./wiki/API-Coverage.md) - All 117 tools
- [DOCUMENTATION_INDEX.md](./DOCUMENTATION_INDEX.md) - Doc index

---

## ✨ Summary

### v2.0 Demo Highlights

| Feature | Demos | APIs Used |
|---------|-------|-----------|
| Agent Detection | 2 | 2 new |
| Multi-Tenancy | 2 | 7 new |
| Resource Stats | 2 | 4 new |
| User Management | 2 | 6 new |
| AWR Metrics | 2 | 5 new |
| **Total** | **10** | **24 new** |

### Key Takeaways

1. ✅ **117 total tools** available for OCI monitoring
2. ✅ **Read-only design** ensures production safety
3. ✅ **Agent detection** helps optimize API usage
4. ✅ **Multi-tenancy** enables multi-account operations
5. ✅ **Comprehensive monitoring** from infrastructure to SQL

---

**Demo Guide Last Updated**: November 18, 2025
**Version**: 2.0.0
**Total Demos**: 25 (10 new + 15 original)
