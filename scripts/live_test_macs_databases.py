import os
#!/usr/bin/env python3
"""
Test v2.0 resource statistics APIs with MACS-managed databases.
Verifies if the regional endpoint fix works with Priority 1 databases.
"""

import json
from datetime import datetime, timedelta
from pathlib import Path
import sys



def main():
    ROOT = Path(__file__).resolve().parents[1]
    if str(ROOT) not in sys.path:
        sys.path.insert(0, str(ROOT))

    from mcp_oci_opsi.tools.tools_database_discovery import list_database_insights_by_management_type
    from mcp_oci_opsi.tools.tools_opsi_resource_stats import (
        summarize_database_insight_resource_statistics,
        summarize_database_insight_resource_usage,
        summarize_database_insight_resource_utilization_insight,
        summarize_database_insight_tablespace_usage_trend
    )

    COMPARTMENT_ID = os.getenv("OCI_COMPARTMENT_ID", "ocid1.compartment.oc1..example")
    TIME_START = (datetime.utcnow() - timedelta(days=7)).isoformat() + "Z"
    TIME_END = datetime.utcnow().isoformat() + "Z"

    print("=" * 80)
    print("TESTING V2.0 RESOURCE STATISTICS APIs WITH MACS DATABASES")
    print("=" * 80)
    print()
    print(f"Compartment: {COMPARTMENT_ID}")
    print(f"Time Range: {TIME_START} to {TIME_END}")
    print()

    # Step 1: Find MACS-managed databases
    print("=" * 80)
    print("STEP 1: Finding MACS-Managed Databases")
    print("=" * 80)
    print()

    result = list_database_insights_by_management_type(compartment_id=COMPARTMENT_ID)

    if "error" in result:
        print(f"❌ Error: {result['error']}")
        exit(1)

    print(f"Total databases found: {result.get('total_databases', 0)}")
    print()

    # Get MACS databases
    macs_databases = []
    for category in result.get('databases_by_priority', []):
        if category.get('priority') == 1:  # Priority 1 = MACS or Autonomous
            for db in category.get('databases', []):
                if 'MACS' in db.get('entity_source', ''):
                    macs_databases.append(db)

    print(f"MACS-Managed databases: {len(macs_databases)}")
    print()

    if len(macs_databases) == 0:
        print("❌ No MACS-managed databases found!")
        print()
        print("Testing with Autonomous Database instead...")
        print()

        # Fall back to any Priority 1 database
        for category in result.get('databases_by_priority', []):
            if category.get('priority') == 1:
                macs_databases = category.get('databases', [])[:3]  # Take first 3
                break

    if len(macs_databases) == 0:
        print("❌ No Priority 1 databases found at all!")
        exit(1)

    # Show databases we'll test
    for i, db in enumerate(macs_databases[:3], 1):  # Test max 3 databases
        print(f"Database {i}:")
        print(f"  Name: {db.get('database_display_name', 'Unknown')}")
        print(f"  Type: {db.get('database_type', 'Unknown')}")
        print(f"  Entity Source: {db.get('entity_source', 'Unknown')}")
        print(f"  Database Insight ID: {db.get('id', 'Unknown')}")
        print(f"  Database ID: {db.get('database_id', 'Unknown')}")
        print()

    # Step 2: Test v2.0 APIs with each database
    for i, db in enumerate(macs_databases[:3], 1):  # Test max 3 databases
        db_name = db.get('database_display_name', 'Unknown')
        db_insight_id = db.get('id')

        print("=" * 80)
        print(f"TESTING DATABASE {i}: {db_name}")
        print("=" * 80)
        print()

        # Test 1: Resource Statistics
        print("Test 1: summarize_database_insight_resource_statistics()")
        print("-" * 80)

        try:
            result = summarize_database_insight_resource_statistics(
                compartment_id=COMPARTMENT_ID,
                resource_metric="CPU",
                time_interval_start=TIME_START,
                time_interval_end=TIME_END,
                database_id=[db_insight_id]
            )

            if "error" in result:
                error_dict = result.get('error', {})
                if isinstance(error_dict, dict):
                    status = error_dict.get('status', 'Unknown')
                    endpoint = error_dict.get('request_endpoint', 'Unknown')
                    print(f"❌ FAILED")
                    print(f"   Status: {status}")
                    print(f"   Endpoint: {endpoint}")
                    print(f"   Message: {error_dict.get('message', 'Unknown')}")
                else:
                    print(f"❌ FAILED: {error_dict}")
            else:
                print(f"✅ SUCCESS!")
                print(f"   Items returned: {result.get('count', 0)}")
                print(f"   Profile used: {result.get('profile_used', 'DEFAULT')}")
                if result.get('count', 0) > 0:
                    item = result['items'][0]
                    print(f"   Sample data:")
                    print(f"     - Database: {item['database_details']['database_display_name']}")
                    print(f"     - Resource: {item['current_statistics']['resource_name']}")
                    print(f"     - Usage: {item['current_statistics']['usage']}")
                    print(f"     - Utilization: {item['current_statistics']['utilization_percent']}%")
        except Exception as e:
            print(f"❌ EXCEPTION: {str(e)}")

        print()

        # Test 2: Resource Usage
        print("Test 2: summarize_database_insight_resource_usage()")
        print("-" * 80)

        try:
            result = summarize_database_insight_resource_usage(
                compartment_id=COMPARTMENT_ID,
                resource_metric="CPU",
                time_interval_start=TIME_START,
                time_interval_end=TIME_END,
                database_id=[db_insight_id]
            )

            if "error" in result:
                error_dict = result.get('error', {})
                if isinstance(error_dict, dict):
                    status = error_dict.get('status', 'Unknown')
                    endpoint = error_dict.get('request_endpoint', 'Unknown')
                    print(f"❌ FAILED")
                    print(f"   Status: {status}")
                    print(f"   Endpoint: {endpoint}")
                else:
                    print(f"❌ FAILED: {error_dict}")
            else:
                print(f"✅ SUCCESS!")
                print(f"   Data points: {result.get('data_points', 0)}")
                print(f"   Profile used: {result.get('profile_used', 'DEFAULT')}")
        except Exception as e:
            print(f"❌ EXCEPTION: {str(e)}")

        print()

        # Test 3: Resource Utilization Insight
        print("Test 3: summarize_database_insight_resource_utilization_insight()")
        print("-" * 80)

        try:
            result = summarize_database_insight_resource_utilization_insight(
                compartment_id=COMPARTMENT_ID,
                resource_metric="CPU",
                time_interval_start=TIME_START,
                time_interval_end=TIME_END,
                database_id=[db_insight_id]
            )

            if "error" in result:
                error_dict = result.get('error', {})
                if isinstance(error_dict, dict):
                    status = error_dict.get('status', 'Unknown')
                    endpoint = error_dict.get('request_endpoint', 'Unknown')
                    print(f"❌ FAILED")
                    print(f"   Status: {status}")
                    print(f"   Endpoint: {endpoint}")
                else:
                    print(f"❌ FAILED: {error_dict}")
            else:
                print(f"✅ SUCCESS!")
                print(f"   Insights count: {result.get('count', 0)}")
                print(f"   Profile used: {result.get('profile_used', 'DEFAULT')}")
        except Exception as e:
            print(f"❌ EXCEPTION: {str(e)}")

        print()

        # Test 4: Tablespace Usage Trend
        print("Test 4: summarize_database_insight_tablespace_usage_trend()")
        print("-" * 80)

        try:
            result = summarize_database_insight_tablespace_usage_trend(
                compartment_id=COMPARTMENT_ID,
                time_interval_start=TIME_START,
                time_interval_end=TIME_END,
                database_id=[db_insight_id]
            )

            if "error" in result:
                error_dict = result.get('error', {})
                if isinstance(error_dict, dict):
                    status = error_dict.get('status', 'Unknown')
                    endpoint = error_dict.get('request_endpoint', 'Unknown')
                    print(f"❌ FAILED")
                    print(f"   Status: {status}")
                    print(f"   Endpoint: {endpoint}")
                else:
                    print(f"❌ FAILED: {error_dict}")
            else:
                print(f"✅ SUCCESS!")
                print(f"   Tablespaces: {result.get('count', 0)}")
                print(f"   Profile used: {result.get('profile_used', 'DEFAULT')}")
        except Exception as e:
            print(f"❌ EXCEPTION: {str(e)}")

        print()

    print("=" * 80)
    print("TESTING COMPLETE")
    print("=" * 80)

if __name__ == "__main__":
    if os.getenv("RUN_OPSI_LIVE_TESTS") != "true":
        raise SystemExit("Set RUN_OPSI_LIVE_TESTS=true to execute this live test script.")
    main()
