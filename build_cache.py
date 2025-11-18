#!/usr/bin/env python3
"""Build initial cache for your compartments.

This script builds a local cache of database and host information from OCI Operations Insights.
The cache enables instant responses (<50ms) with zero API calls for inventory queries.

Configuration:
    Set the CACHE_COMPARTMENT_IDS environment variable with comma-separated compartment OCIDs:
    export CACHE_COMPARTMENT_IDS="ocid1.compartment...,ocid1.compartment..."

    Or add to your .env file:
    CACHE_COMPARTMENT_IDS=ocid1.compartment...,ocid1.compartment...

Usage:
    # Use default OCI profile
    $ python3 build_cache.py

    # Use specific OCI profile
    $ python3 build_cache.py --profile production

    # Interactive profile selection
    $ python3 build_cache.py --select-profile

Example:
    $ export CACHE_COMPARTMENT_IDS="ocid1.compartment.oc1..aaa...,ocid1.compartment.oc1..bbb..."
    $ python3 build_cache.py --profile tenancy1
"""

import os
import sys
import argparse
from dotenv import load_dotenv
from mcp_oci_opsi.cache import get_cache
from mcp_oci_opsi.config_enhanced import list_all_profiles, get_profile_info

# Load environment variables from .env file
load_dotenv()

def get_compartment_ids():
    """Get compartment IDs from environment variable.

    Returns:
        List of compartment OCIDs to cache

    Raises:
        ValueError if CACHE_COMPARTMENT_IDS is not set
    """
    compartments_str = os.getenv("CACHE_COMPARTMENT_IDS", "")

    if not compartments_str:
        raise ValueError(
            "CACHE_COMPARTMENT_IDS environment variable not set.\n"
            "\n"
            "Please set it with your compartment OCIDs:\n"
            "  export CACHE_COMPARTMENT_IDS=\"ocid1.compartment...,ocid1.compartment...\"\n"
            "\n"
            "Or add to your .env file:\n"
            "  CACHE_COMPARTMENT_IDS=ocid1.compartment...,ocid1.compartment...\n"
        )

    # Split by comma and strip whitespace
    compartments = [c.strip() for c in compartments_str.split(",") if c.strip()]

    if not compartments:
        raise ValueError("No valid compartment OCIDs found in CACHE_COMPARTMENT_IDS")

    return compartments


def select_profile_interactive():
    """Interactively select an OCI profile from available profiles."""
    try:
        profiles = list_all_profiles()

        if not profiles:
            print("❌ No OCI profiles found in ~/.oci/config", file=sys.stderr)
            return None

        if len(profiles) == 1:
            print(f"📝 Only one profile found: {profiles[0]}")
            return profiles[0]

        print("📋 Available OCI Profiles:")
        print()

        # Get details for each profile
        valid_profiles = []
        for idx, profile_name in enumerate(profiles, 1):
            info = get_profile_info(profile_name)
            status = "✅" if info.get("valid") else "❌"
            region = info.get("region", "N/A")
            tenancy = info.get("tenancy_id", "N/A")
            tenancy_short = tenancy[:30] + "..." if len(tenancy) > 30 else tenancy

            print(f"  {idx}. {status} {profile_name}")
            print(f"     Region: {region}")
            print(f"     Tenancy: {tenancy_short}")

            if info.get("valid"):
                valid_profiles.append(profile_name)
            else:
                print(f"     ⚠️  Error: {info.get('error', 'Invalid')}")
            print()

        if not valid_profiles:
            print("❌ No valid profiles found", file=sys.stderr)
            return None

        while True:
            try:
                choice = input(f"Select profile (1-{len(profiles)}): ").strip()
                idx = int(choice) - 1

                if 0 <= idx < len(profiles):
                    selected = profiles[idx]
                    info = get_profile_info(selected)

                    if info.get("valid"):
                        print(f"✅ Selected: {selected}")
                        return selected
                    else:
                        print(f"❌ Profile '{selected}' is invalid: {info.get('error')}")
                        print("Please select a different profile.")
                else:
                    print(f"❌ Invalid choice. Please enter a number between 1 and {len(profiles)}")
            except (ValueError, KeyboardInterrupt):
                print("\n❌ Profile selection cancelled", file=sys.stderr)
                return None

    except Exception as e:
        print(f"❌ Error loading profiles: {e}", file=sys.stderr)
        return None


def main():
    """Build cache for all configured compartments."""
    # Parse command line arguments
    parser = argparse.ArgumentParser(
        description="Build OCI Operations Insights cache with multi-profile support"
    )
    parser.add_argument(
        "--profile",
        type=str,
        help="OCI CLI profile name to use (from ~/.oci/config)"
    )
    parser.add_argument(
        "--select-profile",
        action="store_true",
        help="Interactively select OCI profile from available profiles"
    )

    args = parser.parse_args()

    # Determine which profile to use
    profile = None
    if args.select_profile:
        profile = select_profile_interactive()
        if profile is None:
            return 1
    elif args.profile:
        # Validate the specified profile
        info = get_profile_info(args.profile)
        if not info.get("valid"):
            print(f"❌ Profile '{args.profile}' is invalid: {info.get('error')}", file=sys.stderr)
            return 1
        profile = args.profile
        print(f"📝 Using profile: {profile}")
        print(f"   Region: {info.get('region')}")
        print()

    try:
        compartments = get_compartment_ids()
    except ValueError as e:
        print(f"❌ Configuration Error: {e}", file=sys.stderr)
        return 1

    print("🔄 Building cache for your compartments...")
    print(f"   Scanning {len(compartments)} root compartments")
    if profile:
        print(f"   Using OCI profile: {profile}")
    print()

    cache = get_cache()

    try:
        if profile:
            result = cache.build_cache_with_profile(compartments, profile=profile)
        else:
            result = cache.build_cache(compartments)

        print("✅ Cache built successfully!")
        print()
        print(f"📊 Statistics:")
        if result.get("tenancy_name"):
            print(f"   Tenancy: {result['tenancy_name']}")
        if result.get("profile_used"):
            print(f"   Profile: {result['profile_used']}")
        if result.get("region"):
            print(f"   Region: {result['region']}")
        print(f"   Compartments scanned: {result['compartments_scanned']}")
        print(f"   Total databases: {result['statistics']['total_databases']}")
        print(f"   Total hosts: {result['statistics']['total_hosts']}")
        print()
        print(f"📁 Databases by compartment:")
        for comp_name, count in result['statistics']['databases_by_compartment'].items():
            print(f"   {comp_name}: {count} databases")
        print()
        print(f"🗄️  Databases by type:")
        for db_type, count in result['statistics']['databases_by_type'].items():
            print(f"   {db_type}: {count}")
        print()
        print(f"💾 Cache saved to: {cache.cache_file}")
        print(f"⏰ Last updated: {result['last_updated']}")
        print()
        print("🚀 Cache ready! Use fast cache tools for instant responses.")

        return 0

    except Exception as e:
        print(f"❌ Error building cache: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
