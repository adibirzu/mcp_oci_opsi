"""FastMCP tools for OCI Database Management SQL Watch."""

from typing import Any

from .oci_clients import get_dbm_client


def get_status(database_id: str) -> dict[str, Any]:
    """
    Get SQL Watch status for a managed database.

    Retrieves the Database Management feature status to check if SQL Watch
    is enabled for the specified managed database.

    Args:
        database_id: Managed Database OCID.

    Returns:
        Dictionary containing SQL Watch status and managed database details.

    Example:
        >>> result = get_status("ocid1.manageddatabase.oc1..aaaaaa...")
        >>> if result["sqlwatch_enabled"]:
        ...     print("SQL Watch is enabled")
        >>> else:
        ...     print("SQL Watch is disabled")
    """
    try:
        client = get_dbm_client()

        # Get managed database details
        managed_db = client.get_managed_database(managed_database_id=database_id)

        result = {
            "database_id": database_id,
            "database_name": getattr(managed_db.data, "name", None),
            "database_type": getattr(managed_db.data, "database_type", None),
            "database_sub_type": getattr(managed_db.data, "database_sub_type", None),
            "management_option": getattr(managed_db.data, "management_option", None),
            "deployment_type": getattr(managed_db.data, "deployment_type", None),
            "is_cluster": getattr(managed_db.data, "is_cluster", None),
            "lifecycle_state": getattr(managed_db.data, "lifecycle_state", None),
        }

        # Check for database management features
        # SQL Watch is typically part of the database management features
        sqlwatch_enabled = False
        feature_details = {}

        # Try to get feature configurations
        try:
            # List database management features for this database
            features_response = client.list_database_management_features(
                managed_database_id=database_id,
            )

            if hasattr(features_response, "data"):
                features = features_response.data
                feature_list = features if isinstance(features, list) else getattr(features, "items", [])

                for feature in feature_list:
                    feature_name = getattr(feature, "feature", None) or getattr(feature, "name", None)
                    feature_status = getattr(feature, "status", None)

                    feature_details[str(feature_name)] = {
                        "status": str(feature_status),
                        "enabled": str(feature_status).upper() == "ENABLED",
                    }

                    # Check for SQL Watch or related features
                    if feature_name and "SQLWATCH" in str(feature_name).upper():
                        sqlwatch_enabled = str(feature_status).upper() == "ENABLED"

        except AttributeError:
            # Feature list API might not be available, try alternate method
            # Check managed database properties for feature flags
            if hasattr(managed_db.data, "database_management_config"):
                db_mgmt_config = managed_db.data.database_management_config
                if hasattr(db_mgmt_config, "features"):
                    for feature in db_mgmt_config.features:
                        feature_name = getattr(feature, "feature", None)
                        feature_status = getattr(feature, "status", None)

                        feature_details[str(feature_name)] = {
                            "status": str(feature_status),
                            "enabled": str(feature_status).upper() == "ENABLED",
                        }

                        if feature_name and "SQLWATCH" in str(feature_name).upper():
                            sqlwatch_enabled = str(feature_status).upper() == "ENABLED"

        result["sqlwatch_enabled"] = sqlwatch_enabled
        result["features"] = feature_details
        result["features_count"] = len(feature_details)

        return result

    except Exception as e:
        return {
            "error": str(e),
            "type": type(e).__name__,
            "database_id": database_id,
        }


def enable_on_db(database_id: str) -> dict[str, Any]:
    """
    Enable SQL Watch on a managed database.

    Submits a request to enable the SQL Watch feature for the specified
    managed database. This operation may be asynchronous and return a
    work request OCID for tracking.

    Args:
        database_id: Managed Database OCID.

    Returns:
        Dictionary containing operation status and work request OCID if applicable.

    Example:
        >>> result = enable_on_db("ocid1.manageddatabase.oc1..aaaaaa...")
        >>> if "work_request_id" in result:
        ...     print(f"Work request: {result['work_request_id']}")
        >>> elif "success" in result:
        ...     print("SQL Watch enabled successfully")

    Note:
        - Enabling SQL Watch may require specific IAM permissions
        - The operation may take several minutes to complete
        - Check the work request status to monitor progress
    """
    try:
        client = get_dbm_client()

        # Try to enable SQL Watch using the Database Management feature API
        try:
            from oci.database_management.models import EnableDatabaseManagementFeatureDetails

            # Create enable feature details
            enable_details = EnableDatabaseManagementFeatureDetails(
                feature="SQLWATCH",
            )

            # Enable the feature
            response = client.enable_database_management_feature(
                managed_database_id=database_id,
                enable_database_management_feature_details=enable_details,
            )

            result = {
                "database_id": database_id,
                "feature": "SQLWATCH",
                "status": "enabled" if response.status == 200 else "pending",
            }

            # Check for work request
            if hasattr(response, "opc_work_request_id") and response.opc_work_request_id:
                result["work_request_id"] = response.opc_work_request_id
            elif hasattr(response.headers, "opc-work-request-id"):
                result["work_request_id"] = response.headers["opc-work-request-id"]

            # Include response data if available
            if hasattr(response, "data") and response.data:
                result["response_data"] = {
                    "id": getattr(response.data, "id", None),
                    "status": getattr(response.data, "status", None),
                    "time_accepted": str(getattr(response.data, "time_accepted", None)),
                }

            return result

        except (AttributeError, ImportError):
            # Fall back to raw API call if SDK model not available
            path = f"/20201101/managedDatabases/{database_id}/actions/enableDatabaseManagement"

            body = {
                "feature": "SQLWATCH",
            }

            response = client.base_client.call_api(
                resource_path=path,
                method="POST",
                body=body,
                response_type="object",
            )

            result = {
                "database_id": database_id,
                "feature": "SQLWATCH",
                "status": "enabled" if response.status == 200 else "pending",
            }

            # Extract work request ID from headers
            if hasattr(response, "headers"):
                opc_work_request_id = (
                    response.headers.get("opc-work-request-id") or
                    response.headers.get("opc_work_request_id")
                )
                if opc_work_request_id:
                    result["work_request_id"] = opc_work_request_id

            # Include response data
            if hasattr(response, "data"):
                result["response_data"] = str(response.data)

            return result

    except Exception as e:
        # Check if error is due to feature already being enabled
        error_message = str(e).lower()
        if "already enabled" in error_message or "already exists" in error_message:
            return {
                "database_id": database_id,
                "feature": "SQLWATCH",
                "status": "already_enabled",
                "message": "SQL Watch is already enabled on this database",
            }

        return {
            "error": str(e),
            "type": type(e).__name__,
            "database_id": database_id,
            "feature": "SQLWATCH",
        }


