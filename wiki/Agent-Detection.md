# Agent Detection & Prioritization

Comprehensive guide to the agent detection features in MCP OCI OPSI Server.

---

## Overview

The agent detection system automatically identifies and classifies databases based on their monitoring agent type, providing insights into API compatibility and migration opportunities.

### Key Features

- ✅ Automatic agent type detection
- ✅ Priority-based classification (1-3 scale)
- ✅ Agent adoption percentage tracking
- ✅ API compatibility matrix
- ✅ Smart migration recommendations

---

## Agent Types

### Priority 1 (Highest) - Full API Support

#### Management Agent (MACS)
- **Entity Source**: `MACS_MANAGED_EXTERNAL_DATABASE`
- **Agent Type**: Management Agent Cloud Service (MACS)
- **API Support**: ✅ Full Support (all APIs)
- **Recommended**: ✅ Yes

**Capabilities**:
- Complete SQL statistics
- Full resource monitoring
- Capacity planning
- Forecasting
- SQL plan analysis
- Warehouse queries

#### Autonomous Database
- **Entity Source**: `AUTONOMOUS` or `AUTONOMOUS_DATABASE`
- **Agent Type**: Cloud Agent (Built-in)
- **API Support**: ✅ Full Support
- **Recommended**: ✅ Yes

**Capabilities**:
- Native OCI integration
- All OPSI APIs supported
- Real-time metrics
- Advanced analytics

### Priority 2 (Medium) - Good API Support

#### PE Co-managed Database
- **Entity Source**: `PE_COMANAGED_DATABASE`
- **Agent Type**: Cloud Agent (Co-managed)
- **API Support**: ✅ Good Support
- **Recommended**: ✅ Yes

#### MySQL Database Service
- **Entity Source**: `MDS_MYSQL_DATABASE_SYSTEM`
- **Agent Type**: Cloud Agent (Built-in)
- **API Support**: ✅ Good Support (limited SQL APIs)
- **Recommended**: ✅ Yes

### Priority 3 (Lowest) - Limited API Support

#### Enterprise Manager Managed
- **Entity Source**: `EM_MANAGED_EXTERNAL_DATABASE`
- **Agent Type**: Enterprise Manager Agent
- **API Support**: ⚠️ Partial Support
- **Recommended**: ❌ No (migrate to MACS)

**Limitations**:
- SQL Statistics API returns 404
- Use warehouse queries instead
- Limited capacity planning
- Delayed resource statistics

**Alternatives**:
- Enable OPSI warehouse for SQL statistics
- Migrate to Management Agent (MACS)
- Use Database Management Service Performance Hub

---

## Usage

### List Databases by Agent Type

```python
from mcp_oci_opsi.tools_database_discovery import list_database_insights_by_management_type

result = list_database_insights_by_management_type(
    compartment_id="ocid1.compartment.oc1..xxx",
    profile="production"  # Optional
)

# View summary
summary = result['summary']
print(f"Total databases: {summary['total_databases']}")
print(f"Agent-based: {summary['agent_based_databases']}")
print(f"Adoption: {summary['agent_based_percentage']}%")
print(f"Recommendation: {summary['recommendation']}")
```

### Check Agent Adoption

```python
# Get agent adoption percentage
adoption = result['summary']['agent_based_percentage']

if adoption > 80:
    print("✅ Excellent! Most databases use agent-based monitoring")
elif adoption > 50:
    print("⚠️ Good, but consider migrating remaining databases")
else:
    print("❌ Consider migrating to Management Agent (MACS)")
```

### List Databases by Priority

```python
# Get databases sorted by priority
by_type = result['databases_by_type']

# Priority 1 databases (MACS and Autonomous)
high_priority = []
high_priority.extend(by_type.get('MACS_MANAGED_EXTERNAL_DATABASE', []))
high_priority.extend(by_type.get('AUTONOMOUS', []))
high_priority.extend(by_type.get('AUTONOMOUS_DATABASE', []))

print(f"High priority databases: {len(high_priority)}")

# Priority 3 databases (EM-managed - migration candidates)
migration_candidates = by_type.get('EM_MANAGED_EXTERNAL_DATABASE', [])
print(f"Migration candidates: {len(migration_candidates)}")
```

### Get API Compatibility for Database

```python
from mcp_oci_opsi.tools_database_discovery import get_database_api_compatibility

compatibility = get_database_api_compatibility(
    database_insight_id="ocid1.databaseinsight.oc1..xxx"
)

print(f"Entity Source: {compatibility['entity_source']}")
print(f"Database Type: {compatibility['database_type']}")
print("\nAPI Compatibility:")
for api, details in compatibility['api_compatibility'].items():
    status = "✅" if details['supported'] else "❌"
    print(f"  {status} {api}: {details['note']}")

print(f"\nRecommendations:")
for rec in compatibility['recommendations']:
    print(f"  • {rec}")
```

---

## API Compatibility Matrix

### Full Support (Priority 1)

| API | MACS | Autonomous | EM-Managed |
|-----|------|------------|------------|
| `list_database_insights` | ✅ | ✅ | ✅ |
| `summarize_sql_statistics` | ✅ | ✅ | ❌ |
| `summarize_database_insight_resource_statistics` | ✅ | ✅ | ✅ |
| `summarize_database_insight_resource_capacity_trend` | ✅ | ✅ | ✅ |
| `summarize_database_insight_resource_forecast_trend` | ✅ | ✅ | ⚠️ |
| `get_sql_plan` | ✅ | ✅ | ❌ |
| `query_warehouse_standard` | ✅ | ✅ | ✅* |

