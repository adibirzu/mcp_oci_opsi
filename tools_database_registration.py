"""FastMCP tools for OCI Database Registration and Enablement."""

from typing import Any, Optional

from .oci_clients import get_opsi_client, get_dbm_client


def enable_database_insight(
    database_id: str,
    compartment_id: str,
    entity_source: str = "AUTONOMOUS_DATABASE",
    credential_details: Optional[dict] = None,
) -> dict[str, Any]:
    """
    Enable Operations Insights for a database.

    Registers a database with Operations Insights to start collecting performance data.

    Args:
        database_id: Database OCID to enable insights for.
        compartment_id: Compartment OCID where the database insight will be created.
        entity_source: Database type (AUTONOMOUS_DATABASE, EM_MANAGED_EXTERNAL_DATABASE, etc.).
        credential_details: Optional credential details for database connection.

    Returns:
        Dictionary containing enablement status and database insight OCID.

    Example:
        >>> result = enable_database_insight(
        ...     database_id="ocid1.autonomousdatabase.oc1..aaa...",
        ...     compartment_id="ocid1.compartment.oc1..bbb..."
        ... )
        >>> print(f"Database Insight ID: {result['database_insight_id']}")
    """
    try:
        client = get_opsi_client()

        # Try using the SDK method
        try:
            from oci.opsi.models import (
                CreateDatabaseInsightDetails,
                CreateAutonomousDatabaseInsightDetails,
                CreateEmManagedExternalDatabaseInsightDetails,
            )

            # Create appropriate insight details based on entity source
            if entity_source == "AUTONOMOUS_DATABASE":
                insight_details = CreateAutonomousDatabaseInsightDetails(
                    compartment_id=compartment_id,
                    database_id=database_id,
                    entity_source=entity_source,
                )
            else:
                # For EM managed or other database types
                insight_details = CreateEmManagedExternalDatabaseInsightDetails(
                    compartment_id=compartment_id,
                    enterprise_manager_bridge_id=credential_details.get("em_bridge_id") if credential_details else None,
                    enterprise_manager_entity_identifier=database_id,
                    entity_source=entity_source,
                )

            response = client.create_database_insight(
                create_database_insight_details=insight_details,
            )

            return {
                "database_id": database_id,
                "database_insight_id": response.data.id,
                "status": response.data.status,
                "lifecycle_state": response.data.lifecycle_state,
                "entity_source": entity_source,
                "message": "Database insight created successfully",
            }

        except (AttributeError, ImportError) as e:
            # Fallback to raw API call
            path = "/20200630/databaseInsights"

            body = {
                "compartmentId": compartment_id,
                "databaseId": database_id,
                "entitySource": entity_source,
            }

            if credential_details:
                body["credentialDetails"] = credential_details

            response = client.base_client.call_api(
                resource_path=path,
                method="POST",
                body=body,
                response_type="object",
            )

            if response.status in [200, 201]:
                data = response.data
                return {
                    "database_id": database_id,
                    "database_insight_id": getattr(data, "id", None),
                    "status": getattr(data, "status", None),
                    "message": "Database insight created successfully",
                }

            return {
                "error": f"API call failed with status {response.status}",
                "database_id": database_id,
            }

    except Exception as e:
        error_msg = str(e).lower()
        if "already exists" in error_msg or "already enabled" in error_msg:
            return {
                "database_id": database_id,
                "status": "already_enabled",
                "message": "Database insight already exists for this database",
            }

        return {
            "error": str(e),
            "type": type(e).__name__,
            "database_id": database_id,
        }


def disable_database_insight(
    database_insight_id: str,
) -> dict[str, Any]:
    """
    Disable Operations Insights for a database.

    Args:
        database_insight_id: Database Insight OCID to disable.

    Returns:
        Dictionary containing disablement status.
    """
    try:
        client = get_opsi_client()

        response = client.delete_database_insight(
            database_insight_id=database_insight_id,
        )

        return {
            "database_insight_id": database_insight_id,
            "status": "deleted",
            "message": "Database insight disabled successfully",
        }

    except Exception as e:
        return {
            "error": str(e),
            "type": type(e).__name__,
            "database_insight_id": database_insight_id,
        }


