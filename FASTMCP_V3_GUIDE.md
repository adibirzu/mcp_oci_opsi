# FastMCP v3.0 Enhancement Guide

This guide covers the new features in MCP OCI OPSI Server v3.0, built on FastMCP 2.0.

## What's New in v3.0

| Feature | Description |
|---------|-------------|
| **OCI IAM OAuth** | Enterprise authentication with OCI Identity Domains |
| **API Key Fallback** | Seamless fallback to ~/.oci/config for development |
| **MCP Resources** | Read-only data endpoints for efficient access |
| **MCP Prompts** | Guided DBA workflow templates |
| **Server Composition** | Modular sub-servers with tool prefixes |
| **Context Support** | Progress reporting and structured logging |
| **Disk-Based Token Storage** | No Redis required - encrypted file storage |

## Quick Start

### Development Mode (stdio)

```bash
# Uses API Key authentication from ~/.oci/config
python -m mcp_oci_opsi
```

### Production Mode (HTTP with OAuth)

```bash
# Set environment variables (see .env.production.example)
export MCP_TRANSPORT=http
export FASTMCP_OAUTH_ENABLED=1
export FASTMCP_SERVER_AUTH_OCI_CONFIG_URL=https://idcs-xxx.identity.oraclecloud.com/.well-known/openid-configuration
export FASTMCP_SERVER_AUTH_OCI_CLIENT_ID=your-client-id
export FASTMCP_SERVER_AUTH_OCI_CLIENT_SECRET=your-client-secret
export FASTMCP_SERVER_BASE_URL=https://your-server.example.com
export JWT_SIGNING_KEY=$(python -c "import secrets; print(secrets.token_hex(32))")
export STORAGE_ENCRYPTION_KEY=$(python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())")

python -m mcp_oci_opsi
```

## Authentication

### Hybrid Authentication

The server supports multiple authentication methods with automatic fallback:

1. **OCI IAM OAuth** (Production): Enterprise SSO via OCI Identity Domains
2. **API Key** (Development): Traditional ~/.oci/config authentication
3. **Resource Principal** (Future): For OCI Functions deployment

```python
# Detection happens automatically
from mcp_oci_opsi.auth import detect_auth_mode, AuthMode

mode = detect_auth_mode()
# Returns: AuthMode.OAUTH, AuthMode.API_KEY, or AuthMode.RESOURCE_PRINCIPAL
```

### Setting Up OAuth

1. **Create OAuth Application in OCI**:
   - Go to OCI Console → Identity → Domains → Your Domain
   - Click "Integrated Applications" → "Add Application"
   - Choose "Confidential Application"
   - Configure redirect URL: `{your-server}/oauth/callback`

2. **Configure Environment**:
   ```bash
   FASTMCP_SERVER_AUTH_OCI_IAM_GUID=idcs-xxx.identity.oraclecloud.com
   FASTMCP_SERVER_AUTH_OCI_CONFIG_URL=https://idcs-xxx.identity.oraclecloud.com/.well-known/openid-configuration
   FASTMCP_SERVER_AUTH_OCI_CLIENT_ID=your-client-id
   FASTMCP_SERVER_AUTH_OCI_CLIENT_SECRET=your-client-secret
   FASTMCP_SERVER_BASE_URL=https://your-server.example.com
   ```

3. **Generate Security Keys**:
   ```bash
   # JWT signing key
   python -c "import secrets; print(secrets.token_hex(32))"

   # Fernet encryption key for token storage
   python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
   ```

## Tool Organization

Tools are organized into prefixed sub-servers:

| Prefix | Server | Description |
|--------|--------|-------------|
| `cache_` | cache-tools | Instant operations (zero API calls) |
| `opsi_` | opsi-tools | Operations Insights analytics |
| `dbm_` | dbm-tools | Database Management operations |
| `admin_` | admin-tools | Profile and configuration |

### Examples

```python
# Cache tools (instant, no API calls)
cache_get_fleet_summary()
cache_search_databases(name="PayDB")

# OPSI tools (API calls)
opsi_list_database_insights(compartment_id="...")
opsi_summarize_sql_insights(compartment_id="...")

# DBM tools (API calls)
dbm_get_tablespace_usage(managed_database_id="...")
dbm_list_awr_snapshots(managed_database_id="...", awr_db_id="...")

# Admin tools
admin_ping()
admin_whoami()
admin_diagnose_opsi_permissions(compartment_id="...")
```

## Resources

Resources provide read-only access to data via URI patterns:

```
resource://fleet/summary          # Fleet overview
resource://fleet/statistics       # Detailed statistics
resource://fleet/compartments     # Compartment list
resource://database/{id}          # Database info
resource://database/{id}/tablespaces
resource://database/{id}/users
resource://config/profiles        # OCI profiles
resource://config/current         # Current config
resource://auth/status            # Auth status
resource://welcome                # Getting started
```

### Accessing Resources

Resources are automatically available to MCP clients. They can also be accessed programmatically:

```python
# Within a tool using Context
@app.tool
async def my_tool(ctx: Context):
    fleet = await ctx.read_resource("resource://fleet/summary")
    return fleet
```

## Prompts

Prompts are reusable workflow templates for common DBA tasks:

### Analysis Prompts

| Prompt | Description |
|--------|-------------|
| `analyze_database_performance(database_name, time_range)` | Comprehensive performance analysis |
| `investigate_slow_query(sql_id)` | SQL investigation workflow |
| `analyze_wait_events(database_name, wait_class)` | Wait event analysis |
| `analyze_resource_contention(compartment_name)` | Resource contention analysis |
| `daily_health_check()` | Daily DBA health check |

### Operations Prompts