*Requires warehouse to be enabled

---

## Migration Planning

### Identify Migration Candidates

```python
# Get EM-managed databases
result = list_database_insights_by_management_type(
    compartment_id="ocid1.compartment.oc1..xxx"
)

em_databases = result['databases_by_type'].get('EM_MANAGED_EXTERNAL_DATABASE', [])

if em_databases:
    print(f"⚠️ {len(em_databases)} databases should migrate to MACS:")
    for db in em_databases:
        print(f"  - {db['database_name']} ({db['database_type']})")
        print(f"    ID: {db['database_id']}")
        print(f"    Status: {db['status']}")
        print()
```

### Migration Benefits

**From EM-Managed to MACS:**
- ✅ Full SQL statistics API support
- ✅ SQL plan analysis capabilities
- ✅ Better forecasting accuracy
- ✅ Real-time resource metrics
- ✅ Reduced latency
- ✅ Simplified architecture

---

## Fleet Analysis

### Generate Fleet Report

```python
result = list_database_insights_by_management_type(
    compartment_id="ocid1.compartment.oc1..xxx"
)

print("=" * 80)
print("FLEET MONITORING REPORT")
print("=" * 80)

summary = result['summary']
print(f"\nTotal Databases: {summary['total_databases']}")
print(f"Agent-Based: {summary['agent_based_databases']} ({summary['agent_based_percentage']}%)")
print(f"\n{summary['recommendation']}")

print("\nBreakdown by Type:")
for entity_type, info in summary['by_management_type'].items():
    status = "🤖" if info['agent_based'] else "📋"
    priority = info['priority']
    print(f"  {status} [P{priority}] {info['display_name']}: {info['count']}")
```

### Track Agent Adoption Over Time

```python
import json
from datetime import datetime

# Save current snapshot
snapshot = {
    "timestamp": datetime.utcnow().isoformat(),
    "total": summary['total_databases'],
    "agent_based": summary['agent_based_databases'],
    "percentage": summary['agent_based_percentage'],
    "by_type": {k: v['count'] for k, v in summary['by_management_type'].items()}
}

# Append to history file
with open('agent_adoption_history.json', 'a') as f:
    f.write(json.dumps(snapshot) + '\n')
```

---

## Best Practices

### 1. Regular Monitoring

```python
# Weekly agent adoption check
result = list_database_insights_by_management_type(
    compartment_id="ocid1.compartment.oc1..xxx"
)

adoption = result['summary']['agent_based_percentage']

if adoption < 80:
    # Generate migration plan
    migration_candidates = result['databases_by_type'].get('EM_MANAGED_EXTERNAL_DATABASE', [])
    # Plan migrations...
```

### 2. Prioritize High-Value Databases

```python
# Get production databases first
prod_result = list_database_insights_by_management_type(
    compartment_id="ocid1.compartment.oc1..production"
)

# Focus on EM-managed production databases
em_prod = prod_result['databases_by_type'].get('EM_MANAGED_EXTERNAL_DATABASE', [])
if em_prod:
    print(f"High priority: {len(em_prod)} production databases need migration")
```

### 3. Validate After Migration

```python
# After migrating a database
post_migration = get_database_api_compatibility(
    database_insight_id="ocid1.databaseinsight.oc1..newly-migrated"
)

if post_migration['entity_source'] == 'MACS_MANAGED_EXTERNAL_DATABASE':
    print("✅ Migration successful! Full API support enabled.")
else:
    print("⚠️ Migration incomplete or failed")
```

---

## Troubleshooting

### Agent Type Not Detected

```python
# Manual check
from mcp_oci_opsi.oci_clients import get_opsi_client

client = get_opsi_client()
response = client.get_database_insight("ocid1.databaseinsight.oc1..xxx")
db_insight = response.data

print(f"Entity Source: {db_insight.entity_source}")
print(f"Database Type: {db_insight.database_type}")
```

### API Returns 404 for SQL Statistics

This is expected for EM-managed databases. Use warehouse queries instead:

```python
from mcp_oci_opsi.tools_opsi import query_warehouse_standard

# Use warehouse query instead of summarize_sql_statistics
result = query_warehouse_standard(
    compartment_id="ocid1.compartment.oc1..xxx",
    warehouse_query="SELECT * FROM SQL_STATS WHERE..."
)
```

---

## FAQ

**Q: Can I convert an EM-managed database to MACS?**
A: Yes, by enabling the Management Agent on the database host and reconfiguring OPSI.

**Q: Will migration cause downtime?**
A: No, agent migration typically doesn't require database downtime.

**Q: What's the difference between MACS and Cloud Agent?**
A: MACS is for external databases, Cloud Agent is built-in for OCI-native services.

**Q: Can I have both EM and MACS on the same database?**
A: It's possible but not recommended. Choose one monitoring approach.

---

## Related Pages

- [Multi-Tenancy](./Multi-Tenancy) - Work with multiple OCI accounts
- [Resource Monitoring](./Resource-Monitoring) - Monitor resource usage
- [Troubleshooting](./Troubleshooting) - Common issues and solutions

---

**Last Updated**: 2025-11-18
