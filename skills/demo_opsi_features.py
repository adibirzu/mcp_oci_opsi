import os
#!/usr/bin/env python3
"""
Demo Script: OCI Operations Insights MCP Server Features
This script demonstrates 15 key Operations Insights capabilities with real data.
"""

from datetime import datetime, timedelta
import json
from mcp_oci_opsi.tools.tools_opsi import list_database_insights
from mcp_oci_opsi.tools.tools_opsi_extended import (
    list_host_insights,
    summarize_sql_statistics,
    summarize_host_insight_resource_forecast_trend,
    summarize_host_insight_resource_capacity_trend,
    summarize_host_insight_resource_usage,
    summarize_host_insight_resource_statistics,
    summarize_host_insight_disk_statistics,
    summarize_host_insight_network_usage_trend,
    summarize_host_insight_top_processes_usage,
)

# Configuration
COMPARTMENT_ID = os.getenv("OCI_COMPARTMENT_ID", "ocid1.compartment.oc1..example")
TIME_END = datetime.now()
TIME_START = TIME_END - timedelta(days=7)
TIME_START_STR = TIME_START.isoformat() + "Z"
TIME_END_STR = TIME_END.isoformat() + "Z"


def print_section(title, number):
    """Print a section header."""
    print("\n" + "=" * 80)
    print(f"{number}. {title}")
    print("=" * 80)


def print_result(result, key_fields=None, max_items=3):
    """Print formatted result with key fields."""
    if "error" in result:
        print(f"❌ Error: {result['error']}")
        return

    print(f"✅ Success! Found {result.get('count', 0)} items")

    if key_fields and result.get('items'):
        for i, item in enumerate(result['items'][:max_items], 1):
            print(f"\n  Item {i}:")
            for field in key_fields:
                value = item.get(field)
                if isinstance(value, (int, float)) and value is not None:
                    if value > 1000000:
                        print(f"    {field}: {value:,.0f}")
                    elif isinstance(value, float):
                        print(f"    {field}: {value:.2f}")
                    else:
                        print(f"    {field}: {value}")
                else:
                    print(f"    {field}: {value}")


