"""FastMCP tools for OCI profile management and multi-tenancy support."""

from typing import Any, Optional

from ..config_enhanced import (
    list_all_profiles,
    list_all_profiles_with_details,
    get_profile_info,
    validate_profile,
    get_current_profile,
    get_tenancy_info,
    clear_config_cache,
)
from .oci_clients_enhanced import (
    get_identity_client,
    clear_client_cache,
)


def list_oci_profiles_enhanced() -> dict[str, Any]:
    """
    List all OCI profiles with comprehensive configuration details and validation status.

    This enhanced version provides detailed information about each profile including
    tenancy, region, user, and validates whether each profile is properly configured.
    Perfect for multi-tenancy scenarios where you need to manage multiple OCI accounts.

    Returns:
        Dictionary containing:
            - count: Total number of profiles found
            - current_profile: Name of currently active profile
            - profiles: List of profile details with validation status

    Example:
        >>> result = list_oci_profiles_enhanced()
        >>> print(f"Found {result['count']} profiles")
        >>> for profile in result['profiles']:
        ...     status = "✓" if profile['valid'] else "✗"
        ...     print(f"{status} {profile['profile_name']}: {profile.get('region', 'N/A')}")
    """
    try:
        profiles = list_all_profiles_with_details()
        current = get_current_profile()

        return {
            "count": len(profiles),
            "current_profile": current,
            "profiles": profiles,
            "success": True,
        }

    except Exception as e:
        return {
            "error": str(e),
            "type": type(e).__name__,
            "success": False,
        }


def get_oci_profile_details(profile: str) -> dict[str, Any]:
    """
    Get comprehensive configuration details for a specific OCI profile.

    Retrieves and validates all configuration details for the specified profile,
    including tenancy information, user details, and region configuration.

    Args:
        profile: Profile name to query (from ~/.oci/config)

    Returns:
        Dictionary containing:
            - profile_name: The profile name
            - exists: Whether the profile exists
            - valid: Whether configuration is valid
            - tenancy_id: Tenancy OCID
            - user_id: User OCID
            - region: Configured region
            - fingerprint: API key fingerprint
            - key_file: Path to private key file

    Example:
        >>> details = get_oci_profile_details("production")
        >>> if details['valid']:
        ...     print(f"Profile region: {details['region']}")
        ...     print(f"Tenancy: {details['tenancy_id']}")
    """
    try:
        info = get_profile_info(profile)
        return {
            **info,
            "success": True,
        }

    except Exception as e:
        return {
            "error": str(e),
            "type": type(e).__name__,
            "profile_name": profile,
            "success": False,
        }


def validate_oci_profile(profile: str) -> dict[str, Any]:
    """
    Validate that an OCI profile exists and is properly configured.

    Performs comprehensive validation of the profile configuration including:
    - Profile exists in ~/.oci/config
    - Required fields are present (tenancy, user, key_file, fingerprint, region)
    - Configuration file is properly formatted
    - API key file exists and is readable

    Args:
        profile: Profile name to validate

    Returns:
        Dictionary containing:
            - profile: Profile name
            - valid: True if profile is valid and usable
            - exists: True if profile exists in config file
            - error: Error message if validation failed

    Example:
        >>> result = validate_oci_profile("production")
        >>> if result['valid']:
        ...     print("Profile is ready to use")
        ... else:
        ...     print(f"Validation failed: {result.get('error')}")
    """
    try:
        is_valid = validate_profile(profile)
        info = get_profile_info(profile)

        return {
            "profile": profile,
            "valid": is_valid,
            "exists": info.get("exists", False),
            "error": info.get("error") if not is_valid else None,
            "success": True,
        }

    except Exception as e:
        return {
            "profile": profile,
            "valid": False,
            "exists": False,
            "error": str(e),
            "type": type(e).__name__,
            "success": False,
        }


