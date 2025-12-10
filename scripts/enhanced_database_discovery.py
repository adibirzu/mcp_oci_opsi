#!/usr/bin/env python3
"""
Enhanced Database Discovery Script

This script discovers all databases across compartments and checks their
monitoring status with OCI Observability tools. It uses configuration
variables and provides comprehensive reporting.

Features:
- Multi-profile support (from OCI config)
- Comprehensive monitoring status checks
- Configurable compartment discovery
- Detailed reporting with JSON output

Usage:
    python enhanced_database_discovery.py

Configuration:
    Set OCI_CLI_PROFILE in environment or use default
    Set COMPARTMENT_IDS in environment for specific compartments
    Set DISCOVERY_DEPTH for recursive scanning (default: full tree)
    Set OPSI_SELECTED_COMPARTMENTS as comma-separated names/OCIDs to restrict scanning (applies when profile is 'emdemo')
"""

import os
import json
from datetime import datetime
from typing import Dict, List, Optional
import argparse

import oci
from oci.config import from_file
from dotenv import load_dotenv
from mcp_oci_opsi.cache_enhanced import get_enhanced_cache

# Load environment variables
load_dotenv()


class EnhancedDatabaseDiscovery:
    """Enhanced database discovery with comprehensive monitoring checks."""

    def __init__(self, profile: Optional[str] = None, region: Optional[str] = None):
        """Initialize with OCI profile and region."""
        self.profile = profile or os.getenv('OCI_CLI_PROFILE', 'DEFAULT')
        self.region = region or os.getenv('OCI_REGION')

        # Load OCI configuration
        try:
            self.config = from_file(profile_name=self.profile)
            if self.region:
                self.config['region'] = self.region
            print(f"✅ Using profile: {self.profile}, Region: {self.config['region']}")
        except Exception as e:
            raise Exception(f"Failed to load OCI profile '{self.profile}': {e}")

        # Initialize OCI clients
        self.identity_client = oci.identity.IdentityClient(self.config)
        self.opsi_client = oci.opsi.OperationsInsightsClient(self.config)
        # Resolve DB Management client across SDK variants
        try:
            from oci.database_management import DatabaseManagementClient as _DBMClient
        except Exception:
            try:
                from oci.database_management import DbManagementClient as _DBMClient
            except Exception as e:
                raise ImportError(f"OCI database_management client not available: {e}")
        self.dbm_client = _DBMClient(self.config)

        # Prepare region-scoped clients for NEW_INSTALL bootstrap (use same scoping as emdemo script)
        self.new_install = os.getenv('NEW_INSTALL', '').lower() == 'true'
        if self.new_install:
            cfg_london = dict(self.config)
            cfg_london['region'] = 'uk-london-1'
            try:
                self.opsi_client_london = oci.opsi.OperationsInsightsClient(cfg_london)
            except Exception:
                self.opsi_client_london = self.opsi_client
            cfg_ashburn = dict(self.config)
            cfg_ashburn['region'] = 'us-ashburn-1'
            try:
                self.dbm_client_ashburn = _DBMClient(cfg_ashburn)
            except Exception:
                self.dbm_client_ashburn = self.dbm_client

        # Results storage
        self.results = {
            'timestamp': datetime.utcnow().isoformat(),
            'profile': self.profile,
            'region': self.config['region'],
            'tenancy_id': self.config['tenancy'],
            'compartments_discovered': [],
            'databases_found': [],
            'monitoring_summary': {},
            'statistics': {}
        }

        # Optional filter via env: OPSI_SELECTED_COMPARTMENTS (comma-separated names/OCIDs/paths)
        selected_env = os.getenv('OPSI_SELECTED_COMPARTMENTS', '')
        selected = set([s.strip() for s in selected_env.split(',') if s.strip()])
        # NEW_INSTALL bootstrap: if no filters provided and this is a fresh setup,
        # restrict to the standard emdemo targets so we don't scan the entire tenancy.
        if (not selected) and os.getenv('NEW_INSTALL', '').lower() == 'true':
            selected = {
                'OandM-Demo/dbmgmt',
                'OandM-Demo/OperationsInsights',
                'OandM-Demo/OperationsInsights/Exadatas',
            }
            print("   🚀 NEW_INSTALL detected: defaulting OPSI_SELECTED_COMPARTMENTS to emdemo targets")
        self.selected_compartments = selected

        # Enhanced cache for incremental writes
        try:
            self.enhanced_cache = get_enhanced_cache(self.profile)
            # Ensure cache is loaded (non-fatal if it doesn't exist yet)
            self.enhanced_cache.load()
        except Exception:
            self.enhanced_cache = None

        # Write interval (compartments), 0 means disable incremental save
        try:
            self.write_interval = int(os.getenv('DISCOVERY_WRITE_INTERVAL', '0'))
        except Exception:
            self.write_interval = 0
        self._save_counter = 0

        # Optional region list to iterate (overrides single region)
        self.region_list: List[str] = []

    def discover_compartments(self, root_compartment_ids: Optional[List[str]] = None) -> List[Dict]:
        """
        Discover all compartments recursively.

        Args:
            root_compartment_ids: Specific compartment IDs to start from.
                                If None, uses tenancy root.

        Returns:
            List of compartment dictionaries with hierarchy info
        """
        if not root_compartment_ids:
            root_compartment_ids = [self.config['tenancy']]

        print(f"🔍 Discovering compartments starting from: {root_compartment_ids}")

        all_compartments = []

        for root_id in root_compartment_ids:
            # Get compartment tree recursively
            compartments = oci.pagination.list_call_get_all_results(
                self.identity_client.list_compartments,
                compartment_id=root_id,
                compartment_id_in_subtree=True
            ).data

            # Add root compartment
            try:
                root_comp = self.identity_client.get_compartment(root_id).data
                compartments.insert(0, root_comp)
            except:
                pass

            # Process compartments
            for comp in compartments:
                if comp.lifecycle_state == 'ACTIVE':
                    # Build full path
                    path_parts = []
                    current = comp
                    while current:
                        path_parts.insert(0, current.name)
                        if current.compartment_id == self.config['tenancy']:
                            break
                        try:
                            current = self.identity_client.get_compartment(current.compartment_id).data
                        except:
                            break

                    comp_info = {
                        'id': comp.id,
                        'name': comp.name,
                        'description': getattr(comp, 'description', ''),
                        'path': '/'.join(path_parts),
                        'parent_id': getattr(comp, 'compartment_id', None),
                        'level': len(path_parts) - 1,
                        'databases': {
                            'operations_insights': {'count': 0, 'items': []},
                            'database_management': {'count': 0, 'items': []}
                        }
                    }
                    all_compartments.append(comp_info)

        self.results['compartments_discovered'] = all_compartments
        print(f"📁 Found {len(all_compartments)} active compartments")
        return all_compartments

    def _incremental_cache_flush(self, compartment: Dict, save_now: bool = False):
        """
        Update enhanced cache incrementally with the current compartment scan results.
        Saves to disk based on write_interval or if save_now is True.
        """
        if not self.enhanced_cache:
            return

        try:
            # Sync compartment metadata
            comp_id = compartment['id']
            comp_entry = {
                "id": comp_id,
                "name": compartment['name'],
                "description": compartment.get('description', ''),
                "parent_id": compartment.get('parent_id'),
                "lifecycle_state": "ACTIVE",
                "level": compartment.get('level', 0),
            }
            self.enhanced_cache.cache_data["compartments"][comp_id] = comp_entry

            # Sync databases discovered in this compartment
            # Ops Insights
            for db in compartment['databases'].get('operations_insights', {}).get('items', []):
                db_id = db.get('id')
                if not db_id:
                    continue
                self.enhanced_cache.cache_data["databases"][db_id] = {
                    "id": db_id,
                    "database_id": db.get("id"),
                    "database_name": db.get("name"),
                    "database_display_name": db.get("name"),
                    "database_type": db.get("type"),
                    "database_version": db.get("version"),
                    "entity_source": db.get("entity_source"),
                    "compartment_id": db.get("compartment_id"),
                    "compartment_name": db.get("compartment_path"),
                    "status": db.get("status"),
                    "lifecycle_state": "ACTIVE",
                    "time_created": None,
                }

            # DB Management
            for db in compartment['databases'].get('database_management', {}).get('items', []):
                db_key = f"dbm::{db.get('id') or db.get('name') or comp_id}"
                self.enhanced_cache.cache_data["databases"][db_key] = {
                    "id": db_key,
                    "database_id": db.get("id"),
                    "database_name": db.get("name"),
                    "database_display_name": db.get("name"),
                    "database_type": db.get("type"),
                    "database_version": None,
                    "entity_source": None,
                    "compartment_id": db.get("compartment_id"),
                    "compartment_name": db.get("compartment_path"),
                    "status": db.get("management_option") or "MANAGED",
                    "lifecycle_state": "ACTIVE",
                    "time_created": None,
                }

            # Recompute statistics occasionally
            try:
                self.enhanced_cache._calculate_enhanced_statistics()
            except Exception:
                pass

            # Save based on interval or force
            self._save_counter += 1
            if save_now or (self.write_interval and (self._save_counter % self.write_interval == 0)):
                self.enhanced_cache.save()
        except Exception:
            # Non-fatal, continue scanning
            pass

    def scan_databases_in_compartment(self, compartment: Dict) -> Dict:
        """Scan for databases in a specific compartment."""
        comp_id = compartment['id']
        comp_name = compartment['name']
        comp_path = compartment['path']

        print(f"🔎 Scanning {comp_path}")

        # Choose region-specific clients when NEW_INSTALL scaffold is used (aligns with emdemo script behavior)
        opsi_client = self.opsi_client
        dbm_client = self.dbm_client
        if os.getenv('NEW_INSTALL', '').lower() == 'true':
            if comp_path.startswith('OandM-Demo/OperationsInsights'):
                opsi_client = getattr(self, 'opsi_client_london', opsi_client)
            if comp_path.endswith('dbmgmt') or comp_path == 'OandM-Demo/dbmgmt' or comp_path.endswith('/dbmgmt'):
                dbm_client = getattr(self, 'dbm_client_ashburn', dbm_client)

        # Check Operations Insights
        try:
            db_insights = oci.pagination.list_call_get_all_results(
                opsi_client.list_database_insights,
                compartment_id=comp_id
            ).data

            compartment['databases']['operations_insights']['count'] = len(db_insights)
            for db in db_insights:
                db_info = {
                    'id': db.id,
                    'name': db.database_display_name or db.database_name,
                    'type': db.database_type,
                    'version': getattr(db, 'database_version', 'Unknown'),
                    'status': db.status,
                    'entity_source': getattr(db, 'entity_source', 'UNKNOWN'),
                    'compartment_id': comp_id,
                    'compartment_path': comp_path,
                    'monitoring_type': 'operations_insights',
                    'source': 'opsi'
                }
                compartment['databases']['operations_insights']['items'].append(db_info)
                self.results['databases_found'].append(db_info)

        except Exception as e:
            compartment['databases']['operations_insights']['error'] = str(e)
            print(f"   ⚠️  Ops Insights error: {str(e)[:100]}...")

        # Check Database Management
        try:
            managed_dbs = oci.pagination.list_call_get_all_results(
                dbm_client.list_managed_databases,
                compartment_id=comp_id
            ).data

            compartment['databases']['database_management']['count'] = len(managed_dbs)
            for db in managed_dbs:
                db_info = {
                    'id': db.id,
                    'name': db.name,
                    'type': db.database_type,
                    'subtype': db.database_sub_type,
                    'management_option': db.management_option,
                    'workload_type': getattr(db, 'workload_type', 'Unknown'),
                    'compartment_id': comp_id,
                    'compartment_path': comp_path,
                    'monitoring_type': 'database_management',
                    'source': 'dbmgmt'
                }
                compartment['databases']['database_management']['items'].append(db_info)
                self.results['databases_found'].append(db_info)

        except Exception as e:
            compartment['databases']['database_management']['error'] = str(e)
            print(f"   ⚠️  DB Management error: {str(e)[:100]}...")

        total_dbs = (
            compartment['databases']['operations_insights']['count'] +
            compartment['databases']['database_management']['count']
        )

        if total_dbs > 0:
            print(f"   ✅ Found {total_dbs} databases ({compartment['databases']['operations_insights']['count']} Ops Insights, {compartment['databases']['database_management']['count']} DB Mgmt)")

        return compartment

    def generate_monitoring_summary(self) -> Dict:
        """Generate comprehensive monitoring summary."""
        summary = {
            'total_databases': len(self.results['databases_found']),
            'by_monitoring_type': {},
            'by_compartment': {},
            'by_database_type': {},
            'by_entity_source': {},
            'compartments_with_databases': [],
            'unmonitored_databases': [],
            'monitoring_gaps': []
        }

        # Group by monitoring type
        for db in self.results['databases_found']:
            mon_type = db.get('monitoring_type', 'unknown')
            if mon_type not in summary['by_monitoring_type']:
                summary['by_monitoring_type'][mon_type] = []
            summary['by_monitoring_type'][mon_type].append(db)

        # Group by compartment
        for comp in self.results['compartments_discovered']:
            comp_path = comp['path']
            total_dbs = (
                comp['databases']['operations_insights']['count'] +
                comp['databases']['database_management']['count']
            )

            if total_dbs > 0:
                summary['compartments_with_databases'].append({
                    'path': comp_path,
                    'total_databases': total_dbs,
                    'operations_insights': comp['databases']['operations_insights']['count'],
                    'database_management': comp['databases']['database_management']['count']
                })

                summary['by_compartment'][comp_path] = total_dbs

        # Group by database type and entity source
        for db in self.results['databases_found']:
            # By database type
            db_type = db.get('type', 'Unknown')
            if db_type not in summary['by_database_type']:
                summary['by_database_type'][db_type] = []
            summary['by_database_type'][db_type].append(db)

            # By entity source (for Ops Insights)
            entity_source = db.get('entity_source', 'N/A')
            if entity_source != 'N/A':
                if entity_source not in summary['by_entity_source']:
                    summary['by_entity_source'][entity_source] = []
                summary['by_entity_source'][entity_source].append(db)

        # Identify monitoring gaps
        opsi_dbs = set()
        dbm_dbs = set()

        for db in self.results['databases_found']:
            db_name = db.get('name', '')
            if db.get('monitoring_type') == 'operations_insights':
                opsi_dbs.add(db_name)
            elif db.get('monitoring_type') == 'database_management':
                dbm_dbs.add(db_name)

        # Databases only in DB Management (not in Ops Insights)
        only_dbm = dbm_dbs - opsi_dbs
        if only_dbm:
            summary['monitoring_gaps'].append({
                'type': 'dbm_only',
                'description': 'Databases in Database Management but not Operations Insights',
                'databases': list(only_dbm),
                'recommendation': 'Consider enabling Operations Insights for full monitoring'
            })

        self.results['monitoring_summary'] = summary
        self.results['statistics'] = {
            'compartments_total': len(self.results['compartments_discovered']),
            'compartments_with_databases': len(summary['compartments_with_databases']),
            'databases_total': summary['total_databases'],
            'monitoring_types': list(summary['by_monitoring_type'].keys()),
            'database_types': list(summary['by_database_type'].keys()),
            'entity_sources': list(summary['by_entity_source'].keys())
        }

        return summary

    def run_discovery(self, root_compartment_ids: Optional[List[str]] = None) -> Dict:
        """Run complete database discovery with optional region/compartment filtering and incremental writes."""
        print("🚀 Starting Enhanced Database Discovery")
        print("=" * 60)

        # Discover compartments once (identity is global)
        compartments = self.discover_compartments(root_compartment_ids)

        # Base selection: OPSI_SELECTED_COMPARTMENTS via env (existing behavior for emdemo)
        compartments_to_scan = compartments

        # Apply explicit include filters if provided (names/paths/ocids)
        explicit_filters = getattr(self, 'explicit_compartment_filters', set())
        if explicit_filters:
            compartments_to_scan = [
                c for c in compartments
                if (c['id'] in explicit_filters)
                or (c['name'] in explicit_filters)
                or (c['path'] in explicit_filters)
            ]
            print(f"   📂 Filtered to {len(compartments_to_scan)} selected compartment(s) via explicit filters")

        # Maintain emdemo behavior if env filters exist and no explicit filters were passed
        if not explicit_filters and (self.profile.lower() == 'emdemo') and getattr(self, 'selected_compartments', None):
            compartments_to_scan = [
                c for c in compartments
                if (c['id'] in self.selected_compartments)
                or (c['name'] in self.selected_compartments)
                or (c['path'] in self.selected_compartments)
            ]
            print(f"   📂 Filtered to {len(compartments_to_scan)} selected compartment(s) via OPSI_SELECTED_COMPARTMENTS")

        print("\n🔎 Scanning for databases...")

        # Regions to iterate
        regions = self.region_list[:] if self.region_list else [self.config['region']]
        for r in regions:
            print(f"\n🌐 Region scope: {r}")
            # Re-scope clients for this region
            try:
                cfg_region = dict(self.config)
                cfg_region['region'] = r
                self.opsi_client = oci.opsi.OperationsInsightsClient(cfg_region)
                # Resolve DBM client variant again for region
                try:
                    from oci.database_management import DatabaseManagementClient as _DBMClient
                except Exception:
                    from oci.database_management import DbManagementClient as _DBMClient
                self.dbm_client = _DBMClient(cfg_region)
            except Exception as e:
                print(f"   ⚠️  Failed to set clients for region {r}: {e}")
                continue

            scanned = 0
            for compartment in compartments_to_scan:
                self.scan_databases_in_compartment(compartment)
                # Incremental write to enhanced cache
                self._incremental_cache_flush(compartment, save_now=False)
                scanned += 1

            # Force a save at end of region
            self._incremental_cache_flush({"id": "", "name": "", "databases": {"operations_insights": {"items": []}, "database_management": {"items": []}}}, save_now=True)
            print(f"   ✅ Completed region {r}, compartments scanned: {scanned}")

        # Generate summary
        print("\n📊 Generating monitoring summary...")
        summary = self.generate_monitoring_summary()

        # Print results
        self.print_results(summary)

        return self.results

    def print_results(self, summary: Dict):
        """Print formatted results."""
        print("\n🎯 DISCOVERY COMPLETE")
        print("=" * 60)

        print(f"📊 Total Databases Found: {summary['total_databases']}")
        print(f"📁 Compartments Scanned: {len(self.results['compartments_discovered'])}")
        print(f"🏢 Compartments with DBs: {len(summary['compartments_with_databases'])}")

        print("\n📈 By Monitoring Type:")
        for mon_type, dbs in summary['by_monitoring_type'].items():
            print(f"   {mon_type}: {len(dbs)} databases")

        print("\n🏗️  By Database Type:")
        for db_type, dbs in summary['by_database_type'].items():
            print(f"   {db_type}: {len(dbs)} databases")

        if summary['by_entity_source']:
            print("\n🔧 By Entity Source (Ops Insights):")
            for entity, dbs in summary['by_entity_source'].items():
                print(f"   {entity}: {len(dbs)} databases")

        print("\n📂 Compartments with Databases:")
        for comp in sorted(summary['compartments_with_databases'], key=lambda x: x['total_databases'], reverse=True):
            print(f"   {comp['path']}: {comp['total_databases']} DBs")
            print(f"      Ops Insights: {comp['operations_insights']}, DB Management: {comp['database_management']}")

        if summary['monitoring_gaps']:
            print("\n⚠️  Monitoring Gaps:")
            for gap in summary['monitoring_gaps']:
                print(f"   {gap['type'].upper()}: {gap['description']}")
                print(f"      {gap['recommendation']}")
                print(f"      Affected: {', '.join(gap['databases'][:3])}")
                if len(gap['databases']) > 3:
                    print(f"      ... and {len(gap['databases']) - 3} more")

    def save_results(self, filename: str = None):
        """Save results to JSON file (safe path by default, avoids repo exposure)."""
        # Safe output dir: DISCOVERY_OUTPUT_DIR or ~/.local/share/emdemo, fallback to /tmp
        output_dir = os.getenv('DISCOVERY_OUTPUT_DIR')
        if not output_dir:
            try:
                output_dir = os.path.join(os.path.expanduser('~'), '.local', 'share', 'emdemo')
            except Exception:
                output_dir = os.getenv('TMPDIR', '/tmp')
        try:
            os.makedirs(output_dir, exist_ok=True)
        except Exception:
            output_dir = os.getenv('TMPDIR', '/tmp')

        # Default filename if not provided
        if not filename:
            timestamp = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
            filename = f"database_discovery_{self.profile}_{timestamp}.json"

        # If filename is not absolute, redirect into safe dir
        if not os.path.isabs(filename):
            filename = os.path.join(output_dir, filename)

        with open(filename, 'w') as f:
            json.dump(self.results, f, indent=2, default=str)

        print(f"\n💾 Results saved to: {filename}")

        # Also persist updates into the MCP enhanced cache file so the agent/UI can read during/after scan
        try:
            if self.enhanced_cache:
                # Ensure latest stats are reflected and flush to the profile-scoped enhanced cache file
                try:
                    self.enhanced_cache._calculate_enhanced_statistics()
                except Exception:
                    pass
                if self.enhanced_cache.save():
                    print(f"🗂️ Enhanced cache updated: {self.enhanced_cache.cache_file}")
        except Exception:
            # Non-fatal if cache save fails
            pass

        return filename


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description='Enhanced OCI Database Discovery')
    parser.add_argument('--profile', help='OCI CLI profile name')
    parser.add_argument('--region', help='OCI region override')
    parser.add_argument('--regions', nargs='*', help='Regions list to iterate (e.g. eu-frankfurt-1 us-phoenix-1 uk-london-1)')
    parser.add_argument('--include-compartments', nargs='*', help='Filter compartments by name/path (any match)')
    parser.add_argument('--include-compartment-ocids', nargs='*', help='Filter compartments by OCID (any match)')
    parser.add_argument('--write-interval', type=int, default=0, help='Incremental write interval (compartments). 0 disables incremental saves.')
    parser.add_argument('--compartments', nargs='*', help='Root compartment OCIDs to scan')
    parser.add_argument('--output', help='Output JSON filename')

    args = parser.parse_args()

    try:
        # Initialize discovery
        discovery = EnhancedDatabaseDiscovery(
            profile=args.profile,
            region=args.region
        )

        # Configure region list if provided
        if args.regions:
            # Accept comma-separated forms too
            regions = []
            for item in args.regions:
                regions.extend([p.strip() for p in str(item).split(',') if p.strip()])
            discovery.region_list = regions

        # Filters: names/paths and ocids
        filters = set()
        if args.include_compartments:
            for item in args.include_compartments:
                filters.update([p.strip() for p in str(item).split(',') if p.strip()])
        if args.include_compartment_ocids:
            for item in args.include_compartment_ocids:
                filters.update([p.strip() for p in str(item).split(',') if p.strip()])
        discovery.explicit_compartment_filters = filters

        # Incremental write interval
        if args.write_interval is not None:
            discovery.write_interval = max(0, int(args.write_interval))

        # Run discovery
        results = discovery.run_discovery(args.compartments)

        # Save results
        output_file = discovery.save_results(args.output)

        print(f"\n✅ Discovery completed successfully!")
        print(f"📄 Full results available in: {output_file}")

    except Exception as e:
        print(f"❌ Discovery failed: {e}")
        exit(1)


if __name__ == '__main__':
    main()