| Prompt | Description |
|--------|-------------|
| `enable_monitoring(compartment_name)` | Enable SQL Watch workflow |
| `security_audit(compartment_name)` | Security audit workflow |
| `tablespace_maintenance(database_name)` | Tablespace maintenance |
| `plan_baseline_management(database_name)` | SPM management |
| `profile_setup(profile_name)` | OCI profile setup |

### Reporting Prompts

| Prompt | Description |
|--------|-------------|
| `capacity_planning_report(compartment_name, forecast_days)` | Capacity planning |
| `performance_summary_report(database_name, days)` | Performance summary |
| `fleet_inventory_report()` | Fleet inventory |
| `awr_comparison_report(database_name, baseline, compare)` | AWR comparison |
| `compliance_report(compartment_name)` | Compliance audit |

### Using Prompts

In Claude Desktop/Code, prompts appear as available templates. Use them like:

```
Use the daily_health_check prompt to check my fleet
```

## Context Features

Tools can use Context for enhanced capabilities:

### Progress Reporting

```python
@app.tool
async def long_operation(ctx: Context):
    await ctx.report_progress(progress=0, total=100)
    # ... do work ...
    await ctx.report_progress(progress=50, total=100)
    # ... more work ...
    await ctx.report_progress(progress=100, total=100)
```

### Logging

```python
@app.tool
async def my_tool(ctx: Context):
    await ctx.debug("Starting operation")
    await ctx.info("Processing data")
    await ctx.warning("Deprecated parameter used")
    await ctx.error("Operation failed")
```

## Deployment

### Docker

```bash
# Build
docker build -t mcp-oci-opsi .

# Run with environment file
docker run -d \
  --name mcp-oci-opsi \
  -p 8000:8000 \
  --env-file .env.production \
  -v ~/.oci:/home/mcp/.oci:ro \
  -v mcp-data:/data \
  mcp-oci-opsi
```

### Docker Compose

```bash
# Copy and configure environment
cp .env.production.example .env

# Start
docker-compose up -d

# View logs
docker-compose logs -f
```

### OCI Deployment Options

1. **OCI Container Instance**: Managed container hosting
2. **OCI Kubernetes (OKE)**: For high-availability deployments
3. **VM with Docker**: Traditional VM deployment
4. **Any Cloud Provider**: AWS, GCP, Azure with Docker

## Configuration Reference

### Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `MCP_TRANSPORT` | No | `stdio` | Transport mode (stdio, http) |
| `MCP_HTTP_HOST` | No | `0.0.0.0` | HTTP bind address |
| `MCP_HTTP_PORT` | No | `8000` | HTTP port |
| `MCP_VERSION` | No | `v3` | Server version (v2, v3) |
| `MCP_DEBUG` | No | `0` | Debug mode |
| `OCI_CLI_PROFILE` | No | `DEFAULT` | OCI profile name |
| `OCI_REGION` | No | From config | OCI region override |
| `OCI_COMPARTMENT_ID` | No | Tenancy root | Default compartment |
| `FASTMCP_OAUTH_ENABLED` | No | `0` | Enable OAuth |
| `FASTMCP_SERVER_AUTH_OCI_CONFIG_URL` | OAuth | - | OIDC config URL |
| `FASTMCP_SERVER_AUTH_OCI_CLIENT_ID` | OAuth | - | OAuth client ID |
| `FASTMCP_SERVER_AUTH_OCI_CLIENT_SECRET` | OAuth | - | OAuth client secret |
| `FASTMCP_SERVER_BASE_URL` | OAuth | - | Public server URL |
| `JWT_SIGNING_KEY` | OAuth | - | JWT signing key |
| `STORAGE_ENCRYPTION_KEY` | No | - | Fernet encryption key |

## Version Selection

Switch between server versions:

```bash
# v3 (default) - FastMCP 2.0 enhanced
MCP_VERSION=v3 python -m mcp_oci_opsi

# v2 - Original server (backward compatible)
MCP_VERSION=v2 python -m mcp_oci_opsi
```

## Migration from v2

The v3 server is backward compatible with v2. Key differences:

1. **Tool names**: Tools now have prefixes (e.g., `get_fleet_summary` → `cache_get_fleet_summary`)
2. **Resources**: New resource endpoints for read-only data
3. **Prompts**: New workflow templates available
4. **Auth**: OAuth support added (optional)

For gradual migration, set `MCP_VERSION=v2` to use the original server.

## Troubleshooting

### Check Authentication Status

```python
admin_get_auth_status()
```

### Validate Profile

```python
admin_validate_oci_profile(profile="your-profile")
```

### Diagnose Permissions

```python
admin_diagnose_opsi_permissions(compartment_id="...")
```

### Generate New Keys

```python
admin_generate_oauth_keys()
```

## File Structure

```
mcp_oci_opsi/
├── __init__.py
├── __main__.py           # Entry point with version selection
├── main.py               # v2 server (original)
├── main_v3.py            # v3 server (FastMCP 2.0)
├── config.py             # OCI configuration
├── cache.py              # Local cache
├── oci_clients.py        # OCI SDK clients
├── auth/
│   ├── __init__.py
│   ├── hybrid_auth.py    # Hybrid authentication
│   └── oci_oauth.py      # OAuth provider
├── servers/
│   ├── __init__.py
│   ├── cache_server.py   # Cache tools + resources
│   ├── opsi_server.py    # OPSI tools + resources
│   ├── dbm_server.py     # DBM tools + resources
│   └── admin_server.py   # Admin tools + resources
├── prompts/
│   ├── __init__.py
│   ├── analysis_prompts.py
│   ├── operations_prompts.py
│   └── reporting_prompts.py
├── skills_loader.py      # Skills loading
└── tools_skills.py       # Skills tools
```
