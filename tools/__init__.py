"""
Unified tools namespace for mcp_oci_opsi.

This package provides a clean, organized import surface for all MCP tools.
All tools are located in this folder (mcp_oci_opsi/tools/).

Example:
    from mcp_oci_opsi.tools import opsi as tools_opsi
    from mcp_oci_opsi.tools import dbmanagement as tools_dbmanagement
"""

# Operations Insights domains
from . import tools_opsi as opsi
from . import tools_opsi_extended as opsi_extended
from . import tools_opsi_sql_insights as opsi_sql_insights
from . import tools_opsi_resource_stats as opsi_resource_stats
from . import tools_opsi_diagnostics as opsi_diagnostics

# Database Management domains
from . import tools_dbmanagement as dbmanagement
from . import tools_dbmanagement_monitoring as dbmanagement_monitoring
from . import tools_dbmanagement_sql_plans as dbmanagement_sql_plans
from . import tools_dbmanagement_awr_metrics as dbmanagement_awr_metrics
from . import tools_dbmanagement_tablespaces as dbmanagement_tablespaces
from . import tools_dbmanagement_users as dbmanagement_users

# SQL Watch domains
from . import tools_sqlwatch as sqlwatch
from . import tools_sqlwatch_bulk as sqlwatch_bulk

# Database enablement / discovery / direct DB access
from . import tools_database_registration as database_registration
from . import tools_database_discovery as database_discovery
from . import tools_oracle_database as oracle_database

# Cache, visualization, profiles, skills
from . import tools_cache as cache
from . import tools_cache_enhanced
from . import tools_visualization as visualization
from . import tools_profile_management as profile_management
from . import tools_skills as skills
from . import tools_skills_v2  # Programmatic skills (v2)

__all__ = [
    # OPSI
    "opsi", "opsi_extended", "opsi_sql_insights", "opsi_resource_stats", "opsi_diagnostics",
    # DBM
    "dbmanagement", "dbmanagement_monitoring", "dbmanagement_sql_plans",
    "dbmanagement_awr_metrics", "dbmanagement_tablespaces", "dbmanagement_users",
    # SQLWatch
    "sqlwatch", "sqlwatch_bulk",
    # Database
    "database_registration", "database_discovery", "oracle_database",
    # Misc
    "cache", "tools_cache_enhanced", "visualization", "profile_management", "skills", "tools_skills_v2",
]
