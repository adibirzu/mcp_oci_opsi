#!/usr/bin/env python3
"""Test the fixed SQL statistics function."""

from pathlib import Path
import sys
import json
import os

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from mcp_oci_opsi.tools.tools_opsi_extended import summarize_sql_statistics
from mcp_oci_opsi.config import get_oci_config, get_current_profile

def test_sql_stats():
    """Test the SQL statistics function with proper data extraction."""

    # Display authentication configuration
    print("=" * 80)
    print("OCI Authentication & Configuration Check")
    print("=" * 80)
    
    try:
        profile = get_current_profile()
        config = get_oci_config()
        region = config.get("region", "Unknown")
        tenancy = config.get("tenancy", "Unknown")
        user = config.get("user", "Unknown")
        
        print(f"\n📊 Current Configuration:")
        print(f"  OCI Profile: {profile}")
        print(f"  Region: {region}")
        print(f"  Tenancy: {tenancy}")
        print(f"  User: {user}")
        print()
    except Exception as e:
        print(f"\n❌ Failed to load OCI configuration: {e}")
        print("   Make sure ~/.oci/config exists and OCI_CLI_PROFILE is set correctly")
        return

    # Test parameters
    compartment_id = os.getenv("OCI_ID", "ocid1.compartment.oc1..example")
    time_start = "2025-11-11T00:00:00Z"
    time_end = "2025-11-18T10:00:00Z"

    print("=" * 80)
    print("Testing SQL Statistics Function")
    print("=" * 80)

    result = summarize_sql_statistics(
        compartment_id=compartment_id,
        time_interval_start=time_start,
        time_interval_end=time_end
    )

    print(f"\nResult structure:")
    print(f"  Type: {type(result)}")
    print(f"  Keys: {result.keys() if isinstance(result, dict) else 'N/A'}")
    print()

    # Check for errors first
    if isinstance(result, dict) and 'error' in result:
        print(f"❌ ERROR: {result['error']}")
        print(f"Full response: {json.dumps(result, indent=2, default=str)}")
        return

    # Handle different response formats
    count = result.get('count') or len(result.get('items', []))
    print(f"Result summary:")
    print(f"  Total SQL statements: {count}")

    if count > 0:
        items = result.get('items', [])
        if items:
            first_item = items[0]
            print(f"\nFirst SQL statement:")
            print(f"  SQL ID: {first_item.get('sql_identifier')}")
            print(f"  Database: {first_item.get('database_display_name')} ({first_item.get('database_name')})")
            print(f"  Database ID: {first_item.get('database_id')}")
            print(f"\n  Performance Metrics:")
            print(f"    Executions: {first_item.get('executions_count', 'N/A')}")
            print(f"    CPU Time: {first_item.get('cpu_time_in_sec', 'N/A')} sec")
            print(f"    I/O Time: {first_item.get('io_time_in_sec', 'N/A')} sec")
            print(f"    DB Time: {first_item.get('database_time_in_sec', 'N/A')} sec")
            print(f"    DB Time %: {first_item.get('database_time_pct', 'N/A')}%")
            print(f"    Avg Active Sessions: {first_item.get('average_active_sessions', 'N/A')}")
            print(f"    Plan Count: {first_item.get('plan_count', 'N/A')}")
            print(f"    Category: {first_item.get('category', 'N/A')}")

            # Check if all key metrics are present
            key_metrics = ['executions_count', 'cpu_time_in_sec', 'database_time_in_sec']
            all_present = all(first_item.get(metric) is not None for metric in key_metrics)

            if all_present:
                print(f"\n✅ SUCCESS: All key metrics are now populated!")
            else:
                print(f"\n⚠️  Some metrics are null (may be expected if no data available)")

            # Show full JSON for first item
            print(f"\nFull first item (JSON):")
            print(json.dumps(first_item, indent=2, default=str))
    else:
        print(f"\n⚠️  No SQL statements found in time range")
        print(f"This is expected if no SQL activity occurred during the period")
        print(f"\nFull response:")
        print(json.dumps(result, indent=2, default=str))

if __name__ == "__main__":
    test_sql_stats()
