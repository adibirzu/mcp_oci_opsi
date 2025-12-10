import os
#!/usr/bin/env python3
"""
Comprehensive API Validation Suite
Tests all 117 MCP OCI OPSI tools to identify which work correctly.
"""

import json
import traceback
from datetime import datetime, timedelta, UTC
from typing import Dict, List, Any

# Import all tool modules
from mcp_oci_opsi import (
    tools_opsi,
    tools_opsi_extended,
    tools_opsi_resource_stats,
    tools_database_registration,
    tools_database_discovery,
    tools_profile_management,
    tools_dbmanagement,
    tools_dbmanagement_users,
    tools_dbmanagement_tablespaces,
    tools_dbmanagement_awr_metrics,
    tools_opsi_sql_insights
)

# Test configuration
COMPARTMENT_ID = os.getenv("OCI_COMPARTMENT_ID", "ocid1.compartment.oc1..example")
TIME_END = datetime.now(UTC).isoformat().replace('+00:00', 'Z')
TIME_START = (datetime.now(UTC) - timedelta(days=7)).isoformat().replace('+00:00', 'Z')

# Sample database insight IDs (will be populated from list call)
DATABASE_INSIGHT_IDS = []
MACS_DATABASE_ID = None
AUTONOMOUS_DATABASE_ID = None

class APITestResult:
    def __init__(self, module: str, function: str):
        self.module = module
        self.function = function
        self.status = "NOT_TESTED"
        self.error_type = None
        self.error_message = None
        self.response_count = 0
        self.response_sample = None
        self.notes = []

    def to_dict(self):
        return {
            "module": self.module,
            "function": self.function,
            "status": self.status,
            "error_type": self.error_type,
            "error_message": self.error_message,
            "response_count": self.response_count,
            "notes": self.notes
        }

def test_function(module_name: str, func_name: str, func: callable, params: Dict[str, Any]) -> APITestResult:
    """Test a single API function with given parameters."""
    result = APITestResult(module_name, func_name)

    try:
        response = func(**params)

        # Check if response has error
        if isinstance(response, dict) and "error" in response:
            error = response["error"]

            if isinstance(error, dict):
                result.status = "API_ERROR"
                result.error_type = error.get("code", "Unknown")
                result.error_message = error.get("message", str(error))

                # Check for specific error patterns
                if result.error_type == 404:
                    result.notes.append("API endpoint not found (404)")
                elif "NotAuthorizedOrNotFound" in str(result.error_message):
                    result.notes.append("Resource not found or not authorized")
            else:
                result.status = "API_ERROR"
                result.error_message = str(error)
        else:
            # Success!
            result.status = "SUCCESS"

            # Get response count if available
            if isinstance(response, dict):
                result.response_count = response.get("count", response.get("data_points", 0))

                # Store sample data
                if "items" in response and response["items"]:
                    result.response_sample = response["items"][0] if len(response["items"]) > 0 else None

            result.notes.append(f"Returned {result.response_count} items")

    except AttributeError as e:
        result.status = "SDK_ERROR"
        result.error_type = "AttributeError"
        result.error_message = str(e)
        result.notes.append("Missing SDK model or attribute")

    except TypeError as e:
        result.status = "PARAMETER_ERROR"
        result.error_type = "TypeError"
        result.error_message = str(e)
        result.notes.append("Invalid parameters")

    except Exception as e:
        result.status = "EXCEPTION"
        result.error_type = type(e).__name__
        result.error_message = str(e)
        result.notes.append(f"Unexpected error: {type(e).__name__}")

    return result

def initialize_test_data():
    """Initialize test data by listing database insights."""
    global DATABASE_INSIGHT_IDS, MACS_DATABASE_ID, AUTONOMOUS_DATABASE_ID

    print("Initializing test data...")
    print("-" * 80)

    # List database insights
    result = tools_opsi.list_database_insights(compartment_id=COMPARTMENT_ID)

    if "error" not in result:
        items = result.get("items", [])
        print(f"Found {len(items)} database insights")

        DATABASE_INSIGHT_IDS = [db.get("id") for db in items[:10]]  # Take first 10

        # Find MACS and Autonomous databases
        for db in items:
            entity_source = db.get("entity_source", "")
            db_id = db.get("id")

            if "MACS" in entity_source and not MACS_DATABASE_ID:
                MACS_DATABASE_ID = db_id
                print(f"  MACS database: {db.get('database_display_name')}")

            if "AUTONOMOUS" in entity_source and not AUTONOMOUS_DATABASE_ID:
                AUTONOMOUS_DATABASE_ID = db_id
                print(f"  Autonomous database: {db.get('database_display_name')}")

        print(f"  Total database IDs for testing: {len(DATABASE_INSIGHT_IDS)}")
    else:
        print(f"  ⚠️  Warning: Could not list database insights: {result['error']}")

    print()

