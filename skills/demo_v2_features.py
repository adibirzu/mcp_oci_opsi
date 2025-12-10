import os
#!/usr/bin/env python3
"""
Demo Script: MCP OCI OPSI Server v2.0 Features
Showcases 20+ new v2.0 capabilities including agent detection, multi-tenancy,
user management, tablespace monitoring, and AWR metrics.
"""

from datetime import datetime, timedelta
import json

# v2.0 New Imports
from mcp_oci_opsi.tools.tools_database_discovery import (
    list_database_insights_by_management_type,
    get_database_api_compatibility
)
from mcp_oci_opsi.tools.tools_profile_management import (
    list_oci_profiles_enhanced,
    get_oci_profile_details,
    compare_oci_profiles
)
from mcp_oci_opsi.tools.tools_opsi_resource_stats import (
    summarize_database_insight_resource_statistics,
    summarize_database_insight_resource_usage,
    summarize_database_insight_tablespace_usage_trend
)
from mcp_oci_opsi.tools.tools_dbmanagement_users import (
    list_users,
    list_roles,
    list_system_privileges
)
from mcp_oci_opsi.tools.tools_dbmanagement_tablespaces import (
    list_tablespaces,
    get_tablespace
)
from mcp_oci_opsi.tools.tools_dbmanagement_awr_metrics import (
    summarize_awr_db_cpu_usages,
    summarize_awr_db_wait_event_buckets,
    summarize_awr_db_parameter_changes
)

# Configuration
COMPARTMENT_ID = os.getenv("OCI_COMPARTMENT_ID", "ocid1.compartment.oc1..example")
MANAGED_DATABASE_ID = None  # Will be populated from discovery
TIME_END = datetime.now()
TIME_START = TIME_END - timedelta(days=7)
TIME_START_STR = TIME_START.isoformat() + "Z"
TIME_END_STR = TIME_END.isoformat() + "Z"


def print_header():
    """Print demo header."""
    print("=" * 80)
    print("MCP OCI OPSI SERVER v2.0 - NEW FEATURES DEMO")
    print("=" * 80)
    print("\n🎉 What's New in v2.0:")
    print("  ✨ 18 new APIs")
    print("  🤖 Agent detection & prioritization")
    print("  👥 Multi-tenancy support")
    print("  📊 Resource statistics")
    print("  🔐 User management")
    print("  💾 Tablespace monitoring")
    print("  ⚡ AWR performance metrics")
    print(f"\nCompartment: {COMPARTMENT_ID}")
    print(f"Time Range: {TIME_START_STR} to {TIME_END_STR}")
    print(f"Duration: 7 days\n")


def print_section(title, number):
    """Print a section header."""
    print("\n" + "=" * 80)
    print(f"{number}. {title}")
    print("=" * 80)


def print_result(result, key_fields=None, max_items=3):
    """Print formatted result with key fields."""
    if "error" in result:
        print(f"❌ Error: {result['error']}")
        return False

    count = result.get('count', 0)
    if count == 0:
        print("⚠️  No items found")
        return False

    print(f"✅ Success! Found {count} items")

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

    return True


