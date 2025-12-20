#!/usr/bin/env python3
"""
Tenancy Review Script for MCP OCI OPSI - Multi-Region Support

This script performs a comprehensive review of your OCI tenancy across ALL subscribed
regions and builds an optimized cache for fast database inventory queries.

Features:
- 🌍 MULTI-REGION: Automatically scans all subscribed regions
- Scans all compartments in tenancy
- Builds comprehensive database cache with region information
- Generates inventory report
- Provides optimization recommendations
- Validates Operations Insights setup

Usage:
    python3 tenancy_review.py
    python3 tenancy_review.py --profile emdemo
    python3 tenancy_review.py --compartment ocid1.compartment.oc1..example...
    python3 tenancy_review.py --regions us-phoenix-1,uk-london-1  # Specific regions only
"""

import argparse
import json
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List

# Add parent directory to path for imports
# Need to go up 2 levels (scripts -> mcp_oci_opsi -> root) to allow 'from mcp_oci_opsi...'
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from mcp_oci_opsi.cache import DatabaseCache
from mcp_oci_opsi.config import get_oci_config, list_available_profiles
from mcp_oci_opsi.oci_clients import get_opsi_client, list_all
import oci


class TenancyReviewer:
    """Comprehensive OCI tenancy review and cache builder with multi-region support."""

    def __init__(self, profile: str = None, compartment_id: str = None, regions: List[str] = None):
        """
        Initialize tenancy reviewer.

        Args:
            profile: OCI CLI profile to use
            compartment_id: Optional single compartment to scan (defaults to all)
            regions: Optional list of specific regions to scan (defaults to all subscribed)
        """
        if profile:
            os.environ["OCI_CLI_PROFILE"] = profile

        self.config = get_oci_config()
        self.home_region = self.config.get("region")
        self.identity_client = oci.identity.IdentityClient(self.config)
        
        # Use profile-specific cache file
        profile_name = os.getenv("OCI_CLI_PROFILE", "DEFAULT")
        safe_profile = profile_name.replace(" ", "_").replace("/", "_")
        cache_dir = os.getenv("MCP_CACHE_DIR") or os.getenv("OCI_MCP_CACHE_DIR") or str(Path.home() / ".mcp-oci" / "cache")
        cache_path = Path(os.path.expanduser(cache_dir)) / f"opsi_cache_{safe_profile}.json"
        self.cache = DatabaseCache(cache_file=str(cache_path))
        
        self.target_compartment = compartment_id
        self.target_regions = regions

        # Will be populated with subscribed regions
        self.subscribed_regions = []

        self.review_data = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "profile": os.getenv("OCI_CLI_PROFILE", "DEFAULT"),
            "home_region": self.home_region,
            "scanned_regions": [],
            "tenancy_id": self.config.get("tenancy"),
            "compartments": {},
            "databases": {},
            "hosts": {},
            "exadata_systems": {},
            "statistics": {},
            "recommendations": [],
        }

    def run_review(self) -> Dict[str, Any]:
        """
        Run comprehensive tenancy review.

        Returns:
            Dictionary with review results and recommendations
        """
        print("=" * 80)
        print("🌍 OCI TENANCY REVIEW - MCP OCI OPSI (MULTI-REGION)")
        print("=" * 80)
        print()

        # Step 1: Identify user and tenancy
        self._print_step("1/7", "Identifying user and tenancy")
        self._get_tenancy_info()

        # Step 2: Discover subscribed regions
        self._print_step("2/7", "Discovering subscribed regions")
        self._discover_regions()

        # Step 3: Scan compartments
        self._print_step("3/7", "Scanning compartments")
        self._scan_compartments()

        # Step 4: Scan database insights (multi-region)
        self._print_step("4/7", "Scanning database insights across regions")
        self._scan_database_insights_multiregion()

        # Step 5: Scan host insights (multi-region)
        self._print_step("5/7", "Scanning host insights across regions")
        self._scan_host_insights_multiregion()

        # Step 6: Scan Exadata systems (multi-region)
        self._print_step("6/7", "Scanning Exadata insights across regions")
        self._scan_exadata_insights_multiregion()

        # Step 7: Generate recommendations
        self._print_step("7/7", "Generating recommendations")
        self._generate_recommendations()

        # Build cache
        print()
        print("Building optimized cache...")
        self._build_cache()

        # Generate report
        print()
        self._print_summary()

        return self.review_data

    def _print_step(self, step: str, message: str):
        """Print a step header."""
        print()
        print(f"[{step}] {message}")
        print("-" * 80)

    def _get_tenancy_info(self):
        """Get tenancy and user information."""
        try:
            tenancy = self.identity_client.get_tenancy(
                tenancy_id=self.config["tenancy"]
            ).data

            user = self.identity_client.get_user(user_id=self.config["user"]).data

            self.review_data["tenancy_name"] = tenancy.name
            self.review_data["user_name"] = user.name

            print(f"  Tenancy: {tenancy.name}")
            print(f"  User: {user.name}")
            print(f"  Region: {self.config.get('region')}")
            print(f"  Profile: {self.review_data['profile']}")

        except Exception as e:
            print(f"  ⚠️  Warning: Could not get tenancy info: {e}")

    def _discover_regions(self):
        """Discover all subscribed regions in the tenancy."""
        try:
            # Use identity client to get region subscriptions
            region_subscriptions = list_all(
                self.identity_client.list_region_subscriptions,
                tenancy_id=self.config["tenancy"]
            )

            all_regions = []
            for region_sub in region_subscriptions:
                if region_sub.status == "READY":
                    region_name = region_sub.region_name
                    all_regions.append(region_name)

            # Filter to target regions if specified
            if self.target_regions:
                self.subscribed_regions = [
                    r for r in all_regions if r in self.target_regions
                ]
                print(f"  Targeting specific regions: {', '.join(self.subscribed_regions)}")
            else:
                self.subscribed_regions = all_regions
                print(f"  ✓ Found {len(self.subscribed_regions)} subscribed regions:")
                for region in self.subscribed_regions:
                    indicator = "🏠" if region == self.home_region else "  "
                    print(f"    {indicator} {region}")

            self.review_data["scanned_regions"] = self.subscribed_regions

        except Exception as e:
            print(f"  ⚠️  Warning: Could not discover regions: {e}")
            print(f"  Falling back to home region only: {self.home_region}")
            self.subscribed_regions = [self.home_region]
            self.review_data["scanned_regions"] = [self.home_region]

    def _scan_compartments(self):
        """Scan all compartments in tenancy."""
        try:
            # Determine root compartment
            if self.target_compartment:
                root_compartments = [self.target_compartment]
                print(f"  Scanning single compartment: {self.target_compartment}")
            else:
                root_compartments = [self.config["tenancy"]]
                print(f"  Scanning entire tenancy (root compartment)")

            all_compartments = {}

            for root_id in root_compartments:
                # Add root compartment
                try:
                    root_comp = self.identity_client.get_compartment(
                        compartment_id=root_id
                    ).data
                    all_compartments[root_id] = {
                        "id": root_id,
                        "name": root_comp.name,
                        "description": root_comp.description,
                        "lifecycle_state": root_comp.lifecycle_state,
                        "parent_id": None,
                    }
                except Exception:
                    all_compartments[root_id] = {
                        "id": root_id,
                        "name": "Root (Tenancy)",
                        "description": "Root compartment",
                        "lifecycle_state": "ACTIVE",
                        "parent_id": None,
                    }

                # Get all child compartments recursively
                child_compartments = list_all(
                    self.identity_client.list_compartments,
                    compartment_id=root_id,
                    compartment_id_in_subtree=True,
                )

                for comp in child_compartments:
                    if comp.lifecycle_state == "ACTIVE":
                        all_compartments[comp.id] = {
                            "id": comp.id,
                            "name": comp.name,
                            "description": comp.description,
                            "lifecycle_state": comp.lifecycle_state,
                            "parent_id": root_id,
                        }

            self.review_data["compartments"] = all_compartments
            print(f"  ✓ Found {len(all_compartments)} active compartments")

        except Exception as e:
            print(f"  ⚠️  Error scanning compartments: {e}")

    def _scan_database_insights(self):
        """Scan all database insights."""
        databases = {}
        compartment_db_counts = {}

        for comp_id, comp_info in self.review_data["compartments"].items():
            try:
                db_insights = list_all(
                    self.opsi_client.list_database_insights,
                    compartment_id=comp_id,
                )

                active_dbs = [db for db in db_insights if db.lifecycle_state == "ACTIVE"]

                if active_dbs:
                    compartment_db_counts[comp_info["name"]] = len(active_dbs)

                for db in active_dbs:
                    databases[db.id] = {
                        "id": db.id,
                        "database_id": getattr(db, "database_id", None),
                        "database_name": getattr(db, "database_name", None),
                        "database_display_name": getattr(
                            db, "database_display_name", None
                        ),
                        "database_type": getattr(db, "database_type", None),
                        "database_version": getattr(db, "database_version", None),
                        "entity_source": getattr(db, "entity_source", None),
                        "compartment_id": comp_id,
                        "compartment_name": comp_info["name"],
                        "status": db.status,
                        "lifecycle_state": db.lifecycle_state,
                        "time_created": str(getattr(db, "time_created", None)),
                    }

            except Exception as e:
                # Compartment might not have OPSI enabled
                pass

        self.review_data["databases"] = databases
        print(f"  ✓ Found {len(databases)} database insights")

        if compartment_db_counts:
            print()
            print("  Database distribution by compartment:")
            for comp_name, count in sorted(
                compartment_db_counts.items(), key=lambda x: x[1], reverse=True
            ):
                print(f"    • {comp_name}: {count} databases")

    def _scan_database_insights_multiregion(self):
        """Scan database insights across all subscribed regions."""
        from mcp_oci_opsi.oci_clients import extract_region_from_ocid

        databases = {}
        region_db_counts = {}
        compartment_db_counts = {}

        for region in self.subscribed_regions:
            print(f"\n  Scanning region: {region}")
            region_count = 0

            try:
                # Create region-specific OPSI client
                opsi_client = get_opsi_client(region=region)

                for comp_id, comp_info in self.review_data["compartments"].items():
                    try:
                        db_insights = list_all(
                            opsi_client.list_database_insights,
                            compartment_id=comp_id,
                        )

                        active_dbs = [db for db in db_insights if db.lifecycle_state == "ACTIVE"]

                        if active_dbs:
                            comp_key = f"{comp_info['name']} ({region})"
                            compartment_db_counts[comp_key] = compartment_db_counts.get(comp_key, 0) + len(active_dbs)

                        for db in active_dbs:
                            # Extract region from OCID as backup
                            ocid_region = extract_region_from_ocid(db.id) if hasattr(db, 'id') else None

                            databases[db.id] = {
                                "id": db.id,
                                "database_id": getattr(db, "database_id", None),
                                "database_name": getattr(db, "database_name", None),
                                "database_display_name": getattr(db, "database_display_name", None),
                                "database_type": getattr(db, "database_type", None),
                                "database_version": getattr(db, "database_version", None),
                                "entity_source": getattr(db, "entity_source", None),
                                "compartment_id": comp_id,
                                "compartment_name": comp_info["name"],
                                "region": ocid_region or region,  # Store region info!
                                "status": db.status,
                                "lifecycle_state": db.lifecycle_state,
                                "time_created": str(getattr(db, "time_created", None)),
                            }
                            region_count += 1

                    except Exception as e:
                        # Compartment might not have OPSI enabled in this region
                        pass

                region_db_counts[region] = region_count
                print(f"    ✓ Found {region_count} databases")

            except Exception as e:
                print(f"    ⚠️  Error scanning region {region}: {e}")
                region_db_counts[region] = 0

        self.review_data["databases"] = databases

        total_dbs = len(databases)
        print(f"\n  ✅ Total: {total_dbs} database insights across all regions")

        if region_db_counts:
            print("\n  Database distribution by region:")
            for region, count in sorted(region_db_counts.items(), key=lambda x: x[1], reverse=True):
                indicator = "🏠" if region == self.home_region else "  "
                print(f"    {indicator} {region}: {count} databases")

        if compartment_db_counts:
            print("\n  Database distribution by compartment (top 10):")
            for comp_name, count in sorted(compartment_db_counts.items(), key=lambda x: x[1], reverse=True)[:10]:
                print(f"    • {comp_name}: {count} databases")

    def _scan_host_insights_multiregion(self):
        """Scan host insights across all subscribed regions."""
        from mcp_oci_opsi.oci_clients import extract_region_from_ocid

        hosts = {}
        region_host_counts = {}
        compartment_host_counts = {}

        for region in self.subscribed_regions:
            print(f"\n  Scanning region: {region}")
            region_count = 0

            try:
                # Create region-specific OPSI client
                opsi_client = get_opsi_client(region=region)

                for comp_id, comp_info in self.review_data["compartments"].items():
                    try:
                        host_insights = list_all(
                            opsi_client.list_host_insights,
                            compartment_id=comp_id,
                        )

                        active_hosts = [
                            h for h in host_insights if h.lifecycle_state == "ACTIVE"
                        ]

                        if active_hosts:
                            comp_key = f"{comp_info['name']} ({region})"
                            compartment_host_counts[comp_key] = compartment_host_counts.get(comp_key, 0) + len(active_hosts)

                        for host in active_hosts:
                            # Extract region from OCID as backup
                            ocid_region = extract_region_from_ocid(host.id) if hasattr(host, 'id') else None

                            hosts[host.id] = {
                                "id": host.id,
                                "host_name": getattr(host, "host_name", None),
                                "host_display_name": getattr(host, "host_display_name", None),
                                "host_type": getattr(host, "host_type", None),
                                "platform_type": getattr(host, "platform_type", None),
                                "compartment_id": comp_id,
                                "compartment_name": comp_info["name"],
                                "region": ocid_region or region,  # Store region info!
                                "status": host.status,
                                "lifecycle_state": host.lifecycle_state,
                            }
                            region_count += 1

                    except Exception:
                        # Compartment might not have OPSI enabled in this region
                        pass

                region_host_counts[region] = region_count
                print(f"    ✓ Found {region_count} hosts")

            except Exception as e:
                print(f"    ⚠️  Error scanning region {region}: {e}")
                region_host_counts[region] = 0

        self.review_data["hosts"] = hosts

        total_hosts = len(hosts)
        print(f"\n  ✅ Total: {total_hosts} host insights across all regions")

        if region_host_counts:
            print("\n  Host distribution by region:")
            for region, count in sorted(region_host_counts.items(), key=lambda x: x[1], reverse=True):
                indicator = "🏠" if region == self.home_region else "  "
                print(f"    {indicator} {region}: {count} hosts")

        if compartment_host_counts:
            print("\n  Host distribution by compartment (top 5):")
            for comp_name, count in sorted(compartment_host_counts.items(), key=lambda x: x[1], reverse=True)[:5]:
                print(f"    • {comp_name}: {count} hosts")

    def _scan_host_insights(self):
        """Scan all host insights (DEPRECATED - use _scan_host_insights_multiregion)."""
        hosts = {}
        compartment_host_counts = {}

        for comp_id, comp_info in self.review_data["compartments"].items():
            try:
                host_insights = list_all(
                    self.opsi_client.list_host_insights,
                    compartment_id=comp_id,
                )

                active_hosts = [
                    h for h in host_insights if h.lifecycle_state == "ACTIVE"
                ]

                if active_hosts:
                    compartment_host_counts[comp_info["name"]] = len(active_hosts)

                for host in active_hosts:
                    hosts[host.id] = {
                        "id": host.id,
                        "host_name": getattr(host, "host_name", None),
                        "host_display_name": getattr(host, "host_display_name", None),
                        "host_type": getattr(host, "host_type", None),
                        "platform_type": getattr(host, "platform_type", None),
                        "compartment_id": comp_id,
                        "compartment_name": comp_info["name"],
                        "status": host.status,
                        "lifecycle_state": host.lifecycle_state,
                    }

            except Exception:
                pass

        self.review_data["hosts"] = hosts
        print(f"  ✓ Found {len(hosts)} host insights")

        if compartment_host_counts:
            print()
            print("  Host distribution by compartment:")
            for comp_name, count in sorted(
                compartment_host_counts.items(), key=lambda x: x[1], reverse=True
            ):
                print(f"    • {comp_name}: {count} hosts")

    def _scan_exadata_insights_multiregion(self):
        """Scan Exadata insights across all subscribed regions."""
        from mcp_oci_opsi.oci_clients import extract_region_from_ocid

        exadata_systems = {}
        region_exa_counts = {}
        compartment_exa_counts = {}

        for region in self.subscribed_regions:
            print(f"\n  Scanning region: {region}")
            region_count = 0

            try:
                # Create region-specific OPSI client
                opsi_client = get_opsi_client(region=region)

                for comp_id, comp_info in self.review_data["compartments"].items():
                    try:
                        exa_insights = list_all(
                            opsi_client.list_exadata_insights,
                            compartment_id=comp_id,
                        )

                        active_exa = [e for e in exa_insights if e.lifecycle_state == "ACTIVE"]

                        if active_exa:
                            comp_key = f"{comp_info['name']} ({region})"
                            compartment_exa_counts[comp_key] = compartment_exa_counts.get(comp_key, 0) + len(active_exa)

                        for exa in active_exa:
                            # Extract region from OCID as backup
                            ocid_region = extract_region_from_ocid(exa.id) if hasattr(exa, 'id') else None

                            exadata_systems[exa.id] = {
                                "id": exa.id,
                                "exadata_name": getattr(exa, "exadata_display_name", None),
                                "exadata_type": getattr(exa, "exadata_type", None),
                                "compartment_id": comp_id,
                                "compartment_name": comp_info["name"],
                                "region": ocid_region or region,  # Store region info!
                                "status": exa.status,
                                "lifecycle_state": exa.lifecycle_state,
                            }
                            region_count += 1

                    except Exception:
                        # Compartment might not have OPSI enabled in this region
                        pass

                region_exa_counts[region] = region_count
                print(f"    ✓ Found {region_count} Exadata systems")

            except Exception as e:
                print(f"    ⚠️  Error scanning region {region}: {e}")
                region_exa_counts[region] = 0

        self.review_data["exadata_systems"] = exadata_systems

        total_exa = len(exadata_systems)
        print(f"\n  ✅ Total: {total_exa} Exadata insights across all regions")

        if region_exa_counts:
            print("\n  Exadata distribution by region:")
            for region, count in sorted(region_exa_counts.items(), key=lambda x: x[1], reverse=True):
                indicator = "🏠" if region == self.home_region else "  "
                print(f"    {indicator} {region}: {count} Exadata systems")

        if compartment_exa_counts:
            print("\n  Exadata distribution by compartment (top 5):")
            for comp_name, count in sorted(compartment_exa_counts.items(), key=lambda x: x[1], reverse=True)[:5]:
                print(f"    • {comp_name}: {count} Exadata systems")

    def _scan_exadata_insights(self):
        """Scan Exadata systems (DEPRECATED - use _scan_exadata_insights_multiregion)."""
        exadata_systems = {}
        compartment_exa_counts = {}

        for comp_id, comp_info in self.review_data["compartments"].items():
            try:
                exa_insights = list_all(
                    self.opsi_client.list_exadata_insights,
                    compartment_id=comp_id,
                )

                active_exa = [e for e in exa_insights if e.lifecycle_state == "ACTIVE"]

                if active_exa:
                    compartment_exa_counts[comp_info["name"]] = len(active_exa)

                for exa in active_exa:
                    exadata_systems[exa.id] = {
                        "id": exa.id,
                        "exadata_name": getattr(exa, "exadata_display_name", None),
                        "exadata_type": getattr(exa, "exadata_type", None),
                        "compartment_id": comp_id,
                        "compartment_name": comp_info["name"],
                        "status": exa.status,
                        "lifecycle_state": exa.lifecycle_state,
                    }

            except Exception:
                pass

        self.review_data["exadata_systems"] = exadata_systems
        print(f"  ✓ Found {len(exadata_systems)} Exadata systems")

        if compartment_exa_counts:
            print()
            print("  Exadata distribution by compartment:")
            for comp_name, count in sorted(
                compartment_exa_counts.items(), key=lambda x: x[1], reverse=True
            ):
                print(f"    • {comp_name}: {count} Exadata systems")

    def _generate_recommendations(self):
        """Generate optimization recommendations."""
        recommendations = []

        # Database type analysis
        db_types = {}
        for db in self.review_data["databases"].values():
            db_type = db.get("database_type", "Unknown")
            db_types[db_type] = db_types.get(db_type, 0) + 1

        self.review_data["statistics"]["databases_by_type"] = db_types
        self.review_data["statistics"]["total_databases"] = len(
            self.review_data["databases"]
        )
        self.review_data["statistics"]["total_hosts"] = len(
            self.review_data["hosts"]
        )
        self.review_data["statistics"]["total_exadata"] = len(
            self.review_data["exadata_systems"]
        )
        self.review_data["statistics"]["total_compartments"] = len(
            self.review_data["compartments"]
        )

        # Cache optimization recommendations
        if len(self.review_data["databases"]) > 100:
            recommendations.append({
                "category": "Performance",
                "priority": "HIGH",
                "message": f"Large fleet detected ({len(self.review_data['databases'])} databases). Cache system will provide significant performance benefits.",
                "action": "Cache has been built automatically. Use fast cache tools for instant responses.",
            })

        if len(self.review_data["compartments"]) > 10:
            recommendations.append({
                "category": "Organization",
                "priority": "MEDIUM",
                "message": f"Multiple compartments detected ({len(self.review_data['compartments'])}). Consider using compartment-specific queries for faster results.",
                "action": "Use get_databases_by_compartment() for targeted searches.",
            })

        # Database type recommendations
        if "EXTERNAL-NONCDB" in db_types or "EXTERNAL-PDB" in db_types:
            external_count = db_types.get("EXTERNAL-NONCDB", 0) + db_types.get(
                "EXTERNAL-PDB", 0
            )
            recommendations.append({
                "category": "Database Types",
                "priority": "INFO",
                "message": f"Found {external_count} external databases. These require Database Management agents for full monitoring.",
                "action": "Verify Database Management agents are deployed and configured.",
            })

        # Autonomous database recommendations
        adb_types = ["ATP-D", "ATP-S", "ADW-D", "ADW-S"]
        adb_count = sum(db_types.get(t, 0) for t in adb_types)
        if adb_count > 0:
            recommendations.append({
                "category": "Autonomous Databases",
                "priority": "INFO",
                "message": f"Found {adb_count} Autonomous Databases with automatic Operations Insights integration.",
                "action": "Use SQL performance tools for detailed analysis of ATP/ADW databases.",
            })

        # MCP usage recommendations
        recommendations.append({
            "category": "MCP Usage",
            "priority": "HIGH",
            "message": "Cache is now ready for instant database inventory queries.",
            "action": "Try: 'How many databases do I have?' or 'Find database X' for instant responses.",
        })

        self.review_data["recommendations"] = recommendations

        print()
        for rec in recommendations:
            priority_icon = {
                "HIGH": "🔴",
                "MEDIUM": "🟡",
                "LOW": "🟢",
                "INFO": "ℹ️",
            }.get(rec["priority"], "•")

            print(f"  {priority_icon} [{rec['category']}] {rec['message']}")
            print(f"     → {rec['action']}")
            print()

    def _build_cache(self):
        """Build the database cache."""
        compartment_ids = list(self.review_data["compartments"].keys())

        try:
            result = self.cache.build_cache(compartment_ids)
            print(f"  ✓ Cache built successfully")
            print(f"  ✓ Cached {result['statistics']['total_databases']} databases")
            print(f"  ✓ Cached {result['statistics']['total_hosts']} hosts")
            print(f"  ✓ Cache location: {self.cache.cache_file}")
        except Exception as e:
            print(f"  ⚠️  Error building cache: {e}")

    def _print_summary(self):
        """Print review summary."""
        print("=" * 80)
        print("TENANCY REVIEW SUMMARY")
        print("=" * 80)
        print()
        print(f"Tenancy: {self.review_data.get('tenancy_name', 'Unknown')}")
        print(f"Home Region: {self.review_data.get('home_region', 'Unknown')}")

        # Show scanned regions for multi-region context
        scanned_regions = self.review_data.get('scanned_regions', [])
        if scanned_regions:
            print(f"Scanned Regions ({len(scanned_regions)}): {', '.join(scanned_regions)}")

        print(f"Profile: {self.review_data['profile']}")
        print()
        print("INVENTORY:")
        print(f"  • Compartments: {self.review_data['statistics']['total_compartments']}")
        print(f"  • Databases: {self.review_data['statistics']['total_databases']}")
        print(f"  • Hosts: {self.review_data['statistics']['total_hosts']}")
        print(f"  • Exadata Systems: {self.review_data['statistics']['total_exadata']}")
        print()
        print("DATABASE TYPES:")
        for db_type, count in sorted(
            self.review_data["statistics"]["databases_by_type"].items(),
            key=lambda x: x[1],
            reverse=True,
        ):
            print(f"  • {db_type}: {count}")
        print()
        print("=" * 80)
        print("✅ TENANCY REVIEW COMPLETE")
        print("=" * 80)
        print()
        print("NEXT STEPS:")
        print("1. Use fast cache tools for instant database queries")
        print("2. Try: 'How many databases do I have?'")
        print("3. Try: 'Find database X'")
        print("4. Try: 'Show me databases in compartment X'")
        print()
        print(f"Report saved to: {self._save_report()}")

    def _save_report(self) -> str:
        """Save review report to file."""
        cache_dir = os.getenv("MCP_CACHE_DIR") or os.getenv("OCI_MCP_CACHE_DIR") or "~/.mcp-oci/cache"
        report_dir = Path(os.path.expanduser(cache_dir))
        report_dir.mkdir(parents=True, exist_ok=True)

        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        report_file = report_dir / f"tenancy_review_{timestamp}.json"

        with open(report_file, "w") as f:
            json.dump(self.review_data, f, indent=2)

        return str(report_file)


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="OCI Tenancy Review and Cache Builder for MCP OCI OPSI - Multi-Region Support"
    )
    parser.add_argument(
        "--profile",
        help="OCI CLI profile to use (default: from OCI_CLI_PROFILE env or DEFAULT)",
    )
    parser.add_argument(
        "--compartment",
        help="Optional compartment OCID to scan (default: entire tenancy)",
    )
    parser.add_argument(
        "--regions",
        help="Comma-separated list of regions to scan (default: all subscribed regions). Example: us-phoenix-1,uk-london-1",
    )
    parser.add_argument(
        "--list-profiles",
        action="store_true",
        help="List available OCI profiles and exit",
    )

    args = parser.parse_args()

    if args.list_profiles:
        print("Available OCI profiles:")
        try:
            profiles = list_available_profiles()
            for profile in profiles:
                current = " (CURRENT)" if profile == os.getenv("OCI_CLI_PROFILE", "DEFAULT") else ""
                print(f"  • {profile}{current}")
        except Exception as e:
            print(f"Error listing profiles: {e}")
        return

    # Parse regions
    target_regions = None
    if args.regions:
        target_regions = [r.strip() for r in args.regions.split(",")]

    try:
        reviewer = TenancyReviewer(
            profile=args.profile,
            compartment_id=args.compartment,
            regions=target_regions
        )
        reviewer.run_review()
    except KeyboardInterrupt:
        print("\n\nReview cancelled by user.")
        sys.exit(1)
    except Exception as e:
        print(f"\n\nERROR: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
