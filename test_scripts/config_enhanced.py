"""Enhanced OCI configuration with advanced multi-profile support."""

import os
from pathlib import Path
from typing import Any, Optional
from functools import lru_cache
import configparser

import oci
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


@lru_cache(maxsize=32)
def get_oci_config(profile: Optional[str] = None) -> dict[str, Any]:
    """
    Get OCI configuration for specified profile or default.

    This function supports multi-tenancy by allowing you to specify
    which OCI profile to use. Profile configurations are cached for
    performance.

    Args:
        profile: OCI profile name from ~/.oci/config.
                If None, uses OCI_CLI_PROFILE env var or 'DEFAULT'.

    Returns:
        dict: OCI configuration dictionary with keys like 'user', 'key_file',
              'fingerprint', 'tenancy', 'region', etc.

    Raises:
        oci.exceptions.ConfigFileNotFound: If config file doesn't exist
        oci.exceptions.InvalidConfig: If config file is invalid

    Example:
        >>> # Use default profile
        >>> config = get_oci_config()

        >>> # Use specific profile for multi-tenancy
        >>> config = get_oci_config(profile="production")
        >>> config2 = get_oci_config(profile="development")
    """
    # Determine which profile to use
    if profile is None:
        profile = os.getenv("OCI_CLI_PROFILE", "DEFAULT")

    # Check for region override
    region_override = os.getenv("OCI_REGION")

    # Load config from file
    config = oci.config.from_file(profile_name=profile)

    # Override region if specified in environment
    if region_override:
        config["region"] = region_override

    # Validate the config
    oci.config.validate_config(config)

    return config


def list_all_profiles() -> list[str]:
    """
    List all available OCI profiles from the config file.

    Returns:
        List[str]: List of profile names available in ~/.oci/config

    Raises:
        FileNotFoundError: If OCI config file doesn't exist

    Example:
        >>> profiles = list_all_profiles()
        >>> print(f"Found {len(profiles)} profiles: {', '.join(profiles)}")
    """
    config_path = Path.home() / ".oci" / "config"

    if not config_path.exists():
        raise FileNotFoundError(f"OCI config file not found at {config_path}")

    profiles = []
    with open(config_path, 'r') as f:
        for line in f:
            line = line.strip()
            if line.startswith('[') and line.endswith(']'):
                profile_name = line[1:-1]  # Remove brackets
                profiles.append(profile_name)

    return profiles


def get_profile_info(profile: str) -> dict[str, Any]:
    """
    Get detailed configuration information for a specific profile.

    This function provides comprehensive information about a profile
    including tenancy, user, region, and validates the configuration.

    Args:
        profile: Profile name to get information for

    Returns:
        dict: Dictionary containing:
            - profile_name: The profile name
            - exists: Whether the profile exists
            - valid: Whether the configuration is valid
            - tenancy_id: Tenancy OCID (if valid)
            - user_id: User OCID (if valid)
            - region: Configured region (if valid)
            - fingerprint: API key fingerprint (if valid)
            - key_file: Path to private key file (if valid)
            - error: Error message (if invalid)

    Example:
        >>> info = get_profile_info("production")
        >>> if info['valid']:
        ...     print(f"Profile '{info['profile_name']}' is configured for region {info['region']}")
    """
    result = {
        "profile_name": profile,
        "exists": False,
        "valid": False,
    }

    try:
        # Check if profile exists
        available_profiles = list_all_profiles()
        if profile not in available_profiles:
            result["error"] = f"Profile '{profile}' not found in ~/.oci/config"
            return result

        result["exists"] = True

        # Try to load and validate the configuration
        try:
            config = get_oci_config(profile=profile)

            result["valid"] = True
            result["tenancy_id"] = config.get("tenancy")
            result["user_id"] = config.get("user")
            result["region"] = config.get("region")
            result["fingerprint"] = config.get("fingerprint")
            result["key_file"] = config.get("key_file")

        except Exception as e:
            result["error"] = f"Configuration validation failed: {str(e)}"
            result["valid"] = False

    except FileNotFoundError as e:
        result["error"] = str(e)

    return result


