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
"""

import os
import json
from datetime import datetime
from typing import Dict, List, Optional
import argparse

import oci
from oci.config import from_file
from dotenv import load_dotenv

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
        self.dbm_client = oci.database_management.DatabaseManagementClient(self.config)

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

    def scan_databases_in_compartment(self, compartment: Dict) -> Dict:
        """Scan for databases in a specific compartment."""
        comp_id = compartment['id']
        comp_name = compartment['name']
        comp_path = compartment['path']

        print(f"🔎 Scanning {comp_path}")

        # Check Operations Insights
        try:
            db_insights = oci.pagination.list_call_get_all_results(
                self.opsi_client.list_database_insights,
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
                    'monitoring_type': 'operations_insights'
                }
                compartment['databases']['operations_insights']['items'].append(db_info)
                self.results['databases_found'].append(db_info)

        except Exception as e:
            compartment['databases']['operations_insights']['error'] = str(e)
            print(f"   ⚠️  Ops Insights error: {str(e)[:100]}...")

        # Check Database Management
        try:
            managed_dbs = oci.pagination.list_call_get_all_results(
                self.dbm_client.list_managed_databases,
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
                    'monitoring_type': 'database_management'
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
        """Run complete database discovery."""
        print("🚀 Starting Enhanced Database Discovery")
        print("=" * 60)

        # Discover compartments
        compartments = self.discover_compartments(root_compartment_ids)

        # Scan each compartment for databases
        print("\n🔎 Scanning for databases...")
        for compartment in compartments:
            self.scan_databases_in_compartment(compartment)

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
        """Save results to JSON file."""
        if not filename:
            timestamp = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
            filename = f"database_discovery_{self.profile}_{timestamp}.json"

        with open(filename, 'w') as f:
            json.dump(self.results, f, indent=2, default=str)

        print(f"\n💾 Results saved to: {filename}")
        return filename


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description='Enhanced OCI Database Discovery')
    parser.add_argument('--profile', help='OCI CLI profile name')
    parser.add_argument('--region', help='OCI region override')
    parser.add_argument('--compartments', nargs='*', help='Root compartment OCIDs to scan')
    parser.add_argument('--output', help='Output JSON filename')

    args = parser.parse_args()

    try:
        # Initialize discovery
        discovery = EnhancedDatabaseDiscovery(
            profile=args.profile,
            region=args.region
        )

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
