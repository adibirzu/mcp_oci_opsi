"""OCI client factories and utilities."""

from typing import Any, Callable, List

import oci

from .config import get_oci_config, get_signer_and_region


def get_opsi_client(use_resource_principal: bool = False) -> oci.opsi.OperationsInsightsClient:
    """
    Create and return an OCI Operations Insights client.

    Args:
        use_resource_principal: If True, use Resource Principal authentication.
                              Defaults to False (user principal).

    Returns:
        oci.opsi.OperationsInsightsClient: Configured Operations Insights client.

    Example:
        >>> client = get_opsi_client()
        >>> response = client.list_database_insights(compartment_id="ocid1...")
    """
    if use_resource_principal:
        signer, region = get_signer_and_region(use_resource_principal=True)
        # When using signer, pass empty config dict
        client = oci.opsi.OperationsInsightsClient(
            config={},
            signer=signer,
        )
        client.base_client.set_region(region)
    else:
        # User principal - use config directly
        config = get_oci_config()
        client = oci.opsi.OperationsInsightsClient(config)

    return client


def get_dbm_client(use_resource_principal: bool = False) -> oci.database_management.DbManagementClient:
    """
    Create and return an OCI Database Management client.

    Args:
        use_resource_principal: If True, use Resource Principal authentication.
                              Defaults to False (user principal).

    Returns:
        oci.database_management.DbManagementClient: Configured Database Management client.

    Example:
        >>> client = get_dbm_client()
        >>> response = client.list_managed_databases(compartment_id="ocid1...")
    """
    if use_resource_principal:
        signer, region = get_signer_and_region(use_resource_principal=True)
        # When using signer, pass empty config dict
        client = oci.database_management.DbManagementClient(
            config={},
            signer=signer,
        )
        client.base_client.set_region(region)
    else:
        # User principal - use config directly
        config = get_oci_config()
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