def demo():
    """Run the complete v2.0 demo."""
    global MANAGED_DATABASE_ID

    print_header()

    # ==============================================================
    # SECTION 1: AGENT DETECTION & PRIORITIZATION (NEW v2.0)
    # ==============================================================

    print("\n" + "🤖 " * 40)
    print("SECTION 1: AGENT DETECTION & PRIORITIZATION")
    print("🤖 " * 40)

    # DEMO 1: Agent Detection and Classification
    print_section("Agent Detection - Database Fleet Classification", 1)
    print("PROMPT: Classify all databases by agent type and show adoption rate\n")

    try:
        result = list_database_insights_by_management_type(
            compartment_id=COMPARTMENT_ID
        )

        if result.get('summary'):
            summary = result['summary']
            print(f"📊 Fleet Summary:")
            print(f"   Total Databases: {summary['total_databases']}")
            print(f"   Agent-Based: {summary['agent_based_databases']} ({summary['agent_based_percentage']}%)")
            print(f"   Non-Agent: {summary['total_databases'] - summary['agent_based_databases']}")
            print(f"\n💡 {summary['recommendation']}")

            print(f"\n📋 Breakdown by Agent Type:")
            for entity_type, info in summary.get('by_management_type', {}).items():
                status = "🤖" if info['agent_based'] else "📋"
                priority = info['priority']
                print(f"   {status} [Priority {priority}] {info['display_name']}: {info['count']}")

            # Get first database for later demos
            if result.get('databases') and len(result['databases']) > 0:
                first_db = result['databases'][0]
                print(f"\n🔍 Using database for subsequent demos: {first_db.get('database_name')}")
        else:
            print("⚠️  No summary data available")

    except Exception as e:
        print(f"❌ Error: {e}")

    # DEMO 2: API Compatibility Check
    print_section("API Compatibility Matrix", 2)
    print("PROMPT: Check which APIs are supported for a specific database\n")

    try:
        # Get database list
        db_list = list_database_insights_by_management_type(
            compartment_id=COMPARTMENT_ID
        )

        if db_list.get('databases') and len(db_list['databases']) > 0:
            db_id = db_list['databases'][0]['id']

            compat = get_database_api_compatibility(database_insight_id=db_id)

            print(f"Database: {compat.get('database_name', 'Unknown')}")
            print(f"Entity Source: {compat.get('entity_source', 'Unknown')}")
            print(f"Database Type: {compat.get('database_type', 'Unknown')}")
            print(f"Priority: {compat.get('priority', 'Unknown')}")

            print(f"\n📊 API Compatibility:")
            for api, details in compat.get('api_compatibility', {}).items():
                status = "✅" if details.get('supported') else "❌"
                print(f"   {status} {api}")
                if details.get('note'):
                    print(f"      → {details['note']}")

            if compat.get('recommendations'):
                print(f"\n💡 Recommendations:")
                for rec in compat['recommendations']:
                    print(f"   • {rec}")
        else:
            print("⚠️  No databases available for compatibility check")

    except Exception as e:
        print(f"❌ Error: {e}")

    # ==============================================================
    # SECTION 2: MULTI-TENANCY & PROFILE MANAGEMENT (NEW v2.0)
    # ==============================================================

    print("\n" + "👥 " * 40)
    print("SECTION 2: MULTI-TENANCY & PROFILE MANAGEMENT")
    print("👥 " * 40)

    # DEMO 3: List and Validate Profiles
    print_section("OCI Profile Management", 3)
    print("PROMPT: List all OCI profiles and validate configuration\n")

    try:
        profiles = list_oci_profiles_enhanced()

        print(f"📊 Profile Summary:")
        print(f"   Total Profiles: {profiles.get('total_profiles', 0)}")
        print(f"   Valid: {profiles.get('valid_profiles', 0)}")
        print(f"   Invalid: {profiles.get('invalid_profiles', 0)}")

        print(f"\n📋 Available Profiles:")
        for profile in profiles.get('profiles', [])[:5]:  # Show first 5
            status = "✅" if profile.get('valid') else "❌"
            print(f"   {status} {profile.get('name')}")
            print(f"      Region: {profile.get('region', 'Unknown')}")
            print(f"      Tenancy: {profile.get('tenancy_name', 'Unknown')}")
            if not profile.get('valid'):
                print(f"      Error: {profile.get('error', 'Unknown')}")

    except Exception as e:
        print(f"❌ Error: {e}")

    # DEMO 4: Compare Profiles
    print_section("Profile Comparison", 4)
    print("PROMPT: Compare two OCI profiles to identify differences\n")

    try:
        profiles = list_oci_profiles_enhanced()
        profile_list = profiles.get('profiles', [])

        if len(profile_list) >= 2:
            prof1 = profile_list[0].get('name')
            prof2 = profile_list[1].get('name')

            comparison = compare_oci_profiles(prof1, prof2)

            print(f"Comparing: {prof1} vs {prof2}\n")
            print(f"Profile 1 ({prof1}):")
            print(f"   Tenancy: {comparison['profile1'].get('tenancy_name')}")
            print(f"   Region: {comparison['profile1'].get('region')}")

            print(f"\nProfile 2 ({prof2}):")
            print(f"   Tenancy: {comparison['profile2'].get('tenancy_name')}")
            print(f"   Region: {comparison['profile2'].get('region')}")

            print(f"\n🔍 Comparison:")
            print(f"   Same Tenancy: {'✅' if comparison.get('same_tenancy') else '❌'}")
            print(f"   Same Region: {'✅' if comparison.get('same_region') else '❌'}")
            print(f"   Same User: {'✅' if comparison.get('same_user') else '❌'}")
        else:
            print("⚠️  Need at least 2 profiles for comparison")

    except Exception as e:
        print(f"❌ Error: {e}")

    # ==============================================================
    # SECTION 3: RESOURCE STATISTICS (NEW v2.0)
    # ==============================================================

    print("\n" + "📊 " * 40)
    print("SECTION 3: RESOURCE STATISTICS & MONITORING")
    print("📊 " * 40)

    # DEMO 5: CPU Resource Statistics
    print_section("CPU Resource Statistics", 5)
    print("PROMPT: Show CPU utilization across all databases\n")

    try:
        stats = summarize_database_insight_resource_statistics(
            compartment_id=COMPARTMENT_ID,
            resource_metric="CPU"
        )

        if stats.get('items'):
            for i, item in enumerate(stats['items'][:3], 1):
                db_details = item.get('database_details', {})
                current = item.get('current_statistics', {})

                print(f"\nDatabase {i}: {db_details.get('database_name', 'Unknown')}")
                print(f"   Type: {db_details.get('database_type', 'Unknown')}")
                print(f"   Utilization: {current.get('utilization_percent', 0):.1f}%")
                print(f"   Usage: {current.get('usage', 0):.2f}")
                print(f"   Capacity: {current.get('capacity', 0):.2f}")
        else:
            print("⚠️  No resource statistics available")

    except Exception as e:
        print(f"❌ Error: {e}")

    # DEMO 6: Tablespace Usage Trends
    print_section("Tablespace Usage Trends", 6)
    print("PROMPT: Show tablespace storage trends for capacity planning\n")

    try:
        trends = summarize_database_insight_tablespace_usage_trend(
            compartment_id=COMPARTMENT_ID,
            time_interval_start=TIME_START_STR,
            time_interval_end=TIME_END_STR
        )

        if trends.get('items'):
            for i, item in enumerate(trends['items'][:3], 1):
                print(f"\nTablespace {i}: {item.get('tablespace_name', 'Unknown')}")
                print(f"   Database: {item.get('database_name', 'Unknown')}")
                print(f"   Size (GB): {item.get('tablespace_size_in_gbs', 0):.2f}")
                print(f"   Used (GB): {item.get('tablespace_used_in_gbs', 0):.2f}")
                print(f"   Usage %: {item.get('usage_percent', 0):.1f}%")
        else:
            print("⚠️  No tablespace trends available")

    except Exception as e:
        print(f"❌ Error: {e}")

    # ==============================================================
    # SECTION 4: USER MANAGEMENT (NEW v2.0)
    # ==============================================================

    print("\n" + "🔐 " * 40)
    print("SECTION 4: USER & PRIVILEGE MANAGEMENT")
    print("🔐 " * 40)

    # Get a managed database ID for user queries
    print_section("Finding Managed Database", 7)
    print("INFO: Need a managed database ID for user/tablespace queries\n")

    # This would need a real managed database ID
    print("⚠️  Skipping user management demos (requires managed database ID)")
    print("   To run these demos, set MANAGED_DATABASE_ID in the script\n")

    # DEMO 7: List Database Users (commented out - needs managed DB)
    # print_section("Database Users", 7)
    # print("PROMPT: List all database users for security audit\n")
    #
    # if MANAGED_DATABASE_ID:
    #     try:
    #         users = list_users(managed_database_id=MANAGED_DATABASE_ID)
    #         print_result(users, key_fields=['name', 'status', 'profile', 'authentication_type'])
    #     except Exception as e:
    #         print(f"❌ Error: {e}")

    # DEMO 8: List Roles (commented out - needs managed DB)
    # print_section("Database Roles", 8)
    # print("PROMPT: List all database roles\n")
    #
    # if MANAGED_DATABASE_ID:
    #     try:
    #         roles = list_roles(managed_database_id=MANAGED_DATABASE_ID)
    #         print_result(roles, key_fields=['name', 'common', 'oracle_maintained'])
    #     except Exception as e:
    #         print(f"❌ Error: {e}")

    # ==============================================================
    # SECTION 5: AWR METRICS (NEW v2.0)
    # ==============================================================

    print("\n" + "⚡ " * 40)
    print("SECTION 5: AWR PERFORMANCE METRICS")
    print("⚡ " * 40)

    print("⚠️  Skipping AWR metrics demos (requires managed database ID)")
    print("   To run these demos, set MANAGED_DATABASE_ID in the script\n")

    # DEMO 9: CPU Usage from AWR (commented out - needs managed DB)
    # print_section("AWR CPU Usage", 9)
    # print("PROMPT: Show CPU usage trends from AWR\n")
    #
    # if MANAGED_DATABASE_ID:
    #     try:
    #         cpu = summarize_awr_db_cpu_usages(
    #             managed_database_id=MANAGED_DATABASE_ID,
    #             time_greater_than_or_equal_to=TIME_START_STR,
    #             time_less_than_or_equal_to=TIME_END_STR
    #         )
    #         print_result(cpu, key_fields=['timestamp', 'usage_pct', 'load'])
    #     except Exception as e:
    #         print(f"❌ Error: {e}")

    # DEMO 10: Wait Events (commented out - needs managed DB)
    # print_section("AWR Wait Events", 10)
    # print("PROMPT: Identify top wait events impacting performance\n")
    #
    # if MANAGED_DATABASE_ID:
    #     try:
    #         events = summarize_awr_db_wait_event_buckets(
    #             managed_database_id=MANAGED_DATABASE_ID,
    #             time_greater_than_or_equal_to=TIME_START_STR,
    #             time_less_than_or_equal_to=TIME_END_STR
    #         )
    #         print_result(events, key_fields=['name', 'total_time_waited', 'total_waits'])
    #     except Exception as e:
    #         print(f"❌ Error: {e}")

    # ==============================================================
    # FINAL SUMMARY
    # ==============================================================

    print("\n" + "=" * 80)
    print("DEMO COMPLETE - v2.0 FEATURES SUMMARY")
    print("=" * 80)

    print("\n✅ Demonstrated v2.0 Features:")
    print("   1. 🤖 Agent Detection & Prioritization")
    print("      - Automatic agent type classification")
    print("      - API compatibility checking")
    print("      - Migration recommendations")
    print()
    print("   2. 👥 Multi-Tenancy Support")
    print("      - Profile listing and validation")
    print("      - Profile comparison")
    print("      - Multi-account operations")
    print()
    print("   3. 📊 Resource Statistics")
    print("      - CPU utilization monitoring")
    print("      - Tablespace usage trends")
    print("      - Capacity planning")
    print()
    print("   4. 🔐 User Management (Requires Managed DB)")
    print("      - User listing and details")
    print("      - Role management")
    print("      - Privilege auditing")
    print()
    print("   5. ⚡ AWR Metrics (Requires Managed DB)")
    print("      - CPU usage analysis")
    print("      - Wait event tracking")
    print("      - Parameter changes")

    print("\n" + "=" * 80)
    print("📚 For More Information:")
    print("   - README_UPDATED.md - Complete v2.0 documentation")
    print("   - wiki/Quick-Start.md - Quick start guide")
    print("   - wiki/Agent-Detection.md - Agent detection guide")
    print("   - V2.0_RELEASE_SUMMARY.md - Full release notes")
    print("=" * 80)


if __name__ == "__main__":
    demo()
