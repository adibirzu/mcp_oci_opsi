"""FastMCP tools for cached database inventory - optimized for speed and minimal tokens."""

import os
from typing import Any, Dict, List, Optional

from ..cache import get_cache
from ..cache_enhanced import get_enhanced_cache
from ..config_enhanced import get_oci_config, list_all_profiles
from .oci_clients_enhanced import get_identity_client


def _sanitize_profile_env_key(profile: Optional[str]) -> str:
    """Convert profile name to a safe env suffix (alnum + underscore)."""
    if not profile:
        return ""
    return "".join(ch if ch.isalnum() else "_" for ch in profile.upper())


def _env_list(var: str) -> List[str]:
    """Parse a comma-separated env var into a trimmed list."""
    raw = os.getenv(var, "")
    return [item.strip() for item in raw.split(",") if item.strip()]


def _env_list_for_profile(base_var: str, profile: Optional[str]) -> List[str]:
    """Check profile-specific env (BASE_<PROFILE>) first, then BASE."""
    if profile:
        prof_key = _sanitize_profile_env_key(profile)
        prof_var = f"{base_var}_{prof_key}"
        prof_values = _env_list(prof_var)
        if prof_values:
            return prof_values
    return _env_list(base_var)


def _default_profile() -> Optional[str]:
    """Optional default profile hint from environment."""
    return os.getenv("MCP_OPSI_DEFAULT_PROFILE")


