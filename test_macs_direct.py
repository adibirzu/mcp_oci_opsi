#!/usr/bin/env python3
"""Test v2.0 resource statistics APIs with MACS databases directly."""

from datetime import datetime, timedelta, UTC

from mcp_oci_opsi.tools_opsi_resource_stats import (
    summarize_database_insight_resource_statistics,
    summarize_database_insight_resource_usage,
    summarize_database_insight_resource_utilization_insight,
    summarize_database_insight_tablespace_usage_trend
)

COMPARTMENT_ID = "ocid1.compartment.oc1..aaaaaaaaje7atqmhsmy3ca4exqvq6zkhjeuzs3ioe2q2exarjmlqey3iljtq"
TIME_START = (datetime.now(UTC) - timedelta(days=7)).isoformat().replace('+00:00', 'Z')
TIME_END = datetime.now(UTC).isoformat().replace('+00:00', 'Z')

# MACS databases from London region
MACS_DATABASES = [
    {
        "name": "ECREDITS",
        "id": "ocid1.opsidatabaseinsight.oc1.uk-london-1.amaaaaaaqgp2kriaeertra7fnxhxvcd4kragbsagxwztbgafyyfownoydcsq",
        "database_id": "ocid1.externalpluggabledatabase.oc1.uk-london-1.anwgiljtqgp2kriagkiba5edzjhr2o23nps36i4opz5bz5upcrcwylhsk3aa",
        "type": "EXTERNAL-PDB"
    },
    {
        "name": "EREWARDS",
        "id": "ocid1.opsidatabaseinsight.oc1.uk-london-1.amaaaaaaqgp2kria2x3tdg5hkomkbkk4wwq35jqxntk5jwmg6vdglufg24sa",
        "database_id": "ocid1.externalpluggabledatabase.oc1.uk-london-1.anwgiljtqgp2krialwty6gk4r7lszn2f2rzlf2rcdesvvdg4nxvanmniltiq",
        "type": "EXTERNAL-PDB"
    },
    {
        "name": "ELOYALTY",
        "id": "ocid1.opsidatabaseinsight.oc1.uk-london-1.amaaaaaaqgp2kriamz7hyrnjnbxjeugh2rudfdwvprfcnhb77w4ro6yrml3q",
        "database_id": "ocid1.externalpluggabledatabase.oc1.uk-london-1.anwgiljtqgp2kria7ilmnjjoforv5ptsfo367tn4ocd6v3g2dr6jn3xylveq",
        "type": "EXTERNAL-PDB"
    }
]

print("=" * 80)
print("TESTING V2.0 RESOURCE STATISTICS APIs WITH MACS DATABASES")
print("=" * 80)
print()
print(f"Compartment: {COMPARTMENT_ID}")
print(f"Time Range: {TIME_START} to {TIME_END}")
print(f"Profile Region: UK London (uk-london-1)")
print(f"Database Region: UK London (uk-london-1)")
print()
print("📝 Note: These databases are in the SAME region as the profile,")
print("   so this tests that the regional endpoint detection doesn't break")
print("   same-region queries.")
print()

