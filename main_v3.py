#!/usr/bin/env python3
"""
MCP OCI OPSI Server v3.0 - Enhanced Database Discovery

This is a simplified MCP server implementation that provides:
- Automatic cache building and skills loading on startup
- Multi-tenancy support with profile management
- Comprehensive database discovery and monitoring
- Enhanced DBA tools for Oracle Cloud Infrastructure

Since MCP libraries require Python 3.10+, this version provides
a command-line interface for database discovery operations.
"""

import os
import sys
import argparse
import logging
from typing import Optional

# Add parent directory to path to allow imports from mcp_oci_opsi package
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import oci
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
try:
    from mcp_oci_opsi.logging_config import configure_logging
except ImportError:
    # Fallback if run in a way where relative imports work or path is different
    from .logging_config import configure_logging

# Ensure logging configured if main_v3.py invoked directly
configure_logging()

# Import enhanced config and cache for initialization
from mcp_oci_opsi import config_enhanced
from mcp_oci_opsi import cache_enhanced
from mcp_oci_opsi import skills_loader
from mcp_oci_opsi.scripts import enhanced_database_discovery

logger = logging.getLogger(__name__)

def initialize_server():
    """
    Initialize the MCP server with cache building and skills loading.

    This function runs on server startup to:
    1. Build/update database cache for all available profiles
    2. Load and validate skills
    3. Ensure multi-tenancy setup is ready
    """
    print("\n🚀 Initializing MCP OCI OPSI Server...")
    logger.info("Initializing MCP OCI OPSI Server (v3)")

    # Load skills first
    print("📚 Loading DBA skills...")
    try:
        skills_loader_instance = skills_loader.get_skills_loader()
        skills = skills_loader_instance.list_skills()
        print(f"✅ Loaded {len(skills)} DBA skills")
        logger.info("Skills loaded", extra={"count": len(skills)})
    except Exception as e:
        print(f"⚠️  Skills loading error: {e}")
        logger.exception("Skills loading error", exc_info=e)

    # Build cache for all available profiles
    print("\n💾 Building database cache for all profiles...")
    profiles = config_enhanced.list_all_profiles_with_details()

    for profile_info in profiles:
        if not profile_info.get('valid', False):
            print(f"⚠️  Skipping invalid profile: {profile_info['profile_name']}")
            continue

        profile_name = profile_info['profile_name']
        region = profile_info.get('region', 'us-ashburn-1')  # Default region

        print(f"🔄 Building cache for profile: {profile_name} (region: {region})")

        try:
            # Get tenancy OCID for this profile
            config = config_enhanced.get_oci_config(profile=profile_name)
            tenancy_ocid = config['tenancy']

            # Initialize cache for this profile
            cache = cache_enhanced.get_enhanced_cache(profile=profile_name)

            # Optional region override via env to support targeted discovery without hardcoding
            region_override = os.getenv("OPSI_INIT_REGION_OVERRIDE")
            if region_override:
                os.environ["MCP_OPSI_REGION_OVERRIDE"] = region_override
                print(f"   🌍 Using region override for OPSI: {region_override}")

            # Check if cache needs updating (older than 24 hours)
            import time
            cache_age_hours = 0
            if cache.cache_data.get('metadata', {}).get('last_updated'):
                from datetime import datetime, timezone
                cache_time = datetime.fromisoformat(cache.cache_data['metadata']['last_updated'].replace('Z', '+00:00')).astimezone(timezone.utc)
                now_utc = datetime.now(timezone.utc)
                cache_age_hours = (now_utc - cache_time).total_seconds() / 3600

            init_mode = os.getenv("OPSI_INIT_MODE", "light").lower()  # none | light | full
            skip_build = init_mode in ("none", "light")
            if skip_build:
                print(f"   ⚙️  OPSI_INIT_MODE={init_mode} -> skipping cache build for fast startup")
            if (not skip_build) and (cache_age_hours > 24 or not cache.cache_data.get('databases')):
                print(f"   📊 Building fresh cache for {profile_name}...")
                # Run cache building synchronously but with timeout to avoid blocking
                import signal
                from contextlib import contextmanager

                @contextmanager
                def timeout_context(seconds):
                    def timeout_handler(signum, frame):
                        raise TimeoutError(f"Operation timed out after {seconds} seconds")

                    signal.signal(signal.SIGALRM, timeout_handler)
                    signal.alarm(seconds)
                    try:
                        yield
                    finally:
                        signal.alarm(0)

                try:
                    with timeout_context(300):  # 5 minute timeout
                        result = cache.build_enhanced_cache([tenancy_ocid])
                    print(f"   ✅ Cache built: {result['statistics']['total_databases']} databases, {result['statistics']['total_hosts']} hosts")
                except TimeoutError:
                    print(f"   ⚠️  Cache build timed out for {profile_name}, continuing...")
                except Exception as cache_error:
                    print(f"   ❌ Cache build failed for {profile_name}: {cache_error}")
                finally:
                    # Clear any region override after attempting the build
                    if "region_override" in locals() and region_override:
                        os.environ.pop("MCP_OPSI_REGION_OVERRIDE", None)
            else:
                print(f"   ✅ Using cached data (age: {cache_age_hours:.1f} hours)")
                # Clear any region override if we didn't rebuild
                if "region_override" in locals() and region_override:
                    os.environ.pop("MCP_OPSI_REGION_OVERRIDE", None)

        except Exception as e:
            print(f"   ❌ Cache build failed for {profile_name}: {e}")
            logger.exception("Cache build failed", exc_info=e, extra={"profile": profile_name})

    print("🎯 MCP OCI OPSI Server initialization complete!\n")


