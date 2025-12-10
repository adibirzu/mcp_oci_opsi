"""
Database Discovery Skill - Fast fleet enumeration using cached data
Tier 1 (Cache-based, < 100ms)

This skill provides fast database discovery using cached data, following
the skillz pattern for composable AI agent skills.

Reference: https://github.com/intellectronica/skillz
"""

from typing import List, Dict, Optional
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)


@dataclass
class DatabaseInfo:
    """Normalized database information"""
    ocid: str
    name: str
    db_type: str  # 'adb', 'base', 'exadata', etc.
    lifecycle_state: str
    compartment_id: str
    region: str
    cpu_count: Optional[int] = None
    storage_gb: Optional[float] = None


class DatabaseDiscoverySkill:
    """
    Skill: Fast database fleet discovery
    
    Uses cached data to provide instant database listings.
    Falls back to API calls only when cache is stale.
    
    Tier: 1 (Cache-based, < 100ms)
    Category: Discovery
    """
    
    def __init__(self, cache_manager):
        """
        Initialize the database discovery skill
        
        Args:
            cache_manager: Cache manager instance for accessing cached data
        """
        self.cache = cache_manager
        self.tier = 1  # Cache-based operation
        self.category = "discovery"
        self.name = "database_discovery"
        self.description = "Fast database fleet discovery using cached data"
    
    def discover_databases(
        self, 
        compartment_id: Optional[str] = None,
        region: Optional[str] = None,
        db_type: Optional[str] = None
    ) -> List[DatabaseInfo]:
        """
        Discover databases using cached data
        
        Args:
            compartment_id: Filter by compartment (None = all)
            region: Filter by region (None = all)
            db_type: Filter by type ('adb', 'base', etc.)
        
        Returns:
            List of DatabaseInfo objects
        """
        logger.info(
            f"Discovering databases: compartment={compartment_id}, "
            f"region={region}, db_type={db_type}"
        )
        
        # Check cache first
        cached = self.cache.get_cached_databases()
        
        if not cached or self.cache.is_stale():
            logger.warning("Cache miss or stale - triggering refresh")
            # Cache miss or stale - trigger refresh
            self.cache.refresh_databases()
            cached = self.cache.get_cached_databases()
        
        # Filter results
        results = cached
        if compartment_id:
            results = [db for db in results if db.compartment_id == compartment_id]
        if region:
            results = [db for db in results if db.region == region]
        if db_type:
            results = [db for db in results if db.db_type == db_type]
        
        logger.info(f"Found {len(results)} databases matching criteria")
        return results
    
    def get_database_by_name(self, name: str) -> Optional[DatabaseInfo]:
        """
        Find database by name (case-insensitive)
        
        Args:
            name: Database name to search for
        
        Returns:
            DatabaseInfo object if found, None otherwise
        """
        databases = self.discover_databases()
        name_lower = name.lower()
        
        for db in databases:
            if db.name.lower() == name_lower:
                logger.info(f"Found database: {db.name} ({db.ocid})")
                return db
        
        logger.warning(f"Database not found: {name}")
        return None
    
    def get_database_by_ocid(self, ocid: str) -> Optional[DatabaseInfo]:
        """
        Find database by OCID
        
        Args:
            ocid: Database OCID to search for
        
        Returns:
            DatabaseInfo object if found, None otherwise
        """
        databases = self.discover_databases()
        
        for db in databases:
            if db.ocid == ocid:
                logger.info(f"Found database: {db.name} ({db.ocid})")
                return db
        
        logger.warning(f"Database not found: {ocid}")
        return None
    
    def get_fleet_summary(self) -> Dict:
        """
        Get high-level fleet statistics
        
        Returns:
            Dict containing fleet statistics:
                - total: Total database count
                - by_type: Count by database type
                - by_state: Count by lifecycle state
                - by_region: Count by region
                - total_cpu: Total CPU count
                - total_storage_gb: Total storage in GB
        """
        databases = self.discover_databases()
        
        summary = {
            "total": len(databases),
            "by_type": self._count_by(databases, "db_type"),
            "by_state": self._count_by(databases, "lifecycle_state"),
            "by_region": self._count_by(databases, "region"),
            "total_cpu": sum(db.cpu_count or 0 for db in databases),
            "total_storage_gb": sum(db.storage_gb or 0 for db in databases)
        }
        
        logger.info(f"Fleet summary: {summary['total']} databases")
        return summary
    
    def search_databases(self, query: str) -> List[DatabaseInfo]:
        """
        Search databases by name or OCID (partial match)
        
        Args:
            query: Search query string
        
        Returns:
            List of matching DatabaseInfo objects
        """
        databases = self.discover_databases()
        query_lower = query.lower()
        
        results = [
            db for db in databases
            if query_lower in db.name.lower() or query_lower in db.ocid.lower()
        ]
        
        logger.info(f"Search '{query}' found {len(results)} databases")
        return results
    
    def get_databases_by_compartment(self, compartment_id: str) -> List[DatabaseInfo]:
        """
        Get all databases in a compartment
        
        Args:
            compartment_id: Compartment OCID
        
        Returns:
            List of DatabaseInfo objects
        """
        return self.discover_databases(compartment_id=compartment_id)
    
    def get_databases_by_region(self, region: str) -> List[DatabaseInfo]:
        """
        Get all databases in a region
        
        Args:
            region: Region name (e.g., 'us-ashburn-1')
        
        Returns:
            List of DatabaseInfo objects
        """
        return self.discover_databases(region=region)
    
    def get_databases_by_type(self, db_type: str) -> List[DatabaseInfo]:
        """
        Get all databases of a specific type
        
        Args:
            db_type: Database type ('adb', 'base', 'exadata', etc.)
        
        Returns:
            List of DatabaseInfo objects
        """
        return self.discover_databases(db_type=db_type)
    
    def _count_by(self, databases: List[DatabaseInfo], field: str) -> Dict[str, int]:
        """
        Helper to count databases by field
        
        Args:
            databases: List of DatabaseInfo objects
            field: Field name to count by
        
        Returns:
            Dict mapping field values to counts
        """
        counts = {}
        for db in databases:
            value = getattr(db, field)
            counts[value] = counts.get(value, 0) + 1
        return counts
    
    def get_metadata(self) -> Dict:
        """
        Get skill metadata
        
        Returns:
            Dict containing skill metadata
        """
        return {
            "name": self.name,
            "description": self.description,
            "tier": self.tier,
            "category": self.category,
            "version": "1.0.0",
            "author": "Oracle DB Team"
        }
