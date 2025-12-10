"""Caching infrastructure for fast database inventory lookups."""

import json
import os
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

import oci

from .config import get_oci_config
from .oci_clients import get_opsi_client, list_all


class DatabaseCache:
    """Fast local cache for database inventory across compartments."""

    def __init__(self, cache_file: Optional[str] = None):
        """
        Initialize cache with custom or default location.

        Args:
            cache_file: Optional path to cache file. Defaults to ~/.mcp_oci_opsi_cache.json
        """
        if cache_file:
            self.cache_file = Path(cache_file)
        else:
            self.cache_file = Path.home() / ".mcp_oci_opsi_cache.json"

        self.cache_data: Dict[str, Any] = {
            "metadata": {
                "last_updated": None,
                "profile": None,
                "region": None,
            },
            "compartments": {},
            "databases": {},
            "hosts": {},
            "statistics": {
                "total_databases": 0,
                "total_hosts": 0,
                "databases_by_type": {},
                "databases_by_compartment": {},
                "databases_by_status": {},
            },
        }

    def load(self) -> bool:
        """
        Load cache from file.

        Returns:
            bool: True if cache loaded successfully, False otherwise
        """
        try:
            if self.cache_file.exists():
                with open(self.cache_file, "r") as f:
                    self.cache_data = json.load(f)
                return True
            return False
        except Exception:
            return False

    def save(self) -> bool:
        """
        Save cache to file.

        Returns:
            bool: True if saved successfully, False otherwise
        """
        try:
            with open(self.cache_file, "w") as f:
                json.dump(self.cache_data, f, indent=2)
            return True
        except Exception:
            return False

    def build_cache(self, compartment_ids: List[str]) -> Dict[str, Any]:
        """
        Build cache by scanning all specified compartments and their children.

        Args:
            compartment_ids: List of root compartment OCIDs to scan

        Returns:
            Dict with build results and statistics
        """
        config = get_oci_config()
        opsi_client = get_opsi_client()
        identity_client = oci.identity.IdentityClient(config)

        # Update metadata
        self.cache_data["metadata"]["last_updated"] = datetime.utcnow().isoformat() + "Z"
        self.cache_data["metadata"]["profile"] = os.getenv("OCI_CLI_PROFILE", "DEFAULT")
        self.cache_data["metadata"]["region"] = config.get("region")

        # Clear existing data
        self.cache_data["compartments"] = {}
        self.cache_data["databases"] = {}
        self.cache_data["hosts"] = {}

        # Scan each compartment and its children
        all_compartments = set()
        for root_compartment_id in compartment_ids:
            # Get the root compartment
            all_compartments.add(root_compartment_id)

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
                        # Store compartment info
                        self.cache_data["compartments"][comp.id] = {
                            "id": comp.id,
                            "name": comp.name,
                            "description": comp.description,
                            "parent_id": root_compartment_id,
                        }
            except Exception:
                pass

        # Scan database insights in all compartments
        for compartment_id in all_compartments:
            try:
                db_insights = list_all(
                    opsi_client.list_database_insights,
                    compartment_id=compartment_id,
                )

                for db in db_insights:
                    if db.lifecycle_state == "ACTIVE":
                        db_id = db.id
                        self.cache_data["databases"][db_id] = {
                            "id": db_id,
                            "database_id": getattr(db, "database_id", None),
                            "database_name": getattr(db, "database_name", None),
                            "database_display_name": getattr(db, "database_display_name", None),
                            "database_type": getattr(db, "database_type", None),
                            "database_version": getattr(db, "database_version", None),
                            "entity_source": getattr(db, "entity_source", None),
                            "compartment_id": compartment_id,
                            "compartment_name": self.cache_data["compartments"].get(
                                compartment_id, {}
                            ).get("name", "Unknown"),
                            "status": db.status,
                            "lifecycle_state": db.lifecycle_state,
                        }
            except Exception:
                pass

        # Scan host insights in all compartments
        for compartment_id in all_compartments:
            try:
                host_insights = list_all(
                    opsi_client.list_host_insights,
                    compartment_id=compartment_id,
                )

                for host in host_insights:
                    if host.lifecycle_state == "ACTIVE":
                        host_id = host.id
                        self.cache_data["hosts"][host_id] = {
                            "id": host_id,
                            "host_name": getattr(host, "host_name", None),
                            "host_display_name": getattr(host, "host_display_name", None),
                            "host_type": getattr(host, "host_type", None),
                            "platform_type": getattr(host, "platform_type", None),
                            "compartment_id": compartment_id,
                            "compartment_name": self.cache_data["compartments"].get(
                                compartment_id, {}
                            ).get("name", "Unknown"),
                            "status": host.status,
                            "lifecycle_state": host.lifecycle_state,
                        }
            except Exception:
                pass

        # Calculate statistics
        self._calculate_statistics()

        # Save to file
        self.save()

        return {
            "cache_built": True,
            "last_updated": self.cache_data["metadata"]["last_updated"],
            "compartments_scanned": len(all_compartments),
            "statistics": self.cache_data["statistics"],
        }

    def _calculate_statistics(self):
        """Calculate statistics from cached data."""
        stats = self.cache_data["statistics"]

        # Reset counts
        stats["total_databases"] = len(self.cache_data["databases"])
        stats["total_hosts"] = len(self.cache_data["hosts"])
        stats["databases_by_type"] = {}
        stats["databases_by_compartment"] = {}
        stats["databases_by_status"] = {}

        # Count by type
        for db in self.cache_data["databases"].values():
            db_type = db.get("database_type", "Unknown")
            stats["databases_by_type"][db_type] = stats["databases_by_type"].get(db_type, 0) + 1

            compartment_name = db.get("compartment_name", "Unknown")
            stats["databases_by_compartment"][compartment_name] = (
                stats["databases_by_compartment"].get(compartment_name, 0) + 1
            )

            status = db.get("status", "Unknown")
            stats["databases_by_status"][status] = stats["databases_by_status"].get(status, 0) + 1

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

    def get_database_region(self, database_name_or_insight_id: str) -> Optional[str]:
        """
        Get the region for a database from cache.

        This method supports automatic region detection for multi-region deployments.
        It searches the cache by either database name or database insight OCID and
        returns the region where that database is located.

        Args:
            database_name_or_insight_id: Database name (e.g., "PayDB") or
                                        database insight OCID (e.g., "ocid1.opsidatabaseinsight...")

        Returns:
            Region name (e.g., "us-phoenix-1") or None if database not found or no region info

        Example:
            >>> cache = DatabaseCache()
            >>> cache.load()
            >>> region = cache.get_database_region("PayDB")
            >>> print(region)  # Output: "us-phoenix-1"
        """
        # Search by OCID first (exact match)
        if database_name_or_insight_id in self.cache_data["databases"]:
            db_info = self.cache_data["databases"][database_name_or_insight_id]
            return db_info.get("region")

        # Search by name (case-insensitive)
        for db_id, db_info in self.cache_data["databases"].items():
            if isinstance(db_info, dict):
                db_name = db_info.get("database_name", "")
                db_display_name = db_info.get("database_display_name", "")

                if (db_name and db_name.lower() == database_name_or_insight_id.lower()) or \
                   (db_display_name and db_display_name.lower() == database_name_or_insight_id.lower()):
                    return db_info.get("region")

        return None

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
            age_hours = (datetime.now(cache_time.tzinfo) - cache_time).total_seconds() / 3600
            return age_hours < max_age_hours
        except Exception:
            return False

    def is_valid(self, max_age_hours: int = 24) -> bool:
        """
        Check if cache is valid (convenience wrapper for is_cache_valid).

        Args:
            max_age_hours: Maximum cache age in hours

        Returns:
            bool: True if cache is valid, False if expired or missing
        """
        return self.is_cache_valid(max_age_hours)

    def build_cache_with_profile(
        self,
        compartment_ids: List[str],
        profile: Optional[str] = None,
        region: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Build cache with specific OCI CLI profile for multi-tenancy support.

        This method allows building cache for different tenancies by specifying
        the OCI CLI profile name.

        Args:
            compartment_ids: List of root compartment OCIDs to scan
            profile: OCI CLI profile name (e.g., "tenancy1", "tenancy2")
                    If None, uses current/default profile

        Returns:
            Dict with build results and statistics including:
            - cache_built: Boolean success indicator
            - profile_used: Profile name that was used
            - tenancy_name: Name of the tenancy
            - last_updated: Timestamp of cache build
            - compartments_scanned: Number of compartments scanned
            - statistics: Database and host counts

        Example:
            >>> cache = DatabaseCache()
            >>> # Build cache for tenancy1
            >>> result = cache.build_cache_with_profile(
            ...     compartment_ids=["ocid1.compartment.oc1..example"],
            ...     profile="tenancy1"
            ... )
            >>> print(f"Built cache for {result['tenancy_name']}")
        """
        # Set profile/region if specified
        old_profile = None
        old_region = None
        if profile:
            old_profile = os.environ.get("OCI_CLI_PROFILE")
            os.environ["OCI_CLI_PROFILE"] = profile
        if region:
            old_region = os.environ.get("OCI_REGION")
            os.environ["OCI_REGION"] = region

        try:
            config = get_oci_config()
            opsi_client = get_opsi_client(region=region)
            identity_client = oci.identity.IdentityClient(config)

            # Get tenancy information
            tenancy = identity_client.get_tenancy(config["tenancy"]).data

            # Update metadata
            self.cache_data["metadata"]["last_updated"] = datetime.utcnow().isoformat() + "Z"
            self.cache_data["metadata"]["profile"] = profile or os.getenv("OCI_CLI_PROFILE", "DEFAULT")
            self.cache_data["metadata"]["region"] = region or config.get("region")
            self.cache_data["metadata"]["tenancy_name"] = tenancy.name
            self.cache_data["metadata"]["tenancy_id"] = config["tenancy"]

            # Clear existing data
            self.cache_data["compartments"] = {}
            self.cache_data["databases"] = {}
            self.cache_data["hosts"] = {}

            # Scan each compartment and its children
            all_compartments = set()
            for root_compartment_id in compartment_ids:
                # Get the root compartment
                all_compartments.add(root_compartment_id)

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
                            # Store compartment info
                            self.cache_data["compartments"][comp.id] = {
                                "id": comp.id,
                                "name": comp.name,
                                "description": comp.description,
                                "parent_id": root_compartment_id,
                            }
                except Exception:
                    pass

            # Scan database insights in all compartments
            for compartment_id in all_compartments:
                try:
                    db_insights = list_all(
                        opsi_client.list_database_insights,
                        compartment_id=compartment_id,
                    )

                    for db in db_insights:
                        if db.lifecycle_state == "ACTIVE":
                            db_id = db.id
                            self.cache_data["databases"][db_id] = {
                                "id": db_id,
                                "database_id": getattr(db, "database_id", None),
                                "database_name": getattr(db, "database_name", None),
                                "database_display_name": getattr(db, "database_display_name", None),
                                "database_type": getattr(db, "database_type", None),
                                "database_version": getattr(db, "database_version", None),
                                "entity_source": getattr(db, "entity_source", None),
                                "compartment_id": compartment_id,
                                "compartment_name": self.cache_data["compartments"].get(
                                    compartment_id, {}
                                ).get("name", "Unknown"),
                                "status": db.status,
                                "lifecycle_state": db.lifecycle_state,
                            }
                except Exception:
                    pass

            # Scan host insights in all compartments
            for compartment_id in all_compartments:
                try:
                    host_insights = list_all(
                        opsi_client.list_host_insights,
                        compartment_id=compartment_id,
                    )

                    for host in host_insights:
                        if host.lifecycle_state == "ACTIVE":
                            host_id = host.id
                            self.cache_data["hosts"][host_id] = {
                                "id": host_id,
                                "host_name": getattr(host, "host_name", None),
                                "host_display_name": getattr(host, "host_display_name", None),
                                "host_type": getattr(host, "host_type", None),
                                "platform_type": getattr(host, "platform_type", None),
                                "entity_source": getattr(host, "entity_source", None),
                                "compartment_id": compartment_id,
                                "compartment_name": self.cache_data["compartments"].get(
                                    compartment_id, {}
                                ).get("name", "Unknown"),
                                "status": host.status,
                                "lifecycle_state": host.lifecycle_state,
                            }
                except Exception:
                    pass

            # Calculate statistics
            self._calculate_statistics()

            # Save to file
            self.save()

            return {
                "cache_built": True,
                "profile_used": profile or "DEFAULT",
                "tenancy_name": tenancy.name,
                "tenancy_id": config["tenancy"],
                "region": config.get("region"),
                "last_updated": self.cache_data["metadata"]["last_updated"],
                "compartments_scanned": len(all_compartments),
                "statistics": self.cache_data["statistics"],
            }

        finally:
            # Restore original profile
            if profile is not None:
                if old_profile:
                    os.environ["OCI_CLI_PROFILE"] = old_profile
                else:
                    os.environ.pop("OCI_CLI_PROFILE", None)
            if region is not None:
                if old_region:
                    os.environ["OCI_REGION"] = old_region
                else:
                    os.environ.pop("OCI_REGION", None)


# Global cache instances per profile (default + others)
_cache_map: Dict[str, DatabaseCache] = {}


def _cache_key(profile: Optional[str]) -> str:
    return (profile or os.getenv("OCI_CLI_PROFILE") or "DEFAULT").strip()


def get_cache(profile: Optional[str] = None) -> DatabaseCache:
    """
    Get (or create) a cache instance for the given profile. Each profile uses its
    own cache file to keep tenant data isolated.

    Args:
        profile: Optional OCI profile name. Defaults to env/DEFAULT.

    Returns:
        DatabaseCache instance scoped to the profile.
    """
    key = _cache_key(profile)
    if key not in _cache_map:
        cache_file = Path.home() / f".mcp_oci_opsi_cache_{key}.json"
        _cache_map[key] = DatabaseCache(cache_file=cache_file)
    return _cache_map[key]
