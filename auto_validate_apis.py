import os
#!/usr/bin/env python3
"""
Auto-Discovering API Validation Suite
Automatically finds and tests all API functions in the MCP OCI OPSI server.
"""

import json
import inspect
from datetime import datetime, timedelta, UTC
from typing import Dict, List, Any, Callable
import importlib

# Test configuration
COMPARTMENT_ID = os.getenv("OCI_COMPARTMENT_ID", "ocid1.compartment.oc1..example")
TIME_END = datetime.now(UTC).isoformat().replace('+00:00', 'Z')
TIME_START = (datetime.now(UTC) - timedelta(days=7)).isoformat().replace('+00:00', 'Z')

class APITestResult:
    def __init__(self, module: str, function: str):
        self.module = module
        self.function = function
        self.status = "NOT_TESTED"
        self.error_type = None
        self.error_message = None
        self.response_count = 0
        self.notes = []

    def to_dict(self):
        return {
            "module": self.module,
            "function": self.function,
            "status": self.status,
            "error_type": self.error_type,
            "error_message": self.error_message[:200] if self.error_message else None,
            "response_count": self.response_count,
            "notes": self.notes
        }

def get_function_params(func: Callable) -> Dict[str, Any]:
    """Generate test parameters based on function signature."""
    sig = inspect.signature(func)
    params = {}

    for param_name, param in sig.parameters.items():
        if param_name == "compartment_id":
            params[param_name] = COMPARTMENT_ID
        elif param_name in ["time_interval_start", "start_time"]:
            params[param_name] = TIME_START
        elif param_name in ["time_interval_end", "end_time"]:
            params[param_name] = TIME_END
        elif param_name == "resource_metric":
            params[param_name] = "CPU"
        elif param_name in ["limit", "page_size"]:
            params[param_name] = 10

    return params

def test_function(module_name: str, func_name: str, func: Callable) -> APITestResult:
    """Test a single API function."""
    result = APITestResult(module_name, func_name)

    # Generate parameters
    params = get_function_params(func)

    try:
        response = func(**params)

        # Check if response has error
        if isinstance(response, dict) and "error" in response:
            error = response["error"]

            if isinstance(error, dict):
                result.status = "API_ERROR"
                result.error_type = str(error.get("code", error.get("status", "Unknown")))
                result.error_message = error.get("message", str(error))[:200]

                # Categorize error
                if result.error_type == "404" or "404" in result.error_message:
                    result.notes.append("API endpoint returns 404")
                elif "NotAuthorizedOrNotFound" in result.error_message:
                    result.notes.append("Resource not found or not authorized")
                elif "compartment" in result.error_message.lower():
                    result.notes.append("Compartment issue")
            else:
                result.status = "API_ERROR"
                result.error_message = str(error)[:200]
        else:
            # Success!
            result.status = "SUCCESS"

            # Get response count if available
            if isinstance(response, dict):
                result.response_count = response.get("count", response.get("data_points", 0))
                result.notes.append(f"Returned {result.response_count} items")

    except AttributeError as e:
        result.status = "SDK_ERROR"
        result.error_type = "AttributeError"
        result.error_message = str(e)[:200]
        result.notes.append("Missing SDK model/attribute")

    except TypeError as e:
        result.status = "PARAMETER_ERROR"
        result.error_type = "TypeError"
        result.error_message = str(e)[:200]
        result.notes.append("Invalid/missing parameters")

    except Exception as e:
        result.status = "EXCEPTION"
        result.error_type = type(e).__name__
        result.error_message = str(e)[:200]

    return result

def discover_and_test_module(module_name: str) -> List[APITestResult]:
    """Discover all functions in a module and test them."""
    results = []

    try:
        module = importlib.import_module(f"mcp_oci_opsi.{module_name}")
    except ImportError:
        print(f"  ⚠️  Could not import {module_name}")
        return results

    # Find all public functions
    functions = []
    for name in dir(module):
        if name.startswith("_"):
            continue

        obj = getattr(module, name)
        if callable(obj) and hasattr(obj, "__module__") and module_name in obj.__module__:
            functions.append(name)

    print(f"\n{module_name}: Found {len(functions)} functions")
    print("-" * 80)

    for func_name in sorted(functions):
        func = getattr(module, func_name)

        print(f"  Testing {func_name}...", end=" ")

        result = test_function(module_name, func_name, func)
        results.append(result)

        # Print result
        status_icon = {
            "SUCCESS": "✅",
            "API_ERROR": "❌",
            "SDK_ERROR": "⚠️",
            "PARAMETER_ERROR": "⏭️",
            "EXCEPTION": "❌",
            "NOT_TESTED": "⏭️"
        }.get(result.status, "❓")

        print(f"{status_icon} {result.status}", end="")
        if result.response_count > 0:
            print(f" ({result.response_count} items)")
        else:
            print()

    return results

