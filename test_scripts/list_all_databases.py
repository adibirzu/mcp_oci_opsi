import os
#!/usr/bin/env python3
"""List all database insights and their entity sources."""

from mcp_oci_opsi.tools.tools_opsi import list_database_insights

COMPARTMENT_ID = os.getenv("OCI_COMPARTMENT_ID", "ocid1.compartment.oc1..example")

print("=" * 80)
print("LISTING ALL DATABASE INSIGHTS")
print("=" * 80)
print()

result = list_database_insights(compartment_id=COMPARTMENT_ID)

if "error" in result:
    print(f"❌ Error: {result['error']}")
    exit(1)

print(f"Total databases: {result.get('count', 0)}")
print()

# Group by entity source
by_entity_source = {}
for item in result.get('items', []):
    entity_source = item.get('entity_source', 'UNKNOWN')
    if entity_source not in by_entity_source:
        by_entity_source[entity_source] = []
    by_entity_source[entity_source].append(item)

# Show summary
print("Databases by Entity Source:")
print("-" * 80)
for entity_source, dbs in sorted(by_entity_source.items()):
    print(f"\n{entity_source}: {len(dbs)} databases")

    # Show first 3 of each type
    for i, db in enumerate(dbs[:3], 1):
        print(f"  {i}. {db.get('database_display_name', 'Unknown')}")
        print(f"     Type: {db.get('database_type', 'Unknown')}")
        print(f"     Status: {db.get('status', 'Unknown')}")
        print(f"     ID: {db.get('id', 'Unknown')}")
        print(f"     Database ID: {db.get('database_id', 'Unknown')}")

print()
print("=" * 80)
print()

# Find MACS databases specifically
macs_dbs = []
for entity_source, dbs in by_entity_source.items():
    if 'MACS' in entity_source:
        macs_dbs.extend(dbs)

print(f"MACS-Managed Databases: {len(macs_dbs)}")
if macs_dbs:
    for i, db in enumerate(macs_dbs[:5], 1):
        print(f"\n  {i}. {db.get('database_display_name', 'Unknown')}")
        print(f"     Entity Source: {db.get('entity_source', 'Unknown')}")
        print(f"     Database Insight ID: {db.get('id', 'Unknown')}")