def enable_database_management(
    database_id: str,
    service_name: str,
    credential_details: dict,
    enable_management_type: str = "ADVANCED",
) -> dict[str, Any]:
    """
    Enable Database Management for a database.

    Args:
        database_id: Database OCID to enable management for.
        service_name: Database service name for connection.
        credential_details: Credentials for database connection (username, password, role).
        enable_management_type: Management type (BASIC or ADVANCED).

    Returns:
        Dictionary containing enablement status and work request OCID.

    Example:
        >>> result = enable_database_management(
        ...     database_id="ocid1.autonomousdatabase.oc1..aaa...",
        ...     service_name="mydb_high",
        ...     credential_details={
        ...         "userName": "admin",
        ...         "passwordSecretId": "ocid1.vaultsecret...",
        ...         "role": "SYSDBA"
        ...     }
        ... )
    """
    try:
        # This uses the database service API, not database management API
        import oci

        config = oci.config.from_file()
        database_client = oci.database.DatabaseClient(config)

        try:
            from oci.database.models import EnableDatabaseManagementDetails

            enable_details = EnableDatabaseManagementDetails(
                credential_details=credential_details,
                private_end_point_id=None,  # Public endpoint
                management_type=enable_management_type,
                service_name=service_name,
            )

            response = database_client.enable_database_management(
                database_id=database_id,
                enable_database_management_details=enable_details,
            )

            result = {
                "database_id": database_id,
                "management_type": enable_management_type,
                "status": "enabled" if response.status == 200 else "pending",
            }

            # Check for work request
            if hasattr(response, "opc_work_request_id") and response.opc_work_request_id:
                result["work_request_id"] = response.opc_work_request_id
            elif hasattr(response, "headers"):
                work_req = response.headers.get("opc-work-request-id")
                if work_req:
                    result["work_request_id"] = work_req

            return result

        except Exception as e:
            return {
                "error": str(e),
                "type": type(e).__name__,
                "database_id": database_id,
            }

    except Exception as e:
        return {
            "error": str(e),
            "type": type(e).__name__,
            "database_id": database_id,
        }


def get_database_insight_status(
    database_id: str,
    compartment_id: str,
) -> dict[str, Any]:
    """
    Check if Operations Insights is enabled for a database.

    Args:
        database_id: Database OCID to check.
        compartment_id: Compartment OCID containing the database.

    Returns:
        Dictionary containing insight enablement status.
    """
    try:
        client = get_opsi_client()

        # List database insights and find matching database
        response = client.list_database_insights(
            compartment_id=compartment_id,
        )

        insights = []
        for insight in response.data:
            if insight.database_id == database_id:
                insights.append({
                    "database_insight_id": insight.id,
                    "database_id": insight.database_id,
                    "database_name": insight.database_name,
                    "status": insight.status,
                    "lifecycle_state": insight.lifecycle_state,
                    "entity_source": getattr(insight, "entity_source", None),
                })

        return {
            "database_id": database_id,
            "insights_enabled": len(insights) > 0,
            "insights": insights,
            "count": len(insights),
        }

    except Exception as e:
        return {
            "error": str(e),
            "type": type(e).__name__,
            "database_id": database_id,
        }


