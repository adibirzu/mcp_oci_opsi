"""Enhanced caching infrastructure with static tenancy and database metadata.

This module extends the basic cache with:
- Tenancy information (name, home region, subscriptions)
- Region list and availability domains
- Full compartment hierarchy (tree structure)
- Extended database metadata
- User and identity information

Purpose: Minimize token usage by caching static OCI data that rarely changes.
"""

import json
import os
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

import oci

from .config import get_oci_config
from .oci_clients import get_opsi_client, list_all


def _get_shared_cache_dir() -> Path:
    raw = os.getenv("MCP_CACHE_DIR") or os.getenv("OCI_MCP_CACHE_DIR")
    if raw:
        return Path(os.path.expanduser(raw))
    return Path.home() / ".mcp-oci" / "cache"


def _maybe_write_redis(cache_key: str, payload: Dict[str, Any]) -> None:
    backend = os.getenv("MCP_CACHE_BACKEND", "file").lower()
    redis_url = os.getenv("MCP_REDIS_URL") or os.getenv("REDIS_URL")
    if backend != "redis" or not redis_url:
        return
    try:
        import redis  # type: ignore
    except Exception:
        return
    try:
        prefix = os.getenv("MCP_CACHE_KEY_PREFIX", "mcp:cache")
        client = redis.Redis.from_url(redis_url)
        client.set(f"{prefix}:{cache_key}", json.dumps(payload, default=str))
    except Exception:
        return


