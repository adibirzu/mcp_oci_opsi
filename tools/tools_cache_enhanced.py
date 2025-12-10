from __future__ import annotations

import os
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from ..cache_enhanced import get_enhanced_cache, EnhancedDatabaseCache
from ..config_enhanced import get_oci_config


def _is_enhanced_cache_stale(cache: EnhancedDatabaseCache, max_age_hours: int) -> bool:
    try:
        meta = cache.cache_data.get("metadata", {})
        ts = meta.get("last_updated")
        if not ts:
            return True
        cache_time = datetime.fromisoformat(ts.replace("Z", "+00:00")).astimezone(timezone.utc)
        now_utc = datetime.now(timezone.utc)
        return (now_utc - cache_time).total_seconds() / 3600.0 > max_age_hours
    except Exception:
        return True


def ensure_enhanced_cache(
    profile: Optional[str] = None,
    max_age_hours: int = 24,
    compartments: Optional[List[str]] = None,
) -> Dict[str, Any]:
    """
    Ensure the enhanced cache exists and is not stale. Builds it lazily if needed.
    """
    try:
        cache = get_enhanced_cache(profile=profile)
        cache.load()

        stale = _is_enhanced_cache_stale(cache, max_age_hours)
        empty_regions = not cache.cache_data.get("regions")
        empty_comps = not cache.cache_data.get("compartments")

        if stale or empty_regions or empty_comps:
            cfg = get_oci_config(profile=profile)
            tenancy = cfg.get("tenancy")
            targets = compartments or ([tenancy] if tenancy else [])
            if not targets:
                return {
                    "success": False,
                    "error": "Unable to determine root compartment (tenancy) for enhanced cache build",
                    "profile": profile,
                }

            result = cache.build_enhanced_cache(targets)
            return {
                "success": True,
                "rebuilt": True,
                "profile": profile or os.getenv("OCI_CLI_PROFILE", "DEFAULT"),
                "last_updated": result.get("last_updated"),
                "statistics": result.get("statistics"),
            }

        # Cache OK
        return {
            "success": True,
            "rebuilt": False,
            "profile": profile or os.getenv("OCI_CLI_PROFILE", "DEFAULT"),
            "last_updated": cache.cache_data.get("metadata", {}).get("last_updated"),
            "statistics": cache.cache_data.get("statistics", {}),
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "type": type(e).__name__,
            "profile": profile,
        }


def list_cached_regions(profile: Optional[str] = None, max_age_hours: int = 24) -> Dict[str, Any]:
    """
    Return regions from the enhanced cache. Builds the cache on-demand if empty/stale.
    """
    try:
        cache = get_enhanced_cache(profile=profile)
        cache.load()

        # Lazy build if no regions
        if not cache.cache_data.get("regions"):
            ensure = ensure_enhanced_cache(profile=profile, max_age_hours=max_age_hours)
            if not ensure.get("success"):
                return {
                    "success": False,
                    "error": ensure.get("error", "Failed to ensure enhanced cache"),
                    "profile": profile,
                }

        regions_map = cache.cache_data.get("regions", {})
        regions = list(regions_map.values())

        return {
            "success": True,
            "profile": profile or os.getenv("OCI_CLI_PROFILE", "DEFAULT"),
            "total": len(regions),
            "regions": regions,
        }
    except Exception as e:
        return {"success": False, "error": str(e), "type": type(e).__name__, "profile": profile}


def get_compartment_tree(
    profile: Optional[str] = None,
    root_id: Optional[str] = None,
    max_age_hours: int = 24,
) -> Dict[str, Any]:
    """
    Return the compartment tree from the enhanced cache. Builds on-demand if empty/stale.
    """
    try:
        cache = get_enhanced_cache(profile=profile)
        cache.load()

        # Lazy build if no compartments
        if not cache.cache_data.get("compartments"):
            ensure = ensure_enhanced_cache(profile=profile, max_age_hours=max_age_hours)
            if not ensure.get("success"):
                return {
                    "success": False,
                    "error": ensure.get("error", "Failed to ensure enhanced cache"),
                    "profile": profile,
                }

        tree = cache.get_compartment_tree(root_id=root_id)
        return {
            "success": True,
            "profile": profile or os.getenv("OCI_CLI_PROFILE", "DEFAULT"),
            "total": len(tree),
            "tree": tree,
        }
    except Exception as e:
        return {"success": False, "error": str(e), "type": type(e).__name__, "profile": profile}


def list_enhanced_compartments(
    profile: Optional[str] = None,
    max_age_hours: int = 24,
) -> Dict[str, Any]:
    """
    Return a flat list of compartments from enhanced cache (id, name, parent_id, level, lifecycle_state).
    """
    try:
        cache = get_enhanced_cache(profile=profile)
        cache.load()

        if not cache.cache_data.get("compartments"):
            ensure = ensure_enhanced_cache(profile=profile, max_age_hours=max_age_hours)
            if not ensure.get("success"):
                return {
                    "success": False,
                    "error": ensure.get("error", "Failed to ensure enhanced cache"),
                    "profile": profile,
                }

        comps_map = cache.cache_data.get("compartments", {})
        comps = []
        for cid, comp in comps_map.items():
            if isinstance(comp, dict):
                comps.append(
                    {
                        "id": comp.get("id") or cid,
                        "name": comp.get("name"),
                        "description": comp.get("description"),
                        "parent_id": comp.get("parent_id"),
                        "level": comp.get("level", 0),
                        "lifecycle_state": comp.get("lifecycle_state"),
                    }
                )

        # Sort by level then name for UX predictability
        comps.sort(key=lambda x: (x.get("level", 0), x.get("name") or ""))

        return {
            "success": True,
            "profile": profile or os.getenv("OCI_CLI_PROFILE", "DEFAULT"),
            "total": len(comps),
            "compartments": comps,
        }
    except Exception as e:
        return {"success": False, "error": str(e), "type": type(e).__name__, "profile": profile}