def run_discovery(profile: Optional[str] = None, region: Optional[str] = None,
                 compartments: Optional[list] = None, output: Optional[str] = None):
    """Run enhanced database discovery."""
    try:
        discovery = enhanced_database_discovery.EnhancedDatabaseDiscovery(profile=profile, region=region)
        results = discovery.run_discovery(compartments)
        discovery.save_results(output)
        return True
    except Exception as e:
        print(f"❌ Discovery failed: {e}")
        return False


def show_fleet_summary():
    """Show instant fleet summary from cache."""
    try:
        from mcp_oci_opsi.tools.tools_cache import get_fleet_summary
        summary = get_fleet_summary()
        print("\n📊 Fleet Summary:")
        print(f"   Databases: {summary.get('total_databases', 0)}")
        print(f"   Hosts: {summary.get('total_hosts', 0)}")
        print(f"   Compartments: {summary.get('total_compartments', 0)}")
        return True
    except Exception as e:
        print(f"❌ Failed to get fleet summary: {e}")
        return False


def show_available_skills():
    """Show available DBA skills."""
    try:
        from mcp_oci_opsi.tools.tools_skills import list_available_skills
        skills = list_available_skills()
        print(f"\n🎯 Available DBA Skills: {skills.get('count', 0)}")
        for skill in skills.get('skills', []):
            print(f"   • {skill['name']}: {skill['description']}")
        return True
    except Exception as e:
        print(f"❌ Failed to load skills: {e}")
        return False


