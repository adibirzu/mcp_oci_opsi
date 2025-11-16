"""FastMCP tools for OCI Database Management comprehensive operations."""

from typing import Any, Optional

from .oci_clients import get_dbm_client, list_all, extract_region_from_ocid


def list_managed_databases(
    compartment_id: str,
    lifecycle_state: Optional[str] = None,
    name: Optional[str] = None,
) -> dict[str, Any]:
    """
    List all managed databases in a compartment.

    Args:
        compartment_id: Compartment OCID to query.
        lifecycle_state: Filter by lifecycle state (e.g., "ACTIVE").
        name: Filter by database name.

    Returns:
        Dictionary containing list of managed databases with their details.
    """
    try:
        client = get_dbm_client()

        kwargs = {"compartment_id": compartment_id}
        if lifecycle_state:
            kwargs["lifecycle_state"] = lifecycle_state
        if name:
            kwargs["name"] = name

        # Use list_all for automatic pagination
        managed_dbs = list_all(
            client.list_managed_databases,
            **kwargs,
        )

        items = []
        for db in managed_dbs:
            items.append({
                "id": db.id,
                "name": db.name,
                "database_type": getattr(db, "database_type", None),
                "database_sub_type": getattr(db, "database_sub_type", None),
                "deployment_type": getattr(db, "deployment_type", None),
                "management_option": getattr(db, "management_option", None),
                "workload_type": getattr(db, "workload_type", None),
                "is_cluster": getattr(db, "is_cluster", None),
                "lifecycle_state": db.lifecycle_state,
                "time_created": str(db.time_created),
            })

        return {
            "compartment_id": compartment_id,
            "items": items,
            "count": len(items),
        }

    except Exception as e:
        return {
            "error": str(e),
            "type": type(e).__name__,
            "compartment_id": compartment_id,
        }


def get_managed_database(database_id: str) -> dict[str, Any]:
    """
    Get detailed information about a specific managed database.

    Database Management is regional - this function automatically detects
    the database region from the OCID and queries the correct endpoint.

    Args:
        database_id: Managed Database OCID.

    Returns:
        Dictionary containing detailed managed database information.
    """
    try:
        # Detect region from database OCID
        region = extract_region_from_ocid(database_id)
        if region:
            print(f"Detected database region: {region}")

        client = get_dbm_client(region=region)

        response = client.get_managed_database(managed_database_id=database_id)
        db = response.data

        result = {
            "id": db.id,
            "name": db.name,
            "compartment_id": db.compartment_id,
            "database_type": getattr(db, "database_type", None),
            "database_sub_type": getattr(db, "database_sub_type", None),
            "deployment_type": getattr(db, "deployment_type", None),
            "management_option": getattr(db, "management_option", None),
            "workload_type": getattr(db, "workload_type", None),
            "database_status": getattr(db, "database_status", None),
            "database_version": getattr(db, "database_version", None),
            "is_cluster": getattr(db, "is_cluster", None),
            "lifecycle_state": db.lifecycle_state,
            "time_created": str(db.time_created),
            "additional_details": getattr(db, "additional_details", {}),
        }

        if region:
            result["detected_region"] = region

        return result

    except Exception as e:
        error_msg = str(e)
        error_result = {
            "error": error_msg,
            "type": type(e).__name__,
            "database_id": database_id,
        }

        if "NotAuthorizedOrNotFound" in error_msg or "404" in error_msg:
            error_result["troubleshooting"] = {
                "possible_causes": [
                    "Database Management not enabled for this database",
                    "Missing IAM permissions for Database Management",
                    "Database OCID is incorrect",
                    "Regional mismatch"
                ],
                "required_permissions": [
                    "Allow group <YourGroup> to read database-family in compartment",
                    "Allow group <YourGroup> to use database-management-family in compartment"
                ],
                "next_steps": [
                    "Verify Database Management is enabled for the database",
                    "Check IAM policies",
                    "Confirm the OCID is correct"
                ]
            }

            detected_region = extract_region_from_ocid(database_id)
            if detected_region:
                error_result["detected_database_region"] = detected_region

        return error_result


def get_tablespace_usage(
    database_id: str,
) -> dict[str, Any]:
    """
    Get tablespace usage information for a managed database.

    Args:
        database_id: Managed Database OCID.

    Returns:
        Dictionary containing tablespace usage metrics.
    """
    try:
        client = get_dbm_client()

        # List tablespaces for the managed database
        response = client.list_tablespaces(
            managed_database_id=database_id,
        )

        tablespaces = []
        if hasattr(response.data, "items"):
            for ts in response.data.items:
                tablespaces.append({
                    "name": getattr(ts, "name", None),
                    "type": getattr(ts, "type", None),
                    "status": getattr(ts, "status", None),
                    "block_size_bytes": getattr(ts, "block_size_bytes", None),
                    "size_in_mbs": getattr(ts, "size_in_mbs", None),
                    "used_in_mbs": getattr(ts, "used_in_mbs", None),
                    "used_percent": getattr(ts, "used_percent", None),
                    "is_default": getattr(ts, "is_default", None),
                })
        elif isinstance(response.data, list):
            for ts in response.data:
                tablespaces.append({
                    "name": getattr(ts, "name", None),
                    "type": getattr(ts, "type", None),
                    "status": getattr(ts, "status", None),
                    "size_in_mbs": getattr(ts, "size_in_mbs", None),
                    "used_in_mbs": getattr(ts, "used_in_mbs", None),
                    "used_percent": getattr(ts, "used_percent", None),
                })

        return {
            "database_id": database_id,
            "tablespaces": tablespaces,
            "count": len(tablespaces),
        }

    except Exception as e:
        return {
            "error": str(e),
            "type": type(e).__name__,
            "database_id": database_id,
        }