def disable_on_db(database_id: str) -> dict[str, Any]:
    """
    Disable SQL Watch on a managed database.

    Submits a request to disable the SQL Watch feature for the specified
    managed database. This operation may be asynchronous and return a
    work request OCID for tracking.

    Args:
        database_id: Managed Database OCID.

    Returns:
        Dictionary containing operation status and work request OCID if applicable.

    Example:
        >>> result = disable_on_db("ocid1.manageddatabase.oc1..aaaaaa...")
        >>> if "work_request_id" in result:
        ...     print(f"Work request: {result['work_request_id']}")
    """
    try:
        client = get_dbm_client()

        try:
            from oci.database_management.models import DisableDatabaseManagementFeatureDetails

            # Create disable feature details
            disable_details = DisableDatabaseManagementFeatureDetails(
                feature="SQLWATCH",
            )

            # Disable the feature
            response = client.disable_database_management_feature(
                managed_database_id=database_id,
                disable_database_management_feature_details=disable_details,
            )

            result = {
                "database_id": database_id,
                "feature": "SQLWATCH",
                "status": "disabled" if response.status == 200 else "pending",
            }

            # Check for work request
            if hasattr(response, "opc_work_request_id") and response.opc_work_request_id:
                result["work_request_id"] = response.opc_work_request_id
            elif hasattr(response.headers, "opc-work-request-id"):
                result["work_request_id"] = response.headers["opc-work-request-id"]

            return result

        except (AttributeError, ImportError):
            # Fall back to raw API call
            path = f"/20201101/managedDatabases/{database_id}/actions/disableDatabaseManagement"

            body = {
                "feature": "SQLWATCH",
            }

            response = client.base_client.call_api(
                resource_path=path,
                method="POST",
                body=body,
                response_type="object",
            )

            result = {
                "database_id": database_id,
                "feature": "SQLWATCH",
                "status": "disabled" if response.status == 200 else "pending",
            }

            # Extract work request ID
            if hasattr(response, "headers"):
                opc_work_request_id = (
                    response.headers.get("opc-work-request-id") or
                    response.headers.get("opc_work_request_id")
                )
                if opc_work_request_id:
                    result["work_request_id"] = opc_work_request_id

            return result

    except Exception as e:
        return {
            "error": str(e),
            "type": type(e).__name__,
            "database_id": database_id,
            "feature": "SQLWATCH",
        }


def get_work_request_status(work_request_id: str) -> dict[str, Any]:
    """
    Get the status of a Database Management work request.

    Retrieves the current status of a work request created by SQL Watch
    enable/disable operations.

    Args:
        work_request_id: Work Request OCID.

    Returns:
        Dictionary containing work request status and progress.

    Example:
        >>> result = get_work_request_status("ocid1.workrequest.oc1..aaaaaa...")
        >>> print(f"Status: {result['status']}, Progress: {result['percent_complete']}%")
    """
    try:
        client = get_dbm_client()

        response = client.get_work_request(work_request_id=work_request_id)

        work_request = response.data

        result = {
            "work_request_id": work_request_id,
            "operation_type": getattr(work_request, "operation_type", None),
            "status": getattr(work_request, "status", None),
            "percent_complete": getattr(work_request, "percent_complete", None),
            "time_accepted": str(getattr(work_request, "time_accepted", None)),
            "time_started": str(getattr(work_request, "time_started", None)),
            "time_finished": str(getattr(work_request, "time_finished", None)),
        }

        # Include resources if available
        if hasattr(work_request, "resources") and work_request.resources:
            result["resources"] = [
                {
                    "entity_type": getattr(resource, "entity_type", None),
                    "entity_id": getattr(resource, "entity_id", None),
                    "action_type": getattr(resource, "action_type", None),
                }
                for resource in work_request.resources
            ]

        return result

    except Exception as e:
        return {
            "error": str(e),
            "type": type(e).__name__,
            "work_request_id": work_request_id,
        }