class EnhancedDatabaseCache:
    """Enhanced cache with comprehensive tenancy and resource metadata."""

    def __init__(self, cache_file: Optional[str] = None, profile: Optional[str] = None):
        """
        Initialize enhanced cache.

        Args:
            cache_file: Optional path to cache file. Defaults to $MCP_CACHE_DIR/opsi_cache_enhanced_{profile}.json
            profile: OCI profile name. Defaults to "DEFAULT" or OCI_CLI_PROFILE env var.
        """
        self.profile = profile or os.getenv("OCI_CLI_PROFILE", "DEFAULT")
        
        if cache_file:
            self.cache_file = Path(cache_file)
        else:
            safe_profile = self.profile.replace(" ", "_").replace("/", "_")
            self.cache_file = _get_shared_cache_dir() / f"opsi_cache_enhanced_{safe_profile}.json"

        self.cache_file.parent.mkdir(parents=True, exist_ok=True)

        self.cache_data: Dict[str, Any] = {
            "version": "2.0",
            "metadata": {
                "last_updated": None,
                "profile": None,
                "build_duration_seconds": 0,
            },
            "tenancy": {
                "id": None,
                "name": None,
                "home_region": None,
                "home_region_key": None,
                "description": None,
            },
            "regions": {},  # All subscribed regions
            "availability_domains": {},  # ADs by region
            "compartments": {},  # All compartments with hierarchy
            "compartment_tree": [],  # Tree structure for visualization
            "databases": {},  # Database insights
            "hosts": {},  # Host insights
            "database_details": {},  # Extended database metadata
            "statistics": {
                "total_databases": 0,
                "total_hosts": 0,
                "total_compartments": 0,
                "total_regions": 0,
                "databases_by_type": {},
                "databases_by_compartment": {},
                "databases_by_region": {},
                "databases_by_status": {},
                "databases_by_version": {},
                "databases_by_entity_source": {},
            },
        }

    def load(self) -> bool:
        """Load cache from file."""
        try:
            if self.cache_file.exists():
                with open(self.cache_file, "r") as f:
                    self.cache_data = json.load(f)
                return True
            return False
        except Exception:
            return False

    def save(self) -> bool:
        """Save cache to file."""
        try:
            with open(self.cache_file, "w") as f:
                json.dump(self.cache_data, f, indent=2)
            safe_profile = self.profile.replace(" ", "_").replace("/", "_")
            _maybe_write_redis(f"opsi_cache_enhanced:{safe_profile}", self.cache_data)
            return True
        except Exception:
            return False

    def build_enhanced_cache(self, compartment_ids: List[str]) -> Dict[str, Any]:
        """
        Build comprehensive cache with all static tenancy data.

        This method fetches and caches:
        1. Tenancy information
        2. All subscribed regions
        3. Availability domains per region
        4. Full compartment hierarchy
        5. Database insights with extended metadata
        6. Host insights
        7. Comprehensive statistics

        Args:
            compartment_ids: List of root compartment OCIDs to scan

        Returns:
            Dict with build results and statistics
        """
        start_time = datetime.utcnow()
        
        # Save original profile to restore later
        original_profile = os.environ.get("OCI_CLI_PROFILE")
        if self.profile:
            os.environ["OCI_CLI_PROFILE"] = self.profile

        try:
            config = get_oci_config()

            # Initialize clients
            identity_client = oci.identity.IdentityClient(config)
            opsi_client = get_opsi_client()

            # Update metadata
            self.cache_data["metadata"]["last_updated"] = datetime.utcnow().isoformat() + "Z"
            self.cache_data["metadata"]["profile"] = self.profile

            print(f"📊 Building Enhanced Cache for profile: {self.profile}...")
            print()

            # ========================================================================
            # 1. Fetch Tenancy Information
            # ========================================================================
            print("1️⃣  Fetching tenancy information...")
            try:
                tenancy_id = config.get("tenancy")
                tenancy = identity_client.get_tenancy(tenancy_id).data

                self.cache_data["tenancy"] = {
                    "id": tenancy.id,
                    "name": tenancy.name,
                    "home_region": tenancy.home_region_key,
                    "home_region_key": tenancy.home_region_key,
                    "description": getattr(tenancy, "description", None),
                }
                print(f"   ✅ Tenancy: {tenancy.name}")
                print(f"   ✅ Home Region: {tenancy.home_region_key}")
            except Exception as e:
                print(f"   ❌ Failed to fetch tenancy: {e}")

            # ========================================================================
            # 2. Fetch All Subscribed Regions
            # ========================================================================
            print("\n2️⃣  Fetching subscribed regions...")
            try:
                region_subscriptions = list_all(
                    identity_client.list_region_subscriptions,
                    tenancy_id=config.get("tenancy"),
                )

                for region_sub in region_subscriptions:
                    region_name = region_sub.region_name
                    self.cache_data["regions"][region_name] = {
                        "name": region_name,
                        "key": region_sub.region_key,
                        "is_home_region": region_sub.is_home_region,
                        "status": region_sub.status,
                    }
                    print(f"   ✅ {region_name} ({region_sub.region_key})")

                self.cache_data["statistics"]["total_regions"] = len(self.cache_data["regions"])
            except Exception as e:
                print(f"   ❌ Failed to fetch regions: {e}")

            # ========================================================================
            # 3. Fetch Availability Domains (for current region only, to save time)
            # ========================================================================
            print("\n3️⃣  Fetching availability domains...")
            try:
                current_region = config.get("region")
                ads = list_all(
                    identity_client.list_availability_domains,
                    compartment_id=config.get("tenancy"),
                )

                self.cache_data["availability_domains"][current_region] = []
                for ad in ads:
                    ad_data = {
                        "name": ad.name,
                        "id": ad.id,
                    }
                    self.cache_data["availability_domains"][current_region].append(ad_data)
                    print(f"   ✅ {ad.name}")
            except Exception as e:
                print(f"   ❌ Failed to fetch ADs: {e}")

            # ========================================================================
            # 4. Fetch Compartment Hierarchy
            # ========================================================================
            print("\n4️⃣  Fetching compartment hierarchy...")
            all_compartments = set()
            compartment_relationships = {}  # parent_id -> [child_ids]

            for root_compartment_id in compartment_ids:
                all_compartments.add(root_compartment_id)

                # Add root compartment
                try:
                    root_comp = identity_client.get_compartment(root_compartment_id).data
                    self.cache_data["compartments"][root_compartment_id] = {
                        "id": root_comp.id,
                        "name": root_comp.name,
                        "description": root_comp.description,
                        "parent_id": None,
                        "lifecycle_state": root_comp.lifecycle_state,
                        "level": 0,
                    }
                    print(f"   ✅ Root: {root_comp.name}")
                except Exception:
                    pass

                # Get all child compartments recursively
                try:
                    child_compartments = list_all(
                        identity_client.list_compartments,
                        compartment_id=root_compartment_id,
                        compartment_id_in_subtree=True,
                    )

                    for comp in child_compartments:
                        if comp.lifecycle_state == "ACTIVE":
                            all_compartments.add(comp.id)

                            # Determine level in hierarchy
                            parent_id = getattr(comp, "compartment_id", root_compartment_id)
                            level = 1
                            if parent_id in self.cache_data["compartments"]:
                                level = self.cache_data["compartments"][parent_id].get("level", 0) + 1

                            self.cache_data["compartments"][comp.id] = {
                                "id": comp.id,
                                "name": comp.name,
                                "description": comp.description,
                                "parent_id": parent_id,
                                "lifecycle_state": comp.lifecycle_state,
                                "level": level,
                            }

                            # Track relationships
                            if parent_id not in compartment_relationships:
                                compartment_relationships[parent_id] = []
                            compartment_relationships[parent_id].append(comp.id)

                            print(f"   ✅ {'  ' * level}{comp.name}")
                except Exception as e:
                    print(f"   ⚠️  Error fetching children for {root_compartment_id}: {e}")

            self.cache_data["statistics"]["total_compartments"] = len(all_compartments)
            print(f"\n   Total compartments: {len(all_compartments)}")

            # ========================================================================
            # 5. Fetch Database Insights with Extended Metadata
            # ========================================================================
            print("\n5️⃣  Fetching database insights...")
            db_count = 0

            for compartment_id in all_compartments:
                try:
                    db_insights = list_all(
                        opsi_client.list_database_insights,
                        compartment_id=compartment_id,
                    )

                    for db in db_insights:
                        if db.lifecycle_state == "ACTIVE":
                            db_id = db.id
                            compartment_name = self.cache_data["compartments"].get(
                                compartment_id, {}
                            ).get("name", "Unknown")

                            # Basic info
                            self.cache_data["databases"][db_id] = {
                                "id": db_id,
                                "database_id": getattr(db, "database_id", None),
                                "database_name": getattr(db, "database_name", None),
                                "database_display_name": getattr(db, "database_display_name", None),
                                "database_type": getattr(db, "database_type", None),
                                "database_version": getattr(db, "database_version", None),
                                "entity_source": getattr(db, "entity_source", None),
                                "compartment_id": compartment_id,
                                "compartment_name": compartment_name,
                                "status": db.status,
                                "lifecycle_state": db.lifecycle_state,
                                "time_created": getattr(db, "time_created", None),
                            }

                            # Try to get extended database details
                            try:
                                db_detail = opsi_client.get_database_insight(db_id).data
                                self.cache_data["database_details"][db_id] = {
                                    "processor_count": getattr(db_detail, "processor_count", None),
                                    "entity_source": getattr(db_detail, "entity_source", None),
                                    "freeform_tags": getattr(db_detail, "freeform_tags", {}),
                                    "defined_tags": getattr(db_detail, "defined_tags", {}),
                                }
                            except Exception:
                                pass

                            db_count += 1
                            print(f"   ✅ {db.database_display_name or db.database_name} ({db.database_type})")
                except Exception as e:
                    print(f"   ⚠️  Error scanning compartment {compartment_id}: {e}")

            print(f"\n   Total databases: {db_count}")

            # ========================================================================
            # 6. Fetch Host Insights
            # ========================================================================
            print("\n6️⃣  Fetching host insights...")
            host_count = 0

            for compartment_id in all_compartments:
                try:
                    host_insights = list_all(
                        opsi_client.list_host_insights,
                        compartment_id=compartment_id,
                    )

                    for host in host_insights:
                        if host.lifecycle_state == "ACTIVE":
                            host_id = host.id
                            compartment_name = self.cache_data["compartments"].get(
                                compartment_id, {}
                            ).get("name", "Unknown")

                            self.cache_data["hosts"][host_id] = {
                                "id": host_id,
                                "host_name": getattr(host, "host_name", None),
                                "host_display_name": getattr(host, "host_display_name", None),
                                "host_type": getattr(host, "host_type", None),
                                "platform_type": getattr(host, "platform_type", None),
                                "compartment_id": compartment_id,
                                "compartment_name": compartment_name,
                                "status": host.status,
                                "lifecycle_state": host.lifecycle_state,
                            }

                            host_count += 1
                            print(f"   ✅ {host.host_display_name or host.host_name}")
                except Exception:
                    pass

            print(f"\n   Total hosts: {host_count}")

            # ========================================================================
            # 7. Calculate Comprehensive Statistics
            # ========================================================================
            print("\n7️⃣  Calculating statistics...")
            self._calculate_enhanced_statistics()

            # Calculate build duration
            end_time = datetime.utcnow()
            duration_seconds = (end_time - start_time).total_seconds()
            self.cache_data["metadata"]["build_duration_seconds"] = round(duration_seconds, 2)

            # Save to file
            self.save()

            print(f"\n✅ Enhanced cache built in {duration_seconds:.2f}s")
            print(f"✅ Cache saved to: {self.cache_file}")
            print()

            return {
                "cache_built": True,
                "last_updated": self.cache_data["metadata"]["last_updated"],
                "build_duration_seconds": duration_seconds,
                "statistics": self.cache_data["statistics"],
            }

        except Exception as e:
            # Re-raise to let caller handle
            raise e
        finally:
            # Restore original profile if we changed it
            if original_profile is not None:
                os.environ["OCI_CLI_PROFILE"] = original_profile
            elif "OCI_CLI_PROFILE" in os.environ and self.profile:
                 # If it wasn't set before but we set it, unset it? 
                 # Or just leave it as we found it (None)
                 if original_profile is None:
                     del os.environ["OCI_CLI_PROFILE"]

    def _calculate_enhanced_statistics(self):
        """Calculate comprehensive statistics from cached data."""
        stats = self.cache_data["statistics"]

        # Reset counts
        stats["total_databases"] = len(self.cache_data["databases"])
        stats["total_hosts"] = len(self.cache_data["hosts"])
        stats["databases_by_type"] = {}
        stats["databases_by_compartment"] = {}
        stats["databases_by_region"] = {}
        stats["databases_by_status"] = {}
        stats["databases_by_version"] = {}
        stats["databases_by_entity_source"] = {}

        # Count by various dimensions
        for db in self.cache_data["databases"].values():
            # By type
            db_type = db.get("database_type", "Unknown")
            stats["databases_by_type"][db_type] = stats["databases_by_type"].get(db_type, 0) + 1

            # By compartment
            compartment_name = db.get("compartment_name", "Unknown")
            stats["databases_by_compartment"][compartment_name] = (
                stats["databases_by_compartment"].get(compartment_name, 0) + 1
            )

            # By status
            status = db.get("status", "Unknown")
            stats["databases_by_status"][status] = stats["databases_by_status"].get(status, 0) + 1

            # By version
            version = db.get("database_version", "Unknown")
            stats["databases_by_version"][version] = stats["databases_by_version"].get(version, 0) + 1

            # By entity source
            entity_source = db.get("entity_source", "Unknown")
            stats["databases_by_entity_source"][entity_source] = (
                stats["databases_by_entity_source"].get(entity_source, 0) + 1
            )

    def get_tenancy_info(self) -> Dict[str, Any]:
        """Get cached tenancy information (zero tokens, instant)."""
        return {
            "tenancy": self.cache_data["tenancy"],
            "regions": list(self.cache_data["regions"].values()),
            "total_regions": len(self.cache_data["regions"]),
            "home_region": self.cache_data["tenancy"]["home_region"],
        }

    def get_compartment_tree(self, root_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Get compartment hierarchy as a tree structure.

        Args:
            root_id: Optional root compartment ID. If None, returns all roots.

        Returns:
            List of compartment tree nodes
        """
        def build_tree(parent_id):
            """Recursively build tree."""
            children = []
            for comp_id, comp in self.cache_data["compartments"].items():
                if comp.get("parent_id") == parent_id:
                    node = {
                        "id": comp_id,
                        "name": comp["name"],
                        "description": comp.get("description"),
                        "level": comp.get("level", 0),
                        "children": build_tree(comp_id)
                    }
                    children.append(node)
            return children

        if root_id:
            return build_tree(root_id)
        else:
            # Get all roots (compartments with no parent)
            roots = []
            for comp_id, comp in self.cache_data["compartments"].items():
                if comp.get("parent_id") is None:
                    node = {
                        "id": comp_id,
                        "name": comp["name"],
                        "description": comp.get("description"),
                        "level": 0,
                        "children": build_tree(comp_id)
                    }
                    roots.append(node)
            return roots

    def search_databases(
        self, name: Optional[str] = None, compartment: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Search databases in cache by name or compartment.

        Args:
            name: Database name filter (case-insensitive partial match)
            compartment: Compartment name filter (case-insensitive partial match)

        Returns:
            List of matching databases
        """
        results = []

        for db in self.cache_data["databases"].values():
            if name and name.lower() not in (
                db.get("database_name", "").lower()
                + db.get("database_display_name", "").lower()
            ):
                continue

            if compartment and compartment.lower() not in db.get("compartment_name", "").lower():
                continue

            results.append(db)

        return results

    def get_database(self, db_id: str) -> Optional[Dict[str, Any]]:
        """
        Get database by OCID.

        Args:
            db_id: Database insight OCID

        Returns:
            Database data or None if not found
        """
        return self.cache_data["databases"].get(db_id)

    def get_statistics(self) -> Dict[str, Any]:
        """
        Get cache statistics.

        Returns:
            Statistics dictionary
        """
        return {
            "metadata": self.cache_data["metadata"],
            "statistics": self.cache_data["statistics"],
        }

    def get_compartments(self) -> Dict[str, Any]:
        """
        Get all compartments in cache.

        Returns:
            Dictionary of compartments
        """
        return self.cache_data["compartments"]

    def is_cache_valid(self, max_age_hours: int = 24) -> bool:
        """
        Check if cache is valid based on age.

        Args:
            max_age_hours: Maximum cache age in hours

        Returns:
            bool: True if cache is valid, False if expired or missing
        """
        if not self.cache_file.exists():
            return False

        last_updated = self.cache_data["metadata"].get("last_updated")
        if not last_updated:
            return False

        try:
            cache_time = datetime.fromisoformat(last_updated.replace("Z", "+00:00"))
            age_hours = (datetime.utcnow().replace(tzinfo=cache_time.tzinfo) - cache_time).total_seconds() / 3600
            return age_hours < max_age_hours
        except Exception:
            return False


# Singleton instances map
_enhanced_cache_instances: Dict[str, EnhancedDatabaseCache] = {}


def get_enhanced_cache(profile: Optional[str] = None) -> EnhancedDatabaseCache:
    """
    Get singleton enhanced cache instance for a specific profile.
    
    Args:
        profile: OCI profile name. If None, uses current environment profile.
    """
    if profile is None:
        profile = os.getenv("OCI_CLI_PROFILE", "DEFAULT")
        
    global _enhanced_cache_instances
    if profile not in _enhanced_cache_instances:
        instance = EnhancedDatabaseCache(profile=profile)
        instance.load()
        _enhanced_cache_instances[profile] = instance
        
    return _enhanced_cache_instances[profile]
