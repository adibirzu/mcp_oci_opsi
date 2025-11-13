#!/usr/bin/env python3
"""Build initial cache for your compartments.

This script builds a local cache of database and host information from OCI Operations Insights.
The cache enables instant responses (<50ms) with zero API calls for inventory queries.

Configuration:
    Set the CACHE_COMPARTMENT_IDS environment variable with comma-separated compartment OCIDs:
    export CACHE_COMPARTMENT_IDS="ocid1.compartment...,ocid1.compartment..."

    Or add to your .env file:
    CACHE_COMPARTMENT_IDS=ocid1.compartment...,ocid1.compartment...

Example:
    $ export CACHE_COMPARTMENT_IDS="ocid1.compartment.oc1..aaa...,ocid1.compartment.oc1..bbb..."
    $ python3 build_cache.py
"""

import os
import sys
from dotenv import load_dotenv
from mcp_oci_opsi.cache import get_cache

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


def main():
    """Build cache for all configured compartments."""
    try:
        compartments = get_compartment_ids()
    except ValueError as e:
        print(f"❌ Configuration Error: {e}", file=sys.stderr)
        return 1

    print("🔄 Building cache for your compartments...")
    print(f"   Scanning {len(compartments)} root compartments")
    print()

    cache = get_cache()

    try:
        result = cache.build_cache(compartments)

        print("✅ Cache built successfully!")
        print()
        print(f"📊 Statistics:")
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
        return 1


if __name__ == "__main__":
    sys.exit(main())
