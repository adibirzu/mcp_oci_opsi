#!/usr/bin/env python3
"""Diagnostic script to inspect SQL statistics API response structure."""

from datetime import datetime
from mcp_oci_opsi.oci_clients import get_opsi_client
import json

def diagnose_sql_stats_response():
    """Inspect the actual structure of SQL statistics response."""

    compartment_id = "ocid1.compartment.oc1..aaaaaaaaohkmg2l7grhguvry56ipbs6yuqxfqnl2tmzwn6xvwqylwpj3wcla"
    time_start = datetime.fromisoformat("2025-11-11T00:00:00Z".replace("Z", "+00:00"))
    time_end = datetime.fromisoformat("2025-11-18T10:00:00Z".replace("Z", "+00:00"))

    print("=" * 80)
    print("Diagnosing SQL Statistics API Response Structure")
    print("=" * 80)

    try:
        client = get_opsi_client()

        kwargs = {
            "compartment_id": compartment_id,
            "time_interval_start": time_start,
            "time_interval_end": time_end,
        }

        print(f"\nCalling API with:")
        print(f"  compartment_id: {compartment_id}")
        print(f"  time_interval_start: {time_start}")
        print(f"  time_interval_end: {time_end}")

        response = client.summarize_sql_statistics(**kwargs)

        print(f"\n✓ API call successful")
        print(f"\nResponse type: {type(response)}")
        print(f"Response.data type: {type(response.data)}")

        # Check response.data attributes
        print(f"\nResponse.data attributes:")
        for attr in dir(response.data):
            if not attr.startswith('_'):
                print(f"  - {attr}")

        # Check if items exist
        if hasattr(response.data, "items"):
            print(f"\n✓ response.data.items exists")
            print(f"  Items count: {len(response.data.items)}")

            if len(response.data.items) > 0:
                first_item = response.data.items[0]
                print(f"\n  First item type: {type(first_item)}")
                print(f"\n  First item attributes:")
                for attr in dir(first_item):
                    if not attr.startswith('_'):
                        value = getattr(first_item, attr, None)
                        if not callable(value):
                            print(f"    - {attr}: {value} (type: {type(value).__name__})")

                # Try to access statistics
                print(f"\n  Checking for statistics data...")
                if hasattr(first_item, 'statistics'):
                    print(f"    ✓ first_item.statistics exists")
                    stats = first_item.statistics
                    print(f"    Statistics type: {type(stats)}")
                    if hasattr(stats, '__dict__'):
                        print(f"    Statistics content: {stats.__dict__}")

                # Try common attribute patterns
                for attr_name in ['executions_count', 'executions', 'execution_count',
                                 'cpu_time_in_sec', 'cpu_time', 'cpu_time_in_seconds']:
                    val = getattr(first_item, attr_name, "NOT_FOUND")
                    if val != "NOT_FOUND":
                        print(f"    ✓ Found: {attr_name} = {val}")
        else:
            print(f"\n✗ response.data.items does NOT exist")

    except Exception as e:
        print(f"\n✗ Error: {e}")
        print(f"  Error type: {type(e).__name__}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    diagnose_sql_stats_response()
