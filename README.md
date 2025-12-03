# MCP OCI OPSI Server

**Version 3.0** | **FastMCP 2.0** | **13 DBA Skills** | **OAuth + API Key Auth** | **Multi-Tenancy**

MCP (Model Context Protocol) server for Oracle Cloud Infrastructure (OCI) Operations Insights. This server provides comprehensive Oracle database monitoring and analysis capabilities through Claude Desktop, Claude Code, or any MCP-compatible client.

> **Quick Links**: [Installation](#installation) | [Quick Start](#quick-start) | [OCI VM Deployment](#oci-vm-deployment) | [API Reference](#available-tools)
>
> **Guides**: [Skills Guide](./SKILLS_GUIDE.md) | [FastMCP v3 Guide](./FASTMCP_V3_GUIDE.md) | [OCI Deployment Guide](./docs/OCI_VM_DEPLOYMENT.md)

---

## What's New in v3.0

| Feature | Description |
|---------|-------------|
| **OCI IAM OAuth** | Enterprise authentication with OCI Identity Domains |
| **API Key Fallback** | Seamless fallback to ~/.oci/config for development |
| **MCP Resources** | 10 read-only data endpoints for efficient access |
| **MCP Prompts** | 15 guided DBA workflow templates |
| **Server Composition** | 4 modular sub-servers with tool prefixes |
| **DBA Skills** | 13 specialized skills for token-efficient workflows |
| **Disk-Based Storage** | No Redis required - encrypted file storage |
| **OCI VM Ready** | Terraform scripts for automated deployment |

---

## Architecture Overview

### High-Level Architecture

```
                                    ┌─────────────────────────────────────┐
                                    │         MCP Clients                 │
                                    │  (Claude Desktop/Code, ChatGPT)     │
                                    └──────────────┬──────────────────────┘
                                                   │
                                    MCP Protocol (stdio/HTTP)
                                                   │
┌──────────────────────────────────────────────────┴──────────────────────────────────────────────────┐
│                                                                                                      │
│                              MCP OCI OPSI SERVER v3.0                                               │
│                                                                                                      │
│  ┌────────────────────────────────────────────────────────────────────────────────────────────────┐ │
│  │                                    FastMCP 2.0 Core                                            │ │
│  │                                                                                                │ │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────┐  │ │
│  │  │   cache_*   │  │   opsi_*    │  │    dbm_*    │  │   admin_*   │  │    Skills Engine    │  │ │
│  │  │   8 tools   │  │   9 tools   │  │   8 tools   │  │  10 tools   │  │    13 DBA skills    │  │ │
│  │  │  4 resources│  │  1 resource │  │  2 resources│  │  3 resources│  │                     │  │ │
│  │  │             │  │             │  │             │  │             │  │  • Fleet Overview   │  │ │
│  │  │ Zero API    │  │ Operations  │  │  Database   │  │   Profile   │  │  • SQL Performance  │  │ │
│  │  │   calls     │  │  Insights   │  │ Management  │  │   Config    │  │  • Capacity Plan    │  │ │
│  │  └─────────────┘  └─────────────┘  └─────────────┘  └─────────────┘  └─────────────────────┘  │ │
│  │                                                                                                │ │
│  │  ┌─────────────────────────────────────────────────────────────────────────────────────────┐  │ │
│  │  │                              15 MCP Prompts (Workflow Templates)                        │  │ │
│  │  │  Analysis: analyze_database_performance, investigate_slow_query, analyze_wait_events   │  │ │
│  │  │  Operations: enable_monitoring, security_audit, tablespace_maintenance                 │  │ │
│  │  │  Reporting: capacity_planning_report, fleet_inventory_report, compliance_report        │  │ │
│  │  └─────────────────────────────────────────────────────────────────────────────────────────┘  │ │
│  └────────────────────────────────────────────────────────────────────────────────────────────────┘ │
│                                                                                                      │
│  ┌────────────────────────────────────────────────────────────────────────────────────────────────┐ │
│  │                                  Authentication Layer                                          │ │
│  │                                                                                                │ │
│  │  ┌─────────────────────┐  ┌─────────────────────┐  ┌─────────────────────────────────────┐   │ │
│  │  │    OCI IAM OAuth    │  │    API Key Auth     │  │     Resource Principal (Future)     │   │ │
│  │  │  (Production/HTTP)  │  │  (Development/stdio)│  │     (OCI Functions/Containers)      │   │ │
│  │  │                     │  │                     │  │                                     │   │ │
│  │  │  • OIDC Proxy       │  │  • ~/.oci/config    │  │  • Instance metadata auth           │   │ │
│  │  │  • Token Exchange   │  │  • Profile support  │  │  • Dynamic credentials              │   │ │
│  │  │  • Disk storage     │  │  • Multi-tenancy    │  │  • Auto-rotation                    │   │ │
│  │  └─────────────────────┘  └─────────────────────┘  └─────────────────────────────────────┘   │ │
│  └────────────────────────────────────────────────────────────────────────────────────────────────┘ │
│                                                                                                      │
│  ┌────────────────────────────────────────────────────────────────────────────────────────────────┐ │
│  │                                    OCI SDK Client Layer                                        │ │
│  │  • Operations Insights Client    • Database Management Client    • Identity Client             │ │
│  │  • Client caching (16 clients)   • Multi-region support          • Automatic pagination        │ │
│  └────────────────────────────────────────────────────────────────────────────────────────────────┘ │
│                                                                                                      │
└──────────────────────────────────────────────────────────────────────────────────────────────────────┘
                                                   │
                                    HTTPS REST API Calls
                                    (Regional endpoints)
                                                   │
┌──────────────────────────────────────────────────┴──────────────────────────────────────────────────┐
│                                                                                                      │
│                                 ORACLE CLOUD INFRASTRUCTURE                                          │
│                                                                                                      │
│  ┌──────────────────────────┐  ┌──────────────────────────┐  ┌──────────────────────────┐           │
│  │  Operations Insights     │  │  Database Management     │  │      Identity            │           │
│  │                          │  │                          │  │                          │           │
│  │  • Host Insights         │  │  • Managed Databases     │  │  • Users & Groups        │           │
│  │  • Database Insights     │  │  • SQL Plan Baselines    │  │  • Compartments          │           │
│  │  • SQL Statistics        │  │  • Performance Hub       │  │  • Policies              │           │
│  │  • Capacity Planning     │  │  • ADDM / AWR            │  │  • Identity Domains      │           │
│  │  • ML Forecasting        │  │  • Tablespaces           │  │                          │           │
│  └──────────────────────────┘  └──────────────────────────┘  └──────────────────────────┘           │
│                                                                                                      │
│  Regional Endpoints: operationsinsights.{region}.oci.oraclecloud.com                                │
│                      database.{region}.oraclecloud.com                                               │
│                      identity.{region}.oci.oraclecloud.com                                           │
└──────────────────────────────────────────────────────────────────────────────────────────────────────┘
```

### Tool Organization (v3.0)

| Prefix | Server | Tools | Resources | Description |
|--------|--------|-------|-----------|-------------|
| `cache_` | cache-tools | 8 | 4 | Instant operations (zero API calls) |
| `opsi_` | opsi-tools | 9 | 1 | Operations Insights analytics |
| `dbm_` | dbm-tools | 8 | 2 | Database Management operations |
| `admin_` | admin-tools | 10 | 3 | Profile and configuration |
| *(none)* | main | 5 | 1 | Skills tools + welcome resource |

### Authentication Flow

```
┌────────────────────────────────────────────────────────────────────────────────┐
│                           Authentication Decision Tree                          │
└────────────────────────────────────────────────────────────────────────────────┘
                                       │
                    ┌──────────────────┴──────────────────┐
                    ▼                                      ▼
        ┌─────────────────────┐              ┌─────────────────────┐
        │  HTTP Transport?    │              │  stdio Transport    │
        │  (Production)       │              │  (Development)      │
        └──────────┬──────────┘              └──────────┬──────────┘
                   │                                    │
        ┌──────────┴──────────┐                        │
        ▼                      ▼                        ▼
┌───────────────┐    ┌───────────────┐        ┌───────────────────┐
│ OAuth Enabled │    │ OAuth Not     │        │  API Key Auth     │
│ (FASTMCP_     │    │ Configured    │        │  ~/.oci/config    │
│  OAUTH=1)     │    │               │        │                   │
└───────┬───────┘    └───────┬───────┘        └─────────┬─────────┘
        │                    │                          │
        ▼                    ▼                          ▼
┌───────────────────────────────────────────────────────────────────┐
│                        OCI API Calls                               │
│  • Signed requests with user/tenancy context                      │
│  • Regional endpoint routing                                       │
│  • Automatic retry and error handling                             │
└───────────────────────────────────────────────────────────────────┘
```

---

## Prerequisites

1. **Python 3.10+**
2. **OCI CLI configured** at `~/.oci/config`
3. **Required IAM Policies**:
   ```
   Allow group YourGroup to read operations-insights-family in tenancy
   Allow group YourGroup to read database-management-family in tenancy
   Allow group YourGroup to read compartments in tenancy
   ```

---

## Installation

### Quick Install (Development)

```bash
# Clone repository
git clone https://github.com/adibirzu/mcp_oci_opsi.git
cd mcp_oci_opsi

# Create virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -e .

# Verify installation
python -c "from mcp_oci_opsi.main_v3 import app; print('OK')"
```

### Production Install (Docker)

```bash
# Build image
docker build -t mcp-oci-opsi .

# Run with stdio transport
docker run -it --rm \
  -v ~/.oci:/home/mcp/.oci:ro \
  mcp-oci-opsi

# Run with HTTP transport
docker run -d \
  -p 8000:8000 \
  -v ~/.oci:/home/mcp/.oci:ro \
  -e MCP_TRANSPORT=http \
  mcp-oci-opsi
```

---

## Quick Start

### 1. Build the Cache (Recommended)

```bash
# One-time setup - builds local cache for instant queries
./scripts/setup_and_build.sh

# Or with specific profile
./scripts/setup_and_build.sh --profile PRODUCTION
```

### 2. Configure Claude Desktop/Code

**Claude Desktop** (`~/Library/Application Support/Claude/claude_desktop_config.json`):

```json
{
  "mcpServers": {
    "oci-opsi": {
      "command": "/path/to/mcp_oci_opsi/.venv/bin/python",
      "args": ["-m", "mcp_oci_opsi"],
      "env": {
        "MCP_VERSION": "v3",
        "OCI_CLI_PROFILE": "DEFAULT"
      }
    }
  }
}
```

### 3. Start Using

```
# Instant queries (from cache)
"How many databases do I have?"
"Find database PRODDB01"
"Show fleet summary"

# Real-time analytics (API calls)
"Analyze SQL performance for the last 24 hours"
"Show CPU forecast for next 30 days"
"Generate ADDM report for database X"

# Guided workflows (skills)
"Use the sql-performance skill to analyze slow queries"
"Run daily health check"
```

---

## OCI VM Deployment

Deploy to OCI Compute with automated provisioning using Terraform.

### Quick Deploy

```bash
cd terraform/oci-vm

# Configure variables
cp terraform.tfvars.example terraform.tfvars
# Edit terraform.tfvars with your values

# Deploy
terraform init
terraform plan
terraform apply

# Get connection info
terraform output
```

### What Gets Provisioned

- **OCI Compute Instance** (VM.Standard.E4.Flex, 2 OCPU, 16GB RAM)
- **VCN with Subnet** (public or private)
- **Security Lists** (SSH + optional HTTP)
- **Cloud-Init Provisioning**:
  - Python 3.11 + pip
  - Docker + Docker Compose
  - MCP OCI OPSI Server
  - OCI CLI
  - Systemd service for auto-start

### Detailed Guide

See [docs/OCI_VM_DEPLOYMENT.md](./docs/OCI_VM_DEPLOYMENT.md) for:
- Step-by-step instructions
- Network configuration options
- Security hardening
- OAuth setup for production
- Monitoring and maintenance

---

## Available Tools

### Cache Tools (Instant - Zero API Calls)

| Tool | Description |
|------|-------------|
| `cache_get_fleet_summary` | Fleet overview with counts and types |
| `cache_search_databases` | Search by name, type, compartment |
| `cache_get_databases_by_compartment` | List databases in compartment |
| `cache_get_cached_statistics` | Cache metadata and stats |
| `cache_list_cached_compartments` | All compartments in cache |
| `cache_build_database_cache` | Build/rebuild cache |
| `cache_refresh_cache_if_needed` | Check and refresh cache |
| `cache_get_database_by_id` | Get database by OCID |

### OPSI Tools (Operations Insights)

| Tool | Description |
|------|-------------|
| `opsi_list_database_insights` | List database insights |
| `opsi_summarize_sql_statistics` | SQL performance metrics |
| `opsi_summarize_sql_insights` | SQL anomaly detection |
| `opsi_get_database_capacity_trend` | Historical capacity |
| `opsi_get_database_resource_forecast` | ML forecasting |
| `opsi_list_host_insights` | Host monitoring |
| `opsi_list_exadata_insights` | Exadata monitoring |
| `opsi_query_warehouse` | OPSI warehouse SQL |
| `opsi_summarize_addm_findings` | ADDM analysis |

### DBM Tools (Database Management)

| Tool | Description |
|------|-------------|
| `dbm_list_managed_databases` | List managed databases |
| `dbm_get_managed_database` | Database details |
| `dbm_get_tablespace_usage` | Storage metrics |
| `dbm_list_awr_snapshots` | AWR snapshots |
| `dbm_get_awr_report` | Generate AWR report |
| `dbm_get_addm_report` | ADDM recommendations |
| `dbm_list_sql_plan_baselines` | SPM baselines |
| `dbm_get_database_parameters` | DB parameters |

### Admin Tools

| Tool | Description |
|------|-------------|
| `admin_ping` | Health check |
| `admin_whoami` | Current context |
| `admin_list_profiles` | OCI profiles |
| `admin_validate_profile` | Validate config |
| `admin_switch_profile` | Change profile |
| `admin_get_auth_status` | Auth mode info |
| `admin_diagnose_permissions` | Permission check |
| `admin_generate_oauth_keys` | Generate keys |
| `admin_list_compartments` | Compartment tree |
| `admin_get_tenancy_info` | Tenancy details |

### Skills Tools

| Tool | Description |
|------|-------------|
| `list_available_skills` | List 13 DBA skills |
| `get_skill_context` | Get skill instructions |
| `get_skill_for_query` | Auto-match skill |
| `get_quick_reference` | Task-to-tool mapping |
| `get_token_optimization_tips` | Best practices |

---

## MCP Resources

Access read-only data via URI patterns:

| Resource URI | Description |
|--------------|-------------|
| `resource://fleet/summary` | Fleet overview |
| `resource://fleet/statistics` | Detailed stats |
| `resource://fleet/compartments` | Compartment list |
| `resource://database/{id}` | Database info |
| `resource://database/{id}/tablespaces` | Tablespace usage |
| `resource://config/profiles` | OCI profiles |
| `resource://config/current` | Current config |
| `resource://auth/status` | Auth status |
| `resource://welcome` | Getting started |

---

## MCP Prompts

Reusable workflow templates:

### Analysis Prompts
- `analyze_database_performance(database_name, time_range)`
- `investigate_slow_query(sql_id)`
- `analyze_wait_events(database_name, wait_class)`
- `analyze_resource_contention(compartment_name)`
- `daily_health_check()`

### Operations Prompts
- `enable_monitoring(compartment_name)`
- `security_audit(compartment_name)`
- `tablespace_maintenance(database_name)`
- `plan_baseline_management(database_name)`
- `profile_setup(profile_name)`

### Reporting Prompts
- `capacity_planning_report(compartment_name, forecast_days)`
- `performance_summary_report(database_name, days)`
- `fleet_inventory_report()`
- `awr_comparison_report(database_name, baseline, compare)`
- `compliance_report(compartment_name)`

---

## DBA Skills

13 specialized skills for common DBA tasks:

| Skill | Description | Key Tools |
|-------|-------------|-----------|
| `fleet-overview` | Fleet inventory and health | cache_get_fleet_summary |
| `sql-performance` | SQL analysis and tuning | opsi_summarize_sql_statistics |
| `capacity-planning` | Forecasting and trends | opsi_get_database_resource_forecast |
| `database-diagnostics` | ADDM and troubleshooting | dbm_get_addm_report |
| `awr-analysis` | AWR reports and snapshots | dbm_get_awr_report |
| `host-monitoring` | Host resource monitoring | opsi_list_host_insights |
| `storage-management` | Tablespace monitoring | dbm_get_tablespace_usage |
| `security-audit` | User and privilege audit | admin_diagnose_permissions |
| `sql-watch-management` | SQL Watch configuration | opsi tools |
| `sql-plan-baselines` | SPM management | dbm_list_sql_plan_baselines |
| `multi-tenancy` | Profile management | admin_list_profiles |
| `exadata-monitoring` | Exadata insights | opsi_list_exadata_insights |
| `dba-assistant` | General DBA help | all tools |

---

## Configuration

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `MCP_VERSION` | `v3` | Server version (v2, v3) |
| `MCP_TRANSPORT` | `stdio` | Transport (stdio, http) |
| `MCP_HTTP_HOST` | `0.0.0.0` | HTTP bind address |
| `MCP_HTTP_PORT` | `8000` | HTTP port |
| `OCI_CLI_PROFILE` | `DEFAULT` | OCI profile name |
| `OCI_REGION` | from config | Region override |
| `FASTMCP_OAUTH_ENABLED` | `0` | Enable OAuth |
| `JWT_SIGNING_KEY` | - | JWT signing key (OAuth) |
| `STORAGE_ENCRYPTION_KEY` | - | Token encryption key |

### OAuth Configuration (Production)

See [FASTMCP_V3_GUIDE.md](./FASTMCP_V3_GUIDE.md) for OAuth setup with OCI Identity Domains.

---

## Documentation

| Document | Description |
|----------|-------------|
| [FASTMCP_V3_GUIDE.md](./FASTMCP_V3_GUIDE.md) | Complete v3.0 guide |
| [SKILLS_GUIDE.md](./SKILLS_GUIDE.md) | DBA skills reference |
| [docs/OCI_VM_DEPLOYMENT.md](./docs/OCI_VM_DEPLOYMENT.md) | OCI VM deployment |
| [docs/ARCHITECTURE.md](./docs/ARCHITECTURE.md) | Detailed architecture |
| [CACHE_SYSTEM.md](./CACHE_SYSTEM.md) | Cache system docs |
| [SECURITY.md](./SECURITY.md) | Security guidelines |

---

## License

MIT

## Contributing

Contributions welcome! Please see [CONTRIBUTING.md](./CONTRIBUTING.md).

## Resources

- [Model Context Protocol](https://modelcontextprotocol.io/)
- [FastMCP Documentation](https://gofastmcp.com/)
- [OCI Operations Insights](https://docs.oracle.com/en-us/iaas/operations-insights/)
- [OCI Python SDK](https://docs.oracle.com/en-us/iaas/tools/python/latest/)
