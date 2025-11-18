# Quick Start Guide

Get started with MCP OCI OPSI Server in minutes.

---

## First Steps

### 1. Verify Installation

```bash
# Check Python environment
python3 --version  # Should be 3.8+

# Verify OCI CLI
oci --version

# Test OCI connectivity
oci iam region list
```

### 2. Build Cache

```bash
# Build cache interactively
python3 build_cache.py --select-profile

# Follow prompts to select your OCI profile
```

### 3. Run Your First Query

```python
from mcp_oci_opsi.tools_cache import get_cached_statistics

# Get fleet statistics
stats = get_cached_statistics()

print(f"Total databases: {stats['statistics']['total_databases']}")
print(f"Total hosts: {stats['statistics']['total_hosts']}")
print(f"Profile: {stats['statistics']['profile']}")
```

---

## Common Tasks

### List All Databases

```python
from mcp_oci_opsi.tools_cache import search_cached_databases

# Get all databases
result = search_cached_databases()

print(f"Found {result['count']} databases:\n")
for db in result['databases']:
    print(f"  • {db['database_name']} ({db['database_type']})")
    print(f"    Status: {db['status']}")
    print(f"    ID: {db['id']}")
    print()
```

### Check Agent Adoption

```python
from mcp_oci_opsi.tools_database_discovery import list_database_insights_by_management_type

# Get agent statistics
result = list_database_insights_by_management_type(
    compartment_id="ocid1.compartment.oc1..xxx"
)

summary = result['summary']
print(f"Total databases: {summary['total_databases']}")
print(f"Agent-based: {summary['agent_based_databases']} ({summary['agent_based_percentage']}%)")
print(f"\nRecommendation: {summary['recommendation']}")
```

### Monitor CPU Usage

```python
from mcp_oci_opsi.tools_opsi_resource_stats import summarize_database_insight_resource_statistics

# Get CPU statistics
stats = summarize_database_insight_resource_statistics(
    compartment_id="ocid1.compartment.oc1..xxx",
    resource_metric="CPU"
)

print("Database CPU Utilization:\n")
for item in stats['items']:
    db_name = item['database_details']['database_name']
    utilization = item['current_statistics']['utilization_percent']
    usage = item['current_statistics']['usage']
    capacity = item['current_statistics']['capacity']

    print(f"  {db_name}:")
    print(f"    Utilization: {utilization}%")
    print(f"    Usage: {usage} / {capacity}")
    print()
```

### Check Database Users

```python
from mcp_oci_opsi.tools_dbmanagement_users import list_users

# List database users
users = list_users(
    managed_database_id="ocid1.manageddatabase.oc1..xxx"
)

print(f"Total users: {users['count']}\n")
for user in users['items'][:10]:  # Show first 10
    print(f"  • {user['name']}")
    print(f"    Status: {user['status']}")
    print(f"    Profile: {user.get('profile', 'DEFAULT')}")
    print()
```

### Monitor Tablespace Usage

```python
from mcp_oci_opsi.tools_dbmanagement_tablespaces import list_tablespaces

# Get tablespace information
tablespaces = list_tablespaces(
    managed_database_id="ocid1.manageddatabase.oc1..xxx"
)

print(f"Total tablespaces: {tablespaces['count']}\n")
for ts in tablespaces['items']:
    name = ts['name']
    size_mb = ts.get('allocated_size_in_mbs', 0)
    used_mb = ts.get('used_size_in_mbs', 0)
    pct_used = (used_mb / size_mb * 100) if size_mb > 0 else 0

    print(f"  {name}:")
    print(f"    Size: {size_mb:.2f} MB")
    print(f"    Used: {used_mb:.2f} MB ({pct_used:.1f}%)")
    print(f"    Type: {ts.get('type', 'UNKNOWN')}")
    print()
```

### Analyze AWR Wait Events

