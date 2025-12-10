#!/usr/bin/env python3
"""Debug script to check OCID region extraction."""

from mcp_oci_opsi.oci_clients import extract_region_from_ocid

# Test with the database insight OCID
database_insight_ocid = os.getenv("OCI_ID", "ocid1.opsidatabaseinsight.oc1..example")

# Test with the actual database OCID
database_ocid = "ocid1.autonomousdatabase.oc1.phx.abyhqljrle7d5sncqtlnfak4eynlmhjqodvavhfsdwwuhjm5drlw2ouei2qa"

print("OCID Region Extraction Debug")
print("=" * 80)
print()

print("Database Insight OCID:")
print(f"  {database_insight_ocid}")
print(f"  Parts: {database_insight_ocid.split('.')}")
region = extract_region_from_ocid(database_insight_ocid)
print(f"  Extracted Region: {region}")
print()

print("Actual Database OCID:")
print(f"  {database_ocid}")
print(f"  Parts: {database_ocid.split('.')}")
region = extract_region_from_ocid(database_ocid)
print(f"  Extracted Region: {region}")
print()

print("Analysis:")
print("  Database Insight OCID format: ocid1.opsidatabaseinsight.oc1..<unique_id>")
print("  Database OCID format: ocid1.autonomousdatabase.oc1.phx.<unique_id>")
print()
print("  Problem: Database insight OCIDs don't contain region!")
print("  Solution: Need to query the database insight to get the actual database OCID")