def demo():
    """Run the complete demo."""
    print("=" * 80)
    print("OCI OPERATIONS INSIGHTS MCP SERVER - FEATURE DEMO")
    print("=" * 80)
    print(f"\nCompartment: {COMPARTMENT_ID}")
    print(f"Time Range: {TIME_START_STR} to {TIME_END_STR}")
    print(f"Duration: 7 days")

    # ==============================================================
    # PROMPT 1: List all database insights in compartment
    # ==============================================================
    print_section("List Database Insights in Compartment", 1)
    print("PROMPT: Show me all databases with Operations Insights enabled")

    result = list_database_insights(
        compartment_id=COMPARTMENT_ID,
        lifecycle_state="ACTIVE"
    )
    print_result(result, key_fields=['database_display_name', 'database_type', 'status'])

    # ==============================================================
    # PROMPT 2: Get SQL performance statistics
    # ==============================================================
    print_section("SQL Performance Statistics (Last 7 Days)", 2)
    print("PROMPT: What are the most resource-intensive SQL statements in the last week?")

    result = summarize_sql_statistics(
        compartment_id=COMPARTMENT_ID,
        time_interval_start=TIME_START_STR,
        time_interval_end=TIME_END_STR
    )
    print_result(result, key_fields=[
        'sql_identifier', 'database_display_name', 'executions_count',
        'cpu_time_in_sec', 'database_time_pct', 'category'
    ])

    # ==============================================================
    # PROMPT 3: List all hosts with insights enabled
    # ==============================================================
    print_section("List Host Insights in Compartment", 3)
    print("PROMPT: Show me all monitored hosts")

    result = list_host_insights(
        compartment_id=COMPARTMENT_ID,
        lifecycle_state="ACTIVE"
    )
    print_result(result, key_fields=['host_display_name', 'platform_type', 'processor_count'])

    # Save first host ID for subsequent queries
    first_host_id = None
    if result.get('items') and len(result['items']) > 0:
        first_host_id = result['items'][0]['id']

    # ==============================================================
    # PROMPT 4: Host CPU forecast (30 days)
    # ==============================================================
    print_section("Host CPU Capacity Forecast (30 Days)", 4)
    print("PROMPT: What is the CPU forecast for the next 30 days?")

    result = summarize_host_insight_resource_forecast_trend(
        compartment_id=COMPARTMENT_ID,
        resource_metric="CPU",
        time_interval_start=TIME_START_STR,
        time_interval_end=TIME_END_STR,
        forecast_days=30,
        statistic="AVG"
    )
    print_result(result, key_fields=['end_timestamp', 'usage', 'high_value', 'low_value'], max_items=5)

    # ==============================================================
    # PROMPT 5: Host Memory forecast
    # ==============================================================
    print_section("Host Memory Capacity Forecast (15 Days)", 5)
    print("PROMPT: Show me the memory forecast for the next 2 weeks")

    result = summarize_host_insight_resource_forecast_trend(
        compartment_id=COMPARTMENT_ID,
        resource_metric="LOGICAL_MEMORY",
        time_interval_start=TIME_START_STR,
        time_interval_end=TIME_END_STR,
        forecast_days=15,
        statistic="AVG"
    )

    if result.get('count', 0) > 0:
        print(f"✅ Success! {result['count']} forecast data points")
        print(f"   Usage Unit: {result.get('usage_unit')}")
        print(f"   Forecast Days: {result.get('forecast_days')}")
    else:
        print_result(result)

    # ==============================================================
    # PROMPT 6: Host capacity trends
    # ==============================================================
    print_section("Host CPU Capacity Trends (Historical)", 6)
    print("PROMPT: Show me historical CPU capacity trends")

    result = summarize_host_insight_resource_capacity_trend(
        compartment_id=COMPARTMENT_ID,
        resource_metric="CPU",
        time_interval_start=TIME_START_STR,
        time_interval_end=TIME_END_STR
    )
    print_result(result, key_fields=['end_timestamp', 'usage', 'capacity', 'utilization_percent'], max_items=5)

    # ==============================================================
    # PROMPT 7: Current host resource usage
    # ==============================================================
    print_section("Current Host Resource Usage Summary", 7)
    print("PROMPT: What is the current CPU usage across all hosts?")

    result = summarize_host_insight_resource_usage(
        compartment_id=COMPARTMENT_ID,
        resource_metric="CPU",
        time_interval_start=TIME_START_STR,
        time_interval_end=TIME_END_STR
    )
    print_result(result, key_fields=['host_name', 'platform_type', 'usage', 'capacity', 'utilization_percent'])

    # ==============================================================
    # PROMPT 8: Host resource statistics
    # ==============================================================
    print_section("Host Memory Resource Statistics", 8)
    print("PROMPT: Show me memory statistics for all hosts")

    result = summarize_host_insight_resource_statistics(
        compartment_id=COMPARTMENT_ID,
        resource_metric="MEMORY",
        time_interval_start=TIME_START_STR,
        time_interval_end=TIME_END_STR
    )
    print_result(result, key_fields=['resource_name', 'usage', 'capacity', 'utilization_percent'])

    # ==============================================================
    # PROMPT 9: Disk I/O statistics
    # ==============================================================
    print_section("Host Disk I/O Statistics", 9)
    print("PROMPT: What are the disk I/O patterns?")

    result = summarize_host_insight_disk_statistics(
        compartment_id=COMPARTMENT_ID,
        time_interval_start=TIME_START_STR,
        time_interval_end=TIME_END_STR
    )
    print_result(result, key_fields=['disk_name', 'disk_read_in_mbs', 'disk_write_in_mbs', 'disk_iops'])

    # ==============================================================
    # PROMPT 10: Network usage trends
    # ==============================================================
    print_section("Host Network Usage Trends", 10)
    print("PROMPT: Show me network usage trends over the last week")

    result = summarize_host_insight_network_usage_trend(
        compartment_id=COMPARTMENT_ID,
        time_interval_start=TIME_START_STR,
        time_interval_end=TIME_END_STR
    )
    print_result(result, key_fields=['end_timestamp', 'network_read_in_mbs', 'network_write_in_mbs'], max_items=5)

    # ==============================================================
    # PROMPT 11: Top CPU-consuming processes
    # ==============================================================
    print_section("Top CPU-Consuming Processes", 11)
    print("PROMPT: Which processes are consuming the most CPU?")

    result = summarize_host_insight_top_processes_usage(
        compartment_id=COMPARTMENT_ID,
        resource_metric="CPU",
        time_interval_start=TIME_START_STR,
        time_interval_end=TIME_END_STR,
        limit=10
    )
    print_result(result, key_fields=['process_name', 'process_command', 'cpu_usage', 'memory_usage'])

    # ==============================================================
    # PROMPT 12: Storage capacity forecast
    # ==============================================================
    print_section("Storage Capacity Forecast", 12)
    print("PROMPT: When will we run out of storage capacity?")

    result = summarize_host_insight_resource_forecast_trend(
        compartment_id=COMPARTMENT_ID,
        resource_metric="STORAGE",
        time_interval_start=TIME_START_STR,
        time_interval_end=TIME_END_STR,
        forecast_days=30
    )

    if result.get('count', 0) > 0:
        print(f"✅ Success! Storage forecast for next 30 days")
        print(f"   Data points: {result['count']}")
        if result.get('forecast_items'):
            first = result['forecast_items'][0]
            last = result['forecast_items'][-1]
            print(f"\n   Current forecast: {first.get('usage')} {result.get('usage_unit', '')}")
            print(f"   30-day forecast: {last.get('usage')} {result.get('usage_unit', '')}")
            growth = ((last.get('usage', 0) - first.get('usage', 1)) / first.get('usage', 1)) * 100
            print(f"   Growth trend: {growth:.1f}%")
    else:
        print_result(result)

    # ==============================================================
    # PROMPT 13: High-utilization CPU hosts
    # ==============================================================
    print_section("High CPU Utilization Hosts", 13)
    print("PROMPT: Which hosts have high CPU utilization?")

    result = summarize_host_insight_resource_capacity_trend(
        compartment_id=COMPARTMENT_ID,
        resource_metric="CPU",
        time_interval_start=TIME_START_STR,
        time_interval_end=TIME_END_STR,
        utilization_level="HIGH_UTILIZATION"
    )

    if result.get('count', 0) > 0:
        print(f"✅ Found {result['count']} high-utilization data points")
        print_result(result, key_fields=['end_timestamp', 'usage', 'capacity', 'utilization_percent'], max_items=3)
    else:
        print("✅ No high CPU utilization detected - all systems healthy!")

    # ==============================================================
    # PROMPT 14: SQL statements with changing plans
    # ==============================================================
    print_section("SQL Statements with Performance Issues", 14)
    print("PROMPT: Show me SQL statements that are degrading or changing execution plans")

    result = summarize_sql_statistics(
        compartment_id=COMPARTMENT_ID,
        time_interval_start=TIME_START_STR,
        time_interval_end=TIME_END_STR
    )

    # Filter for problematic SQL
    problematic_sql = []
    if result.get('items'):
        for sql in result['items']:
            categories = sql.get('category', [])
            if any(cat in ['DEGRADING', 'CHANGING_PLANS'] for cat in categories):
                problematic_sql.append(sql)

    print(f"✅ Found {len(problematic_sql)} SQL statements with performance issues")
    for i, sql in enumerate(problematic_sql[:3], 1):
        print(f"\n  SQL {i}: {sql.get('sql_identifier')}")
        print(f"    Database: {sql.get('database_display_name')}")
        print(f"    Categories: {', '.join(sql.get('category', []))}")
        print(f"    Executions: {sql.get('executions_count', 0):,}")
        print(f"    DB Time %: {sql.get('database_time_pct')}%")

    # ==============================================================
    # PROMPT 15: Overall health summary
    # ==============================================================
    print_section("Overall System Health Summary", 15)
    print("PROMPT: Give me an overall health summary of my infrastructure")

    # Collect summary data
    db_insights = list_database_insights(compartment_id=COMPARTMENT_ID)
    host_insights = list_host_insights(compartment_id=COMPARTMENT_ID)
    sql_stats = summarize_sql_statistics(
        compartment_id=COMPARTMENT_ID,
        time_interval_start=TIME_START_STR,
        time_interval_end=TIME_END_STR
    )

    print("\n📊 INFRASTRUCTURE HEALTH SUMMARY")
    print(f"\n  Databases Monitored: {db_insights.get('count', 0)}")
    print(f"  Hosts Monitored: {host_insights.get('count', 0)}")
    print(f"  SQL Statements Analyzed: {sql_stats.get('count', 0)}")

    # Count problematic SQL
    if sql_stats.get('items'):
        degrading = sum(1 for sql in sql_stats['items']
                       if 'DEGRADING' in sql.get('category', []))
        changing_plans = sum(1 for sql in sql_stats['items']
                            if 'CHANGING_PLANS' in sql.get('category', []))
        print(f"\n  ⚠️  SQL Issues:")
        print(f"    - Degrading performance: {degrading}")
        print(f"    - Changing execution plans: {changing_plans}")

    print("\n" + "=" * 80)
    print("DEMO COMPLETE!")
    print("=" * 80)


if __name__ == "__main__":
    try:
        demo()
    except KeyboardInterrupt:
        print("\n\n❌ Demo interrupted by user")
    except Exception as e:
        print(f"\n\n❌ Demo failed with error: {e}")
        import traceback
        traceback.print_exc()
