"""OCI client factories and utilities."""

from typing import Any, Callable, List, Optional

import oci
import os

from .config import get_oci_config, get_signer_and_region


def get_ocid_resource_type(ocid: str) -> Optional[str]:
    """
    Extract the resource type from an OCI OCID.

    OCI OCIDs have the format:
    ocid1.<RESOURCE_TYPE>.<REALM>.[REGION][.FUTURE_USE].<UNIQUE_ID>

    Args:
        ocid: OCI resource OCID string.

    Returns:
        str: Resource type (e.g., "opsidatabaseinsight", "autonomousdatabase", "database")
             or None if not parseable.

    Example:
        >>> resource_type = get_ocid_resource_type("ocid1.opsidatabaseinsight.oc1.phx.aaa...")
        >>> print(resource_type)  # "opsidatabaseinsight"

        >>> resource_type = get_ocid_resource_type("ocid1.autonomousdatabase.oc1.phx.aaa...")
        >>> print(resource_type)  # "autonomousdatabase"
    """
    if not ocid or not isinstance(ocid, str):
        return None

    try:
        # Split OCID into parts
        parts = ocid.split(".")

        if len(parts) < 2:
            return None

        # The resource type is in the 2nd position (index 1)
        # Format: ocid1.<resource>.<realm>.<region>.<unique_id>
        return parts[1]

    except (IndexError, AttributeError):
        return None


def extract_region_from_ocid(ocid: str) -> Optional[str]:
    """
    Extract region from an OCI resource OCID.

    OCI OCIDs have the format:
    ocid1.<RESOURCE_TYPE>.<REALM>.[REGION][.FUTURE_USE].<UNIQUE_ID>

    Args:
        ocid: OCI resource OCID string.

    Returns:
        str: Region code (e.g., "us-phoenix-1", "uk-london-1") or None if not found.

    Example:
        >>> region = extract_region_from_ocid("ocid1.database.oc1.phx.aaa...")
        >>> print(region)  # "us-phoenix-1"
    """
    if not ocid or not isinstance(ocid, str):
        return None

    try:
        # Split OCID into parts
        parts = ocid.split(".")

        if len(parts) < 4:
            return None

        # The region is typically in the 4th position (index 3)
        # Format: ocid1.<resource>.<realm>.<region>.<unique_id>
        region_code = parts[3]

        # Map common short codes to full region names
        region_map = {
            "phx": "us-phoenix-1",
            "iad": "us-ashburn-1",
            "fra": "eu-frankfurt-1",
            "lhr": "uk-london-1",
            "ams": "eu-amsterdam-1",
            "zrh": "eu-zurich-1",
            "jed": "me-jeddah-1",
            "mel": "ap-melbourne-1",
            "syd": "ap-sydney-1",
            "gru": "sa-saopaulo-1",
            "vcp": "sa-vinhedo-1",
            "yul": "ca-montreal-1",
            "yyz": "ca-toronto-1",
            "nrt": "ap-tokyo-1",
            "kix": "ap-osaka-1",
            "icn": "ap-seoul-1",
            "bom": "ap-mumbai-1",
            "hyd": "ap-hyderabad-1",
            "sin": "ap-singapore-1",
            "dxb": "me-dubai-1",
            "cwl": "uk-cardiff-1",
            "ltn": "uk-gov-london-1",
            "pia": "us-gov-ashburn-1",
            "tus": "us-gov-phoenix-1",
            "lin": "eu-milan-1",
            "mrs": "eu-marseille-1",
            "arn": "eu-stockholm-1",
            "cdg": "eu-paris-1",
            "jnb": "af-johannesburg-1",
            "mtz": "il-jerusalem-1",
            "scl": "sa-santiago-1",
            "vap": "sa-valparaiso-1",
        }

        # Check if it's a short code that needs mapping
        if region_code in region_map:
            return region_map[region_code]

        # If it's already a full region name (e.g., "us-phoenix-1"), return as-is
        # Full region names contain hyphens
        if "-" in region_code:
            return region_code

        # Unknown format
        return None

    except (IndexError, AttributeError):
        return None


def get_opsi_client(use_resource_principal: bool = False, region: str = None) -> oci.opsi.OperationsInsightsClient:
    """
    Create and return an OCI Operations Insights client.

    Args:
        use_resource_principal: If True, use Resource Principal authentication.
                              Defaults to False (user principal).
        region: Optional region override. If provided, the client will be configured
               for this specific region. This is important for Operations Insights
               as database insights are region-specific.

    Returns:
        oci.opsi.OperationsInsightsClient: Configured Operations Insights client.

    Example:
        >>> client = get_opsi_client()
        >>> response = client.list_database_insights(compartment_id="ocid1...")

        >>> # Query a database in a specific region
        >>> client = get_opsi_client(region="us-phoenix-1")
        >>> response = client.summarize_sql_statistics(...)
    """
    if use_resource_principal:
        signer, default_region = get_signer_and_region(use_resource_principal=True)
        # When using signer, pass empty config dict
        client = oci.opsi.OperationsInsightsClient(
            config={},
            signer=signer,
        )
        client.base_client.set_region(region or default_region)
    else:
        # User principal - use config directly
        config = get_oci_config()

        # Allow environment override for demo/targeted scans (e.g., emdemo -> uk-london-1)
        # Only apply if explicit region param wasn't passed
        env_override = os.getenv("MCP_OPSI_REGION_OVERRIDE")
        if env_override and not region:
            region = env_override

        # Override region if specified
        if region:
            config["region"] = region

        client = oci.opsi.OperationsInsightsClient(config)

    return client