```python
from mcp_oci_opsi.tools_dbmanagement_awr_metrics import summarize_awr_db_wait_event_buckets

# Get wait events for last 24 hours
from datetime import datetime, timedelta

end_time = datetime.utcnow()
start_time = end_time - timedelta(days=1)

wait_events = summarize_awr_db_wait_event_buckets(
    managed_database_id="ocid1.manageddatabase.oc1..xxx",
    time_greater_than_or_equal_to=start_time.strftime("%Y-%m-%dT%H:%M:%SZ"),
    time_less_than_or_equal_to=end_time.strftime("%Y-%m-%dT%H:%M:%SZ")
)

print("Top Wait Events:\n")
for event in wait_events['items'][:10]:  # Top 10
    print(f"  {event['name']}:")
    print(f"    Total time: {event.get('total_time_waited', 0)} ms")
    print(f"    Waits: {event.get('total_waits', 0)}")
    print()
```

---

## Quick Reference

### Get Database by Name

```python
from mcp_oci_opsi.tools_cache import search_cached_databases

# Search by name
result = search_cached_databases(database_name="PROD")

if result['count'] > 0:
    db = result['databases'][0]
    print(f"Found: {db['database_name']}")
    print(f"ID: {db['id']}")
```

### Get Database by Compartment

```python
from mcp_oci_opsi.tools_cache import get_databases_by_compartment

# Get all databases in a compartment
result = get_databases_by_compartment(
    compartment_id="ocid1.compartment.oc1..xxx"
)

print(f"Databases in compartment: {result['count']}")
```

### Get SQL Statistics

```python
from mcp_oci_opsi.tools_opsi import summarize_sql_statistics

# Get top SQL by executions
sql_stats = summarize_sql_statistics(
    compartment_id="ocid1.compartment.oc1..xxx",
    database_id=["ocid1.databaseinsight.oc1..xxx"]
)

print("Top SQL Statements:\n")
for sql in sql_stats['items'][:5]:  # Top 5
    print(f"  SQL ID: {sql['sql_identifier']}")
    print(f"    Executions: {sql['executions_count']}")
    print(f"    CPU time: {sql['cpu_time_in_sec']}s")
    print()
```

### Get AWR Report

```python
from mcp_oci_opsi.tools_dbmanagement import get_awr_db_report

# Generate AWR report
awr = get_awr_db_report(
    managed_database_id="ocid1.manageddatabase.oc1..xxx",
    awr_db_id="12345",
    begin_snapshot_id=100,
    end_snapshot_id=102
)

# Save to file
with open("awr_report.html", "w") as f:
    f.write(awr['report'])

print("AWR report saved to awr_report.html")
```

---

## Working with Multiple Profiles

### List Available Profiles

```python
from mcp_oci_opsi.tools_profile_management import list_oci_profiles_enhanced

# Get all profiles
profiles = list_oci_profiles_enhanced()

print("Available OCI Profiles:\n")
for profile in profiles['profiles']:
    status = "✅" if profile['valid'] else "❌"
    print(f"  {status} {profile['name']}")
    print(f"     Region: {profile['region']}")
    print(f"     Tenancy: {profile.get('tenancy_name', 'Unknown')}")
    print()
```

### Switch Between Profiles

```python
# Method 1: Pass profile parameter
from mcp_oci_opsi.tools_cache import search_cached_databases

# Use production profile
prod_dbs = search_cached_databases(profile="production")

# Use development profile
dev_dbs = search_cached_databases(profile="development")

# Method 2: Set environment variable
import os
os.environ['OCI_CLI_PROFILE'] = 'production'

# Now all operations use production profile
result = search_cached_databases()
```

### Compare Profiles

