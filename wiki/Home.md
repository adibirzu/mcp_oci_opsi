# Welcome to MCP OCI OPSI Server Wiki

**MCP server for Oracle Cloud Infrastructure Operations Insights and Database Management (v3)**

[![Version](https://img.shields.io/badge/version-3.0.0-blue.svg)](../README.md)

---

## 🚀 Quick Links

- **[Installation](./Installation)** - Get started quickly
- **[Configuration](./Configuration)** - OCI auth + transport options
- **[Quick Start](./Quick-Start)** - Common usage examples
- **[Troubleshooting](./Troubleshooting)** - Common issues and solutions
- **[API Coverage](./API-Coverage)** - Detailed API coverage report

---

## 📊 What's New in v3

- Structured logging + health tools for all sub-servers
- Async cache build tasks (`cache_start_cache_build_task` + `cache_get_task_status`)
- Prebuilt prompts and troubleshooting playbook for cache-first DBA workflows
- Pagination + rate-limit hints on OPSI/DBM tools for safer large-tenancy usage

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

- Cache-first workflow (zero API calls) with async background builds
- Prompt templates and troubleshooting playbook for guided tool use
- Health/readiness tools for cache/OPSI/DBM/admin servers
- Multi-tenancy via OCI CLI profiles

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
10. **[API Coverage](./API-Coverage)** - API coverage details
11. **[Troubleshooting](./Troubleshooting)** - Common issues

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
    compartment_id="[Link to Secure Variable: OCI_COMPARTMENT_OCID]"
)

print(f"Agent adoption: {result['summary']['agent_based_percentage']}%")
```

### 2. Monitor CPU Usage
```python
from mcp_oci_opsi.tools_opsi_resource_stats import summarize_database_insight_resource_statistics

stats = summarize_database_insight_resource_statistics(
    compartment_id="[Link to Secure Variable: OCI_COMPARTMENT_OCID]",
    resource_metric="CPU"
)

for db in stats['items']:
    print(f"{db['database_details']['database_name']}: {db['current_statistics']['utilization_percent']}%")
```

### 3. Audit Database Users
```python
from mcp_oci_opsi.tools_dbmanagement_users import list_users

users = list_users(managed_database_id="[Link to Secure Variable: OCI_MANAGED_DATABASE_OCID]")
print(f"Total users: {users['count']}")
```

### 4. Analyze Wait Events
```python
from mcp_oci_opsi.tools_dbmanagement_awr_metrics import summarize_awr_db_wait_event_buckets

events = summarize_awr_db_wait_event_buckets(
    managed_database_id="[Link to Secure Variable: OCI_MANAGED_DATABASE_OCID]",
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
