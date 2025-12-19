"""Admin server for profile and configuration management.

This server provides tools for managing OCI profiles, authentication,
diagnostics, and server configuration.

Follows MCP Best Practices:
- Tool annotations for hints (readOnlyHint, destructiveHint, etc.)
- Examples in all docstrings
"""

from typing import Any, Dict, List, Optional
import os
import logging

from fastmcp import FastMCP, Context
from fastmcp.exceptions import ToolError
from fastmcp.tools.tool import ToolAnnotations

from ..config import (
    get_oci_config,
    get_current_profile,
    list_available_profiles,
    get_compartment_id,
)
from ..auth.hybrid_auth import (
    get_authenticated_user,
    detect_auth_mode,
    AuthMode,
)
from ..auth.oci_oauth import (
    is_oauth_configured,
    get_oauth_config_status,
    generate_encryption_key,
    generate_jwt_signing_key,
)
from ..cache import get_cache

logger = logging.getLogger(__name__)


# Create admin sub-server
admin_server = FastMCP(
    name="admin-tools",
    instructions="""
    Admin tools provide profile management, authentication diagnostics,
    and server configuration capabilities.

    Performance: Most operations are local and instant.
    Rate Limits: Unlimited (no API calls except validate_oci_profile).
    """,
)

# Prebuilt troubleshooting answers (local, no API calls)
TROUBLESHOOTING_PLAYBOOK = [
    {
        "issue": "High CPU on database",
        "recommendation": "Check fleet summary, then SQL insights and ADDM findings for the database.",
        "tools": [
            {"name": "cache_get_fleet_summary", "reason": "Instant view of which DBs are hot"},
            {"name": "opsi_summarize_sql_insights", "reason": "Find top SQL contributing to CPU"},
            {"name": "opsi_summarize_addm_db_findings", "reason": "Get ADDM recommendations"},
            {"name": "dbm_get_awr_report", "reason": "Deep dive if needed"},
        ],
    },
    {
        "issue": "Storage nearly full",
        "recommendation": "Inspect tablespace usage and historical capacity trend.",
        "tools": [
            {"name": "dbm_get_tablespace_usage", "reason": "See current free/used per tablespace"},
            {"name": "opsi_get_database_capacity_trend", "reason": "Understand growth history"},
            {"name": "opsi_get_database_resource_forecast", "reason": "Predict when it will run out"},
        ],
    },
    {
        "issue": "Slow SQL performance",
        "recommendation": "Identify regressed SQL and plan changes, then review execution plans.",
        "tools": [
            {"name": "opsi_summarize_sql_insights", "reason": "Spot anomalous or regressed SQL"},
            {"name": "opsi_summarize_sql_plan_insights", "reason": "Compare execution plans"},
            {"name": "dbm_get_awr_report", "reason": "Deep workload analysis"},
        ],
    },
    {
        "issue": "Fleet overview / inventory",
        "recommendation": "Use cache-first tools for zero-API discovery.",
        "tools": [
            {"name": "cache_get_fleet_summary", "reason": "Instant counts and breakdowns"},
            {"name": "cache_search_databases", "reason": "Find DBs by name/compartment instantly"},
            {"name": "opsi_list_database_insights", "reason": "Live list with pagination if needed"},
        ],
    },
    {
        "issue": "Agent readiness / connectivity",
        "recommendation": "Verify MCP health and credentials before running diagnostics.",
        "tools": [
            {"name": "ping", "reason": "Cheap readiness check"},
            {"name": "whoami", "reason": "Confirm identity and profile"},
            {"name": "opsi_health", "reason": "OPSI tool availability"},
            {"name": "dbm_health", "reason": "DBM tool availability"},
        ],
    },
]


@admin_server.tool(
    annotations=ToolAnnotations(
        read_only_hint=True,
        destructive_hint=False,
        idempotent_hint=True,
        open_world_hint=False,
    )
)
async def ping(ctx: Context = None) -> Dict[str, Any]:
    """
    Simple health check to verify server connectivity.

    Returns:
        Health status and server information

    Examples:
        - ping() - Check if server is running
        - Use as first call to verify MCP connection
    """
    if ctx:
        await ctx.debug("Health check ping")

    return {
        "status": "ok",
        "message": "MCP OCI OPSI Server is running",
        "version": "3.0.0",
        "auth_mode": detect_auth_mode().value,
        "cache_last_updated": get_cache().cache_data.get("metadata", {}).get("last_updated"),
    }


