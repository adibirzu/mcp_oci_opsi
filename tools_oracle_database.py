"""FastMCP tools for direct Oracle Database connectivity and queries.

This module provides tools to connect directly to Oracle databases and execute queries,
similar to Oracle's official MCP server for Oracle Database.

Note: Requires oracledb (python-oracledb) package to be installed.
Install with: pip install oracledb
"""

from typing import Any, Optional
import json


def execute_query(
    connection_string: str,
    query: str,
    params: Optional[dict] = None,
    fetch_size: int = 100,
) -> dict[str, Any]:
    """
    Execute a SQL query against an Oracle database.

    Args:
        connection_string: Oracle connection string (user/pass@host:port/service).
        query: SQL query to execute.
        params: Optional query parameters for bind variables.
        fetch_size: Number of rows to fetch (default 100, max 1000).

    Returns:
        Dictionary containing query results with columns and rows.

    Example:
        >>> result = execute_query(
        ...     connection_string="admin/password@host:1521/service",
        ...     query="SELECT table_name, num_rows FROM user_tables WHERE rownum <= 10"
        ... )
        >>> for row in result['rows']:
        ...     print(row)

    Note:
        For security, consider using wallet-based authentication for Autonomous Database.
    """
    try:
        import oracledb

        # Limit fetch size for safety
        fetch_size = min(fetch_size, 1000)

        # Parse connection string
        connection = oracledb.connect(connection_string)
        cursor = connection.cursor()

        # Execute query
        if params:
            cursor.execute(query, params)
        else:
            cursor.execute(query)

        # Fetch results
        columns = [desc[0] for desc in cursor.description] if cursor.description else []
        rows = cursor.fetchmany(fetch_size)

        # Convert to list of dictionaries
        result_rows = []
        for row in rows:
            row_dict = {}
            for i, col in enumerate(columns):
                value = row[i]
                # Convert non-JSON serializable types
                if hasattr(value, 'read'):  # LOB
                    value = value.read()
                elif hasattr(value, 'isoformat'):  # datetime
                    value = value.isoformat()
                row_dict[col] = value
            result_rows.append(row_dict)

        cursor.close()
        connection.close()

        return {
            "query": query,
            "columns": columns,
            "rows": result_rows,
            "row_count": len(result_rows),
            "fetched": len(rows),
            "fetch_size": fetch_size,
        }

    except ImportError:
        return {
            "error": "oracledb package not installed. Install with: pip install oracledb",
            "type": "ImportError",
        }
    except Exception as e:
        return {
            "error": str(e),
            "type": type(e).__name__,
            "query": query,
        }


def execute_query_with_wallet(
    wallet_location: str,
    wallet_password: str,
    dsn: str,
    username: str,
    password: str,
    query: str,
    params: Optional[dict] = None,
    fetch_size: int = 100,
) -> dict[str, Any]:
    """
    Execute a SQL query using Oracle Wallet (for Autonomous Database).

    Args:
        wallet_location: Path to wallet directory.
        wallet_password: Wallet password.
        dsn: Data source name from tnsnames.ora (e.g., "mydb_high").
        username: Database username.
        password: Database password.
        query: SQL query to execute.
        params: Optional query parameters.
        fetch_size: Number of rows to fetch (default 100, max 1000).

    Returns:
        Dictionary containing query results.

    Example:
        >>> result = execute_query_with_wallet(
        ...     wallet_location="/path/to/wallet",
        ...     wallet_password="WalletPassword123",
        ...     dsn="mydb_high",
        ...     username="ADMIN",
        ...     password="DbPassword123",
        ...     query="SELECT * FROM user_tables"
        ... )
    """
    try:
        import oracledb

        fetch_size = min(fetch_size, 1000)

        # Configure wallet
        oracledb.init_oracle_client(config_dir=wallet_location)

        # Connect using wallet
        connection = oracledb.connect(
            user=username,
            password=password,
            dsn=dsn,
        )

        cursor = connection.cursor()

        # Execute query
        if params:
            cursor.execute(query, params)
        else:
            cursor.execute(query)

        # Fetch results
        columns = [desc[0] for desc in cursor.description] if cursor.description else []
        rows = cursor.fetchmany(fetch_size)

        # Convert to list of dictionaries
        result_rows = []
        for row in rows:
            row_dict = {}
            for i, col in enumerate(columns):
                value = row[i]
                if hasattr(value, 'read'):
                    value = value.read()
                elif hasattr(value, 'isoformat'):
                    value = value.isoformat()
                row_dict[col] = value
            result_rows.append(row_dict)

        cursor.close()
        connection.close()

        return {
            "query": query,
            "dsn": dsn,
            "columns": columns,
            "rows": result_rows,
            "row_count": len(result_rows),
        }

    except ImportError:
        return {
            "error": "oracledb package not installed. Install with: pip install oracledb",
            "type": "ImportError",
        }
    except Exception as e:
        return {
            "error": str(e),
            "type": type(e).__name__,
            "query": query,
        }