```python
from mcp_oci_opsi.tools_profile_management import compare_oci_profiles

# Compare two profiles
comparison = compare_oci_profiles(
    profile1="production",
    profile2="development"
)

print("Profile Comparison:\n")
print(f"Production:")
print(f"  Region: {comparison['profile1']['region']}")
print(f"  Tenancy: {comparison['profile1']['tenancy_ocid']}")
print()
print(f"Development:")
print(f"  Region: {comparison['profile2']['region']}")
print(f"  Tenancy: {comparison['profile2']['tenancy_ocid']}")
print()
print(f"Same tenancy: {comparison['same_tenancy']}")
print(f"Same region: {comparison['same_region']}")
```

---

## Performance Tips

### Use Cache for Fast Queries

```python
# ✅ FAST (cached, <50ms)
from mcp_oci_opsi.tools_cache import get_cached_database

db = get_cached_database("ocid1.databaseinsight.oc1..xxx")

# ❌ SLOW (API call, 1-2 seconds)
from mcp_oci_opsi.tools_database_discovery import get_database_insight

db = get_database_insight("ocid1.databaseinsight.oc1..xxx")
```

### Batch Operations

```python
# ✅ GOOD - Single API call
database_ids = [
    "ocid1.databaseinsight.oc1..xxx",
    "ocid1.databaseinsight.oc1..yyy",
    "ocid1.databaseinsight.oc1..zzz"
]

stats = summarize_database_insight_resource_statistics(
    compartment_id="ocid1.compartment.oc1..xxx",
    database_id=database_ids  # Pass list
)

# ❌ BAD - Multiple API calls
for db_id in database_ids:
    stats = summarize_database_insight_resource_statistics(
        compartment_id="ocid1.compartment.oc1..xxx",
        database_id=[db_id]  # Separate calls
    )
```

### Refresh Cache Regularly

```bash
# Add to crontab for daily refresh
0 2 * * * cd /path/to/mcp-oci-opsi && python3 build_cache.py --profile production
```

---

## Common Errors and Solutions

### Error: ProfileNotFound

```python
# Error: Profile 'xyz' not found
# Solution: Check available profiles
from mcp_oci_opsi.tools_profile_management import list_oci_profiles_enhanced

profiles = list_oci_profiles_enhanced()
print([p['name'] for p in profiles['profiles']])
```

### Error: 404 on SQL Statistics

```python
# Error: 404 - EM-managed databases don't support SQL statistics API
# Solution: Check agent type first
from mcp_oci_opsi.tools_database_discovery import get_database_api_compatibility

compat = get_database_api_compatibility(
    database_insight_id="ocid1.databaseinsight.oc1..xxx"
)

if compat['entity_source'] == 'EM_MANAGED_EXTERNAL_DATABASE':
    print("⚠️ Use warehouse queries instead of SQL statistics API")
    # Use query_warehouse_standard instead
```

### Error: Cache Empty

```bash
# Error: Cache is empty or not built
# Solution: Build cache
python3 build_cache.py --select-profile
```

---

## Next Steps

### Learn More Features
1. **[Agent Detection](./Agent-Detection)** - Understand agent types and priorities
2. **[Multi-Tenancy](./Multi-Tenancy)** - Work with multiple OCI accounts
3. **[Resource Monitoring](./Resource-Monitoring)** - Advanced resource analytics
4. **[User Management](./User-Management)** - Audit users and privileges
5. **[AWR Analysis](./AWR-Analysis)** - Performance troubleshooting

### Explore All Tools
- **[Tool Reference](./Tool-Reference)** - Complete catalog of 117 tools
- **[API Coverage](./API-Coverage)** - Detailed API coverage report

### Get Help
- **[Troubleshooting](./Troubleshooting)** - Common issues and solutions
- **[FAQ](./FAQ)** - Frequently asked questions

---

## Code Examples Repository

All examples from this guide are available in the `examples/` directory:

```bash
# Run example scripts
cd examples

# List databases
python3 01_list_databases.py

# Check agent adoption
python3 02_agent_adoption.py

# Monitor resources
python3 03_resource_monitoring.py

# User audit
python3 04_user_audit.py
```

---

**Last Updated**: 2025-11-18
**Version**: 2.0.0
**Tools**: 117