@admin_server.tool(
    annotations=ToolAnnotations(
        read_only_hint=True,
        destructive_hint=False,
        idempotent_hint=True,
        open_world_hint=False,
    )
)
async def whoami(ctx: Context = None) -> Dict[str, Any]:
    """
    Get information about the authenticated user and current context.

    Returns:
        User identity, tenancy, region, and authentication mode

    Examples:
        - whoami() - Get current user details
        - Use to verify authentication is working correctly
        - Check which profile/tenancy is active
    """
    if ctx:
        await ctx.info("Getting authenticated user information")

    try:
        user = get_authenticated_user()

        return {
            "user_id": user.user_id,
            "tenancy_id": user.tenancy_id,
            "region": user.region,
            "auth_mode": user.auth_mode.value,
            "profile": user.profile,
            "email": user.email,
            "display_name": user.display_name,
        }

    except Exception as e:
        raise ToolError(f"Failed to get user information: {e}")


@admin_server.tool(
    annotations=ToolAnnotations(
        read_only_hint=True,
        destructive_hint=False,
        idempotent_hint=True,
        open_world_hint=True,
    )
)
async def get_troubleshooting_playbook(issue: Optional[str] = None, ctx: Context = None) -> Dict[str, Any]:
    """
    Get prebuilt troubleshooting answers and recommended tools.

    Args:
        issue: Optional keyword (e.g., "CPU", "storage", "sql", "fleet", "health")

    Returns:
        Playbook entries with recommended tools and reasons

    Examples:
        - get_troubleshooting_playbook()
        - get_troubleshooting_playbook(issue="cpu")
    """
    if ctx:
        await ctx.info("Retrieving troubleshooting playbook")

    filtered = TROUBLESHOOTING_PLAYBOOK
    if issue:
        key = issue.lower()
        filtered = [entry for entry in TROUBLESHOOTING_PLAYBOOK if key in entry["issue"].lower()]

    return {
        "count": len(filtered),
        "entries": filtered,
        "notes": "Use cache_* tools first where available; rate limits may apply on live OPSI/DBM calls.",
    }


@admin_server.tool(
    annotations=ToolAnnotations(
        read_only_hint=True,
        destructive_hint=False,
        idempotent_hint=True,
        open_world_hint=True,
    )
)
async def list_prompts(ctx: Context = None) -> Dict[str, Any]:
    """
    List prebuilt prompt templates for common DBA troubleshooting flows.

    Returns:
        Prompt definitions with name, description, and template text.
    """
    if ctx:
        await ctx.debug("Listing prompt templates")

    prompts = [
        {
            "name": "cpu-hotspot",
            "description": "Guide the model to diagnose high-CPU databases using cache then OPSI/DBM tools.",
            "template": (
                "You are diagnosing high CPU on Oracle databases. "
                "First call cache_get_fleet_summary and cache_search_databases to identify hot DBs. "
                "Then use opsi_summarize_sql_insights and opsi_summarize_addm_db_findings on the target DB. "
                "If issues persist, pull dbm_get_awr_report for deep dive. "
                "Always recommend actions with thresholds (CPU >80%)."
            ),
        },
        {
            "name": "storage-capacity",
            "description": "Capacity troubleshooting prompt using tablespace and OPSI growth data.",
            "template": (
                "Investigate storage risk. Start with cache_get_fleet_summary to find DBs near limits. "
                "Use dbm_get_tablespace_usage to see free/used, then "
                "opsi_get_database_capacity_trend and opsi_get_database_resource_forecast for growth/forecast. "
                "Recommend remediation (reclaim, add space, move objects)."
            ),
        },
        {
            "name": "slow-sql",
            "description": "SQL performance triage flow.",
            "template": (
                "Triage slow SQL. Use cache_search_databases to locate the DB, then "
                "opsi_summarize_sql_insights (days_back<=30) to find regressed SQL. "
                "If a SQL ID is identified, call opsi_summarize_sql_plan_insights for plan deltas. "
                "Escalate to dbm_get_awr_report only if needed. Provide actions (index, hint, plan baseline)."
            ),
        },
        {
            "name": "fleet-overview",
            "description": "Quick fleet inventory using cache-first tools.",
            "template": (
                "Provide a concise fleet overview. Call cache_get_fleet_summary and cache_search_databases "
                "for counts by type/compartment and any disabled or problematic DBs. "
                "Only use live OPSI listing if cache is missing."
            ),
        },
    ]

    return {"count": len(prompts), "prompts": prompts}