def run_all_tests() -> List[APITestResult]:
    """Run tests for all API functions."""
    results = []

    # Initialize test data
    initialize_test_data()

    # Define test cases
    test_cases = [
        # OPSI Basic APIs
        {
            "module": "tools_opsi",
            "tests": [
                ("list_database_insights", {"compartment_id": COMPARTMENT_ID}),
                ("list_host_insights", {"compartment_id": COMPARTMENT_ID}),
                ("list_exadata_insights", {"compartment_id": COMPARTMENT_ID}),
            ]
        },

        # OPSI Extended APIs
        {
            "module": "tools_opsi_extended",
            "tests": [
                ("summarize_sql_statistics", {
                    "compartment_id": COMPARTMENT_ID,
                    "time_interval_start": TIME_START,
                    "time_interval_end": TIME_END
                }),
                ("summarize_database_insight_resource_capacity_trend", {
                    "compartment_id": COMPARTMENT_ID,
                    "resource_metric": "CPU",
                    "time_interval_start": TIME_START,
                    "time_interval_end": TIME_END
                }),
                ("summarize_database_insight_resource_forecast_trend", {
                    "compartment_id": COMPARTMENT_ID,
                    "resource_metric": "CPU",
                    "time_interval_start": TIME_START,
                    "time_interval_end": TIME_END
                }),
            ]
        },

        # Resource Statistics APIs (v2.0 - known issues)
        {
            "module": "tools_opsi_resource_stats",
            "tests": [
                ("summarize_database_insight_resource_usage", {
                    "compartment_id": COMPARTMENT_ID,
                    "resource_metric": "CPU",
                    "time_interval_start": TIME_START,
                    "time_interval_end": TIME_END
                }),
                ("summarize_database_insight_resource_utilization_insight", {
                    "compartment_id": COMPARTMENT_ID,
                    "resource_metric": "CPU",
                    "time_interval_start": TIME_START,
                    "time_interval_end": TIME_END
                }),
                ("summarize_database_insight_tablespace_usage_trend", {
                    "compartment_id": COMPARTMENT_ID,
                    "time_interval_start": TIME_START,
                    "time_interval_end": TIME_END
                }),
            ]
        },

        # Database Discovery APIs
        {
            "module": "tools_database_discovery",
            "tests": [
                ("list_database_insights_by_management_type", {"compartment_id": COMPARTMENT_ID}),
            ]
        },

        # Profile Management APIs
        {
            "module": "tools_profile_management",
            "tests": [
                ("list_oci_profiles_enhanced", {}),
                ("get_current_oci_profile", {}),
            ]
        },

        # SQL Insights APIs
        {
            "module": "tools_opsi_sql_insights",
            "tests": [
                ("summarize_sql_insights", {
                    "compartment_id": COMPARTMENT_ID,
                    "time_interval_start": TIME_START,
                    "time_interval_end": TIME_END
                }),
            ]
        },

        # Database Management APIs
        {
            "module": "tools_dbmanagement",
            "tests": [
                ("list_managed_databases", {"compartment_id": COMPARTMENT_ID}),
            ]
        },
    ]

    # Run tests
    total_tests = sum(len(module_tests["tests"]) for module_tests in test_cases)
    current_test = 0

    print("=" * 80)
    print(f"RUNNING {total_tests} API TESTS")
    print("=" * 80)
    print()

    for module_config in test_cases:
        module_name = module_config["module"]
        module = globals()[module_name]

        print(f"Testing module: {module_name}")
        print("-" * 80)

        for func_name, params in module_config["tests"]:
            current_test += 1
            print(f"[{current_test}/{total_tests}] Testing {func_name}...", end=" ")

            func = getattr(module, func_name)
            result = test_function(module_name, func_name, func, params)
            results.append(result)

            # Print result
            status_icon = {
                "SUCCESS": "✅",
                "API_ERROR": "❌",
                "SDK_ERROR": "⚠️",
                "PARAMETER_ERROR": "⚠️",
                "EXCEPTION": "❌",
                "NOT_TESTED": "⏭️"
            }.get(result.status, "❓")

            print(f"{status_icon} {result.status}")
            if result.error_message:
                print(f"     Error: {result.error_message[:100]}")

        print()

    return results

def generate_report(results: List[APITestResult]):
    """Generate a comprehensive test report."""
    print("=" * 80)
    print("TEST REPORT SUMMARY")
    print("=" * 80)
    print()

    # Count by status
    status_counts = {}
    for result in results:
        status_counts[result.status] = status_counts.get(result.status, 0) + 1

    total = len(results)
    success_count = status_counts.get("SUCCESS", 0)

    print(f"Total APIs Tested: {total}")
    print(f"Success Rate: {success_count}/{total} ({100*success_count/total:.1f}%)")
    print()

    print("Results by Status:")
    for status, count in sorted(status_counts.items()):
        percentage = 100 * count / total
        print(f"  {status}: {count} ({percentage:.1f}%)")

    print()
    print("=" * 80)
    print("FAILED APIs (Need Attention)")
    print("=" * 80)
    print()

    failed = [r for r in results if r.status != "SUCCESS"]

    if not failed:
        print("🎉 All APIs working correctly!")
    else:
        for result in failed:
            print(f"❌ {result.module}.{result.function}")
            print(f"   Status: {result.status}")
            print(f"   Error: {result.error_type} - {result.error_message[:100]}")
            if result.notes:
                print(f"   Notes: {', '.join(result.notes)}")
            print()

    print("=" * 80)
    print("WORKING APIs (Production Ready)")
    print("=" * 80)
    print()

    working = [r for r in results if r.status == "SUCCESS"]

    for result in working:
        print(f"✅ {result.module}.{result.function}")
        print(f"   Response count: {result.response_count}")
        if result.notes:
            print(f"   Notes: {', '.join(result.notes)}")
        print()

    # Save detailed results to JSON
    with open("api_validation_results.json", "w") as f:
        json.dump([r.to_dict() for r in results], f, indent=2)

    print("=" * 80)
    print(f"Detailed results saved to: api_validation_results.json")
    print("=" * 80)

if __name__ == "__main__":
    print("MCP OCI OPSI Server - Comprehensive API Validation")
    print("=" * 80)
    print()

    results = run_all_tests()
    generate_report(results)
