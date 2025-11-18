#!/usr/bin/env python3
"""
Test script for EM-Managed database warehouse fallback functionality.
"""

from datetime import datetime, timedelta
from mcp_oci_opsi.tools_opsi_extended import summarize_sql_statistics

# Configuration
COMPARTMENT_ID = "ocid1.compartment.oc1..aaaaaaaaohkmg2l7grhguvry56ipbs6yuqxfqnl2tmzwn6xvwqylwpj3wcla"
DATABASE_INSIGHT_ID = "ocid1.opsidatabaseinsight.oc1.uk-london-1.amaaaaaaqgp2kriai6hvr5dforjaiew3upfsvnylpim7gu3jdafo4hex6jpq"

# Use past 7 days
TIME_END = datetime.now()
TIME_START = TIME_END - timedelta(days=7)
TIME_START_STR = TIME_START.isoformat() + "Z"
TIME_END_STR = TIME_END.isoformat() + "Z"


def test_em_managed_fallback():
    """Test SQL Statistics with EM-Managed database fallback."""
    print("=" * 80)
    print("Testing SQL Statistics with EM-Managed Database Fallback")
    print("=" * 80)
    print(f"\nDatabase Insight ID: {DATABASE_INSIGHT_ID}")
    print(f"Compartment: {COMPARTMENT_ID}")
    print(f"Time Range: {TIME_START_STR} to {TIME_END_STR}\n")

    # This should trigger:
    # 1. Direct API call (will get 404 for EM-Managed)
    # 2. Detection of EM-Managed database
    # 3. Automatic fallback to warehouse query
    result = summarize_sql_statistics(
        compartment_id=COMPARTMENT_ID,
        time_interval_start=TIME_START_STR,
        time_interval_end=TIME_END_STR,
        database_id=DATABASE_INSIGHT_ID
    )

    print("RESULT:")
    print("-" * 80)

    if "error" in result:
        print(f"❌ Error: {result['error']}")
        print(f"\nError Type: {result.get('type')}")

        if "em_managed_database" in result:
            print(f"\n⚠️  EM-Managed Database: {result['em_managed_database']}")

        if "additional_info" in result:
            print(f"\nAdditional Info:")
            for key, value in result["additional_info"].items():
                print(f"  {key}: {value}")

        if "troubleshooting" in result:
            print(f"\nTroubleshooting:")
            for key, value in result["troubleshooting"].items():
                print(f"\n  {key}:")
                if isinstance(value, list):
                    for item in value:
                        print(f"    - {item}")
                else:
                    print(f"    {value}")
    else:
        print(f"✅ Success!")
        print(f"\nItems Found: {result.get('count', 0)}")

        if "em_managed_database" in result:
            print(f"\n⚠️  EM-Managed Database: {result['em_managed_database']}")

        if "data_source" in result:
            print(f"Data Source: {result['data_source']}")

        if "note" in result:
            print(f"\nNote: {result['note']}")

        if result.get('count', 0) > 0:
            print(f"\nSample SQL Statistics (first 3):")
            for i, item in enumerate(result.get('items', [])[:3], 1):
                print(f"\n  SQL {i}:")
                print(f"    SQL Identifier: {item.get('sql_identifier')}")
                print(f"    Database: {item.get('database_name', item.get('database_display_name'))}")
                print(f"    Executions: {item.get('executions_count', 0):,}")
                print(f"    CPU Time (sec): {item.get('cpu_time_in_sec', 0):,.2f}")
                print(f"    DB Time %: {item.get('database_time_pct', 0):.2f}%")

    print("\n" + "=" * 80)
    print("Test Complete")
    print("=" * 80)


if __name__ == "__main__":
    try:
        test_em_managed_fallback()
    except KeyboardInterrupt:
        print("\n\nTest interrupted by user")
    except Exception as e:
        print(f"\n\nTest failed with error: {e}")
        import traceback
        traceback.print_exc()
