"""Database Management user and role management APIs."""

from typing import Any, Optional
import oci

from .oci_clients import get_dbm_client, list_all, extract_region_from_ocid


def list_users(
    managed_database_id: str,
    opc_named_credential_id: Optional[str] = None,
    name: Optional[str] = None,
    profile: Optional[str] = None,
) -> dict[str, Any]:
    """
    List database users.

    Args:
        managed_database_id: Managed database OCID
        opc_named_credential_id: Named credential OCID for authentication
        name: Filter by user name
        profile: OCI CLI profile name (optional)

    Returns:
        Dictionary with list of database users and their attributes
    """
    try:
        if profile:
            import os
            old_profile = os.environ.get("OCI_CLI_PROFILE")
            os.environ["OCI_CLI_PROFILE"] = profile

        try:
            # Extract region from OCID
            region = extract_region_from_ocid(managed_database_id)
            client = get_dbm_client(region=region)

            kwargs = {"managed_database_id": managed_database_id}
            if opc_named_credential_id:
                kwargs["opc_named_credential_id"] = opc_named_credential_id
            if name:
                kwargs["name"] = name

            users = list_all(client.list_users, **kwargs)

            items = []
            for user in users:
                items.append({
                    "name": user.name,
                    "status": getattr(user, "status", None),
                    "time_created": str(user.time_created) if hasattr(user, "time_created") else None,
                    "time_locked": str(user.time_locked) if hasattr(user, "time_locked") else None,
                    "time_expiring": str(user.time_expiring) if hasattr(user, "time_expiring") else None,
                    "default_tablespace": getattr(user, "default_tablespace", None),
                    "temp_tablespace": getattr(user, "temp_tablespace", None),
                    "profile": getattr(user, "profile", None),
                    "authentication": getattr(user, "authentication", None),
                })

            return {
                "managed_database_id": managed_database_id,
                "items": items,
                "count": len(items),
                "profile_used": profile or "DEFAULT",
            }

        finally:
            if profile:
                if old_profile:
                    os.environ["OCI_CLI_PROFILE"] = old_profile
                else:
                    os.environ.pop("OCI_CLI_PROFILE", None)

    except Exception as e:
        return {
            "error": str(e),
            "type": type(e).__name__,
            "managed_database_id": managed_database_id,
        }


def get_user(
    managed_database_id: str,
    user_name: str,
    opc_named_credential_id: Optional[str] = None,
    profile: Optional[str] = None,
) -> dict[str, Any]:
    """
    Get detailed information about a specific database user.

    Args:
        managed_database_id: Managed database OCID
        user_name: Database user name
        opc_named_credential_id: Named credential OCID for authentication
        profile: OCI CLI profile name (optional)

    Returns:
        Dictionary with detailed user information including privileges and roles
    """
    try:
        if profile:
            import os
            old_profile = os.environ.get("OCI_CLI_PROFILE")
            os.environ["OCI_CLI_PROFILE"] = profile

        try:
            region = extract_region_from_ocid(managed_database_id)
            client = get_dbm_client(region=region)

            kwargs = {
                "managed_database_id": managed_database_id,
                "user_name": user_name,
            }
            if opc_named_credential_id:
                kwargs["opc_named_credential_id"] = opc_named_credential_id

            response = client.get_user(**kwargs)
            user = response.data

            return {
                "managed_database_id": managed_database_id,
                "user": {
                    "name": user.name,
                    "status": getattr(user, "status", None),
                    "time_created": str(user.time_created) if hasattr(user, "time_created") else None,
                    "time_locked": str(user.time_locked) if hasattr(user, "time_locked") else None,
                    "default_tablespace": getattr(user, "default_tablespace", None),
                    "temp_tablespace": getattr(user, "temp_tablespace", None),
                    "profile": getattr(user, "profile", None),
                    "authentication": getattr(user, "authentication", None),
                    "editions_enabled": getattr(user, "editions_enabled", None),
                },
                "profile_used": profile or "DEFAULT",
            }

        finally:
            if profile:
                if old_profile:
                    os.environ["OCI_CLI_PROFILE"] = old_profile
                else:
                    os.environ.pop("OCI_CLI_PROFILE", None)

    except Exception as e:
        return {
            "error": str(e),
            "type": type(e).__name__,
            "managed_database_id": managed_database_id,
            "user_name": user_name,
        }