def get_dbm_client(use_resource_principal: bool = False, region: str = None) -> oci.database_management.DbManagementClient:
    """
    Create and return an OCI Database Management client.

    Args:
        use_resource_principal: If True, use Resource Principal authentication.
                              Defaults to False (user principal).
        region: Optional region override. If provided, the client will be configured
               for this specific region.

    Returns:
        oci.database_management.DbManagementClient: Configured Database Management client.

    Example:
        >>> client = get_dbm_client()
        >>> response = client.list_managed_databases(compartment_id="ocid1...")

        >>> # Query in a specific region
        >>> client = get_dbm_client(region="us-phoenix-1")
        >>> response = client.get_managed_database(managed_database_id="ocid1...")
    """
    if use_resource_principal:
        signer, default_region = get_signer_and_region(use_resource_principal=True)
        # When using signer, pass empty config dict
        client = oci.database_management.DbManagementClient(
            config={},
            signer=signer,
        )
        client.base_client.set_region(region or default_region)
    else:
        # User principal - use config directly
        config = get_oci_config()

        # Override region if specified
        if region:
            config["region"] = region

        client = oci.database_management.DbManagementClient(config)

    return client


def list_all(
    getter: Callable[..., Any],
    **kwargs: Any,
) -> List[Any]:
    """
    Pagination helper that follows next page tokens to retrieve all results.

    This helper automatically handles pagination for OCI list operations by
    following the `opc-next-page` token until all results are retrieved.

    Args:
        getter: The list method to call (e.g., client.list_database_insights).
        **kwargs: Arguments to pass to the getter method.

    Returns:
        List[Any]: Combined list of all items from all pages.

    Example:
        >>> from functools import partial
        >>> client = get_opsi_client()
        >>> all_insights = list_all(
        ...     client.list_database_insights,
        ...     compartment_id="ocid1.compartment..."
        ... )
        >>> print(f"Found {len(all_insights)} database insights")

    Note:
        - The getter should return a response object with a `data` attribute
          containing the items.
        - The response should have a `next_page` attribute (or None) for pagination.
        - Items from all pages are accumulated and returned as a flat list.
    """
    all_items = []
    page = kwargs.pop("page", None)  # Start with no page token

    while True:
        # Add page token to kwargs if present
        if page:
            kwargs["page"] = page

        # Call the getter function
        response = getter(**kwargs)

        # Extract items from response.data
        if hasattr(response, "data"):
            # Handle different response types
            if isinstance(response.data, list):
                # Simple list response
                all_items.extend(response.data)
            elif hasattr(response.data, "items"):
                # Response with items attribute (common in summary APIs)
                all_items.extend(response.data.items)
            else:
                # Single item response - wrap in list
                all_items.append(response.data)
        else:
            # Unexpected response format
            break

        # Check for next page
        if hasattr(response, "next_page") and response.next_page:
            page = response.next_page
        elif hasattr(response, "opc_next_page") and response.opc_next_page:
            # Some responses use opc_next_page instead
            page = response.opc_next_page
        else:
            # No more pages
            break

        # Remove page from kwargs for next iteration
        kwargs.pop("page", None)

    return all_items


def list_all_generator(
    getter: Callable[..., Any],
    **kwargs: Any,
):
    """
    Generator version of list_all that yields items one at a time.

    This is more memory-efficient for large result sets as it doesn't
    accumulate all items in memory.

    Args:
        getter: The list method to call (e.g., client.list_database_insights).
        **kwargs: Arguments to pass to the getter method.

    Yields:
        Individual items from all pages.

    Example:
        >>> client = get_opsi_client()
        >>> for insight in list_all_generator(
        ...     client.list_database_insights,
        ...     compartment_id="ocid1.compartment..."
        ... ):
        ...     print(f"Processing {insight.database_name}")
    """
    page = kwargs.pop("page", None)

    while True:
        if page:
            kwargs["page"] = page

        response = getter(**kwargs)

        # Yield items from current page
        if hasattr(response, "data"):
            if isinstance(response.data, list):
                for item in response.data:
                    yield item
            elif hasattr(response.data, "items"):
                for item in response.data.items:
                    yield item
            else:
                yield response.data
        else:
            break

        # Check for next page
        if hasattr(response, "next_page") and response.next_page:
            page = response.next_page
        elif hasattr(response, "opc_next_page") and response.opc_next_page:
            page = response.opc_next_page
        else:
            break

        kwargs.pop("page", None)