def run_london_discovery(profile: Optional[str] = None, output: Optional[str] = None):
    """Run discovery specifically for London (UK South) region databases."""
    try:
        print("\n🏛️  London Database Discovery (UK South Region)")
        print("=" * 55)

        # Use emdemo profile by default for London discovery
        profile = profile or 'emdemo'

        # Initialize with London region
        discovery = enhanced_database_discovery.EnhancedDatabaseDiscovery(
            profile=profile,
            region='uk-london-1'  # UK South region
        )

        # Focus on OperationsInsights compartments for OPSI
        # These are the compartments mentioned by user for OPSI in London
        london_compartments = [
            'OandM-Demo/OperationsInsights',
            'OandM-Demo/OperationsInsights/Exadatas'
        ]

        print(f"📍 Target Region: UK South (uk-london-1)")
        print(f"👤 Profile: {profile}")
        print(f"📁 Focus Compartments: {', '.join(london_compartments)}")
        print()

        # Run discovery
        results = discovery.run_discovery(london_compartments)

        if results:
            # Enhanced London-specific summary
            print("\n🏛️  London OPSI Discovery Results")
            print("=" * 40)

            opsi_databases = []
            exadata_databases = []
            total_databases = 0

            for compartment_result in results.get('compartments_checked', []):
                comp_name = compartment_result.get('name', '')
                ops_insights = compartment_result.get('operations_insights', {})
                db_mgmt = compartment_result.get('database_management', {})

                opsi_count = ops_insights.get('count', 0)
                dbm_count = db_mgmt.get('count', 0)

                if 'Exadata' in comp_name:
                    exadata_databases.extend(ops_insights.get('databases', []))
                else:
                    opsi_databases.extend(ops_insights.get('databases', []))

                total_databases += opsi_count + dbm_count

                print(f"📁 {comp_name}")
                print(f"   📊 Operations Insights: {opsi_count} databases")
                print(f"   🛠️  Database Management: {dbm_count} databases")

                # Show database details
                if ops_insights.get('databases'):
                    print("   📋 Databases:")
                    for db in ops_insights['databases']:
                        print(f"      • {db.get('name', 'Unknown')} ({db.get('type', 'Unknown')})")

            print(f"\n🎯 London Discovery Summary")
            print(f"   🏛️  Region: UK South (London)")
            print(f"   📊 Operations Insights DBs: {len(opsi_databases)}")
            print(f"   💎 Exadata DBs: {len(exadata_databases)}")
            print(f"   📈 Total Databases: {total_databases}")

            # Top 15 databases in London (sorted by name for consistency)
            all_london_dbs = opsi_databases + exadata_databases
            if all_london_dbs:
                print(f"\n🔝 Top {min(15, len(all_london_dbs))} Databases in London:")
                sorted_dbs = sorted(all_london_dbs, key=lambda x: x.get('name', ''))
                for i, db in enumerate(sorted_dbs[:15], 1):
                    db_type = "💎" if any(exa_db['id'] == db['id'] for exa_db in exadata_databases) else "📊"
                    print(f"   {i:2d}. {db_type} {db.get('name', 'Unknown')} ({db.get('type', 'Unknown')})")

        # Save results
        discovery.save_results(output or 'london_discovery_results.json')
        print(f"\n💾 Results saved to: {output or 'london_discovery_results.json'}")

        return True

    except Exception as e:
        print(f"❌ London discovery failed: {e}")
        return False


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description='MCP OCI OPSI Server v3.0 - Tenancy Agnostic Database Discovery')
    parser.add_argument('--init-only', action='store_true',
                       help='Only run initialization, do not start server')
    parser.add_argument('--profile', help='OCI profile to use (default: DEFAULT)')
    parser.add_argument('--region', help='OCI region override')
    parser.add_argument('--compartments', nargs='*',
                       help='Specific compartment OCIDs to scan (tenancy agnostic)')
    parser.add_argument('--output', help='Output file for discovery results')
    parser.add_argument('--command', choices=['discover', 'fleet', 'skills', 'london'],
                       help='Run specific command instead of full server')
    parser.add_argument('--london-discovery', action='store_true',
                       help='Run discovery specifically for London (UK South) region')

    args = parser.parse_args()

    # Run initialization
    initialize_server()

    if args.init_only:
        print("✅ Initialization complete. Exiting.")
        return

    if args.command == 'discover':
        success = run_discovery(args.profile, args.region, args.compartments, args.output)
        sys.exit(0 if success else 1)

    elif args.command == 'fleet':
        success = show_fleet_summary()
        sys.exit(0 if success else 1)

    elif args.command == 'skills':
        success = show_available_skills()
        sys.exit(0 if success else 1)

    elif args.command == 'london' or args.london_discovery:
        success = run_london_discovery(args.profile, args.output)
        sys.exit(0 if success else 1)

    # Default: Show help
    print("\n🎯 MCP OCI OPSI Server v3.0 - Tenancy Agnostic Database Discovery")
    print("=" * 70)
    print("Available commands:")
    print("  python main_v3.py --command discover    # Run database discovery")
    print("  python main_v3.py --command fleet       # Show fleet summary")
    print("  python main_v3.py --command skills      # Show available skills")
    print("  python main_v3.py --command london      # Discover DBs in London (UK South)")
    print("  python main_v3.py --init-only           # Only run initialization")
    print("\nTenancy Agnostic Features:")
    print("  • Multi-tenancy support with automatic profile discovery")
    print("  • User-definable compartments for targeted database scanning")
    print("  • Region-specific discovery (e.g., London for OPSI)")
    print("  • Comprehensive database monitoring checks")
    print("  • Automatic cache building on startup")
    print("  • Skills-based DBA guidance")
    print("\nExamples:")
    print("  # Discover databases in specific compartments")
    print("  python main_v3.py --command discover --compartments ocid1.compartment.oc1..example")
    print("  # Run London discovery for OPSI databases")
    print("  python main_v3.py --command london --profile emdemo")


if __name__ == "__main__":
    main()
