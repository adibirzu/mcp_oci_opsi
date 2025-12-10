#!/usr/bin/env python3
"""Build enhanced cache with comprehensive tenancy and database metadata.

This script builds a comprehensive cache that includes:
- Tenancy information (name, home region)
- All subscribed regions
- Availability domains
- Full compartment hierarchy
- Database insights with extended metadata
- Host insights
- Comprehensive statistics

AUTO-DISCOVERY: Automatically discovers all compartments in your tenancy.
No manual configuration required!

Usage:
    # Use default OCI profile (auto-discovers all compartments)
    $ python3 build_enhanced_cache.py

    # Use specific OCI profile
    $ python3 build_enhanced_cache.py --profile production

    # Scan specific compartment only (optional)
    $ python3 build_enhanced_cache.py --compartment ocid1.compartment.oc1..example...

Example:
    $ python3 build_enhanced_cache.py
    $ python3 build_enhanced_cache.py --profile emdemo
"""

import argparse
import os
import sys
from pathlib import Path

# Add the package to path
sys.path.insert(0, str(Path(__file__).parent))

from mcp_oci_opsi.cache_enhanced import get_enhanced_cache
from mcp_oci_opsi.config import get_oci_config
import oci


def auto_discover_compartments(profile=None):
    """
    Auto-discover all compartments in the tenancy.

    Args:
        profile: Optional OCI profile name

    Returns:
        List of compartment OCIDs
    """
    if profile:
        os.environ["OCI_CLI_PROFILE"] = profile

    config = get_oci_config()
    identity_client = oci.identity.IdentityClient(config)

    print("🔍 Auto-discovering compartments in tenancy...")
    print()

    # Get tenancy root compartment
    tenancy_id = config.get("tenancy")
    compartment_ids = [tenancy_id]

    try:
        # Get tenancy info
        tenancy = identity_client.get_tenancy(tenancy_id).data
        print(f"   Tenancy: {tenancy.name}")
        print(f"   Home Region: {tenancy.home_region_key}")
        print()

        # Get all compartments in tenancy (recursive)
        print("   Scanning compartments...")

        # Use pagination to get all compartments
        all_compartments = []
        page = None

        while True:
            response = identity_client.list_compartments(
                compartment_id=tenancy_id,
                compartment_id_in_subtree=True,
                page=page
            )

            all_compartments.extend([c for c in response.data if c.lifecycle_state == "ACTIVE"])

            if not response.has_next_page:
                break
            page = response.next_page

        for comp in all_compartments:
            compartment_ids.append(comp.id)
            print(f"   ✓ {comp.name}")

        print()
        print(f"   Found {len(compartment_ids)} compartments (including tenancy root)")
        print()

    except Exception as e:
        print(f"   ⚠️  Error discovering compartments: {e}")
        print(f"   Will use tenancy root only: {tenancy_id}")
        print()

    return compartment_ids


def main():
    """Main cache build execution."""
    parser = argparse.ArgumentParser(
        description="Build enhanced cache with auto-discovery of compartments"
    )
    parser.add_argument(
        "--profile",
        type=str,
        help="OCI CLI profile to use (default: DEFAULT)"
    )
    parser.add_argument(
        "--compartment",
        type=str,
        help="Specific compartment OCID to scan (default: auto-discover all)"
    )

    args = parser.parse_args()

    print("=" * 80)
    print("MCP OCI OPSI - Enhanced Cache Builder")
    print("=" * 80)
    print()

    # Set profile if specified
    if args.profile:
        os.environ["OCI_CLI_PROFILE"] = args.profile
        print(f"📝 Using OCI profile: {args.profile}")
        print()

    # Get compartments to scan
    if args.compartment:
        print(f"📦 Scanning specific compartment: {args.compartment}")
        compartment_ids = [args.compartment]
    else:
        compartment_ids = auto_discover_compartments(args.profile)

    # Get cache instance
    cache = get_enhanced_cache()

    # Build cache
    try:
        result = cache.build_enhanced_cache(compartment_ids)

        # Display results
        print("=" * 80)
        print("BUILD RESULTS")
        print("=" * 80)
        print()
        print(f"✅ Cache built successfully")
        print(f"✅ Last updated: {result['last_updated']}")
        print(f"✅ Build duration: {result['build_duration_seconds']:.2f}s")
        print()
        print("Statistics:")
        stats = result['statistics']
        print(f"  Total Databases: {stats['total_databases']}")
        print(f"  Total Hosts: {stats['total_hosts']}")
        print(f"  Total Compartments: {stats['total_compartments']}")
        print(f"  Total Regions: {stats['total_regions']}")
        print()

        if stats.get('databases_by_type'):
            print("Databases by Type:")
            for db_type, count in stats['databases_by_type'].items():
                print(f"  {db_type}: {count}")
            print()

        if stats.get('databases_by_entity_source'):
            print("Databases by Entity Source:")
            for source, count in stats['databases_by_entity_source'].items():
                print(f"  {source}: {count}")
            print()

        # Token savings analysis
        print("=" * 80)
        print("TOKEN SAVINGS ANALYSIS")
        print("=" * 80)
        print()
        print("The enhanced cache stores static data that would otherwise require")
        print("multiple API calls and consume thousands of tokens:")
        print()
        print("  ✅ Tenancy Info: Saved ~500 tokens per query")
        print("  ✅ Region List: Saved ~200 tokens per query")
        print("  ✅ Compartments: Saved ~100 tokens per compartment")
        print(f"  ✅ Database Metadata: Saved ~200 tokens × {stats['total_databases']} databases")
        print()

        if stats['total_databases'] > 0:
            estimated_savings = (500 + 200 + (100 * stats['total_compartments']) +
                               (200 * stats['total_databases']))
            print(f"  💰 Estimated token savings per full query: ~{estimated_savings:,} tokens")
            print()

        print("=" * 80)
        print("NEXT STEPS")
        print("=" * 80)
        print()
        print("1. The cache is ready to use with MCP tools")
        print("2. Cache file: ~/.mcp_oci_opsi_cache_enhanced.json")
        print("3. Use get_fleet_summary(), search_databases(), etc. for instant responses")
        print("4. Refresh cache periodically (recommended: weekly)")
        print()
        print("✅ Enhanced cache build complete!")
        print()

    except Exception as e:
        print(f"❌ Cache build failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