for i, db in enumerate(MACS_DATABASES, 1):
    print("=" * 80)
    print(f"DATABASE {i}: {db['name']} ({db['type']})")
    print("=" * 80)
    print(f"Entity Source: MACS_MANAGED_EXTERNAL_DATABASE (Priority 1)")
    print(f"Database Insight ID: {db['id']}")
    print(f"Database ID: {db['database_id']}")
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
            database_id=[db['id']]
        )

        if "error" in result:
            error = result.get('error')
            if isinstance(error, dict):
                print(f"❌ FAILED")
                print(f"   Status: {error.get('status', 'Unknown')}")
                print(f"   Code: {error.get('code', 'Unknown')}")
                print(f"   Message: {error.get('message', 'Unknown')}")
                if 'request_endpoint' in error:
                    endpoint = error['request_endpoint']
                    if 'uk-london-1' in endpoint:
                        print(f"   ✅ Regional endpoint: CORRECT (London)")
                    else:
                        print(f"   ❌ Regional endpoint: WRONG")
                    print(f"   Endpoint: {endpoint}")
            else:
                print(f"❌ FAILED: {error}")
        else:
            print(f"✅ SUCCESS!")
            print(f"   Items returned: {result.get('count', 0)}")
            if result.get('count', 0) > 0:
                item = result['items'][0]
                print(f"   Sample data:")
                print(f"     Database: {item['database_details']['database_display_name']}")
                print(f"     Resource: {item['current_statistics']['resource_name']}")
                print(f"     Usage: {item['current_statistics']['usage']}")
                print(f"     Capacity: {item['current_statistics']['capacity']}")
                print(f"     Utilization: {item['current_statistics']['utilization_percent']}%")
    except Exception as e:
        print(f"❌ EXCEPTION: {str(e)[:200]}")

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
            database_id=[db['id']]
        )

        if "error" in result:
            error = result.get('error')
            if isinstance(error, dict):
                print(f"❌ FAILED")
                print(f"   Status: {error.get('status', 'Unknown')}")
                print(f"   Message: {error.get('message', 'Unknown')}")
                if 'request_endpoint' in error:
                    print(f"   Endpoint: {error['request_endpoint']}")
            else:
                print(f"❌ FAILED: {error}")
        else:
            print(f"✅ SUCCESS!")
            print(f"   Data points: {result.get('data_points', 0)}")
            if result.get('data_points', 0) > 0:
                sample = result['usage_data'][0]
                print(f"   Sample: Time={sample['end_timestamp']}, Usage={sample['usage']}")
    except Exception as e:
        print(f"❌ EXCEPTION: {str(e)[:200]}")

    print()

    # Test 3: Utilization Insight
    print("Test 3: summarize_database_insight_resource_utilization_insight()")
    print("-" * 80)

    try:
        result = summarize_database_insight_resource_utilization_insight(
            compartment_id=COMPARTMENT_ID,
            resource_metric="CPU",
            time_interval_start=TIME_START,
            time_interval_end=TIME_END,
            database_id=[db['id']]
        )

        if "error" in result:
            error = result.get('error')
            if isinstance(error, dict):
                print(f"❌ FAILED")
                print(f"   Status: {error.get('status', 'Unknown')}")
                print(f"   Message: {error.get('message', 'Unknown')}")
            else:
                print(f"❌ FAILED: {error}")
        else:
            print(f"✅ SUCCESS!")
            print(f"   Insights count: {result.get('count', 0)}")
    except Exception as e:
        print(f"❌ EXCEPTION: {str(e)[:200]}")

    print()

    # Test 4: Tablespace Usage
    print("Test 4: summarize_database_insight_tablespace_usage_trend()")
    print("-" * 80)

    try:
        result = summarize_database_insight_tablespace_usage_trend(
            compartment_id=COMPARTMENT_ID,
            time_interval_start=TIME_START,
            time_interval_end=TIME_END,
            database_id=[db['id']]
        )

        if "error" in result:
            error = result.get('error')
            if isinstance(error, dict):
                print(f"❌ FAILED")
                print(f"   Status: {error.get('status', 'Unknown')}")
                print(f"   Message: {error.get('message', 'Unknown')}")
            else:
                print(f"❌ FAILED: {error}")
        else:
            print(f"✅ SUCCESS!")
            print(f"   Tablespaces: {result.get('count', 0)}")
            if result.get('count', 0) > 0:
                ts = result['tablespaces'][0]
                print(f"   Sample: {ts['tablespace_name']} ({ts['tablespace_type']})")
    except Exception as e:
        print(f"❌ EXCEPTION: {str(e)[:200]}")

    print()

print("=" * 80)
print("TESTING SUMMARY")
print("=" * 80)
print()
print("This test validates:")
print("  1. Regional endpoint detection works for MACS databases")
print("  2. API calls don't break when database is in same region as profile")
print("  3. v2.0 resource statistics APIs work with MACS-managed databases")
print()
