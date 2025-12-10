import os
#!/usr/bin/env python3
"""
Advanced diagnostic tool for OCI Operations Insights permissions.
Identifies why you get 404 errors when console works.
"""

import oci
from datetime import datetime, timedelta
from mcp_oci_opsi.oci_clients import get_opsi_client
from mcp_oci_opsi.config import get_oci_config

# Your problematic database insight
DATABASE_INSIGHT_ID = "ocid1.opsidatabaseinsight.oc1.uk-london-1.amaaaaaaqgp2kriai6hvr5dforjaiew3upfsvnylpim7gu3jdafo4hex6jpq"
COMPARTMENT_ID = os.getenv("OCI_COMPARTMENT_ID", "ocid1.compartment.oc1..example")


def print_section(title):
    print("\n" + "=" * 80)
    print(title)
    print("=" * 80)


def check_database_insight_details():
    """Check if we can even GET the database insight."""
    print_section("1. Checking Database Insight Accessibility")

    try:
        config = get_oci_config()
        client = oci.opsi.OperationsInsightsClient(config)

        print(f"Attempting to get database insight: {DATABASE_INSIGHT_ID}")

        response = client.get_database_insight(DATABASE_INSIGHT_ID)
        db_insight = response.data

        print(f"\n✅ SUCCESS - Database insight is accessible!")
        print(f"\nDetails:")
        print(f"  Type: {type(db_insight).__name__}")
        print(f"  Database Name: {getattr(db_insight, 'database_name', getattr(db_insight, 'database_display_name', 'N/A'))}")
        print(f"  Display Name: {getattr(db_insight, 'database_display_name', 'N/A')}")
        print(f"  Status: {db_insight.status}")
        print(f"  Lifecycle State: {db_insight.lifecycle_state}")
        print(f"  Database Type: {db_insight.database_type}")
        print(f"  Entity Source: {db_insight.entity_source}")
        print(f"  Compartment: {db_insight.compartment_id}")

        # Check for EM-Managed databases
        if db_insight.entity_source == "EM_MANAGED_EXTERNAL_DATABASE":
            print(f"\n⚠️  CRITICAL: This is an EM-Managed External Database")
            print(f"   EM-Managed databases have LIMITED API support!")
            print(f"\n   Known limitations:")
            print(f"   ❌ SQL Statistics API may not work")
            print(f"   ❌ Resource Statistics API may have limited data")
            print(f"   ❌ Some capacity planning APIs may return 404")
            print(f"\n   ✅ These APIs typically DO work:")
            print(f"      - list_database_insights()")
            print(f"      - get_database_insight()")
            print(f"      - Warehouse queries (if warehouse enabled)")
            print(f"\n   💡 RECOMMENDED SOLUTIONS:")
            print(f"      1. Use Operations Insights Warehouse queries instead")
            print(f"      2. Enable native OPSI agent on database")
            print(f"      3. Use Database Management APIs as fallback")
            return db_insight

        # Check if enabled
        if db_insight.status != "ENABLED":
            print(f"\n⚠️  WARNING: Database insight status is {db_insight.status}, not ENABLED")
            print(f"   This might cause 404 errors on some APIs")

        return db_insight

    except oci.exceptions.ServiceError as e:
        print(f"\n❌ FAILED to get database insight")
        print(f"   Status: {e.status}")
        print(f"   Code: {e.code}")
        print(f"   Message: {e.message}")
        print(f"\n   This means:")
        if e.status == 404:
            print(f"   - The database insight OCID doesn't exist, OR")
            print(f"   - You don't have permission to READ database insights")
        return None