def main():
    print("=" * 80)
    print("MCP OCI OPSI - Auto-Discovering API Validation")
    print("=" * 80)

    # Modules to test
    modules_to_test = [
        "tools_opsi",
        "tools_opsi_extended",
        "tools_opsi_resource_stats",
        "tools_opsi_sql_insights",
        "tools_database_discovery",
        "tools_database_registration",
        "tools_profile_management",
        "tools_dbmanagement",
        "tools_dbmanagement_users",
        "tools_dbmanagement_tablespaces",
        "tools_dbmanagement_awr_metrics",
    ]

    all_results = []

    for module_name in modules_to_test:
        results = discover_and_test_module(module_name)
        all_results.extend(results)

    # Generate report
    print("\n" + "=" * 80)
    print("TEST REPORT SUMMARY")
    print("=" * 80)

    # Count by status
    status_counts = {}
    for result in all_results:
        status_counts[result.status] = status_counts.get(result.status, 0) + 1

    total = len(all_results)
    success_count = status_counts.get("SUCCESS", 0)
    error_count = status_counts.get("API_ERROR", 0)
    sdk_error_count = status_counts.get("SDK_ERROR", 0)

    print(f"\nTotal APIs Tested: {total}")
    print(f"✅ Working: {success_count} ({100*success_count/total:.1f}%)")
    print(f"❌ API Errors (404): {error_count} ({100*error_count/total:.1f}%)")
    print(f"⚠️  SDK Errors: {sdk_error_count} ({100*sdk_error_count/total:.1f}%)")
    print(f"⏭️  Parameter Errors: {status_counts.get('PARAMETER_ERROR', 0)}")

    # Categorize by module
    print("\n" + "=" * 80)
    print("RESULTS BY MODULE")
    print("=" * 80)

    by_module = {}
    for result in all_results:
        if result.module not in by_module:
            by_module[result.module] = {"success": 0, "failed": 0}

        if result.status == "SUCCESS":
            by_module[result.module]["success"] += 1
        else:
            by_module[result.module]["failed"] += 1

    for module, counts in sorted(by_module.items()):
        total_module = counts["success"] + counts["failed"]
        success_rate = 100 * counts["success"] / total_module if total_module > 0 else 0
        print(f"\n{module}:")
        print(f"  ✅ {counts['success']}/{total_module} working ({success_rate:.0f}%)")

    # List failed APIs
    print("\n" + "=" * 80)
    print("FAILED APIs (Not Production Ready)")
    print("=" * 80)

    failed = [r for r in all_results if r.status in ["API_ERROR", "SDK_ERROR"]]

    if not failed:
        print("\n🎉 All APIs working correctly!")
    else:
        by_error_type = {}
        for result in failed:
            error_key = result.error_type or "Unknown"
            if error_key not in by_error_type:
                by_error_type[error_key] = []
            by_error_type[error_key].append(result)

        for error_type, results in sorted(by_error_type.items()):
            print(f"\n{error_type} ({len(results)} APIs):")
            for result in results[:5]:  # Show first 5 of each type
                print(f"  ❌ {result.module}.{result.function}")
                if result.notes:
                    print(f"     {', '.join(result.notes)}")

            if len(results) > 5:
                print(f"  ... and {len(results) - 5} more")

    # Save detailed results
    with open("api_validation_results.json", "w") as f:
        json.dump({
            "summary": {
                "total": total,
                "success": success_count,
                "api_errors": error_count,
                "sdk_errors": sdk_error_count,
                "success_rate": f"{100*success_count/total:.1f}%"
            },
            "by_module": by_module,
            "results": [r.to_dict() for r in all_results]
        }, f, indent=2)

    print("\n" + "=" * 80)
    print(f"Detailed results saved to: api_validation_results.json")
    print("=" * 80)

if __name__ == "__main__":
    main()