def build_database_cache(
    compartment_ids: Optional[List[str]],
    profile: Optional[str] = None,
    region: Optional[str] = None,
    task_progress: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Build cache by scanning all databases across compartments and their children.

    This scans the entire compartment hierarchy and stores results locally
    for instant retrieval. Cache is saved to ~/.mcp-oci/cache/opsi_cache.json

    Args:
        compartment_ids: List of root compartment OCIDs to scan recursively. If omitted,
                         the function will look for MCP_OPSI_COMPARTMENTS[_<PROFILE>].
        task_progress: Optional task progress tracking (used by MCP clients)

    Returns:
        Dictionary with build status and statistics
    """
    try:
        # Allow environment-driven defaults so this can be published without hardcoded data
        if not compartment_ids:
            env_compartments = _env_list_for_profile("MCP_OPSI_COMPARTMENTS", profile)
            compartment_ids = env_compartments

        if not compartment_ids:
            return {
                "success": False,
                "error": "compartment_ids required to build cache",
                "type": "ValueError",
                "hint": "Set MCP_OPSI_COMPARTMENTS or MCP_OPSI_COMPARTMENTS_<PROFILE> in the environment to avoid hardcoding OCIDs.",
            }

        cache = get_cache(profile=profile)
        if profile:
            result = cache.build_cache_with_profile(compartment_ids, profile=profile, region=region)
        else:
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


def get_cached_statistics(profile: Optional[str] = None, task_progress: Optional[str] = None) -> Dict[str, Any]:
    """
    Get cached database statistics - INSTANT, NO API CALLS.

    Returns fleet-wide statistics from local cache.
    If cache doesn't exist, prompts to build it first.

    Args:
        task_progress: Optional task progress tracking (used by MCP clients)

    Returns:
        Dictionary with statistics and metadata
    """
    try:
        cache = get_cache(profile=profile)

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
    name: Optional[str] = None,
    compartment: Optional[str] = None,
    limit: int = 20,
    profile: Optional[str] = None,
    task_progress: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Search databases in cache - INSTANT, NO API CALLS.

    Ultra-fast database search using local cache.
    Supports partial name matching and compartment filtering.

    Args:
        name: Database name filter (partial, case-insensitive)
        compartment: Compartment name filter (partial, case-insensitive)
        limit: Maximum results to return (default 20)
        task_progress: Optional task progress tracking (used by MCP clients)

    Returns:
        Dictionary with matching databases
    """
    try:
        cache = get_cache(profile=profile)

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


def get_cached_database(
    db_id: str,
    profile: Optional[str] = None,
    task_progress: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Get database details from cache by OCID - INSTANT, NO API CALLS.

    Args:
        db_id: Database insight OCID
        task_progress: Optional task progress tracking (used by MCP clients)

    Returns:
        Dictionary with database details
    """
    try:
        cache = get_cache(profile=profile)

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


def list_cached_compartments(profile: Optional[str] = None, task_progress: Optional[str] = None) -> Dict[str, Any]:
    """
    List all compartments in cache - INSTANT, NO API CALLS.

    Args:
        task_progress: Optional task progress tracking (used by MCP clients)

    Returns:
        Dictionary with all cached compartments
    """
    try:
        cache = get_cache(profile=profile)

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


def get_databases_by_compartment(
    compartment_name: str,
    profile: Optional[str] = None,
    task_progress: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Get all databases in a specific compartment - INSTANT, NO API CALLS.

    Token-efficient: Returns only essential info.

    Args:
        compartment_name: Compartment name (partial match, case-insensitive)
        task_progress: Optional task progress tracking (used by MCP clients)

    Returns:
        Dictionary with databases grouped by compartment
    """
    try:
        cache = get_cache(profile=profile)

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


def get_fleet_summary(profile: Optional[str] = None, task_progress: Optional[str] = None) -> Dict[str, Any]:
    """
    Get concise fleet summary - INSTANT, NO API CALLS, MINIMAL TOKENS.

    Ultra-efficient: Returns only key statistics.
    Perfect for quick overview questions.

    Args:
        task_progress: Optional task progress tracking (used by MCP clients)

    Returns:
        Dictionary with concise fleet summary
    """
    try:
        cache = get_cache(profile=profile)

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


def refresh_cache_if_needed(
    max_age_hours: int = 24,
    profile: Optional[str] = None,
    task_progress: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Check cache age and refresh if expired.

    Args:
        max_age_hours: Maximum cache age in hours before refresh
        task_progress: Optional task progress tracking (used by MCP clients)

    Returns:
        Dictionary with refresh status
    """
    try:
        cache = get_cache(profile=profile)

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


def refresh_all_caches(
    profiles: Optional[List[str]] = None,
    compartment_ids: Optional[List[str]] = None,
    max_age_hours: int = 24,
    task_progress: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Refresh caches for all (or selected) profiles. If cache is valid, it is left unchanged.
    If expired/missing, it will build using the tenancy root (or supplied compartments).
    """
    try:
        # Prefer explicit list, then environment hint, then all profiles
        env_profiles = _env_list("MCP_OPSI_PROFILES")
        profile_list = profiles or env_profiles or list_all_profiles()
        summary: List[Dict[str, Any]] = []

        for prof in profile_list:
            try:
                cache = get_cache(profile=prof)
                cache.load()
                if cache.is_cache_valid(max_age_hours):
                    stats = cache.get_statistics()
                    summary.append({
                        "profile": prof,
                        "cache_valid": True,
                        "last_updated": stats["metadata"].get("last_updated"),
                        "total_databases": stats["statistics"].get("total_databases", 0),
                    })
                    continue

                # Build cache for this profile across subscribed regions
                config = get_oci_config(profile=prof)
                tenancy_root = config.get("tenancy")

                # Allow environment-driven compartment scoping before falling back to tenancy
                env_compartments = _env_list_for_profile("MCP_OPSI_COMPARTMENTS", prof)
                targets = compartment_ids or env_compartments or ([tenancy_root] if tenancy_root else [])
                if not targets:
                    summary.append({
                        "profile": prof,
                        "cache_valid": False,
                        "error": "No compartment_ids provided and tenancy not found",
                        "hint": "Set MCP_OPSI_COMPARTMENTS or MCP_OPSI_COMPARTMENTS_<PROFILE> to scope discovery without hardcoding in code."
                    })
                    continue

                # Regions: environment hint first, then discover
                regions: List[str] = _env_list_for_profile("MCP_OPSI_REGIONS", prof)
                if not regions:
                    try:
                        identity_client = get_identity_client(profile=prof)
                        subs = identity_client.list_region_subscriptions(config["tenancy"]).data
                        regions = [sub.region_name for sub in subs if getattr(sub, "status", "READY") == "READY"]
                    except Exception as reg_err:
                        summary.append({
                            "profile": prof,
                            "cache_valid": False,
                            "error": f"Region discovery failed: {reg_err}",
                            "type": type(reg_err).__name__,
                        })
                        continue

                if not regions:
                    summary.append({
                        "profile": prof,
                        "cache_valid": False,
                        "error": "No subscribed regions found"
                    })
                    continue

                built_any = False
                region_results = []
                for rg in regions:
                    try:
                        result = cache.build_cache_with_profile(targets, profile=prof, region=rg)
                        region_results.append({
                            "region": rg,
                            "last_updated": result.get("last_updated"),
                            "compartments_scanned": result.get("compartments_scanned"),
                            "statistics": result.get("statistics"),
                        })
                        built_any = True
                    except Exception as inner:
                        region_results.append({
                            "region": rg,
                            "error": str(inner),
                            "type": type(inner).__name__,
                        })
                    # Be polite between regions
                    import time
                    time.sleep(0.2)

                # Also build Enhanced Cache (v2) for this profile (using home region/tenancy root)
                try:
                    enhanced_cache = get_enhanced_cache(profile=prof)
                    enhanced_result = enhanced_cache.build_enhanced_cache(targets)
                    region_results.append({
                        "type": "enhanced_cache",
                        "success": True,
                        "last_updated": enhanced_result.get("last_updated"),
                        "statistics": enhanced_result.get("statistics")
                    })
                except Exception as enh_err:
                     region_results.append({
                        "type": "enhanced_cache",
                        "success": False,
                        "error": str(enh_err)
                    })

                summary.append({
                    "profile": prof,
                    "cache_valid": built_any,
                    "regions": region_results,
                })
            except Exception as inner:
                summary.append({
                    "profile": prof,
                    "cache_valid": False,
                    "error": str(inner),
                    "type": type(inner).__name__,
                })

        return {
            "success": True,
            "profiles_processed": len(profile_list),
            "summary": summary,
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "type": type(e).__name__,
        }
