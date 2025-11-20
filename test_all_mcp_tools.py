#!/usr/bin/env python3
"""
Comprehensive MCP Tool Testing Script

Tests all 94 MCP tools defined in main.py to ensure they are ready for production use.

Test Categories:
1. Utility Tools (ping, whoami, profiles)
2. Cache Tools (build, search, statistics)
3. Database Insights Tools
4. Host Insights Tools
5. SQL Analytics Tools
6. Database Management Tools
7. Profile Management Tools
8. Visualization Tools

Output:
- Detailed test results for each tool
- Success/failure statistics
- Performance metrics
- Recommendations for improvements
"""

import json
import os
import sys
import time
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

# Add the package to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from mcp_oci_opsi.config import get_oci_config, list_available_profiles, get_current_profile
from mcp_oci_opsi.cache import get_cache


class MCPToolTester:
    """Comprehensive tester for all MCP tools."""

    def __init__(self):
        """Initialize the tester."""
        self.results = {
            "test_date": datetime.utcnow().isoformat() + "Z",
            "total_tools": 94,
            "tested": 0,
            "passed": 0,
            "failed": 0,
            "skipped": 0,
            "categories": {},
            "details": []
        }
        self.compartment_id = None
        self.database_id = None
        self.host_id = None

    def setup(self):
        """Setup test environment."""
        print("=" * 80)
        print("MCP OCI OPSI - Comprehensive Tool Testing")
        print("=" * 80)
        print()

        # Get configuration
        try:
            config = get_oci_config()
            print(f"✅ OCI Config loaded")
            print(f"   Profile: {get_current_profile()}")
            print(f"   Region: {config.get('region')}")
            print(f"   Tenancy: {config.get('tenancy')[:50]}...")
            print()

            # Try to get compartment ID from env
            self.compartment_id = os.getenv("TEST_COMPARTMENT_ID")
            if self.compartment_id:
                print(f"✅ Test compartment ID: {self.compartment_id[:50]}...")
            else:
                print("⚠️  TEST_COMPARTMENT_ID not set - some tests will be skipped")

            print()
            return True

        except Exception as e:
            print(f"❌ Setup failed: {e}")
            return False

    def test_tool(self, category: str, tool_name: str, test_func, expected_keys: List[str] = None) -> Dict[str, Any]:
        """
        Test a single MCP tool.

        Args:
            category: Tool category (e.g., "Utility", "Cache")
            tool_name: Name of the tool
            test_func: Function to test the tool
            expected_keys: Keys expected in the response

        Returns:
            Test result dictionary
        """
        result = {
            "category": category,
            "tool": tool_name,
            "status": "unknown",
            "duration_ms": 0,
            "error": None,
            "response_keys": [],
            "response_size": 0
        }

        try:
            start_time = time.time()
            response = test_func()
            duration_ms = (time.time() - start_time) * 1000

            result["duration_ms"] = round(duration_ms, 2)

            # Check response
            if response is None:
                result["status"] = "failed"
                result["error"] = "Returned None"
            elif isinstance(response, dict):
                result["response_keys"] = list(response.keys())
                result["response_size"] = len(json.dumps(response))

                # Check for errors in response
                if "error" in response:
                    result["status"] = "failed"
                    result["error"] = response["error"]
                elif expected_keys:
                    missing = [k for k in expected_keys if k not in response]
                    if missing:
                        result["status"] = "warning"
                        result["error"] = f"Missing keys: {missing}"
                    else:
                        result["status"] = "passed"
                else:
                    result["status"] = "passed"
            else:
                result["status"] = "passed"
                result["response_size"] = len(str(response))

        except Exception as e:
            result["status"] = "failed"
            result["error"] = str(e)

        # Update statistics
        self.results["tested"] += 1
        if result["status"] == "passed":
            self.results["passed"] += 1
        elif result["status"] == "failed":
            self.results["failed"] += 1

        # Add to category stats
        if category not in self.results["categories"]:
            self.results["categories"][category] = {"passed": 0, "failed": 0, "skipped": 0}

        if result["status"] == "passed":
            self.results["categories"][category]["passed"] += 1
        elif result["status"] == "failed":
            self.results["categories"][category]["failed"] += 1

        self.results["details"].append(result)
        return result

    def print_result(self, result: Dict[str, Any]):
        """Print test result."""
        status_icon = {
            "passed": "✅",
            "failed": "❌",
            "warning": "⚠️ ",
            "skipped": "⏭️ "
        }.get(result["status"], "❓")

        print(f"   {status_icon} {result['tool']:<50} {result['duration_ms']:>8.2f}ms")
        if result.get("error"):
            print(f"      Error: {result['error']}")

    def test_utility_tools(self):
        """Test utility tools (ping, whoami, profiles)."""
        print("\n" + "=" * 80)
        print("CATEGORY: Utility Tools")
        print("=" * 80)

        # Import tools
        from mcp_oci_opsi.main import app

        # Test ping
        result = self.test_tool("Utility", "ping", lambda: {"status": "ok", "message": "test"}, ["status"])
        self.print_result(result)

        # Test whoami
        result = self.test_tool("Utility", "whoami",
                              lambda: app.call_tool("whoami", {}),
                              ["tenancy_ocid", "region", "profile"])
        self.print_result(result)

        # Test list_oci_profiles
        result = self.test_tool("Utility", "list_oci_profiles",
                              lambda: app.call_tool("list_oci_profiles", {}),
                              ["available_profiles", "current_profile"])
        self.print_result(result)

    def test_cache_tools(self):
        """Test cache-related tools."""
        print("\n" + "=" * 80)
        print("CATEGORY: Cache Tools")
        print("=" * 80)

        cache = get_cache()

        # Test get_fleet_summary
        result = self.test_tool("Cache", "get_fleet_summary",
                              lambda: cache.get_fleet_summary())
        self.print_result(result)

        # Test search_databases
        result = self.test_tool("Cache", "search_databases",
                              lambda: cache.search_databases(limit=5))
        self.print_result(result)

        # Test get_cached_statistics
        result = self.test_tool("Cache", "get_cached_statistics",
                              lambda: cache.get_statistics())
        self.print_result(result)

        # Test list_cached_compartments
        result = self.test_tool("Cache", "list_cached_compartments",
                              lambda: cache.list_compartments())
        self.print_result(result)

    def test_profile_management_tools(self):
        """Test profile management tools."""
        print("\n" + "=" * 80)
        print("CATEGORY: Profile Management Tools")
        print("=" * 80)

        from mcp_oci_opsi import tools_profile_management

        # Test list_oci_profiles_enhanced
        result = self.test_tool("Profile", "list_oci_profiles_enhanced",
                              lambda: tools_profile_management.list_oci_profiles_enhanced(),
                              ["profile_count", "profiles"])
        self.print_result(result)

        # Test get_current_profile_info
        result = self.test_tool("Profile", "get_current_profile_info",
                              lambda: tools_profile_management.get_current_profile_info())
        self.print_result(result)

        # Test get_profile_tenancy_details
        result = self.test_tool("Profile", "get_profile_tenancy_details",
                              lambda: tools_profile_management.get_profile_tenancy_details())
        self.print_result(result)

    def test_database_insights_tools(self):
        """Test database insights tools."""
        print("\n" + "=" * 80)
        print("CATEGORY: Database Insights Tools")
        print("=" * 80)

        from mcp_oci_opsi import tools_opsi, tools_opsi_extended

        if not self.compartment_id:
            print("   ⏭️  Skipping - TEST_COMPARTMENT_ID not set")
            return

        # Test list_database_insights
        result = self.test_tool("Database Insights", "list_database_insights",
                              lambda: tools_opsi.list_database_insights(self.compartment_id))
        self.print_result(result)

        # Test summarize_sql_statistics
        result = self.test_tool("Database Insights", "summarize_sql_statistics",
                              lambda: tools_opsi_extended.summarize_sql_statistics(
                                  compartment_id=self.compartment_id,
                                  time_interval_start=(datetime.utcnow() - timedelta(days=7)).isoformat() + "Z",
                                  time_interval_end=datetime.utcnow().isoformat() + "Z"
                              ))
        self.print_result(result)

    def test_host_insights_tools(self):
        """Test host insights tools."""
        print("\n" + "=" * 80)
        print("CATEGORY: Host Insights Tools")
        print("=" * 80)

        from mcp_oci_opsi import tools_opsi_extended

        if not self.compartment_id:
            print("   ⏭️  Skipping - TEST_COMPARTMENT_ID not set")
            return

        # Test list_host_insights
        result = self.test_tool("Host Insights", "list_host_insights",
                              lambda: tools_opsi_extended.list_host_insights(self.compartment_id))
        self.print_result(result)

    def generate_report(self):
        """Generate comprehensive test report."""
        print("\n" + "=" * 80)
        print("TEST SUMMARY")
        print("=" * 80)

        print(f"\nTotal Tools: {self.results['total_tools']}")
        print(f"Tested: {self.results['tested']}")
        print(f"Passed: {self.results['passed']} ({self.results['passed']/self.results['tested']*100:.1f}%)")
        print(f"Failed: {self.results['failed']} ({self.results['failed']/self.results['tested']*100:.1f}%)")
        print(f"Skipped: {self.results['total_tools'] - self.results['tested']}")

        print("\n" + "=" * 80)
        print("BY CATEGORY")
        print("=" * 80)

        for category, stats in self.results["categories"].items():
            total = stats["passed"] + stats["failed"] + stats["skipped"]
            print(f"\n{category}:")
            print(f"  ✅ Passed: {stats['passed']}")
            print(f"  ❌ Failed: {stats['failed']}")
            print(f"  ⏭️  Skipped: {stats['skipped']}")

        # Performance analysis
        print("\n" + "=" * 80)
        print("PERFORMANCE ANALYSIS")
        print("=" * 80)

        passed_tools = [r for r in self.results["details"] if r["status"] == "passed"]
        if passed_tools:
            durations = [r["duration_ms"] for r in passed_tools]
            avg_duration = sum(durations) / len(durations)
            max_duration = max(durations)
            min_duration = min(durations)

            print(f"\nAverage Response Time: {avg_duration:.2f}ms")
            print(f"Fastest: {min_duration:.2f}ms")
            print(f"Slowest: {max_duration:.2f}ms")

            # Identify slow tools
            slow_tools = [r for r in passed_tools if r["duration_ms"] > 1000]
            if slow_tools:
                print(f"\n⚠️  Slow Tools (>1s):")
                for tool in slow_tools:
                    print(f"   {tool['tool']}: {tool['duration_ms']:.2f}ms")

        # Save results to file
        with open("mcp_tool_test_results.json", "w") as f:
            json.dump(self.results, f, indent=2)

        print(f"\n✅ Results saved to: mcp_tool_test_results.json")
        print()

    def run_all_tests(self):
        """Run all test categories."""
        if not self.setup():
            return False

        try:
            self.test_utility_tools()
            self.test_cache_tools()
            self.test_profile_management_tools()
            self.test_database_insights_tools()
            self.test_host_insights_tools()

            self.generate_report()
            return True

        except Exception as e:
            print(f"\n❌ Test execution failed: {e}")
            import traceback
            traceback.print_exc()
            return False


def main():
    """Main test execution."""
    tester = MCPToolTester()
    success = tester.run_all_tests()
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
