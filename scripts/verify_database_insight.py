import os
#!/usr/bin/env python3
"""Verify database insight is properly enabled and accessible."""

from mcp_oci_opsi.tools.tools_opsi import list_database_insights
from mcp_oci_opsi.tools.tools_database_discovery import get_database_api_compatibility

COMPARTMENT_ID = os.getenv("OCI_COMPARTMENT_ID", "ocid1.compartment.oc1..example")
DATABASE_INSIGHT_ID = os.getenv("OPSI_DATABASE_ID", "ocid1.opsidatabaseinsight.oc1..example")

print("=" * 80)
print("VERIFYING DATABASE INSIGHT STATUS")
print("=" * 80)
print()

# List all database insights in compartment
print("1. Listing all database insights in compartment...")
print()

result = list_database_insights(compartment_id=COMPARTMENT_ID)

if "error" in result:
    print(f"❌ Error: {result['error']}")
else:
    print(f"✅ Found {result.get('count', 0)} database insights")
    print()

    # Find our specific database
    for item in result.get('items', []):
        if item.get('id') == DATABASE_INSIGHT_ID:
            print("Found Sales_US database insight:")
            print(f"  ID: {item.get('id')}")
            print(f"  Database ID: {item.get('database_id')}")
            print(f"  Database Name: {item.get('database_name')}")
            print(f"  Database Type: {item.get('database_type')}")
            print(f"  Status: {item.get('status')}")
            print(f"  Lifecycle State: {item.get('lifecycle_state')}")
            print(f"  Entity Source: {item.get('entity_source')}")
            print()

print("=" * 80)
print("2. Checking API compatibility for this database...")
print()

compat_result = get_database_api_compatibility(
    database_insight_id=DATABASE_INSIGHT_ID
)

if "error" in compat_result:
    print(f"❌ Error: {compat_result['error']}")
else:
    print(f"Database: {compat_result.get('database_name', 'Unknown')}")
    print(f"Entity Source: {compat_result.get('entity_source', 'Unknown')}")
    print(f"Priority: {compat_result.get('priority', 'Unknown')}")
    print()
    print("API Compatibility:")

    apis = compat_result.get('compatible_apis', {})
    for api_name, supported in apis.items():
        status = "✅" if supported else "❌"
        print(f"  {status} {api_name}")

    print()
    if compat_result.get('recommendations'):
        print("Recommendations:")
        for rec in compat_result['recommendations']:
            print(f"  • {rec}")

print("=" * 80)