def list_roles(
    managed_database_id: str,
    opc_named_credential_id: Optional[str] = None,
    name: Optional[str] = None,
    profile: Optional[str] = None,
) -> dict[str, Any]:
    """
    List database roles.

    Args:
        managed_database_id: Managed database OCID
        opc_named_credential_id: Named credential OCID for authentication
        name: Filter by role name
        profile: OCI CLI profile name (optional)

    Returns:
        Dictionary with list of database roles
    """
    try:
        if profile:
            import os
            old_profile = os.environ.get("OCI_CLI_PROFILE")
            os.environ["OCI_CLI_PROFILE"] = profile

        try:
            region = extract_region_from_ocid(managed_database_id)
            client = get_dbm_client(region=region)

            kwargs = {"managed_database_id": managed_database_id}
            if opc_named_credential_id:
                kwargs["opc_named_credential_id"] = opc_named_credential_id
            if name:
                kwargs["name"] = name

            roles = list_all(client.list_roles, **kwargs)

            items = []
            for role in roles:
                items.append({
                    "name": role.name,
                    "authentication_type": getattr(role, "authentication_type", None),
                    "password_required": getattr(role, "password_required", None),
                })

            return {
                "managed_database_id": managed_database_id,
                "items": items,
                "count": len(items),
                "profile_used": profile or "DEFAULT",
            }

        finally:
            if profile:
                if old_profile:
                    os.environ["OCI_CLI_PROFILE"] = old_profile
                else:
                    os.environ.pop("OCI_CLI_PROFILE", None)

    except Exception as e:
        return {
            "error": str(e),
            "type": type(e).__name__,
            "managed_database_id": managed_database_id,
        }


def list_system_privileges(
    managed_database_id: str,
    user_name: str,
    opc_named_credential_id: Optional[str] = None,
    name: Optional[str] = None,
    profile: Optional[str] = None,
) -> dict[str, Any]:
    """
    List system privileges granted to a user.

    Args:
        managed_database_id: Managed database OCID
        user_name: Database user name
        opc_named_credential_id: Named credential OCID for authentication
        name: Filter by privilege name
        profile: OCI CLI profile name (optional)

    Returns:
        Dictionary with list of system privileges
    """
    try:
        if profile:
            import os
            old_profile = os.environ.get("OCI_CLI_PROFILE")
            os.environ["OCI_CLI_PROFILE"] = profile

        try:
            region = extract_region_from_ocid(managed_database_id)
            client = get_dbm_client(region=region)

            kwargs = {
                "managed_database_id": managed_database_id,
                "user_name": user_name,
            }
            if opc_named_credential_id:
                kwargs["opc_named_credential_id"] = opc_named_credential_id
            if name:
                kwargs["name"] = name

            privileges = list_all(client.list_system_privileges, **kwargs)

            items = []
            for priv in privileges:
                items.append({
                    "name": priv.name,
                    "admin_option": getattr(priv, "admin_option", None),
                    "common": getattr(priv, "common", None),
                    "inherited": getattr(priv, "inherited", None),
                })

            return {
                "managed_database_id": managed_database_id,
                "user_name": user_name,
                "items": items,
                "count": len(items),
                "profile_used": profile or "DEFAULT",
            }

        finally:
            if profile:
                if old_profile:
                    os.environ["OCI_CLI_PROFILE"] = old_profile
                else:
                    os.environ.pop("OCI_CLI_PROFILE", None)

    except Exception as e:
        return {
            "error": str(e),
            "type": type(e).__name__,
            "managed_database_id": managed_database_id,
            "user_name": user_name,
        }


