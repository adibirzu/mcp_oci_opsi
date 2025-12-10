"""FastMCP tools for OCI Operations Insights."""

from datetime import datetime
from typing import Any, Optional

from .oci_clients import get_opsi_client, extract_region_from_ocid, get_ocid_resource_type


def list_database_insights(
    compartment_id: str,
    lifecycle_state: Optional[str] = None,
    page: Optional[str] = None,
    limit: Optional[int] = None,
) -> dict[str, Any]:
    """
    List database insights in a compartment with optional filtering.

    Args:
        compartment_id: Compartment OCID to query.
        lifecycle_state: Filter by lifecycle state (e.g., "ACTIVE", "DELETED").
        page: Page token for pagination (from previous response).
        limit: Maximum number of items to return per page.

    Returns:
        Dictionary containing database insights list and pagination info.

    Example:
        >>> result = list_database_insights(
        ...     compartment_id="ocid1.compartment.oc1..example...",
        ...     lifecycle_state="ACTIVE",
        ...     limit=50
        ... )
        >>> print(f"Found {len(result['items'])} database insights")
    """
    try:
        client = get_opsi_client()

        kwargs = {"compartment_id": compartment_id}

        if lifecycle_state:
            kwargs["lifecycle_state"] = lifecycle_state
        if page:
            kwargs["page"] = page
        if limit:
            kwargs["limit"] = limit

        response = client.list_database_insights(**kwargs)

        items = []
        for db_insight in response.data.items:
            items.append({
                "id": db_insight.id,
                "compartment_id": db_insight.compartment_id,
                "database_id": db_insight.database_id,
                "database_name": db_insight.database_name,
                "database_display_name": getattr(db_insight, "database_display_name", None),
                "database_type": db_insight.database_type,
                "database_version": getattr(db_insight, "database_version", None),
                "entity_source": getattr(db_insight, "entity_source", None),
                "processor_count": getattr(db_insight, "processor_count", None),
                "status": db_insight.status,
                "lifecycle_state": db_insight.lifecycle_state,
                "time_created": str(db_insight.time_created),
                "time_updated": str(getattr(db_insight, "time_updated", None)),
                "freeform_tags": getattr(db_insight, "freeform_tags", {}),
                "defined_tags": getattr(db_insight, "defined_tags", {}),
            })

        result = {
            "items": items,
            "count": len(items),
        }

        # Add pagination info if available
        if hasattr(response, "next_page") and response.next_page:
            result["next_page"] = response.next_page
        if hasattr(response, "opc_next_page") and response.opc_next_page:
            result["next_page"] = response.opc_next_page

        return result

    except Exception as e:
        return {
            "error": str(e),
            "type": type(e).__name__,
        }