@admin_server.tool(
    annotations=ToolAnnotations(
        read_only_hint=True,
        destructive_hint=False,
        idempotent_hint=True,
        open_world_hint=False,
    )
)
async def list_oci_profiles(ctx: Context = None) -> Dict[str, Any]:
    """
    List all available OCI profiles from ~/.oci/config.

    Returns:
        List of profile names and current active profile

    Examples:
        - list_oci_profiles() - Show all available profiles
        - Use to see which profiles can be used with validate_oci_profile()
    """
    if ctx:
        await ctx.info("Listing OCI profiles")

    try:
        profiles = list_available_profiles()
        current = get_current_profile()

        return {
            "profiles": profiles,
            "count": len(profiles),
            "current_profile": current,
        }

    except FileNotFoundError as e:
        raise ToolError(f"OCI config file not found: {e}")
    except Exception as e:
        raise ToolError(f"Failed to list profiles: {e}")


@admin_server.tool(
    annotations=ToolAnnotations(
        read_only_hint=True,
        destructive_hint=False,
        idempotent_hint=True,
        open_world_hint=False,
    )
)
async def get_profile_details(
    profile: Optional[str] = None,
    ctx: Context = None,
) -> Dict[str, Any]:
    """
    Get details for an OCI profile.

    Args:
        profile: Profile name (uses current if not specified)

    Returns:
        Profile configuration details (without sensitive data)

    Examples:
        - get_profile_details() - Get current profile details
        - get_profile_details(profile="DEFAULT") - Get specific profile
        - Sensitive fields like fingerprint are partially masked
    """
    if ctx:
        await ctx.info(f"Getting profile details for: {profile or 'current'}")

    try:
        # Temporarily set profile if specified
        original_profile = os.getenv("OCI_CLI_PROFILE")
        if profile:
            os.environ["OCI_CLI_PROFILE"] = profile

        try:
            config = get_oci_config()

            # Mask sensitive information
            return {
                "profile": profile or get_current_profile(),
                "region": config.get("region"),
                "tenancy": config.get("tenancy"),
                "user": config.get("user"),
                "fingerprint": config.get("fingerprint", "")[:8] + "..." if config.get("fingerprint") else None,
                "key_file": config.get("key_file"),
            }

        finally:
            # Restore original profile
            if profile and original_profile:
                os.environ["OCI_CLI_PROFILE"] = original_profile
            elif profile and not original_profile:
                os.environ.pop("OCI_CLI_PROFILE", None)

    except Exception as e:
        raise ToolError(f"Failed to get profile details: {e}")


@admin_server.tool(
    annotations=ToolAnnotations(
        read_only_hint=True,
        destructive_hint=False,
        idempotent_hint=True,
        open_world_hint=True,  # Makes OCI API call
    )
)
async def validate_oci_profile(
    profile: Optional[str] = None,
    ctx: Context = None,
) -> Dict[str, Any]:
    """
    Validate an OCI profile by testing connectivity.

    Args:
        profile: Profile name to validate

    Returns:
        Validation result with tenancy information if successful

    Examples:
        - validate_oci_profile() - Validate current profile
        - validate_oci_profile(profile="PRODUCTION") - Validate specific profile
        - Returns tenancy info if valid, error message if invalid
    """
    if ctx:
        await ctx.info(f"Validating profile: {profile or 'current'}")

    try:
        import oci

        # Temporarily set profile if specified
        original_profile = os.getenv("OCI_CLI_PROFILE")
        if profile:
            os.environ["OCI_CLI_PROFILE"] = profile

        try:
            config = get_oci_config()
            identity_client = oci.identity.IdentityClient(config)

            # Test connectivity by getting tenancy info
            tenancy = identity_client.get_tenancy(config["tenancy"]).data

            return {
                "valid": True,
                "profile": profile or get_current_profile(),
                "tenancy_name": tenancy.name,
                "tenancy_id": config["tenancy"],
                "home_region": tenancy.home_region_key,
                "region": config["region"],
            }

        finally:
            # Restore original profile
            if profile and original_profile:
                os.environ["OCI_CLI_PROFILE"] = original_profile
            elif profile and not original_profile:
                os.environ.pop("OCI_CLI_PROFILE", None)

    except Exception as e:
        return {
            "valid": False,
            "profile": profile or get_current_profile(),
            "error": str(e),
        }


