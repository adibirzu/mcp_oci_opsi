"""Enhanced OCI client factories with multi-profile support."""

from typing import Any, Callable, List, Optional
from functools import lru_cache

import oci

from .config_enhanced import get_oci_config

# Re-export utility functions from base module
from .oci_clients import (
    get_ocid_resource_type,
    extract_region_from_ocid,
    list_all,
    list_all_generator,
)


@lru_cache(maxsize=16)
def get_opsi_client(
    profile: Optional[str] = None,
    region: Optional[str] = None,
    use_resource_principal: bool = False,
) -> oci.opsi.OperationsInsightsClient:
    """
    Create and return an OCI Operations Insights client with multi-profile support.

    This enhanced version supports multiple OCI profiles for multi-tenancy scenarios.
    Clients are cached for performance.

    Args:
        profile: OCI profile name from ~/.oci/config. If None, uses OCI_CLI_PROFILE
                env var or 'DEFAULT'. Enables working with multiple tenancies.
        region: Optional region override. If provided, the client will be configured
               for this specific region. Important for Operations Insights as
               database insights are region-specific.
        use_resource_principal: If True, use Resource Principal authentication.
                              Defaults to False (user principal).

    Returns:
        oci.opsi.OperationsInsightsClient: Configured Operations Insights client.

    Example:
        >>> # Use default profile
        >>> client = get_opsi_client()
        >>> response = client.list_database_insights(compartment_id="ocid1...")

        >>> # Use specific profile for multi-tenancy
        >>> prod_client = get_opsi_client(profile="production")
        >>> dev_client = get_opsi_client(profile="development")

        >>> # Query a database in a specific region
        >>> client = get_opsi_client(profile="production", region="us-phoenix-1")
        >>> response = client.summarize_sql_statistics(...)
    """
    if use_resource_principal:
        # Resource Principal auth (for OCI Functions/Container Instances)
        # Note: This doesn't use profile parameter
        signer = oci.auth.signers.get_resource_principals_signer()
        default_region = signer.region
        client = oci.opsi.OperationsInsightsClient(
            config={},
            signer=signer,
        )
        client.base_client.set_region(region or default_region)
    else:
        # User principal - use config with profile support
        config = get_oci_config(profile=profile)

        # Override region if specified
        if region:
            config["region"] = region

        client = oci.opsi.OperationsInsightsClient(config)

    return client


@lru_cache(maxsize=16)
def get_dbm_client(
    profile: Optional[str] = None,
    region: Optional[str] = None,
    use_resource_principal: bool = False,
) -> oci.database_management.DbManagementClient:
    """
    Create and return an OCI Database Management client with multi-profile support.

    This enhanced version supports multiple OCI profiles for multi-tenancy scenarios.
    Clients are cached for performance.

    Args:
        profile: OCI profile name from ~/.oci/config. If None, uses OCI_CLI_PROFILE
                env var or 'DEFAULT'. Enables working with multiple tenancies.
        region: Optional region override. If provided, the client will be configured
               for this specific region.
        use_resource_principal: If True, use Resource Principal authentication.
                              Defaults to False (user principal).

    Returns:
        oci.database_management.DbManagementClient: Configured Database Management client.

    Example:
        >>> # Use default profile
        >>> client = get_dbm_client()
        >>> response = client.list_managed_databases(compartment_id="ocid1...")

        >>> # Use specific profile for multi-tenancy
        >>> prod_client = get_dbm_client(profile="production")
        >>> dev_client = get_dbm_client(profile="development")

        >>> # Query in a specific region
        >>> client = get_dbm_client(profile="production", region="us-phoenix-1")
        >>> response = client.get_managed_database(managed_database_id="ocid1...")
    """
    if use_resource_principal:
        signer = oci.auth.signers.get_resource_principals_signer()
        default_region = signer.region
        client = oci.database_management.DbManagementClient(
            config={},
            signer=signer,
        )
        client.base_client.set_region(region or default_region)
    else:
        # User principal - use config with profile support
        config = get_oci_config(profile=profile)

        # Override region if specified
        if region:
            config["region"] = region

        client = oci.database_management.DbManagementClient(config)

    return client


@lru_cache(maxsize=16)
def get_identity_client(
    profile: Optional[str] = None,
) -> oci.identity.IdentityClient:
    """
    Create and return an OCI Identity client with multi-profile support.

    Args:
        profile: OCI profile name from ~/.oci/config. If None, uses OCI_CLI_PROFILE
                env var or 'DEFAULT'.

    Returns:
        oci.identity.IdentityClient: Configured Identity client.

    Example:
        >>> # Use default profile
        >>> client = get_identity_client()
        >>> tenancy = client.get_tenancy(get_tenancy_id()).data

        >>> # Use specific profile
        >>> prod_client = get_identity_client(profile="production")
    """
    config = get_oci_config(profile=profile)
    return oci.identity.IdentityClient(config)


@lru_cache(maxsize=16)
def get_database_client(
    profile: Optional[str] = None,
    region: Optional[str] = None,
) -> oci.database.DatabaseClient:
    """
    Create and return an OCI Database client with multi-profile support.

    Args:
        profile: OCI profile name from ~/.oci/config. If None, uses OCI_CLI_PROFILE
                env var or 'DEFAULT'.
        region: Optional region override.

    Returns:
        oci.database.DatabaseClient: Configured Database client.

    Example:
        >>> client = get_database_client(profile="production")
        >>> db = client.get_database(database_id="ocid1...").data
    """
    config = get_oci_config(profile=profile)

    if region:
        config["region"] = region

    return oci.database.DatabaseClient(config)


def clear_client_cache():
    """
    Clear all cached OCI clients.

    Useful when you want to force new client instances to be created,
    for example after updating credentials or changing profiles.

    Example:
        >>> # After rotating API keys
        >>> clear_client_cache()
        >>> # Next client getter will create fresh connections
    """
    get_opsi_client.cache_clear()
    get_dbm_client.cache_clear()
    get_identity_client.cache_clear()
    get_database_client.cache_clear()


def get_client_for_profile(
    client_type: str,
    profile: str,
    region: Optional[str] = None,
):
    """
    Factory function to get any type of OCI client for a specific profile.

    Args:
        client_type: Type of client ("opsi", "dbm", "identity", "database")
        profile: OCI profile name
        region: Optional region override

    Returns:
        Configured OCI client of the requested type

    Example:
        >>> opsi_client = get_client_for_profile("opsi", "production")
        >>> dbm_client = get_client_for_profile("dbm", "development", "us-phoenix-1")
    """
    client_map = {
        "opsi": get_opsi_client,
        "dbm": get_dbm_client,
        "identity": get_identity_client,
        "database": get_database_client,
    }

    if client_type not in client_map:
        raise ValueError(
            f"Unknown client type: {client_type}. "
            f"Valid types: {', '.join(client_map.keys())}"
        )

    getter = client_map[client_type]

    # Call with appropriate parameters
    if client_type in ["opsi", "dbm", "database"]:
        return getter(profile=profile, region=region)
    else:
        return getter(profile=profile)
