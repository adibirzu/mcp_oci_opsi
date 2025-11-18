#!/usr/bin/env python3
"""Test the fixed SQL statistics function."""

from mcp_oci_opsi.tools_opsi_extended import summarize_sql_statistics
import json

def test_sql_stats():
    """Test the SQL statistics function with proper data extraction."""

    compartment_id = "ocid1.compartment.oc1..aaaaaaaaohkmg2l7grhguvry56ipbs6yuqxfqnl2tmzwn6xvwqylwpj3wcla"
    time_start = "2025-11-11T00:00:00Z"
    time_end = "2025-11-18T10:00:00Z"

    print("=" * 80)
    print("Testing Fixed SQL Statistics Function")
    print("=" * 80)

    result = summarize_sql_statistics(
        compartment_id=compartment_id,
        time_interval_start=time_start,
        time_interval_end=time_end
    )

    print(f"\nResult summary:")
    print(f"  Total SQL statements: {result['count']}")

    if result['count'] > 0:
        first_item = result['items'][0]
        print(f"\nFirst SQL statement:")
        print(f"  SQL ID: {first_item.get('sql_identifier')}")
        print(f"  Database: {first_item.get('database_display_name')} ({first_item.get('database_name')})")
        print(f"  Database ID: {first_item.get('database_id')}")
        print(f"\n  Performance Metrics:")
        print(f"    Executions: {first_item.get('executions_count'):,}")
        print(f"    Executions/hour: {first_item.get('executions_per_hour'):,.2f}")
        print(f"    CPU Time: {first_item.get('cpu_time_in_sec'):,.2f} sec")
        print(f"    I/O Time: {first_item.get('io_time_in_sec'):,.2f} sec")
        print(f"    DB Time: {first_item.get('database_time_in_sec'):,.2f} sec")
        print(f"    DB Time %: {first_item.get('database_time_pct')}%")
        print(f"    Avg Active Sessions: {first_item.get('average_active_sessions'):,.2f}")
        print(f"    Plan Count: {first_item.get('plan_count')}")
        print(f"    Category: {first_item.get('category')}")

        # Check if all key metrics are present
        key_metrics = ['executions_count', 'cpu_time_in_sec', 'database_time_in_sec']
        all_present = all(first_item.get(metric) is not None for metric in key_metrics)

        if all_present:
            print(f"\n✅ SUCCESS: All key metrics are now populated!")
        else:
            print(f"\n❌ ISSUE: Some metrics are still null")

        # Show full JSON for first item
        print(f"\nFull first item (JSON):")
        print(json.dumps(first_item, indent=2, default=str))

if __name__ == "__main__":
    test_sql_stats()
