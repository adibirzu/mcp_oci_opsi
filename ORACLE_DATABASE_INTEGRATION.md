# Oracle Database MCP Server Integration Guide

This guide explains how to use the Oracle Database connectivity features in the MCP OCI OPSI server, which provides similar capabilities to Oracle's official Database MCP server.

## Overview

The MCP OCI OPSI server now includes **10 additional tools** for database registration and direct Oracle Database connectivity:

**Database Registration & Enablement (4 tools):**
- Register databases with Operations Insights
- Check enablement status
- Get comprehensive database information
- Disable insights when needed

**Direct Database Queries (6 tools):**
- Execute SQL queries
- Query with wallet (Autonomous Database)
- Get database metadata
- List tables
- Describe table structures
- Get session information

## Setup

### 1. Install Oracle Database Driver (Optional)

For direct database query capabilities, install the `oracledb` package:

```bash
# Using uv
uv pip install "mcp-oci-opsi[database]"

# Using pip
pip install "mcp-oci-opsi[database]"

# Or install directly
pip install oracledb
```

### 2. Download Oracle Instant Client (Optional)

For advanced features, download Oracle Instant Client:
- Visit: https://www.oracle.com/database/technologies/instant-client/downloads.html
- Download the appropriate version for your OS
- Extract and set environment variables

## Usage Patterns

### Pattern 1: Register a Database with Operations Insights

**Step 1: Get Database Information**

```
Claude, get information about database ocid1.autonomousdatabase.oc1..aaaaaa...
```

This uses: `get_database_info(database_id)`

**Step 2: Enable Insights**

```
Claude, register this Autonomous Database with Operations Insights in compartment ocid1.compartment.oc1..bbbbb...
```

This uses: `enable_database_insights(database_id, compartment_id, "AUTONOMOUS_DATABASE")`

**Step 3: Verify Registration**

```
Claude, check if Operations Insights is enabled for database ocid1.autonomousdatabase.oc1..aaaaaa...
```

This uses: `check_database_insight_status(database_id, compartment_id)`

**Step 4: Query Performance Data**

```
Claude, show me the database insights for this compartment
```

This uses: `list_database_insights(compartment_id)`

### Pattern 2: Direct Database Queries

**For Autonomous Database (Recommended - Wallet Authentication):**

```
Claude, query my Autonomous Database using wallet:
- Wallet location: /path/to/wallet
- Wallet password: [password]
- DSN: mydb_high
- Username: ADMIN
- Password: [db_password]
- Query: SELECT table_name, num_rows FROM user_tables WHERE rownum <= 10
```

This uses: `query_with_wallet(wallet_location, wallet_password, dsn, username, password, query)`

**For Regular Databases (Connection String):**

```
Claude, query database with connection string "admin/password@host:1521/service":
SELECT * FROM v$version
```

This uses: `query_oracle_database(connection_string, query)`

### Pattern 3: Database Exploration

**List All Tables:**

```
Claude, list all tables in the database (connection: admin/pass@host:1521/service)
```

This uses: `list_oracle_tables(connection_string)`

**Describe Table Structure:**

```
Claude, describe the EMPLOYEES table structure
```

This uses: `describe_oracle_table(connection_string, "EMPLOYEES")`

**Get Database Metadata:**

```
Claude, show me the database version and instance information
```

This uses: `get_oracle_database_metadata(connection_string)`

## Complete Workflow Example

### Scenario: Onboard and Monitor a New Autonomous Database

**1. Discover the Database**

```
User: "I have an Autonomous Database with OCID ocid1.autonomousdatabase.oc1.iad.aaaaaa...
      Tell me about it."

Claude: [Calls get_database_info]
        "This is an Autonomous Database named 'SALES_DB' with 2 OCPUs, auto-scaling enabled,
         running version 19c. It's in compartment ocid1.compartment.oc1..bbbbb..."
```

**2. Register with Operations Insights**

```
User: "Register this database with Operations Insights."

Claude: [Calls enable_database_insights]
        "Database insight created successfully!
         Database Insight ID: ocid1.databaseinsight.oc1..ccccc...
         Status: ACTIVE
         You can now monitor performance metrics for this database."
```

**3. Verify Registration**

```
User: "Is insights enabled for this database?"

Claude: [Calls check_database_insight_status]
        "Yes, Operations Insights is enabled.
         Database Insight ID: ocid1.databaseinsight.oc1..ccccc...
         Status: ACTIVE"
```

**4. Query the Database Directly**