def list_all_profiles_with_details() -> list[dict[str, Any]]:
    """
    Get all profiles with their configuration details.

    Returns comprehensive information about all available OCI profiles,
    including validation status and key configuration details.

    Returns:
        List[dict]: List of profile information dictionaries

    Example:
        >>> profiles = list_all_profiles_with_details()
        >>> for p in profiles:
        ...     status = "✓" if p['valid'] else "✗"
        ...     print(f"{status} {p['profile_name']}: {p.get('region', 'N/A')}")
    """
    try:
        profile_names = list_all_profiles()
        return [get_profile_info(profile) for profile in profile_names]
    except FileNotFoundError:
        return []


def validate_profile(profile: str) -> bool:
    """
    Validate if a profile exists and is properly configured.

    Args:
        profile: Profile name to validate

    Returns:
        bool: True if profile exists and is valid, False otherwise

    Example:
        >>> if validate_profile("production"):
        ...     # Proceed with operations
        ...     pass
        ... else:
        ...     print("Please configure the production profile first")
    """
    info = get_profile_info(profile)
    return info["exists"] and info["valid"]


def get_current_profile() -> str:
    """
    Get the currently active OCI profile name.

    Returns:
        str: The profile name from OCI_CLI_PROFILE env var or 'DEFAULT'

    Example:
        >>> current = get_current_profile()
        >>> print(f"Currently using profile: {current}")
    """
    return os.getenv("OCI_CLI_PROFILE", "DEFAULT")


def get_profile_cache_key(profile: Optional[str], key_suffix: str) -> str:
    """
    Generate a cache key for profile-specific cached data.

    This allows different profiles to have separate cache entries,
    which is essential for multi-tenancy support.

    Args:
        profile: Profile name, or None for default
        key_suffix: Suffix to identify the type of cached data

    Returns:
        str: Cache key in format "profile_name:suffix"

    Example:
        >>> cache_key = get_profile_cache_key("production", "database_list")
        >>> # Returns: "production:database_list"
    """
    if profile is None:
        profile = get_current_profile()
    return f"{profile}:{key_suffix}"


def get_compartment_id(profile: Optional[str] = None) -> str:
    """
    Get the default compartment ID for a profile.

    Args:
        profile: Profile to get compartment for, or None for default

    Returns:
        str: Compartment OCID. Defaults to tenancy OCID if OCI_COMPARTMENT_ID
             is not set in environment variables.

    Example:
        >>> # Get compartment for default profile
        >>> comp_id = get_compartment_id()

        >>> # Get compartment for specific profile
        >>> prod_comp_id = get_compartment_id(profile="production")
    """
    compartment_id = os.getenv("OCI_COMPARTMENT_ID")

    if compartment_id:
        return compartment_id

    # Fall back to tenancy root
    config = get_oci_config(profile=profile)
    return config["tenancy"]


def get_tenancy_info(profile: Optional[str] = None) -> dict[str, str]:
    """
    Get tenancy information for a profile.

    Args:
        profile: Profile to get tenancy info for, or None for default

    Returns:
        dict: Dictionary with tenancy_id, user_id, and region

    Example:
        >>> info = get_tenancy_info("production")
        >>> print(f"Tenancy: {info['tenancy_id']}, Region: {info['region']}")
    """
    config = get_oci_config(profile=profile)
    return {
        "tenancy_id": config["tenancy"],
        "user_id": config["user"],
        "region": config["region"],
        "fingerprint": config.get("fingerprint"),
    }


def clear_config_cache():
    """
    Clear the configuration cache.

    Useful when OCI config files have been updated and you want
    to reload the configurations.

    Example:
        >>> # After updating ~/.oci/config
        >>> clear_config_cache()
        >>> # Next get_oci_config() call will reload from disk
    """
    get_oci_config.cache_clear()
