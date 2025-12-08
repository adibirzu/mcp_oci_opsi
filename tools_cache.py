"""FastMCP tools for cached database inventory - optimized for speed and minimal tokens."""

from typing import Any, Dict, List, Optional

from .cache import get_cache


def build_database_cache(compartment_ids: List[str]) -> Dict[str, Any]:
    """
    Build cache by scanning all databases across compartments and their children.

    This scans the entire compartment hierarchy and stores results locally
    for instant retrieval. Cache is saved to ~/.mcp_oci_opsi_cache.json

    Args:
        compartment_ids: List of root compartment OCIDs to scan recursively

    Returns:
        Dictionary with build status and statistics
    """
    try:
        cache = get_cache()
        result = cache.build_cache(compartment_ids)
        return {
            "success": True,
            "message": "Cache built successfully",
            **result,
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "type": type(e).__name__,
        }


def get_cached_statistics() -> Dict[str, Any]:
    """
    Get cached database statistics - INSTANT, NO API CALLS.

    Returns fleet-wide statistics from local cache.
    If cache doesn't exist, prompts to build it first.

    Returns:
        Dictionary with statistics and metadata
    """
    try:
        cache = get_cache()

        # Try to load cache
        if not cache.load():
            return {
                "cache_exists": False,
                "message": "Cache not found. Build cache first using build_database_cache()",
            }

        stats = cache.get_statistics()

        return {
            "cache_exists": True,
            "cache_valid": cache.is_cache_valid(24),
            **stats,
        }
    except Exception as e:
        return {
            "error": str(e),
            "type": type(e).__name__,
        }


def search_cached_databases(
    name: Optional[str] = None, compartment: Optional[str] = None, limit: int = 20
) -> Dict[str, Any]:
    """
    Search databases in cache - INSTANT, NO API CALLS.

    Ultra-fast database search using local cache.
    Supports partial name matching and compartment filtering.

    Args:
        name: Database name filter (partial, case-insensitive)
        compartment: Compartment name filter (partial, case-insensitive)
        limit: Maximum results to return (default 20)

    Returns:
        Dictionary with matching databases
    """
    try:
        cache = get_cache()

        if not cache.load():
            return {
                "cache_exists": False,
                "message": "Cache not found. Build cache first using build_database_cache()",
            }

        results = cache.search_databases(name=name, compartment=compartment)

        # Limit results
        limited_results = results[:limit]

        return {
            "cache_exists": True,
            "search_criteria": {
                "name": name,
                "compartment": compartment,
            },
            "total_matches": len(results),
            "returned_count": len(limited_results),
            "databases": limited_results,
        }
    except Exception as e:
        return {
            "error": str(e),
            "type": type(e).__name__,
        }


def get_cached_database(db_id: str) -> Dict[str, Any]:
    """
    Get database details from cache by OCID - INSTANT, NO API CALLS.

    Args:
        db_id: Database insight OCID

    Returns:
        Dictionary with database details
    """
    try:
        cache = get_cache()

        if not cache.load():
            return {
                "cache_exists": False,
                "message": "Cache not found. Build cache first using build_database_cache()",
            }

        db = cache.get_database(db_id)

        if not db:
            return {
                "found": False,
                "database_id": db_id,
                "message": "Database not found in cache",
            }

        return {
            "found": True,
            "database": db,
        }
    except Exception as e:
        return {
            "error": str(e),
            "type": type(e).__name__,
        }


def list_cached_compartments() -> Dict[str, Any]:
    """
    List all compartments in cache - INSTANT, NO API CALLS.

    Returns:
        Dictionary with all cached compartments
    """
    try:
        cache = get_cache()

        if not cache.load():
            return {
                "cache_exists": False,
                "message": "Cache not found. Build cache first using build_database_cache()",
            }

        compartments = cache.get_compartments()

        return {
            "cache_exists": True,
            "count": len(compartments),
            "compartments": list(compartments.values()),
        }
    except Exception as e:
        return {
            "error": str(e),
            "type": type(e).__name__,
        }


def get_databases_by_compartment(compartment_name: str) -> Dict[str, Any]:
    """
    Get all databases in a specific compartment - INSTANT, NO API CALLS.

    Token-efficient: Returns only essential info.

    Args:
        compartment_name: Compartment name (partial match, case-insensitive)

    Returns:
        Dictionary with databases grouped by compartment
    """
    try:
        cache = get_cache()

        if not cache.load():
            return {
                "cache_exists": False,
                "message": "Cache not found. Build cache first using build_database_cache()",
            }

        # Search by compartment
        results = cache.search_databases(compartment=compartment_name)

        # Group by compartment
        by_compartment: Dict[str, List[Dict[str, Any]]] = {}
        for db in results:
            comp_name = db.get("compartment_name", "Unknown")
            if comp_name not in by_compartment:
                by_compartment[comp_name] = []

            # Add minimal info
            by_compartment[comp_name].append(
                {
                    "name": db.get("database_display_name") or db.get("database_name"),
                    "type": db.get("database_type"),
                    "version": db.get("database_version"),
                    "status": db.get("status"),
                    "id": db.get("id"),
                }
            )

        return {
            "cache_exists": True,
            "search_term": compartment_name,
            "total_databases": len(results),
            "compartments": by_compartment,
        }
    except Exception as e:
        return {
            "error": str(e),
            "type": type(e).__name__,
        }


def get_fleet_summary() -> Dict[str, Any]:
    """
    Get concise fleet summary - INSTANT, NO API CALLS, MINIMAL TOKENS.

    Ultra-efficient: Returns only key statistics.
    Perfect for quick overview questions.

    Returns:
        Dictionary with concise fleet summary
    """
    try:
        cache = get_cache()

        if not cache.load():
            return {
                "cache_exists": False,
                "message": "Cache not found. Build cache first using build_database_cache()",
            }

        stats = cache.get_statistics()
        metadata = stats.get("metadata", {})
        statistics = stats.get("statistics", {})

        # Return minimal, token-efficient response
        return {
            "profile": metadata.get("profile"),
            "region": metadata.get("region"),
            "last_updated": metadata.get("last_updated"),
            "databases": statistics.get("total_databases", 0),
            "hosts": statistics.get("total_hosts", 0),
            "by_compartment": statistics.get("databases_by_compartment", {}),
            "by_type": statistics.get("databases_by_type", {}),
            "by_status": statistics.get("databases_by_status", {}),
        }
    except Exception as e:
        return {
            "error": str(e),
            "type": type(e).__name__,
        }


def refresh_cache_if_needed(max_age_hours: int = 24) -> Dict[str, Any]:
    """
    Check cache age and refresh if expired.

    Args:
        max_age_hours: Maximum cache age in hours before refresh

    Returns:
        Dictionary with refresh status
    """
    try:
        cache = get_cache()

        # Try to load existing cache
        cache.load()

        if cache.is_cache_valid(max_age_hours):
            stats = cache.get_statistics()
            return {
                "refresh_needed": False,
                "message": "Cache is still valid",
                "last_updated": stats["metadata"]["last_updated"],
                "statistics": stats["statistics"],
            }

        # Cache expired or doesn't exist - needs rebuild
        return {
            "refresh_needed": True,
            "message": f"Cache is older than {max_age_hours} hours or doesn't exist",
            "action": "Call build_database_cache() to refresh",
        }
    except Exception as e:
        return {
            "error": str(e),
            "type": type(e).__name__,
        }