def query_warehouse_standard(
    compartment_id: str,
    statement: str,
    region: Optional[str] = None,
) -> dict[str, Any]:
    """
    Execute a standard SQL query against the Operations Insights warehouse.

    This tool allows querying OPSI data warehouse using SQL-like syntax to analyze
    database performance metrics, resource utilization, and SQL statistics.

    IMPORTANT: Operations Insights warehouse data is regional. If your query filters
    by specific database OCIDs, you may need to specify the region parameter to query
    the correct regional warehouse.

    Args:
        compartment_id: Compartment OCID for the query scope.
        statement: SQL query statement to execute against the warehouse.
        region: Optional region override. Use this if querying databases in a specific region.
               Example: "us-phoenix-1", "uk-london-1"

    Returns:
        Dictionary containing query results with columns and rows.

    Example:
        >>> result = query_warehouse_standard(
        ...     compartment_id="ocid1.compartment.oc1..example...",
        ...     statement="SELECT database_name, avg_cpu FROM database_stats WHERE time_collected > '2024-01-01'"
        ... )
        >>> for row in result['rows']:
        ...     print(row)

        >>> # Query for a database in a specific region
        >>> result = query_warehouse_standard(
        ...     compartment_id="ocid1.compartment.oc1..example...",
        ...     statement="SELECT * FROM database_sql_statistics WHERE database_id = 'ocid1.opsidatabaseinsight.oc1.phx.aaa...'",
        ...     region="us-phoenix-1"
        ... )

    Note:
        The query capabilities depend on your OCI OPSI warehouse configuration
        and the OPSI schema available in your tenancy. If querying specific databases,
        you may need to query the database's home region.
    """
    try:
        # Try to detect region from database_id in the SQL statement
        if not region and "database_id = " in statement:
            # Extract OCID from statement (simple pattern matching)
            import re
            ocid_pattern = r"ocid1\.[a-zA-Z0-9]+\.oc1\.[a-z0-9]+\.[a-zA-Z0-9]+"
            match = re.search(ocid_pattern, statement)
            if match:
                ocid = match.group(0)
                region = extract_region_from_ocid(ocid)
                if region:
                    print(f"Detected database region from query: {region}")

        client = get_opsi_client(region=region)

        # Try using the SDK method if available (newer SDK versions)
        try:
            # Attempt to use query_opsi_data_object_data method
            from oci.opsi.models import QueryDataObjectJsonResultSetDetails

            query_details = QueryDataObjectJsonResultSetDetails(
                query_string=statement,
                compartment_id=compartment_id,
            )

            response = client.query_opsi_data_object_data(
                compartment_id=compartment_id,
                query_data_object_details=query_details,
            )

            # Extract result data
            if hasattr(response.data, "items"):
                return {
                    "query": statement,
                    "compartment_id": compartment_id,
                    "items": [item.__dict__ if hasattr(item, "__dict__") else item for item in response.data.items],
                    "count": len(response.data.items),
                }
            else:
                return {
                    "query": statement,
                    "compartment_id": compartment_id,
                    "data": response.data.__dict__ if hasattr(response.data, "__dict__") else str(response.data),
                }

        except (AttributeError, ImportError):
            # Fall back to raw API call for older SDK versions
            # Use the 20200630 API version with standard-query endpoint
            path = "/20200630/opsiDataObjects/actions/queryData"

            body = {
                "queryString": statement,
                "compartmentId": compartment_id,
                "resultSetType": "JSON",
            }

            response = client.base_client.call_api(
                resource_path=path,
                method="POST",
                body=body,
                response_type="object",
            )

            # Parse the response
            if response.status == 200:
                data = response.data

                # Extract columns and rows if present
                result = {
                    "query": statement,
                    "compartment_id": compartment_id,
                }

                if hasattr(data, "items"):
                    result["items"] = [
                        item.__dict__ if hasattr(item, "__dict__") else item
                        for item in data.items
                    ]
                    result["count"] = len(data.items)
                elif isinstance(data, dict):
                    result.update(data)
                else:
                    result["data"] = str(data)

                return result
            else:
                return {
                    "error": f"API call failed with status {response.status}",
                    "query": statement,
                }

    except Exception as e:
        error_msg = str(e)
        error_result = {
            "error": error_msg,
            "type": type(e).__name__,
            "query": statement,
        }

        # Add troubleshooting guidance
        if "NotAuthorizedOrNotFound" in error_msg or "404" in error_msg:
            error_result["troubleshooting"] = {
                "possible_causes": [
                    "OPSI warehouse not configured in this region",
                    "Database being queried is in a different region",
                    "Missing IAM permissions for OPSI data objects",
                    "Invalid table or column names in query"
                ],
                "required_permissions": [
                    "Allow group <YourGroup> to read opsi-data-objects in compartment",
                    "Allow group <YourGroup> to use operations-insights-warehouse in compartment"
                ],
                "next_steps": [
                    "If querying a specific database, specify its region explicitly",
                    "Verify Operations Insights warehouse is enabled in the target region",
                    "Check IAM policies for warehouse access"
                ]
            }

            if region:
                error_result["queried_region"] = region

        return error_result