@admin_server.tool(
    annotations=ToolAnnotations(
        read_only_hint=True,
        destructive_hint=False,
        idempotent_hint=True,
        open_world_hint=False,
    )
)
async def get_auth_status(ctx: Context = None) -> Dict[str, Any]:
    """
    Get authentication configuration status.

    Returns status of both OAuth and API Key authentication methods.

    Returns:
        Authentication status and configuration details

    Examples:
        - get_auth_status() - Check which auth methods are configured
        - Use to diagnose authentication issues
        - Shows OAuth, API Key, and Resource Principal status
    """
    if ctx:
        await ctx.info("Getting authentication status")

    oauth_status = get_oauth_config_status()

    # Check API key auth
    api_key_valid = False
    api_key_profile = None
    try:
        config = get_oci_config()
        api_key_valid = True
        api_key_profile = get_current_profile()
    except Exception:
        pass

    return {
        "current_auth_mode": detect_auth_mode().value,
        "oauth": {
            "configured": oauth_status["oauth_configured"],
            "storage_encrypted": oauth_status["storage_encrypted"],
            "missing_required": oauth_status["missing_required"],
            "missing_optional": oauth_status["missing_optional"],
        },
        "api_key": {
            "configured": api_key_valid,
            "profile": api_key_profile,
        },
        "resource_principal": {
            "available": bool(os.getenv("OCI_RESOURCE_PRINCIPAL_VERSION")),
        },
    }


@admin_server.tool(
    annotations=ToolAnnotations(
        read_only_hint=True,
        destructive_hint=False,
        idempotent_hint=True,
        open_world_hint=False,
    )
)
async def get_compartment_info(ctx: Context = None) -> Dict[str, Any]:
    """
    Get current compartment information.

    Returns:
        Compartment ID and source (environment or tenancy)

    Examples:
        - get_compartment_info() - Get current compartment OCID
        - Use to verify which compartment will be used for operations
    """
    if ctx:
        await ctx.info("Getting compartment information")

    compartment_id = get_compartment_id()
    from_env = bool(os.getenv("OCI_COMPARTMENT_ID"))

    return {
        "compartment_id": compartment_id,
        "source": "environment" if from_env else "tenancy_root",
        "env_var_set": from_env,
    }


@admin_server.tool(
    annotations=ToolAnnotations(
        read_only_hint=False,  # Generates new keys
        destructive_hint=False,
        idempotent_hint=False,  # Each call generates different keys
        open_world_hint=False,
    )
)
async def generate_oauth_keys(ctx: Context = None) -> Dict[str, Any]:
    """
    Generate new keys for OAuth configuration.

    Use these keys for STORAGE_ENCRYPTION_KEY and JWT_SIGNING_KEY
    environment variables.

    Returns:
        Generated keys (store these securely!)

    Examples:
        - generate_oauth_keys() - Generate new encryption keys
        - Output includes instructions for secure storage
        - Each call generates unique keys - save them immediately
    """
    if ctx:
        await ctx.warning("Generating new OAuth keys - store these securely!")

    return {
        "storage_encryption_key": generate_encryption_key(),
        "jwt_signing_key": generate_jwt_signing_key(),
        "instructions": [
            "Store these keys securely (e.g., OCI Vault, environment variables)",
            "Set STORAGE_ENCRYPTION_KEY for encrypted token storage",
            "Set JWT_SIGNING_KEY for internal JWT signing",
            "Never commit these keys to source control",
        ],
    }


@admin_server.tool(
    annotations=ToolAnnotations(
        read_only_hint=True,
        destructive_hint=False,
        idempotent_hint=True,
        open_world_hint=False,
    )
)
async def get_server_config(ctx: Context = None) -> Dict[str, Any]:
    """
    Get current server configuration.

    Returns:
        Server configuration including transport and auth settings

    Examples:
        - get_server_config() - View all server settings
        - Shows transport, auth mode, paths, and debug status
    """
    if ctx:
        await ctx.info("Getting server configuration")

    return {
        "transport": os.getenv("MCP_TRANSPORT", "stdio"),
        "host": os.getenv("MCP_HOST", os.getenv("MCP_HTTP_HOST", "0.0.0.0")),
        "port": int(os.getenv("MCP_PORT", os.getenv("MCP_HTTP_PORT", "8000"))),
        "supported_transports": ["stdio", "http", "sse", "streamable-http"],
        "auth_mode": detect_auth_mode().value,
        "oauth_enabled": os.getenv("FASTMCP_OAUTH_ENABLED") == "1",
        "debug_mode": os.getenv("MCP_DEBUG", "0") == "1",
        "cache_path": os.path.expanduser("~/.mcp_oci_opsi_cache.json"),
        "oauth_storage_path": os.path.expanduser("~/.mcp_oci_opsi/oauth"),
    }


