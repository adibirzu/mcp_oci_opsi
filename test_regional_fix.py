#!/usr/bin/env python3
"""
Test Script: Regional Endpoint Fix for Operations Insights
Tests the fix for cross-region 404 errors when querying database insights.
"""

import json
from datetime import datetime

# Import the fixed functions
from mcp_oci_opsi.tools_opsi_resource_stats import (
    summarize_database_insight_resource_statistics,
    summarize_database_insight_resource_usage,
    summarize_database_insight_resource_utilization_insight,
    summarize_database_insight_tablespace_usage_trend
)

# Test parameters from user's error report
COMPARTMENT_ID = "ocid1.compartment.oc1..aaaaaaaaje7atqmhsmy3ca4exqvq6zkhjeuzs3ioe2q2exarjmlqey3iljtq"
DATABASE_ID = "ocid1.opsidatabaseinsight.oc1..aaaaaaaapxtcfxmyln7fmd5zcum6nld7m4ypa5hiivwnz3mfqiu4xv52myea"
DATABASE_NAME = "Sales_US"
TIME_START = "2025-11-11T00:00:00Z"
TIME_END = "2025-11-18T00:00:00Z"

print("=" * 80)
print("TESTING REGIONAL ENDPOINT FIX FOR OPERATIONS INSIGHTS")
print("=" * 80)
print()
print(f"Database: {DATABASE_NAME}")
print(f"Database Insight ID: {DATABASE_ID}")
print(f"Expected Region: Phoenix (us-phoenix-1)")
print(f"Profile Region: London (uk-london-1)")
print(f"Time Range: {TIME_START} to {TIME_END}")
print()
print("Before Fix: API calls went to London endpoint → 404 error")
print("After Fix: Should extract region from OCID → Phoenix endpoint → Success!")
print()

# Test 1: Resource Statistics
print("=" * 80)
print("TEST 1: summarize_database_insight_resource_statistics()")
print("=" * 80)
print("TESTING: CPU resource statistics...")
print()

try:
    result = summarize_database_insight_resource_statistics(
        compartment_id=COMPARTMENT_ID,
        resource_metric="CPU",
        time_interval_start=TIME_START,
        time_interval_end=TIME_END,
        database_id=[DATABASE_ID]
    )

    if "error" in result:
        print(f"❌ FAILED: {result['error']}")
        print(f"   Error Type: {result.get('type', 'Unknown')}")
    else:
        print(f"✅ SUCCESS!")
        print(f"   Profile Used: {result.get('profile_used', 'DEFAULT')}")
        print(f"   Items Returned: {result.get('count', 0)}")
        if result.get('count', 0) > 0:
            print(f"   Sample Data:")
            item = result['items'][0]
            print(f"     - Database: {item['database_details']['database_display_name']}")
            print(f"     - Resource: {item['current_statistics']['resource_name']}")
            print(f"     - Usage: {item['current_statistics']['usage']}")
            print(f"     - Utilization: {item['current_statistics']['utilization_percent']}%")
except Exception as e:
    print(f"❌ EXCEPTION: {str(e)}")
    print(f"   Type: {type(e).__name__}")

print()

# Test 2: Resource Usage
print("=" * 80)
print("TEST 2: summarize_database_insight_resource_usage()")
print("=" * 80)
print("TESTING: Time-series CPU usage data...")
print()

try:
    result = summarize_database_insight_resource_usage(
        compartment_id=COMPARTMENT_ID,
        resource_metric="CPU",
        time_interval_start=TIME_START,
        time_interval_end=TIME_END,
        database_id=[DATABASE_ID]
    )

    if "error" in result:
        print(f"❌ FAILED: {result['error']}")
        print(f"   Error Type: {result.get('type', 'Unknown')}")
    else:
        print(f"✅ SUCCESS!")
        print(f"   Profile Used: {result.get('profile_used', 'DEFAULT')}")
        print(f"   Data Points: {result.get('data_points', 0)}")
        if result.get('data_points', 0) > 0:
            print(f"   Sample Data Point:")
            usage = result['usage_data'][0]
            print(f"     - Timestamp: {usage['end_timestamp']}")
            print(f"     - Usage: {usage['usage']}")
            print(f"     - Utilization: {usage['utilization_percent']}%")
except Exception as e:
    print(f"❌ EXCEPTION: {str(e)}")
    print(f"   Type: {type(e).__name__}")

print()

# Test 3: Utilization Insights
print("=" * 80)
print("TEST 3: summarize_database_insight_resource_utilization_insight()")
print("=" * 80)
print("TESTING: Utilization insights with trend analysis...")
print()

try:
    result = summarize_database_insight_resource_utilization_insight(
        compartment_id=COMPARTMENT_ID,
        resource_metric="CPU",
        time_interval_start=TIME_START,
        time_interval_end=TIME_END,
        database_id=[DATABASE_ID]
    )

    if "error" in result:
        print(f"❌ FAILED: {result['error']}")
        print(f"   Error Type: {result.get('type', 'Unknown')}")
    else:
        print(f"✅ SUCCESS!")
        print(f"   Profile Used: {result.get('profile_used', 'DEFAULT')}")
        print(f"   Insights Count: {result.get('count', 0)}")
        if result.get('count', 0) > 0:
            print(f"   Sample Insight:")
            insight = result['insights'][0]
            print(f"     - Database: {insight['database_details']['database_name']}")
            print(f"     - High Threshold: {insight['utilization_insight']['high_utilization_threshold']}")
            print(f"     - Low Threshold: {insight['utilization_insight']['low_utilization_threshold']}")
except Exception as e:
    print(f"❌ EXCEPTION: {str(e)}")
    print(f"   Type: {type(e).__name__}")

print()

# Test 4: Tablespace Usage Trend
print("=" * 80)
print("TEST 4: summarize_database_insight_tablespace_usage_trend()")
print("=" * 80)
print("TESTING: Tablespace usage trends...")
print()

try:
    result = summarize_database_insight_tablespace_usage_trend(
        compartment_id=COMPARTMENT_ID,
        time_interval_start=TIME_START,
        time_interval_end=TIME_END,
        database_id=[DATABASE_ID]
    )

    if "error" in result:
        print(f"❌ FAILED: {result['error']}")
        print(f"   Error Type: {result.get('type', 'Unknown')}")
    else:
        print(f"✅ SUCCESS!")
        print(f"   Profile Used: {result.get('profile_used', 'DEFAULT')}")
        print(f"   Tablespaces: {result.get('count', 0)}")
        if result.get('count', 0) > 0:
            print(f"   Sample Tablespace:")
            ts = result['tablespaces'][0]
            print(f"     - Database: {ts['database_details']['database_name']}")
            print(f"     - Tablespace: {ts['tablespace_name']}")
            print(f"     - Type: {ts['tablespace_type']}")
            print(f"     - Data Points: {len(ts['usage_data'])}")
except Exception as e:
    print(f"❌ EXCEPTION: {str(e)}")
    print(f"   Type: {type(e).__name__}")

print()
print("=" * 80)
print("TESTING COMPLETE")
print("=" * 80)
print()
print("Expected Results:")
print("  ✅ All 4 tests should succeed (no 404 errors)")
print("  ✅ API calls should go to Phoenix endpoint (not London)")
print("  ✅ Data should be returned for Sales_US database")
print()