def check_api_permissions():
    """Test each API that's failing."""
    print_section("2. Testing Individual API Permissions")

    # Use past dates to avoid InvalidParameter errors
    time_end = datetime.now() - timedelta(hours=1)
    time_start = time_end - timedelta(days=7)

    apis_to_test = [
        {
            "name": "SQL Statistics",
            "function": lambda client: client.summarize_sql_statistics(
                compartment_id=COMPARTMENT_ID,
                time_interval_start=time_start,
                time_interval_end=time_end,
                database_id=[DATABASE_INSIGHT_ID]
            ),
            "required_permissions": [
                "inspect opsi-database-insights",
                "read sql-statistics"
            ]
        },
        {
            "name": "Resource Statistics",
            "function": lambda client: client.summarize_database_insight_resource_statistics(
                compartment_id=COMPARTMENT_ID,
                resource_metric="CPU",
                time_interval_start=time_start,
                time_interval_end=time_end
            ),
            "required_permissions": [
                "inspect opsi-database-insights",
                "read database-insight-resource-statistics"
            ]
        },
        {
            "name": "Resource Capacity Trend",
            "function": lambda client: client.summarize_database_insight_resource_capacity_trend(
                compartment_id=COMPARTMENT_ID,
                resource_metric="CPU",
                time_interval_start=time_start,
                time_interval_end=time_end
            ),
            "required_permissions": [
                "inspect opsi-database-insights",
                "read database-insight-resource-capacity-trend"
            ]
        }
    ]

    config = get_oci_config()
    client = oci.opsi.OperationsInsightsClient(config)

    results = []
    for api in apis_to_test:
        print(f"\nTesting: {api['name']}")
        print(f"Time range: {time_start} to {time_end}")

        try:
            response = api['function'](client)
            print(f"  ✅ SUCCESS - API call worked!")
            if hasattr(response.data, 'items'):
                print(f"     Returned {len(response.data.items)} items")
            results.append({"api": api['name'], "status": "SUCCESS"})
        except oci.exceptions.ServiceError as e:
            print(f"  ❌ FAILED - {e.status} {e.code}")
            print(f"     Message: {e.message}")
            print(f"\n     Required permissions:")
            for perm in api['required_permissions']:
                print(f"       - {perm}")
            results.append({"api": api['name'], "status": "FAILED", "error": e.code})

    return results


def check_iam_user():
    """Check what user/principal we're running as."""
    print_section("3. Checking OCI Authentication Identity")

    try:
        config = get_oci_config()
        identity_client = oci.identity.IdentityClient(config)

        # Get user details
        user = identity_client.get_user(config['user']).data

        print(f"Authenticated as:")
        print(f"  User OCID: {user.id}")
        print(f"  Name: {user.name}")
        print(f"  Description: {getattr(user, 'description', 'N/A')}")
        print(f"\nTenancy:")
        print(f"  Tenancy OCID: {config['tenancy']}")
        print(f"  Region: {config['region']}")

        # Try to get user's groups
        print(f"\nUser's Groups:")
        try:
            user_group_memberships = identity_client.list_user_group_memberships(
                compartment_id=config['tenancy'],
                user_id=user.id
            ).data

            for membership in user_group_memberships:
                group = identity_client.get_group(membership.group_id).data
                print(f"  - {group.name} ({group.id})")
        except Exception as e:
            print(f"  Could not list groups: {e}")

        return user

    except Exception as e:
        print(f"❌ Failed to get user details: {e}")
        return None


def check_console_vs_api_difference():
    """Explain why console might work but API doesn't."""
    print_section("4. Console vs API Differences")

    print("""
Common reasons you can see data in console but get 404 via API:

1. **Different Credentials**
   Console: Uses your web session (might be federated SSO)
   API/CLI: Uses ~/.oci/config file credentials
   → Solution: Verify you're using the same user in both

2. **Different Permissions Scope**
   Console: Often uses dynamic groups or instance principals
   API/CLI: Uses the specific user in config file
   → Solution: Add API user to same groups as your console user

3. **Resource-Specific Permissions**
   Some APIs require permissions on the SPECIFIC resource, not just compartment
   → Solution: Add policies like:
      Allow group YourGroup to read database-insights in compartment WHERE target.id = 'ocid1...'

4. **Entity Source Limitations**
   Some database insight types (PE, EM-MANAGED) have API limitations
   → Solution: Check if database is EM-MANAGED_EXTERNAL_DATABASE type

5. **Federation/SSO**
   Console might use SAML/OIDC federation
   API uses native OCI user
   → Solution: Ensure API user has same group memberships

6. **Time-Based Policies**
   Some policies have time-based conditions
   → Solution: Check if policies have time restrictions
    """)