def list_sql_texts(
    compartment_id: str,
    time_start: str,
    time_end: str,
    database_id: Optional[str] = None,
    sql_identifier: Optional[str] = None,
) -> dict[str, Any]:
    """
    List SQL texts from Operations Insights for analysis.

    Retrieves SQL text data for database SQL statements within a time range,
    useful for SQL performance analysis and tuning.

    IMPORTANT: Operations Insights is regional. If querying a specific database,
    this function automatically detects the database region and queries the correct
    regional endpoint.

    Args:
        compartment_id: Compartment OCID to query.
        time_start: Start time in ISO format (e.g., "2024-01-01T00:00:00Z").
        time_end: End time in ISO format (e.g., "2024-01-31T23:59:59Z").
        database_id: Optional database insight OCID to filter results.
                    Region will be automatically detected from this OCID.
        sql_identifier: Optional SQL identifier to retrieve specific SQL text.

    Returns:
        Dictionary containing SQL text data with statistics.

    Example:
        >>> result = list_sql_texts(
        ...     compartment_id="ocid1.compartment.oc1..example...",
        ...     time_start="2024-01-01T00:00:00Z",
        ...     time_end="2024-01-07T23:59:59Z",
        ...     database_id="ocid1.opsidatabaseinsight.oc1.phx.bbbbb..."
        ... )
        >>> for sql in result['items']:
        ...     print(f"SQL ID: {sql['sql_identifier']}, Executions: {sql['executions']}")

    Note:
        If you get 404 errors, ensure:
        1. The database has Operations Insights enabled
        2. You have required IAM permissions for SQL statistics
        3. SQL Watch is enabled on the database (for ADW/ATP)
    """
    try:
        # Validate OCID type if database_id provided
        if database_id:
            resource_type = get_ocid_resource_type(database_id)

            # Check if user provided wrong OCID type
            if resource_type and resource_type not in ["opsidatabaseinsight", "databaseinsight"]:
                return {
                    "error": f"Invalid OCID type: '{resource_type}'",
                    "provided_ocid": database_id,
                    "troubleshooting": {
                        "issue": f"You provided a '{resource_type}' OCID, but this function requires a 'database insight' OCID",
                        "explanation": [
                            "Operations Insights uses 'database insight' OCIDs, not database OCIDs",
                            "Database insight OCID format: ocid1.opsidatabaseinsight.oc1.<region>...",
                            f"You provided: ocid1.{resource_type}.oc1.<region>..."
                        ],
                        "solution": {
                            "method_1": "Use get_fleet_summary() or search_databases() from cache to find the database insight OCID",
                            "method_2": "Use list_database_insights() to list all insights in your compartment",
                            "method_3": "Ask: 'What is the database insight OCID for PayDB?' (I'll look it up in cache)"
                        },
                        "example": {
                            "wrong_ocid": "ocid1.autonomousdatabase.oc1.phx.xxx (Autonomous Database OCID)",
                            "correct_ocid": "ocid1.opsidatabaseinsight.oc1.phx.yyy (Database Insight OCID)"
                        }
                    }
                }

        # Detect region from database_id if provided
        region = None
        if database_id:
            # Method 1: Extract from OCID
            region = extract_region_from_ocid(database_id)
            if region:
                print(f"Detected region from OCID: {region}")

            # Method 2: Lookup in cache if OCID extraction fails
            if not region:
                try:
                    from mcp_oci_opsi.cache import DatabaseCache
                    cache = DatabaseCache()
                    if cache.load() and cache.is_valid():
                        region = cache.get_database_region(database_id)
                        if region:
                            print(f"Detected region from cache: {region}")
                except Exception:
                    pass  # Cache lookup failed, continue without region

        # Create region-aware client
        client = get_opsi_client(region=region)

        # Convert time strings to datetime objects for API
        time_interval_start = datetime.fromisoformat(time_start.replace("Z", "+00:00"))
        time_interval_end = datetime.fromisoformat(time_end.replace("Z", "+00:00"))

        kwargs = {
            "compartment_id": compartment_id,
            "time_interval_start": time_interval_start,
            "time_interval_end": time_interval_end,
        }

        if database_id:
            kwargs["database_id"] = [database_id]
        if sql_identifier:
            kwargs["sql_identifier"] = [sql_identifier]

        # Try to use summarize_sql_statistics (most common method)
        try:
            response = client.summarize_sql_statistics(**kwargs)

            items = []
            if hasattr(response.data, "items"):
                for item in response.data.items:
                    sql_item = {
                        "sql_identifier": getattr(item, "sql_identifier", None),
                        "database_id": getattr(item, "database_id", None),
                        "sql_text": getattr(item, "sql_text", None),
                        "executions_count": getattr(item, "executions_count", None),
                        "cpu_time_in_sec": getattr(item, "cpu_time_in_sec", None),
                        "elapsed_time_in_sec": getattr(item, "elapsed_time_in_sec", None),
                        "buffer_gets": getattr(item, "buffer_gets", None),
                        "disk_reads": getattr(item, "disk_reads", None),
                        "rows_processed": getattr(item, "rows_processed", None),
                    }
                    items.append(sql_item)

            return {
                "compartment_id": compartment_id,
                "time_start": time_start,
                "time_end": time_end,
                "items": items,
                "count": len(items),
            }

        except AttributeError:
            # Try alternative method: list_sql_texts if available
            try:
                response = client.list_sql_texts(**kwargs)

                items = []
                if hasattr(response.data, "items"):
                    for item in response.data.items:
                        items.append({
                            "sql_identifier": getattr(item, "sql_identifier", None),
                            "sql_text": getattr(item, "sql_text", None),
                            "database_id": getattr(item, "database_id", None),
                        })
                elif isinstance(response.data, list):
                    items = [item.__dict__ if hasattr(item, "__dict__") else item for item in response.data]

                return {
                    "compartment_id": compartment_id,
                    "time_start": time_start,
                    "time_end": time_end,
                    "items": items,
                    "count": len(items),
                }

            except AttributeError:
                # Fall back to raw API call
                path = "/20200630/databaseInsights/sqlTexts"

                query_params = {
                    "compartmentId": compartment_id,
                    "timeIntervalStart": time_start,
                    "timeIntervalEnd": time_end,
                }

                if database_id:
                    query_params["databaseId"] = database_id
                if sql_identifier:
                    query_params["sqlIdentifier"] = sql_identifier

                response = client.base_client.call_api(
                    resource_path=path,
                    method="GET",
                    query_params=query_params,
                    response_type="object",
                )

                if response.status == 200:
                    data = response.data
                    items = []

                    if hasattr(data, "items"):
                        items = [item.__dict__ if hasattr(item, "__dict__") else item for item in data.items]
                    elif isinstance(data, list):
                        items = data

                    return {
                        "compartment_id": compartment_id,
                        "time_start": time_start,
                        "time_end": time_end,
                        "items": items,
                        "count": len(items),
                    }

                return {
                    "error": f"API call failed with status {response.status}",
                    "compartment_id": compartment_id,
                }

    except Exception as e:
        error_msg = str(e)
        error_result = {
            "error": error_msg,
            "type": type(e).__name__,
            "compartment_id": compartment_id,
            "time_start": time_start,
            "time_end": time_end,
        }

        # Add troubleshooting guidance for common errors
        if "NotAuthorizedOrNotFound" in error_msg or "404" in error_msg:
            error_result["troubleshooting"] = {
                "possible_causes": [
                    "Database does not have Operations Insights enabled",
                    "SQL Watch may not be enabled (required for ADW/ATP databases)",
                    "Missing IAM permissions for SQL statistics",
                    "Database insight ID is incorrect",
                    "Regional mismatch - database may be in different region"
                ],
                "required_permissions": [
                    "Allow group <YourGroup> to read sql-statistics in compartment",
                    "Allow group <YourGroup> to read opsi-data-objects in compartment",
                    "Allow group <YourGroup> to use operations-insights-warehouse in compartment"
                ],
                "next_steps": [
                    "For Autonomous Databases: Enable SQL Watch first (use enable_sqlwatch tool)",
                    "Verify database has Operations Insights enabled",
                    "Check IAM policies in the database compartment",
                    "Confirm the database_id OCID is correct"
                ]
            }

            if database_id:
                detected_region = extract_region_from_ocid(database_id)
                if detected_region:
                    error_result["detected_database_region"] = detected_region
                    error_result["troubleshooting"]["regional_note"] = (
                        f"Database appears to be in {detected_region} region. "
                        "The client has been configured for this region automatically."
                    )

        return error_result