def get_profile_tenancy_details(profile: Optional[str] = None) -> dict[str, Any]:
    """
    Get tenancy information for a specific profile.

    Retrieves comprehensive tenancy details including OCID, region, and user information.
    Useful for confirming which tenancy you're working with in multi-tenancy scenarios.

    Args:
        profile: Profile name to query. If None, uses current active profile.

    Returns:
        Dictionary containing:
            - profile: Profile name used
            - tenancy_id: Tenancy OCID
            - user_id: User OCID
            - region: Configured region
            - fingerprint: API key fingerprint
            - tenancy_name: Tenancy display name (if available)

    Example:
        >>> # Get tenancy info for current profile
        >>> info = get_profile_tenancy_details()
        >>> print(f"Working in tenancy: {info['tenancy_id']}")

        >>> # Get tenancy info for specific profile
        >>> prod_info = get_profile_tenancy_details(profile="production")
        >>> dev_info = get_profile_tenancy_details(profile="development")
    """
    try:
        tenancy_info = get_tenancy_info(profile=profile)
        used_profile = profile or get_current_profile()

        # Try to get tenancy name using Identity API
        try:
            identity_client = get_identity_client(profile=profile)
            tenancy = identity_client.get_tenancy(
                tenancy_id=tenancy_info["tenancy_id"]
            ).data

            tenancy_name = tenancy.name
            tenancy_description = tenancy.description
        except Exception:
            # If we can't fetch tenancy details, just use what we have
            tenancy_name = None
            tenancy_description = None

        return {
            "profile": used_profile,
            "tenancy_id": tenancy_info["tenancy_id"],
            "tenancy_name": tenancy_name,
            "tenancy_description": tenancy_description,
            "user_id": tenancy_info["user_id"],
            "region": tenancy_info["region"],
            "fingerprint": tenancy_info.get("fingerprint"),
            "success": True,
        }

    except Exception as e:
        return {
            "error": str(e),
            "type": type(e).__name__,
            "profile": profile or get_current_profile(),
            "success": False,
        }


def compare_oci_profiles(profiles: list[str]) -> dict[str, Any]:
    """
    Compare multiple OCI profiles side-by-side.

    Useful for multi-tenancy scenarios where you need to understand the
    differences between profiles (different tenancies, regions, etc.).

    Args:
        profiles: List of profile names to compare

    Returns:
        Dictionary containing:
            - profiles: List of profile comparison data
            - comparison_table: Formatted comparison table

    Example:
        >>> result = compare_oci_profiles(["production", "development", "testing"])
        >>> for profile in result['profiles']:
        ...     print(f"{profile['name']}: {profile['region']} - {profile['tenancy_id']}")
    """
    try:
        comparison_data = []

        for profile_name in profiles:
            info = get_profile_info(profile_name)
            tenancy_info = None

            if info.get("valid"):
                try:
                    tenancy_info = get_tenancy_info(profile=profile_name)
                except Exception:
                    pass

            profile_data = {
                "name": profile_name,
                "exists": info.get("exists", False),
                "valid": info.get("valid", False),
                "region": info.get("region"),
                "tenancy_id": info.get("tenancy_id"),
                "user_id": info.get("user_id"),
                "error": info.get("error"),
            }

            comparison_data.append(profile_data)

        return {
            "count": len(comparison_data),
            "profiles": comparison_data,
            "success": True,
        }

    except Exception as e:
        return {
            "error": str(e),
            "type": type(e).__name__,
            "success": False,
        }


def refresh_profile_cache() -> dict[str, Any]:
    """
    Refresh the profile configuration cache.

    Forces a reload of all profile configurations from disk. Useful after
    updating ~/.oci/config file or rotating API keys.

    Returns:
        Dictionary with success status

    Example:
        >>> # After editing ~/.oci/config
        >>> result = refresh_profile_cache()
        >>> if result['success']:
        ...     print("Profile cache refreshed successfully")
    """
    try:
        clear_config_cache()
        clear_client_cache()

        return {
            "message": "Profile configuration cache cleared successfully",
            "note": "Next profile operation will reload from ~/.oci/config",
            "success": True,
        }

    except Exception as e:
        return {
            "error": str(e),
            "type": type(e).__name__,
            "success": False,
        }


def get_current_profile_info() -> dict[str, Any]:
    """
    Get information about the currently active OCI profile.

    Returns details about which profile is currently active based on
    the OCI_CLI_PROFILE environment variable or DEFAULT.

    Returns:
        Dictionary containing current profile details

    Example:
        >>> info = get_current_profile_info()
        >>> print(f"Currently using profile: {info['profile_name']}")
        >>> print(f"Region: {info['region']}")
    """
    try:
        current = get_current_profile()
        info = get_profile_info(current)
        tenancy_details = None

        if info.get("valid"):
            try:
                tenancy_details = get_tenancy_info(profile=current)
            except Exception:
                pass

        return {
            "profile_name": current,
            "details": info,
            "tenancy": tenancy_details,
            "success": True,
        }

    except Exception as e:
        return {
            "error": str(e),
            "type": type(e).__name__,
            "success": False,
        }