def generate_required_policies():
    """Generate the exact IAM policies needed."""
    print_section("5. Required IAM Policies")

    print("""
Add these policies to your OCI tenancy:

# Basic Operations Insights Read Access
Allow group DatabaseAdmins to read opsi-database-insights in compartment YourCompartment
Allow group DatabaseAdmins to read sql-statistics in compartment YourCompartment
Allow group DatabaseAdmins to read opsi-data-objects in compartment YourCompartment

# Database Insight Resource Statistics
Allow group DatabaseAdmins to read database-insight-resource-statistics in compartment YourCompartment

# Database Insight Capacity Trends
Allow group DatabaseAdmins to read database-insight-resource-capacity-trend in compartment YourCompartment

# If using warehouse queries
Allow group DatabaseAdmins to use operations-insights-warehouse in compartment YourCompartment

# For managed databases
Allow group DatabaseAdmins to read database-management-family in compartment YourCompartment

# Alternative: Grant broader access
Allow group DatabaseAdmins to read all-resources in compartment YourCompartment where request.permission='OPSI_READ'

# For root compartment access (not recommended, but works)
Allow group DatabaseAdmins to read all-resources in tenancy where request.permission='OPSI_READ'
    """)

    print("\n💡 TIP: Replace 'DatabaseAdmins' with your actual group name")
    print("💡 TIP: Replace 'YourCompartment' with your compartment name or OCID")


def check_alternative_approaches():
    """Suggest alternative ways to get the same data."""
    print_section("6. Alternative Approaches")

    print("""
If direct API calls keep failing, try these alternatives:

1. **Use Warehouse Queries (SQL)**
   Instead of:  summarize_sql_statistics()
   Try:         query_warehouse_standard("SELECT * FROM SqlStats WHERE ...")

   Pros: More flexible, works with different permissions
   Cons: Requires warehouse to be configured

2. **Use List APIs Instead of Summarize**
   Instead of:  summarize_database_insight_resource_statistics()
   Try:         list_database_insights() + iterate through results

   Pros: List APIs often have looser permissions
   Cons: May not have aggregated metrics

3. **Use Database Management APIs**
   Instead of:  Operations Insights APIs
   Try:         Database Management Performance Hub APIs

   Pros: Different permission model
   Cons: Different data model

4. **Use Resource Principal**
   If running on OCI Compute/Functions:
   Instead of:  User credentials
   Try:         Instance principal or resource principal

   Pros: No credential management
   Cons: Only works within OCI
    """)


def main():
    """Run all diagnostics."""
    print("=" * 80)
    print("OCI OPERATIONS INSIGHTS PERMISSION DIAGNOSTIC TOOL")
    print("=" * 80)
    print(f"\nTarget Database Insight: {DATABASE_INSIGHT_ID}")
    print(f"Compartment: {COMPARTMENT_ID}")
    print(f"Current Time: {datetime.now().isoformat()}")

    # Run all checks
    db_insight = check_database_insight_details()
    check_iam_user()
    api_results = check_api_permissions()
    check_console_vs_api_difference()
    generate_required_policies()
    check_alternative_approaches()

    # Final summary
    print_section("7. Summary & Recommendations")

    if db_insight:
        print("✅ Database insight is accessible")
        if db_insight.status == "ENABLED":
            print("✅ Database insight is enabled")
        else:
            print(f"⚠️  Database insight status: {db_insight.status}")
    else:
        print("❌ Cannot access database insight - this is the root cause")
        print("\n   SOLUTION: Add this policy:")
        print("   Allow group YourGroup to read opsi-database-insights in compartment YourCompartment")

    print(f"\nAPI Test Results:")
    failed_apis = [r for r in api_results if r['status'] == 'FAILED']
    if failed_apis:
        print(f"  ❌ {len(failed_apis)} APIs failed")
        for api in failed_apis:
            print(f"     - {api['api']}: {api.get('error', 'Unknown error')}")
        print(f"\n   NEXT STEPS:")
        print(f"   1. Review required permissions in section 5")
        print(f"   2. Add missing policies to your OCI tenancy")
        print(f"   3. Verify you're in the correct group")
        print(f"   4. Wait 1-2 minutes for policy propagation")
    else:
        print(f"  ✅ All APIs working correctly")

    print("\n" + "=" * 80)
    print("DIAGNOSTIC COMPLETE")
    print("=" * 80)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nDiagnostic interrupted by user")
    except Exception as e:
        print(f"\n\nDiagnostic failed with error: {e}")
        import traceback
        traceback.print_exc()
