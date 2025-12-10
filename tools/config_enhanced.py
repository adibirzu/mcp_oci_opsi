"""Config wrapper - imports from parent module.

This module re-exports configuration functions from the root-level config modules
to maintain compatibility with tools that expect config in the same folder.
"""

from ..config_enhanced import (
    get_oci_config,
    list_all_profiles,
    get_profile_info,
    list_all_profiles_with_details,
    validate_profile,
    get_current_profile,
    get_compartment_id,
    get_tenancy_info,
)

__all__ = [
    "get_oci_config",
    "list_all_profiles",
    "get_profile_info",
    "list_all_profiles_with_details",
    "validate_profile",
    "get_current_profile",
    "get_compartment_id",
    "get_tenancy_info",
]