def get_database_metadata(
    connection_string: str,
) -> dict[str, Any]:
    """
    Get database metadata including version, instance info, and parameters.

    Args:
        connection_string: Oracle connection string.

    Returns:
        Dictionary containing database metadata.
    """
    try:
        import oracledb

        connection = oracledb.connect(connection_string)
        cursor = connection.cursor()

        metadata = {}

        # Database version
        cursor.execute("SELECT * FROM v$version WHERE rownum = 1")
        version_row = cursor.fetchone()
        metadata["version"] = version_row[0] if version_row else None

        # Instance info
        cursor.execute("""
            SELECT instance_name, host_name, version, startup_time, status, database_status
            FROM v$instance
        """)
        instance = cursor.fetchone()
        if instance:
            metadata["instance"] = {
                "name": instance[0],
                "host": instance[1],
                "version": instance[2],
                "startup_time": str(instance[3]),
                "status": instance[4],
                "database_status": instance[5],
            }

        # Database info
        cursor.execute("""
            SELECT name, db_unique_name, platform_name, log_mode, open_mode
            FROM v$database
        """)
        database = cursor.fetchone()
        if database:
            metadata["database"] = {
                "name": database[0],
                "unique_name": database[1],
                "platform": database[2],
                "log_mode": database[3],
                "open_mode": database[4],
            }

        cursor.close()
        connection.close()

        return metadata

    except ImportError:
        return {
            "error": "oracledb package not installed",
            "type": "ImportError",
        }
    except Exception as e:
        return {
            "error": str(e),
            "type": type(e).__name__,
        }


def list_tables(
    connection_string: str,
    schema: Optional[str] = None,
) -> dict[str, Any]:
    """
    List tables in the database.

    Args:
        connection_string: Oracle connection string.
        schema: Optional schema name (defaults to current user).

    Returns:
        Dictionary containing list of tables.
    """
    try:
        import oracledb

        connection = oracledb.connect(connection_string)
        cursor = connection.cursor()

        if schema:
            cursor.execute("""
                SELECT table_name, num_rows, tablespace_name
                FROM all_tables
                WHERE owner = :schema
                ORDER BY table_name
            """, {"schema": schema.upper()})
        else:
            cursor.execute("""
                SELECT table_name, num_rows, tablespace_name
                FROM user_tables
                ORDER BY table_name
            """)

        tables = []
        for row in cursor:
            tables.append({
                "table_name": row[0],
                "num_rows": row[1],
                "tablespace_name": row[2],
            })

        cursor.close()
        connection.close()

        return {
            "schema": schema if schema else "current_user",
            "tables": tables,
            "count": len(tables),
        }

    except ImportError:
        return {
            "error": "oracledb package not installed",
            "type": "ImportError",
        }
    except Exception as e:
        return {
            "error": str(e),
            "type": type(e).__name__,
        }


def describe_table(
    connection_string: str,
    table_name: str,
    schema: Optional[str] = None,
) -> dict[str, Any]:
    """
    Describe table structure (columns, data types, constraints).

    Args:
        connection_string: Oracle connection string.
        table_name: Table name to describe.
        schema: Optional schema name.

    Returns:
        Dictionary containing table structure details.
    """
    try:
        import oracledb

        connection = oracledb.connect(connection_string)
        cursor = connection.cursor()

        # Get columns
        if schema:
            cursor.execute("""
                SELECT column_name, data_type, data_length, nullable, data_default
                FROM all_tab_columns
                WHERE owner = :schema AND table_name = :table_name
                ORDER BY column_id
            """, {"schema": schema.upper(), "table_name": table_name.upper()})
        else:
            cursor.execute("""
                SELECT column_name, data_type, data_length, nullable, data_default
                FROM user_tab_columns
                WHERE table_name = :table_name
                ORDER BY column_id
            """, {"table_name": table_name.upper()})

        columns = []
        for row in cursor:
            columns.append({
                "column_name": row[0],
                "data_type": row[1],
                "data_length": row[2],
                "nullable": row[3],
                "default_value": row[4],
            })

        cursor.close()
        connection.close()

        return {
            "table_name": table_name,
            "schema": schema if schema else "current_user",
            "columns": columns,
            "column_count": len(columns),
        }

    except ImportError:
        return {
            "error": "oracledb package not installed",
            "type": "ImportError",
        }
    except Exception as e:
        return {
            "error": str(e),
            "type": type(e).__name__,
        }


def get_session_info(
    connection_string: str,
) -> dict[str, Any]:
    """
    Get current session information.

    Args:
        connection_string: Oracle connection string.

    Returns:
        Dictionary containing session details.
    """
    try:
        import oracledb

        connection = oracledb.connect(connection_string)
        cursor = connection.cursor()

        cursor.execute("""
            SELECT
                sys_context('USERENV', 'SESSION_USER') as session_user,
                sys_context('USERENV', 'CURRENT_SCHEMA') as current_schema,
                sys_context('USERENV', 'DB_NAME') as db_name,
                sys_context('USERENV', 'SERVER_HOST') as server_host,
                sys_context('USERENV', 'INSTANCE_NAME') as instance_name
            FROM dual
        """)

        row = cursor.fetchone()

        session_info = {
            "session_user": row[0],
            "current_schema": row[1],
            "database_name": row[2],
            "server_host": row[3],
            "instance_name": row[4],
        }

        cursor.close()
        connection.close()

        return session_info

    except ImportError:
        return {
            "error": "oracledb package not installed",
            "type": "ImportError",
        }
    except Exception as e:
        return {
            "error": str(e),
            "type": type(e).__name__,
        }