```
User: "Query this database to show me the top 10 tables by size.
      Use wallet at /Users/me/wallet, DSN: salesdb_high,
      username ADMIN, password: [secure]"

Claude: [Calls query_with_wallet]
        "Query Results:
         1. SALES_TRANSACTIONS - 1,234,567 rows
         2. CUSTOMER_ORDERS - 987,654 rows
         3. PRODUCT_CATALOG - 456,789 rows
         ..."
```

**5. Analyze Performance**

```
User: "Show me SQL statistics for this database over the past week"

Claude: [Calls summarize_sql_statistics]
        "SQL Statistics Summary:
         - Total SQL Statements: 1,234
         - Top CPU Consumer: SELECT * FROM sales_transactions (45% CPU)
         - Top I/O Statement: CREATE INDEX idx_customer (10,234 buffer gets)
         ..."
```

## Security Best Practices

### For Autonomous Database

✅ **DO:**
- Use wallet-based authentication
- Store wallet files in secure location
- Use strong wallet passwords
- Rotate database passwords regularly
- Use least-privilege database users

❌ **DON'T:**
- Hardcode passwords in scripts
- Share wallet files publicly
- Use ADMIN user for routine queries
- Store credentials in version control

### For Connection Strings

✅ **DO:**
- Use environment variables for sensitive data
- Implement connection pooling for production
- Use SSL/TLS for network connections
- Audit database access

❌ **DON'T:**
- Embed credentials in connection strings passed to Claude
- Use plain-text password storage
- Share connection strings in chat logs

## Comparison with Oracle's Official Database MCP Server

| Feature | MCP OCI OPSI Server | Oracle DB MCP Server |
|---------|-------------------|---------------------|
| **SQL Query Execution** | ✅ Full support | ✅ Full support |
| **Wallet Authentication** | ✅ Supported | ✅ Supported |
| **Operations Insights Integration** | ✅ **Unique Feature** | ❌ Not included |
| **Database Registration** | ✅ **Unique Feature** | ❌ Not included |
| **Performance Monitoring** | ✅ **26 tools** | ❌ Limited |
| **AWR Reports** | ✅ Supported | ❌ Not included |
| **Fleet Management** | ✅ Supported | ❌ Not included |
| **Capacity Planning** | ✅ ML-based | ❌ Not included |
| **Host Insights** | ✅ Supported | ❌ Not included |
| **Exadata Monitoring** | ✅ Supported | ❌ Not included |

## Advanced Features

### Database Fleet Operations

Monitor all databases across your organization:

```
Claude, show me fleet health metrics for compartment XYZ
```

### ML-Based Capacity Forecasting

Predict future resource needs:

```
Claude, forecast CPU usage for the next 30 days for database ABC
```

### AWR Report Generation

Generate comprehensive performance reports:

```
Claude, generate an AWR report for database DEF between snapshots 100 and 110
```

## Troubleshooting

### Issue: "oracledb package not installed"

**Solution:**
```bash
pip install oracledb
```

### Issue: "DPI-1047: Cannot locate a 64-bit Oracle Client library"

**Solution:**
Download and install Oracle Instant Client, then set:
```bash
export DYLD_LIBRARY_PATH=/path/to/instantclient
```

### Issue: "ORA-01017: invalid username/password"

**Solution:**
- Verify credentials
- Check wallet password
- Ensure database user exists
- Verify connection string format

### Issue: "Database insight already exists"

**Solution:**
This is expected if the database is already registered. Use `check_database_insight_status` to verify.

## Additional Resources

- [OCI Operations Insights Documentation](https://docs.oracle.com/en-us/iaas/operations-insights/)
- [Oracle Database Python Driver](https://python-oracledb.readthedocs.io/)
- [OCI Database Management](https://docs.oracle.com/en-us/iaas/database-management/)
- [Oracle Autonomous Database](https://docs.oracle.com/en-us/iaas/Content/Database/Concepts/adboverview.htm)

## Tool Reference

### Database Registration Tools

1. `enable_database_insights(database_id, compartment_id, entity_source)`
2. `disable_database_insights(database_insight_id)`
3. `check_database_insight_status(database_id, compartment_id)`
4. `get_database_info(database_id)`

### Direct Query Tools

5. `query_oracle_database(connection_string, query, fetch_size)`
6. `query_with_wallet(wallet_location, wallet_password, dsn, username, password, query, fetch_size)`
7. `get_oracle_database_metadata(connection_string)`
8. `list_oracle_tables(connection_string, schema)`
9. `describe_oracle_table(connection_string, table_name, schema)`
10. `get_oracle_session_info(connection_string)`

Total: **35 MCP Tools** (25 existing + 10 new)
