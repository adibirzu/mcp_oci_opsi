# Welcome to MCP OCI OPSI Server Wiki

**Enhanced MCP server for Oracle Cloud Infrastructure Operations Insights and Database Management**

[![Version](https://img.shields.io/badge/version-2.0.0-blue.svg)](https://github.com/your-org/mcp-oci-opsi)
[![Tools](https://img.shields.io/badge/tools-117-green.svg)](./API-Coverage)
[![Coverage](https://img.shields.io/badge/API%20coverage-52%25-yellow.svg)](./API-Coverage)

---

## 🚀 Quick Links

- **[Installation Guide](./Installation)** - Get started in 5 minutes
- **[Configuration](./Configuration)** - Configure for your environment
- **[Quick Start](./Quick-Start)** - Common usage examples
- **[Tool Reference](./Tool-Reference)** - Complete tool catalog (117 tools)
- **[API Coverage](./API-Coverage)** - Detailed API coverage report
- **[Troubleshooting](./Troubleshooting)** - Common issues and solutions

---

## 📊 What's New in v2.0

### Major Enhancements (November 2025)

✨ **18 New APIs** for detailed database analysis
✨ **Agent Detection** - Automatic MACS vs Cloud Agent classification
✨ **Multi-Tenancy** - Support for multiple OCI accounts
✨ **Enhanced Analytics** - Resource stats, user mgmt, tablespace monitoring, AWR metrics

**Statistics:**
- Tool Count: 99 → **117** (+18%)
- API Coverage: 48% → **52%**
- Test Success: **100%**

---

## 🎯 Features

### Core Capabilities

#### Operations Insights (66 tools)
- Database performance monitoring
- Host resource analysis
- SQL performance analytics
- Capacity planning and forecasting
- Exadata infrastructure monitoring

#### Database Management (51 tools)
- Fleet management
- User and role management **[NEW]**
- Tablespace monitoring **[NEW]**
- AWR performance analysis **[NEW]**
- SQL Plan Baseline management
- Performance Hub (ADDM, ASH, AWR)

### Enhanced Features

#### 🤖 Agent Detection
- Automatic MACS vs Cloud Agent identification
- Priority-based classification
- API compatibility matrix
- Migration recommendations

#### 👥 Multi-Tenancy
- Multiple OCI account support
- Interactive profile selection
- No environment changes needed

#### 📈 Advanced Analytics
- Resource statistics & trends
- User privilege auditing
- Tablespace growth patterns
- AWR metrics analysis

---

## 📖 Documentation Structure

### Getting Started
1. **[Installation](./Installation)** - Install and setup
2. **[Configuration](./Configuration)** - Configure OCI credentials
3. **[Quick Start](./Quick-Start)** - First steps and examples

### Features
4. **[Agent Detection](./Agent-Detection)** - Agent type classification
5. **[Multi-Tenancy](./Multi-Tenancy)** - Multiple account management
6. **[Resource Monitoring](./Resource-Monitoring)** - Resource analytics
7. **[User Management](./User-Management)** - User and role management
8. **[Tablespace Management](./Tablespace-Management)** - Storage monitoring
9. **[AWR Analysis](./AWR-Analysis)** - Performance troubleshooting

### Reference
10. **[Tool Reference](./Tool-Reference)** - Complete tool catalog
11. **[API Coverage](./API-Coverage)** - API coverage details
12. **[Performance](./Performance)** - Benchmarks and optimization

### Advanced
13. **[Development](./Development)** - Contributing and development
14. **[Troubleshooting](./Troubleshooting)** - Common issues
15. **[FAQ](./FAQ)** - Frequently asked questions

---

## 🎓 Learning Path

### Beginner
1. Install and configure (15 minutes)
2. Build initial cache (5 minutes)
3. Run first query (5 minutes)
4. Explore cached data (10 minutes)

### Intermediate
1. Agent detection and classification
2. Multi-tenancy operations
3. Resource monitoring
4. User auditing

### Advanced
1. AWR performance analysis
2. Capacity forecasting
3. Custom analytics
4. Bulk operations

---

## 💡 Use Cases

### For Database Administrators
- Monitor database fleet health
- Identify performance bottlenecks
- Manage users and privileges
- Track tablespace growth
- Analyze AWR reports

### For Performance Analysts
- SQL performance analysis
- Wait event identification
- Resource utilization tracking
- Trend analysis
- Capacity planning

### For Security Teams
- User access auditing
- Privilege review
- Role management
- Proxy connection monitoring

### For Capacity Planners
- Resource forecasting
- Growth trend analysis
- Capacity threshold monitoring
- Storage planning

---

## 🔧 Quick Examples

### 1. List Databases by Agent Type
```python
from mcp_oci_opsi.tools_database_discovery import list_database_insights_by_management_type

result = list_database_insights_by_management_type(
    compartment_id="ocid1.compartment.oc1..xxx"
)

print(f"Agent adoption: {result['summary']['agent_based_percentage']}%")
```

### 2. Monitor CPU Usage
```python
from mcp_oci_opsi.tools_opsi_resource_stats import summarize_database_insight_resource_statistics

stats = summarize_database_insight_resource_statistics(
    compartment_id="ocid1.compartment.oc1..xxx",
    resource_metric="CPU"
)

for db in stats['items']:
    print(f"{db['database_details']['database_name']}: {db['current_statistics']['utilization_percent']}%")
```

### 3. Audit Database Users
```python
from mcp_oci_opsi.tools_dbmanagement_users import list_users

users = list_users(managed_database_id="ocid1.manageddatabase.oc1..xxx")
print(f"Total users: {users['count']}")
```

### 4. Analyze Wait Events
```python
from mcp_oci_opsi.tools_dbmanagement_awr_metrics import summarize_awr_db_wait_event_buckets

events = summarize_awr_db_wait_event_buckets(
    managed_database_id="ocid1.manageddatabase.oc1..xxx",
    time_greater_than_or_equal_to="2025-11-17T00:00:00Z",
    time_less_than_or_equal_to="2025-11-18T00:00:00Z"
)

for event in events['items']:
    print(f"{event['name']}: {event['total_time_waited']}ms")
```

---

## 📞 Support

- 📖 **Documentation**: This wiki
- 🐛 **Issues**: [GitHub Issues](https://github.com/your-org/mcp-oci-opsi/issues)
- 💬 **Discussions**: [GitHub Discussions](https://github.com/your-org/mcp-oci-opsi/discussions)
- 📧 **Email**: support@your-org.com

---

## 🤝 Contributing

We welcome contributions! See [Development](./Development) for guidelines.

---

## 📜 License

MIT License - See [LICENSE](../LICENSE) for details.

---

**Last Updated**: 2025-11-18
**Version**: 2.0.0
**Tools**: 117
**Coverage**: 52%
