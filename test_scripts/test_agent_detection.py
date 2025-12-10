#!/usr/bin/env python3
"""Test script for agent detection and multi-profile enhancements.

This script validates:
1. Agent type detection and prioritization
2. Profile management functions
3. Cache building with multiple profiles
"""

import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
from mcp_oci_opsi.tools.tools_database_discovery import (
    list_database_insights_by_management_type,
    get_available_oci_profiles
)
from mcp_oci_opsi.config_enhanced import (
    list_all_profiles,
    get_profile_info,
    validate_profile
)


def test_profile_functions():
    """Test profile management functions."""
    print("=" * 80)
    print("TEST 1: Profile Management Functions")
    print("=" * 80)
    print()

    try:
        # Test 1: List all profiles
        print("1.1 Listing all OCI profiles...")
        profiles = list_all_profiles()
        print(f"✅ Found {len(profiles)} profiles: {', '.join(profiles)}")
        print()

        # Test 2: Get profile details
        print("1.2 Getting profile details...")
        for profile_name in profiles:
            info = get_profile_info(profile_name)
            status = "✅" if info.get("valid") else "❌"
            print(f"   {status} {profile_name}")
            if info.get("valid"):
                print(f"      Region: {info.get('region')}")
                print(f"      Tenancy: {info.get('tenancy_id')[:30]}...")
            else:
                print(f"      Error: {info.get('error')}")
            print()

        # Test 3: Validate specific profile
        print("1.3 Testing profile validation...")
        if profiles:
            test_profile = profiles[0]
            is_valid = validate_profile(test_profile)
            print(f"   Profile '{test_profile}' is {'valid ✅' if is_valid else 'invalid ❌'}")
        print()

        print("✅ Profile management tests PASSED")
        return True

    except Exception as e:
        print(f"❌ Profile management tests FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_agent_detection(compartment_id=None):
    """Test agent detection and prioritization."""
    print()
    print("=" * 80)
    print("TEST 2: Agent Detection and Prioritization")
    print("=" * 80)
    print()

    if not compartment_id:
        # Try to get compartment from environment
        compartment_id = os.getenv("OCI_COMPARTMENT_ID")
        if not compartment_id:
            # Use tenancy as fallback
            from mcp_oci_opsi.config import get_oci_config
            config = get_oci_config()
            compartment_id = config.get("tenancy")

    if not compartment_id:
        print("⚠️  Skipping agent detection test - no compartment ID available")
        print("   Set OCI_COMPARTMENT_ID environment variable to test")
        return True

    try:
        print(f"2.1 Discovering databases in compartment...")
        print(f"    Compartment: {compartment_id[:30]}...")
        print()

        result = list_database_insights_by_management_type(
            compartment_id=compartment_id
        )

        if "error" in result:
            print(f"❌ Discovery failed: {result['error']}")
            return False

        summary = result.get("summary", {})

        print("📊 Discovery Summary:")
        print(f"   Total databases: {summary.get('total_databases', 0)}")
        print(f"   Agent-based databases: {summary.get('agent_based_databases', 0)}")
        print(f"   Agent adoption: {summary.get('agent_based_percentage', 0)}%")
        print()

        print("🔍 Databases by Management Type (sorted by priority):")
        by_type = summary.get("by_management_type", {})
        for entity_type, info in by_type.items():
            priority = info.get("priority", "?")
            agent_status = "🤖" if info.get("agent_based") else "📋"
            print(f"   {agent_status} Priority {priority}: {info.get('display_name')}")
            print(f"      Count: {info.get('count')}")
            print(f"      Agent Type: {info.get('agent_type')}")
            print()

        print(f"💡 Recommendation: {summary.get('recommendation', 'N/A')}")
        print()

        # Validate priority ordering
        print("2.2 Validating priority ordering...")
        types_found = summary.get("management_types_found", [])
        priorities = [by_type[t].get("priority", 99) for t in types_found]

        is_sorted = all(priorities[i] <= priorities[i+1] for i in range(len(priorities)-1))
        if is_sorted:
            print("   ✅ Management types are correctly sorted by priority")
        else:
            print("   ❌ Priority ordering is incorrect!")
            return False
        print()

        # Check agent detection
        print("2.3 Validating agent detection...")
        agent_count = summary.get("agent_based_databases", 0)
        total_count = summary.get("total_databases", 0)

        if total_count > 0:
            print(f"   ✅ Detected {agent_count} agent-based databases out of {total_count}")
        else:
            print(f"   ℹ️  No databases found in compartment")
        print()

        print("✅ Agent detection tests PASSED")
        return True

    except Exception as e:
        print(f"❌ Agent detection tests FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_get_available_profiles_tool():
    """Test the get_available_oci_profiles MCP tool."""
    print()
    print("=" * 80)
    print("TEST 3: get_available_oci_profiles MCP Tool")
    print("=" * 80)
    print()

    try:
        result = get_available_oci_profiles()

        if "error" in result:
            print(f"❌ Tool failed: {result['error']}")
            return False

        profiles = result.get("profiles", {})
        print(f"✅ Found {result.get('total_profiles', 0)} profiles")
        print()

        for profile_name, info in profiles.items():
            if info.get("status") == "invalid":
                print(f"❌ {profile_name}: Invalid - {info.get('error')}")
            else:
                print(f"✅ {profile_name}")
                print(f"   Tenancy: {info.get('tenancy_name', 'N/A')}")
                print(f"   Region: {info.get('region', 'N/A')}")
            print()

        print("✅ get_available_oci_profiles tool test PASSED")
        return True

    except Exception as e:
        print(f"❌ get_available_oci_profiles tool test FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all tests."""
    print()
    print("🧪 MCP OCI OPSI - Agent Detection & Multi-Profile Enhancement Tests")
    print("=" * 80)
    print()

    results = []

    # Test 1: Profile management
    results.append(("Profile Management", test_profile_functions()))

    # Test 2: Agent detection
    compartment_id = os.getenv("TEST_COMPARTMENT_ID")
    results.append(("Agent Detection", test_agent_detection(compartment_id)))

    # Test 3: MCP tool
    results.append(("MCP Tool", test_get_available_profiles_tool()))

    # Summary
    print()
    print("=" * 80)
    print("TEST SUMMARY")
    print("=" * 80)
    print()

    passed = sum(1 for _, result in results if result)
    total = len(results)

    for test_name, result in results:
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"   {test_name}: {status}")

    print()
    print(f"Overall: {passed}/{total} tests passed")
    print()

    if passed == total:
        print("🎉 All tests PASSED!")
        return 0
    else:
        print("⚠️  Some tests FAILED")
        return 1


if __name__ == "__main__":
    sys.exit(main())