def change_database_insight_compartment(
    database_insight_id: str,
    target_compartment_id: str,
) -> dict[str, Any]:
    """
    Move a database insight to a different compartment.

    Args:
        database_insight_id: Database Insight OCID to move.
        target_compartment_id: Target compartment OCID.

    Returns:
        Dictionary containing operation status.
    """
    try:
        client = get_opsi_client()

        try:
            from oci.opsi.models import ChangeDatabaseInsightCompartmentDetails

            change_details = ChangeDatabaseInsightCompartmentDetails(
                compartment_id=target_compartment_id,
            )

            response = client.change_database_insight_compartment(
                database_insight_id=database_insight_id,
                change_database_insight_compartment_details=change_details,
            )

            return {
                "database_insight_id": database_insight_id,
                "target_compartment_id": target_compartment_id,
                "status": "success",
                "message": "Database insight moved to new compartment",
            }

        except Exception as e:
            return {
                "error": str(e),
                "type": type(e).__name__,
                "database_insight_id": database_insight_id,
            }

    except Exception as e:
        return {
            "error": str(e),
            "type": type(e).__name__,
            "database_insight_id": database_insight_id,
        }


def update_database_insight(
    database_insight_id: str,
    freeform_tags: Optional[dict] = None,
    defined_tags: Optional[dict] = None,
) -> dict[str, Any]:
    """
    Update database insight properties like tags.

    Args:
        database_insight_id: Database Insight OCID to update.
        freeform_tags: Optional freeform tags dictionary.
        defined_tags: Optional defined tags dictionary.

    Returns:
        Dictionary containing update status.
    """
    try:
        client = get_opsi_client()

        try:
            from oci.opsi.models import UpdateDatabaseInsightDetails

            update_details = UpdateDatabaseInsightDetails(
                freeform_tags=freeform_tags,
                defined_tags=defined_tags,
            )

            response = client.update_database_insight(
                database_insight_id=database_insight_id,
                update_database_insight_details=update_details,
            )

            return {
                "database_insight_id": database_insight_id,
                "status": "updated",
                "lifecycle_state": response.data.lifecycle_state if hasattr(response, "data") else None,
                "message": "Database insight updated successfully",
            }

        except Exception as e:
            return {
                "error": str(e),
                "type": type(e).__name__,
                "database_insight_id": database_insight_id,
            }

    except Exception as e:
        return {
            "error": str(e),
            "type": type(e).__name__,
            "database_insight_id": database_insight_id,
        }


def get_database_details_from_ocid(
    database_id: str,
) -> dict[str, Any]:
    """
    Get database details using the Database service API.

    Retrieves comprehensive information about a database from OCI Database service.

    Args:
        database_id: Database OCID.

    Returns:
        Dictionary containing database details.
    """
    try:
        import oci

        config = oci.config.from_file()
        database_client = oci.database.DatabaseClient(config)

        # Try to get as autonomous database first
        try:
            response = database_client.get_autonomous_database(
                autonomous_database_id=database_id,
            )

            db = response.data
            return {
                "id": db.id,
                "display_name": db.display_name,
                "db_name": db.db_name,
                "compartment_id": db.compartment_id,
                "lifecycle_state": db.lifecycle_state,
                "db_version": db.db_version,
                "db_workload": getattr(db, "db_workload", None),
                "data_storage_size_in_tbs": getattr(db, "data_storage_size_in_tbs", None),
                "cpu_core_count": db.cpu_core_count,
                "is_auto_scaling_enabled": getattr(db, "is_auto_scaling_enabled", None),
                "is_dedicated": getattr(db, "is_dedicated", None),
                "subnet_id": getattr(db, "subnet_id", None),
                "connection_strings": getattr(db, "connection_strings", {}) if hasattr(db, "connection_strings") else {},
                "time_created": str(db.time_created),
                "database_type": "AUTONOMOUS_DATABASE",
            }

        except:
            # Try as regular database
            response = database_client.get_database(
                database_id=database_id,
            )

            db = response.data
            return {
                "id": db.id,
                "db_name": db.db_name,
                "compartment_id": db.compartment_id,
                "lifecycle_state": db.lifecycle_state,
                "db_version": getattr(db, "db_version", None),
                "db_home_id": db.db_home_id,
                "db_system_id": getattr(db, "db_system_id", None),
                "time_created": str(db.time_created),
                "database_type": "DATABASE",
            }

    except Exception as e:
        return {
            "error": str(e),
            "type": type(e).__name__,
            "database_id": database_id,
        }