@admin_server.tool(
    annotations=ToolAnnotations(
        read_only_hint=True,
        destructive_hint=False,
        idempotent_hint=True,
        open_world_hint=True,  # Makes OCI API calls
    )
)
async def diagnose_opsi_permissions(
    compartment_id: str,
    ctx: Context = None,
) -> Dict[str, Any]:
    """
    Diagnose Operations Insights permissions.

    Tests API access and identifies missing IAM policies.

    Args:
        compartment_id: Compartment OCID to test

    Returns:
        Permission test results and remediation suggestions

    Examples:
        - diagnose_opsi_permissions(compartment_id="ocid1...") - Test permissions
        - Provides IAM policy recommendations for failures
        - Tests OPSI, DBM, and host insights access
    """
    if ctx:
        await ctx.info("Diagnosing OPSI permissions...")
        await ctx.report_progress(progress=0, total=100)

    results = {
        "compartment_id": compartment_id,
        "tests": [],
        "recommendations": [],
    }

    try:
        from ..oci_clients import get_opsi_client, get_dbm_client

        # Test OPSI client
        if ctx:
            await ctx.report_progress(progress=20, total=100)

        try:
            opsi_client = get_opsi_client()
            opsi_client.list_database_insights(compartment_id=compartment_id, limit=1)
            results["tests"].append({
                "test": "list_database_insights",
                "status": "pass",
            })
        except Exception as e:
            results["tests"].append({
                "test": "list_database_insights",
                "status": "fail",
                "error": str(e),
            })
            results["recommendations"].append(
                "Grant: Allow group <group> to read opsi-database-insights in compartment <compartment>"
            )

        # Test DBM client
        if ctx:
            await ctx.report_progress(progress=50, total=100)

        try:
            dbm_client = get_dbm_client()
            dbm_client.list_managed_databases(compartment_id=compartment_id, limit=1)
            results["tests"].append({
                "test": "list_managed_databases",
                "status": "pass",
            })
        except Exception as e:
            results["tests"].append({
                "test": "list_managed_databases",
                "status": "fail",
                "error": str(e),
            })
            results["recommendations"].append(
                "Grant: Allow group <group> to read database-management-family in compartment <compartment>"
            )

        # Test host insights
        if ctx:
            await ctx.report_progress(progress=80, total=100)

        try:
            opsi_client.list_host_insights(compartment_id=compartment_id, limit=1)
            results["tests"].append({
                "test": "list_host_insights",
                "status": "pass",
            })
        except Exception as e:
            results["tests"].append({
                "test": "list_host_insights",
                "status": "fail",
                "error": str(e),
            })
            results["recommendations"].append(
                "Grant: Allow group <group> to read opsi-host-insights in compartment <compartment>"
            )

        if ctx:
            await ctx.report_progress(progress=100, total=100)

        # Summary
        passed = sum(1 for t in results["tests"] if t["status"] == "pass")
        total = len(results["tests"])
        results["summary"] = {
            "passed": passed,
            "total": total,
            "all_passed": passed == total,
        }

        return results

    except Exception as e:
        raise ToolError(f"Permission diagnosis failed: {e}")


# Resources for admin data
@admin_server.resource("resource://config/profiles")
async def profiles_resource() -> Dict[str, Any]:
    """Available OCI profiles as a resource."""
    try:
        return {
            "profiles": list_available_profiles(),
            "current": get_current_profile(),
        }
    except Exception:
        return {"error": "Failed to get profiles"}


@admin_server.resource("resource://config/current")
async def current_config_resource() -> Dict[str, Any]:
    """Current OCI configuration as a resource."""
    try:
        config = get_oci_config()
        return {
            "profile": get_current_profile(),
            "region": config.get("region"),
            "tenancy": config.get("tenancy"),
        }
    except Exception:
        return {"error": "Failed to get config"}


@admin_server.resource("resource://auth/status")
async def auth_status_resource() -> Dict[str, Any]:
    """Authentication status as a resource."""
    return {
        "auth_mode": detect_auth_mode().value,
        "oauth_configured": is_oauth_configured(),
    }
