"""MCP OCI OPSI Server v3.0 - FastMCP 2.0 Enhanced Edition.

This is the main entry point for the enhanced MCP server with:
- Server composition (modular sub-servers)
- Resources for read-only data access
- Prompts for guided DBA workflows
- OCI IAM OAuth + API Key authentication
- Context-aware tools with progress reporting

Usage:
    # stdio transport (Claude Desktop/Code)
    python -m mcp_oci_opsi

    # HTTP transport (production)
    MCP_TRANSPORT=http python -m mcp_oci_opsi

    # With OAuth enabled
    FASTMCP_OAUTH_ENABLED=1 MCP_TRANSPORT=http python -m mcp_oci_opsi
"""

import os
from typing import Optional

from fastmcp import FastMCP, Context
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Import sub-servers
from .servers.cache_server import cache_server
from .servers.opsi_server import opsi_server
from .servers.dbm_server import dbm_server
from .servers.admin_server import admin_server

# Import prompts
from .prompts.analysis_prompts import register_analysis_prompts
from .prompts.operations_prompts import register_operations_prompts
from .prompts.reporting_prompts import register_reporting_prompts

# Import skills tools
from . import tools_skills

# Import auth
from .auth.hybrid_auth import detect_auth_mode, AuthMode
from .auth.oci_oauth import create_oci_auth_provider, is_oauth_configured


def create_app() -> FastMCP:
    """
    Create and configure the MCP application.

    Returns:
        Configured FastMCP instance
    """
    # Determine authentication mode
    auth_mode = detect_auth_mode()
    auth_provider = None

    # Configure OAuth if enabled and configured
    if auth_mode == AuthMode.OAUTH and is_oauth_configured():
        base_url = os.environ.get("FASTMCP_SERVER_BASE_URL", "http://localhost:8000")
        try:
            auth_provider = create_oci_auth_provider(base_url)
            print(f"OAuth authentication enabled with base URL: {base_url}")
        except Exception as e:
            print(f"Warning: OAuth configuration failed: {e}")
            print("Falling back to API Key authentication")
            auth_provider = None

    # Create main server with optional auth
    app = FastMCP(
        name="oci-opsi",
        instructions="""
        MCP OCI OPSI Server - Advanced Oracle Database Monitoring

        This server provides comprehensive Oracle Cloud Infrastructure
        database monitoring and analysis capabilities.

        Key Features:
        - Instant fleet queries from local cache (zero API calls)
        - SQL performance analysis and tuning recommendations
        - Capacity planning with ML-based forecasting
        - ADDM findings and AWR reports
        - Security auditing (users, roles, privileges)
        - Multi-tenancy support with profile management

        Quick Start:
        1. Use get_fleet_summary() for instant fleet overview
        2. Use list_available_skills() to see guided workflows
        3. Use daily_health_check prompt for comprehensive status

        Token Optimization:
        - Always try cache tools first (get_fleet_summary, search_databases)
        - Use skills for guided, efficient workflows
        - Use prompts for complex multi-step operations
        """,
        auth=auth_provider,
    )

    # Mount sub-servers with prefixes (synchronous, live-linking)
    # Cache server - instant operations, zero API calls
    app.mount(cache_server, prefix="cache")

    # OPSI server - Operations Insights analytics
    app.mount(opsi_server, prefix="opsi")

    # DBM server - Database Management operations
    app.mount(dbm_server, prefix="dbm")

    # Admin server - Profile and configuration
    app.mount(admin_server, prefix="admin")

    # Register prompts
    register_analysis_prompts(app)
    register_operations_prompts(app)
    register_reporting_prompts(app)

    # Register skills tools directly on main app
    @app.tool
    def list_available_skills() -> dict:
        """
        List all available DBA skills for enhanced guidance.

        Skills provide specialized workflows for common DBA tasks
        with optimal tool selection and minimal token usage.

        Returns:
            List of available skills with descriptions
        """
        return tools_skills.list_available_skills()

    @app.tool
    def get_skill_context(skill_name: str) -> dict:
        """
        Get detailed context for a specific DBA skill.

        Args:
            skill_name: Name of the skill (e.g., "sql-performance")

        Returns:
            Skill instructions and recommended tools
        """
        return tools_skills.get_skill_context(skill_name)

    @app.tool
    def get_skill_for_query(query: str) -> dict:
        """
        Find the most relevant skill for a user query.

        Automatically detects which skill would be most helpful
        based on the user's question.

        Args:
            query: User's natural language question

        Returns:
            Matched skill with context and recommended tools
        """
        return tools_skills.get_skill_for_query(query)

    @app.tool
    def get_quick_reference(category: Optional[str] = None) -> dict:
        """
        Get a quick reference guide for common DBA tasks.

        Args:
            category: Optional filter (fleet, sql, capacity, diagnostics, storage, security)

        Returns:
            Task-to-tool mapping reference
        """
        return tools_skills.get_quick_reference(category)

    @app.tool
    def get_token_optimization_tips() -> dict:
        """
        Get tips for minimizing token usage in DBA operations.

        Returns:
            Best practices and token-efficient tool recommendations
        """
        return tools_skills.get_token_optimization_tips()

    # Add a welcome resource
    @app.resource("resource://welcome")
    async def welcome_resource() -> dict:
        """Welcome message and getting started guide."""
        return {
            "welcome": "MCP OCI OPSI Server v3.0",
            "description": "Advanced Oracle Database Monitoring",
            "getting_started": [
                "1. Use admin_ping() to verify connectivity",
                "2. Use admin_whoami() to see current context",
                "3. Use cache_get_fleet_summary() for instant fleet overview",
                "4. Use list_available_skills() for guided workflows",
            ],
            "tool_prefixes": {
                "cache_": "Instant operations (zero API calls)",
                "opsi_": "Operations Insights analytics",
                "dbm_": "Database Management operations",
                "admin_": "Profile and configuration",
            },
            "documentation": "https://github.com/adibirzu/mcp_oci_opsi",
        }

    return app


# Create the application
app = create_app()


def main():
    """Run the MCP server with transport selection."""
    transport = os.getenv("MCP_TRANSPORT", "stdio").lower()
    host = os.getenv("MCP_HTTP_HOST", "0.0.0.0")
    port = int(os.getenv("MCP_HTTP_PORT", "8000"))
    debug = os.getenv("MCP_DEBUG", "0") == "1"

    print(f"Starting MCP OCI OPSI Server v3.0")
    print(f"  Transport: {transport}")
    print(f"  Auth Mode: {detect_auth_mode().value}")

    if transport == "http":
        print(f"  HTTP: {host}:{port}")
        try:
            app.run(transport="streamable-http", host=host, port=port)
        except Exception as e:
            print(f"HTTP transport error: {e}")
            print("Trying SSE transport...")
            try:
                app.run(transport="sse", host=host, port=port)
            except Exception as e2:
                print(f"SSE transport error: {e2}")
                print("Falling back to stdio")
                app.run(transport="stdio")
    else:
        # Default: stdio for Claude Desktop/Code
        app.run(transport="stdio")


if __name__ == "__main__":
    main()