def get_database_parameters(
    database_id: str,
    name: Optional[str] = None,
    is_allowed_values_included: bool = False,
) -> dict[str, Any]:
    """
    Get database parameters for a managed database.

    Args:
        database_id: Managed Database OCID.
        name: Optional parameter name filter.
        is_allowed_values_included: Include allowed values for parameters.

    Returns:
        Dictionary containing database parameters.
    """
    try:
        client = get_dbm_client()

        kwargs = {
            "managed_database_id": database_id,
            "is_allowed_values_included": is_allowed_values_included,
        }
        if name:
            kwargs["name"] = name

        response = client.list_database_parameters(
            **kwargs,
        )

        parameters = []
        if hasattr(response.data, "items"):
            for param in response.data.items:
                param_dict = {
                    "name": getattr(param, "name", None),
                    "type": getattr(param, "type", None),
                    "value": getattr(param, "value", None),
                    "display_value": getattr(param, "display_value", None),
                    "is_modified": getattr(param, "is_modified", None),
                    "is_default": getattr(param, "is_default", None),
                    "description": getattr(param, "description", None),
                }
                if is_allowed_values_included:
                    param_dict["allowed_values"] = getattr(param, "allowed_values", [])
                parameters.append(param_dict)

        return {
            "database_id": database_id,
            "parameters": parameters,
            "count": len(parameters),
        }

    except Exception as e:
        return {
            "error": str(e),
            "type": type(e).__name__,
            "database_id": database_id,
        }


def get_awr_db_report(
    database_id: str,
    awr_db_id: str,
    begin_snapshot_id: int,
    end_snapshot_id: int,
    report_format: str = "HTML",
) -> dict[str, Any]:
    """
    Get AWR (Automatic Workload Repository) report for a managed database.

    Args:
        database_id: Managed Database OCID.
        awr_db_id: AWR database ID.
        begin_snapshot_id: Begin snapshot identifier.
        end_snapshot_id: End snapshot identifier.
        report_format: Report format (HTML or TEXT).

    Returns:
        Dictionary containing AWR report data.
    """
    try:
        client = get_dbm_client()

        response = client.summarize_awr_db_report(
            managed_database_id=database_id,
            awr_db_id=awr_db_id,
            begin_snapshot_id=begin_snapshot_id,
            end_snapshot_id=end_snapshot_id,
            report_format=report_format,
        )

        return {
            "database_id": database_id,
            "awr_db_id": awr_db_id,
            "begin_snapshot_id": begin_snapshot_id,
            "end_snapshot_id": end_snapshot_id,
            "report_format": report_format,
            "report": str(response.data) if hasattr(response, "data") else None,
        }

    except Exception as e:
        return {
            "error": str(e),
            "type": type(e).__name__,
            "database_id": database_id,
        }


def list_awr_db_snapshots(
    database_id: str,
    awr_db_id: str,
    time_greater_than_or_equal_to: Optional[str] = None,
    time_less_than_or_equal_to: Optional[str] = None,
) -> dict[str, Any]:
    """
    List AWR snapshots for a managed database.

    Args:
        database_id: Managed Database OCID.
        awr_db_id: AWR database ID.
        time_greater_than_or_equal_to: Start time in ISO format.
        time_less_than_or_equal_to: End time in ISO format.

    Returns:
        Dictionary containing list of AWR snapshots.
    """
    try:
        client = get_dbm_client()

        kwargs = {
            "managed_database_id": database_id,
            "awr_db_id": awr_db_id,
        }
        if time_greater_than_or_equal_to:
            kwargs["time_greater_than_or_equal_to"] = time_greater_than_or_equal_to
        if time_less_than_or_equal_to:
            kwargs["time_less_than_or_equal_to"] = time_less_than_or_equal_to

        snapshots = list_all(
            client.list_awr_db_snapshots,
            **kwargs,
        )

        items = []
        for snap in snapshots:
            items.append({
                "snapshot_id": getattr(snap, "snapshot_id", None),
                "instance_number": getattr(snap, "instance_number", None),
                "time_snapshot_begin": str(getattr(snap, "time_snapshot_begin", None)),
                "time_snapshot_end": str(getattr(snap, "time_snapshot_end", None)),
                "time_db_startup": str(getattr(snap, "time_db_startup", None)),
                "snapshot_identifier": getattr(snap, "snapshot_identifier", None),
            })

        return {
            "database_id": database_id,
            "awr_db_id": awr_db_id,
            "snapshots": items,
            "count": len(items),
        }

    except Exception as e:
        return {
            "error": str(e),
            "type": type(e).__name__,
            "database_id": database_id,
        }


def get_database_fleet_health_metrics(
    compartment_id: str,
    compare_type: str = "HOUR",
) -> dict[str, Any]:
    """
    Get aggregated fleet health metrics for all managed databases in a compartment.

    Args:
        compartment_id: Compartment OCID.
        compare_type: Time period for comparison (HOUR, DAY, WEEK).

    Returns:
        Dictionary containing fleet health metrics.
    """
    try:
        client = get_dbm_client()

        response = client.get_database_fleet_health_metrics(
            compartment_id=compartment_id,
            compare_type=compare_type,
        )

        metrics = response.data if hasattr(response, "data") else None

        result = {
            "compartment_id": compartment_id,
            "compare_type": compare_type,
        }

        if metrics:
            result["fleet_summary"] = {
                "inventory": getattr(metrics, "fleet_summary", {}) if hasattr(metrics, "fleet_summary") else {},
            }

        return result

    except Exception as e:
        return {
            "error": str(e),
            "type": type(e).__name__,
            "compartment_id": compartment_id,
        }