def list_consumer_group_privileges(
    managed_database_id: str,
    user_name: str,
    opc_named_credential_id: Optional[str] = None,
    name: Optional[str] = None,
    profile: Optional[str] = None,
) -> dict[str, Any]:
    """
    List consumer group privileges for a user.

    Consumer groups are used for resource management in Oracle databases.

    Args:
        managed_database_id: Managed database OCID
        user_name: Database user name
        opc_named_credential_id: Named credential OCID for authentication
        name: Filter by consumer group name
        profile: OCI CLI profile name (optional)

    Returns:
        Dictionary with list of consumer group privileges
    """
    try:
        if profile:
            import os
            old_profile = os.environ.get("OCI_CLI_PROFILE")
            os.environ["OCI_CLI_PROFILE"] = profile

        try:
            region = extract_region_from_ocid(managed_database_id)
            client = get_dbm_client(region=region)

            kwargs = {
                "managed_database_id": managed_database_id,
                "user_name": user_name,
            }
            if opc_named_credential_id:
                kwargs["opc_named_credential_id"] = opc_named_credential_id
            if name:
                kwargs["name"] = name

            privileges = list_all(client.list_consumer_group_privileges, **kwargs)

            items = []
            for priv in privileges:
                items.append({
                    "name": priv.name,
                    "grant_option": getattr(priv, "grant_option", None),
                    "initial_group": getattr(priv, "initial_group", None),
                })

            return {
                "managed_database_id": managed_database_id,
                "user_name": user_name,
                "items": items,
                "count": len(items),
                "profile_used": profile or "DEFAULT",
            }

        finally:
            if profile:
                if old_profile:
                    os.environ["OCI_CLI_PROFILE"] = old_profile
                else:
                    os.environ.pop("OCI_CLI_PROFILE", None)

    except Exception as e:
        return {
            "error": str(e),
            "type": type(e).__name__,
            "managed_database_id": managed_database_id,
            "user_name": user_name,
        }


def list_proxy_users(
    managed_database_id: str,
    user_name: str,
    opc_named_credential_id: Optional[str] = None,
    name: Optional[str] = None,
    profile: Optional[str] = None,
) -> dict[str, Any]:
    """
    List proxy users for a database user.

    Proxy users allow one user to connect as another user.

    Args:
        managed_database_id: Managed database OCID
        user_name: Database user name
        opc_named_credential_id: Named credential OCID for authentication
        name: Filter by proxy user name
        profile: OCI CLI profile name (optional)

    Returns:
        Dictionary with list of proxy users
    """
    try:
        if profile:
            import os
            old_profile = os.environ.get("OCI_CLI_PROFILE")
            os.environ["OCI_CLI_PROFILE"] = profile

        try:
            region = extract_region_from_ocid(managed_database_id)
            client = get_dbm_client(region=region)

            kwargs = {
                "managed_database_id": managed_database_id,
                "user_name": user_name,
            }
            if opc_named_credential_id:
                kwargs["opc_named_credential_id"] = opc_named_credential_id
            if name:
                kwargs["name"] = name

            proxy_users = list_all(client.list_proxy_users, **kwargs)

            items = []
            for proxy in proxy_users:
                items.append({
                    "name": proxy.name,
                    "authentication": getattr(proxy, "authentication", None),
                    "flags": getattr(proxy, "flags", None),
                })

            return {
                "managed_database_id": managed_database_id,
                "user_name": user_name,
                "items": items,
                "count": len(items),
                "profile_used": profile or "DEFAULT",
            }

        finally:
            if profile:
                if old_profile:
                    os.environ["OCI_CLI_PROFILE"] = old_profile
                else:
                    os.environ.pop("OCI_CLI_PROFILE", None)

    except Exception as e:
        return {
            "error": str(e),
            "type": type(e).__name__,
            "managed_database_id": managed_database_id,
            "user_name": user_name,
        }
