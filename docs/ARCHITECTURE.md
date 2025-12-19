# MCP OCI OPSI Server - Architecture Documentation

## Overview

The MCP OCI OPSI Server v3.0 is a FastMCP 2.0-based server that provides comprehensive Oracle Cloud Infrastructure database monitoring capabilities. This document details the system architecture, component interactions, and design decisions.

---

## System Architecture

### Component Diagram

```
┌─────────────────────────────────────────────────────────────────────────────────────────────────────┐
│                                        MCP OCI OPSI SERVER v3.0                                     │
├─────────────────────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                                     │
│  ┌───────────────────────────────────────────────────────────────────────────────────────────────┐ │
│  │                                     TRANSPORT LAYER                                           │ │
│  │                                                                                               │ │
│  │  ┌─────────────────────────────┐        ┌─────────────────────────────────────────────────┐  │ │
│  │  │     stdio Transport         │        │           HTTP Transport                        │  │ │
│  │  │                             │        │                                                 │  │ │
│  │  │  • Claude Desktop           │        │  • Streamable HTTP (default)                   │  │ │
│  │  │  • Claude Code              │        │  • SSE (fallback)                              │  │ │
│  │  │  • Local MCP clients        │        │  • Port 8000 (configurable)                    │  │ │
│  │  │  • JSON-RPC over stdin/out  │        │  • CORS support                                │  │ │
│  │  └─────────────────────────────┘        └─────────────────────────────────────────────────┘  │ │
│  └───────────────────────────────────────────────────────────────────────────────────────────────┘ │
│                                               │                                                     │
│                                               ▼                                                     │
│  ┌───────────────────────────────────────────────────────────────────────────────────────────────┐ │
│  │                                   FASTMCP 2.0 CORE                                            │ │
│  │                                                                                               │ │
│  │  ┌──────────────────┐  ┌──────────────────┐  ┌──────────────────┐  ┌──────────────────────┐  │ │
│  │  │   Tool Registry  │  │ Resource Registry│  │  Prompt Registry │  │  Context Manager     │  │ │
│  │  │                  │  │                  │  │                  │  │                      │  │ │
│  │  │  • 40+ tools     │  │  • 10 resources  │  │  • 15 prompts    │  │  • Progress report   │  │ │
│  │  │  • Prefixed      │  │  • URI patterns  │  │  • 3 categories  │  │  • Logging           │  │ │
│  │  │  • Typed params  │  │  • Read-only     │  │  • Parameters    │  │  • Request context   │  │ │
│  │  └──────────────────┘  └──────────────────┘  └──────────────────┘  └──────────────────────┘  │ │
│  │                                                                                               │ │
│  │  ┌────────────────────────────────────────────────────────────────────────────────────────┐  │ │
│  │  │                            Server Composition (mount)                                  │  │ │
│  │  │                                                                                        │  │ │
│  │  │  ┌──────────────┐ ┌──────────────┐ ┌──────────────┐ ┌──────────────┐ ┌─────────────┐  │  │ │
│  │  │  │ cache-tools  │ │ opsi-tools   │ │  dbm-tools   │ │ admin-tools  │ │   main      │  │  │ │
│  │  │  │  prefix:     │ │  prefix:     │ │  prefix:     │ │  prefix:     │ │  (no pfx)   │  │  │ │
│  │  │  │  cache_      │ │  opsi_       │ │  dbm_        │ │  admin_      │ │             │  │  │ │
│  │  │  │              │ │              │ │              │ │              │ │  • Skills   │  │  │ │
│  │  │  │  8 tools     │ │  9 tools     │ │  8 tools     │ │  10 tools    │ │  • Welcome  │  │  │ │
│  │  │  │  4 resources │ │  1 resource  │ │  2 resources │ │  3 resources │ │    resource │  │  │ │
│  │  │  └──────────────┘ └──────────────┘ └──────────────┘ └──────────────┘ └─────────────┘  │  │ │
│  │  └────────────────────────────────────────────────────────────────────────────────────────┘  │ │
│  └───────────────────────────────────────────────────────────────────────────────────────────────┘ │
│                                               │                                                     │
│                                               ▼                                                     │
│  ┌───────────────────────────────────────────────────────────────────────────────────────────────┐ │
│  │                                  AUTHENTICATION LAYER                                         │ │
│  │                                                                                               │ │
│  │  ┌────────────────────────────────────────────────────────────────────────────────────────┐  │ │
│  │  │                          Hybrid Authentication Manager                                 │  │ │
│  │  │                                                                                        │  │ │
│  │  │  detect_auth_mode() → AuthMode.OAUTH | AuthMode.API_KEY | AuthMode.RESOURCE_PRINCIPAL │  │ │
│  │  └────────────────────────────────────────────────────────────────────────────────────────┘  │ │
│  │           │                           │                              │                        │ │
│  │           ▼                           ▼                              ▼                        │ │
│  │  ┌────────────────────┐    ┌────────────────────┐    ┌─────────────────────────────────┐    │ │
│  │  │   OCI IAM OAuth    │    │   API Key Auth     │    │     Resource Principal          │    │ │
│  │  │                    │    │                    │    │                                 │    │ │
│  │  │  ┌──────────────┐  │    │  ┌──────────────┐  │    │  ┌─────────────────────────┐   │    │ │
│  │  │  │ OIDC Proxy   │  │    │  │ Config File  │  │    │  │  Instance Metadata      │   │    │ │
│  │  │  │              │  │    │  │ ~/.oci/config│  │    │  │  Auth (OCI Functions)   │   │    │ │
│  │  │  └──────┬───────┘  │    │  └──────┬───────┘  │    │  └────────────┬────────────┘   │    │ │
│  │  │         ▼          │    │         ▼          │    │               ▼                │    │ │
│  │  │  ┌──────────────┐  │    │  ┌──────────────┐  │    │  ┌─────────────────────────┐   │    │ │
│  │  │  │Token Exchange│  │    │  │ Profile Sel. │  │    │  │  Dynamic Credentials    │   │    │ │
│  │  │  │              │  │    │  │              │  │    │  │  (Auto-rotation)        │   │    │ │
│  │  │  └──────┬───────┘  │    │  └──────────────┘  │    │  └─────────────────────────┘   │    │ │
│  │  │         ▼          │    │                    │    │                                 │    │ │
│  │  │  ┌──────────────┐  │    │                    │    │                                 │    │ │
│  │  │  │ Disk Storage │  │    │                    │    │                                 │    │ │
│  │  │  │ (Encrypted)  │  │    │                    │    │                                 │    │ │
│  │  │  └──────────────┘  │    │                    │    │                                 │    │ │
│  │  └────────────────────┘    └────────────────────┘    └─────────────────────────────────┘    │ │
│  └───────────────────────────────────────────────────────────────────────────────────────────────┘ │
│                                               │                                                     │
│                                               ▼                                                     │
│  ┌───────────────────────────────────────────────────────────────────────────────────────────────┐ │
│  │                                   BUSINESS LOGIC LAYER                                        │ │
│  │                                                                                               │ │
│  │  ┌─────────────────────┐  ┌─────────────────────┐  ┌─────────────────────────────────────┐   │ │
│  │  │   Cache Manager     │  │   Skills Engine     │  │        OCI Client Factory           │   │ │
│  │  │                     │  │                     │  │                                     │   │ │
│  │  │  • Local file cache │  │  • 13 DBA skills    │  │  • Operations Insights Client       │   │ │
│  │  │  • 24-hour validity │  │  • Pattern matching │  │  • Database Management Client       │   │ │
│  │  │  • Zero API calls   │  │  • Tool selection   │  │  • Identity Client                  │   │ │
│  │  │  • Instant queries  │  │  • Token optimize   │  │  • Multi-region support             │   │ │
│  │  └─────────────────────┘  └─────────────────────┘  │  • Client caching (16 clients)      │   │ │
│  │                                                     │  • Automatic pagination             │   │ │
│  │                                                     └─────────────────────────────────────┘   │ │
│  └───────────────────────────────────────────────────────────────────────────────────────────────┘ │
│                                                                                                     │
└─────────────────────────────────────────────────────────────────────────────────────────────────────┘
                                               │
                                               ▼
┌─────────────────────────────────────────────────────────────────────────────────────────────────────┐
│                                 ORACLE CLOUD INFRASTRUCTURE                                          │
│                                                                                                     │
│  ┌─────────────────────────────────────────────────────────────────────────────────────────────┐   │
│  │                                    Regional Endpoints                                        │   │
│  │                                                                                              │   │
│  │  ┌─────────────────────────┐  ┌─────────────────────────┐  ┌─────────────────────────┐     │   │
│  │  │  operationsinsights.    │  │     database.           │  │     identity.            │     │   │
│  │  │  {region}.oci.          │  │  {region}.oraclecloud.  │  │  {region}.oci.           │     │   │
│  │  │  oraclecloud.com        │  │  com                    │  │  oraclecloud.com         │     │   │
│  │  │                         │  │                         │  │                          │     │   │
│  │  │  • Database Insights    │  │  • Managed Databases    │  │  • Compartments          │     │   │
│  │  │  • Host Insights        │  │  • SQL Plan Baselines   │  │  • Users                 │     │   │
│  │  │  • SQL Statistics       │  │  • AWR/ADDM             │  │  • Policies              │     │   │
│  │  │  • Capacity Planning    │  │  • Tablespaces          │  │  • Identity Domains      │     │   │
│  │  │  • ML Forecasting       │  │  • Performance Hub      │  │                          │     │   │
│  │  │  • OPSI Warehouse       │  │                         │  │                          │     │   │
│  │  └─────────────────────────┘  └─────────────────────────┘  └─────────────────────────┘     │   │
│  └─────────────────────────────────────────────────────────────────────────────────────────────┘   │
│                                                                                                     │
└─────────────────────────────────────────────────────────────────────────────────────────────────────┘
```

---

## Package Structure

```
mcp_oci_opsi/
├── __init__.py                    # Package initialization
├── __main__.py                    # Entry point (version selection)
├── main.py                        # v2 server (original FastMCP)
├── main_v3.py                     # v3 server (FastMCP 2.0)
├── config.py                      # OCI configuration management
├── cache.py                       # Local cache implementation
├── oci_clients.py                 # OCI SDK client factories
├── visualization.py               # ASCII chart utilities
│
├── auth/                          # Authentication module
│   ├── __init__.py               # Exports all auth functions
│   ├── hybrid_auth.py            # Hybrid auth manager
│   └── oci_oauth.py              # OCI IAM OAuth provider
│
├── servers/                       # Sub-server modules
│   ├── __init__.py               # Server exports
│   ├── cache_server.py           # Cache tools (8) + resources (4)
│   ├── opsi_server.py            # OPSI tools (9) + resources (1)
│   ├── dbm_server.py             # DBM tools (8) + resources (2)
│   └── admin_server.py           # Admin tools (10) + resources (3)
│
├── prompts/                       # MCP prompt templates
│   ├── __init__.py               # Prompt exports
│   ├── analysis_prompts.py       # Performance analysis prompts
│   ├── operations_prompts.py     # Operations management prompts
│   └── reporting_prompts.py      # Report generation prompts
│
├── skills/                        # DBA skills (SKILL.md files)
│   ├── fleet-overview/
│   ├── sql-performance/
│   ├── capacity-planning/
│   └── ... (13 skills total)
│
├── skills_loader.py               # Skill discovery and loading
├── tools_skills.py                # Skills MCP tools
│
├── tools_cache.py                 # Cache tools implementation
├── tools_opsi.py                  # OPSI tools implementation
├── tools_opsi_extended.py         # Extended OPSI tools
├── tools_dbmanagement.py          # DBM tools implementation
├── tools_dbmanagement_monitoring.py
├── tools_sqlwatch.py
├── tools_database_registration.py
├── tools_oracle_database.py
└── tools_visualization.py
```

---

## Authentication Architecture

### OAuth Flow (Production)

```
┌─────────────────────────────────────────────────────────────────────────────────────────────┐
│                                    OAuth Authentication Flow                                 │
└─────────────────────────────────────────────────────────────────────────────────────────────┘

┌─────────────┐                    ┌─────────────────┐                    ┌──────────────────┐
│   User      │                    │   MCP Server    │                    │  OCI Identity    │
│  (Browser)  │                    │                 │                    │  Domain (IDCS)   │
└──────┬──────┘                    └────────┬────────┘                    └────────┬─────────┘
       │                                    │                                      │
       │  1. Access MCP Server              │                                      │
       │ ─────────────────────────────────> │                                      │
       │                                    │                                      │
       │  2. Redirect to OIDC               │                                      │
       │ <───────────────────────────────── │                                      │
       │                                    │                                      │
       │  3. Authenticate with IdP          │                                      │
       │ ───────────────────────────────────┼─────────────────────────────────────>│
       │                                    │                                      │
       │  4. Authorization Code             │                                      │
       │ <──────────────────────────────────┼──────────────────────────────────────│
       │                                    │                                      │
       │  5. Callback with Code             │                                      │
       │ ─────────────────────────────────> │                                      │
       │                                    │                                      │
       │                                    │  6. Exchange Code for Tokens         │
       │                                    │ ────────────────────────────────────>│
       │                                    │                                      │
       │                                    │  7. ID Token + Access Token          │
       │                                    │ <────────────────────────────────────│
       │                                    │                                      │
       │                                    │  8. Store Tokens (Encrypted Disk)    │
       │                                    │  ┌─────────────────────────────────┐ │
       │                                    │  │  /data/tokens/{user_id}.json   │ │
       │                                    │  │  (Fernet encrypted)            │ │
       │                                    │  └─────────────────────────────────┘ │
       │                                    │                                      │
       │                                    │  9. Token Exchange for OCI           │
       │                                    │ ────────────────────────────────────>│
       │                                    │                                      │
       │                                    │  10. OCI Security Token              │
       │                                    │ <────────────────────────────────────│
       │                                    │                                      │
       │  11. MCP Response                  │                                      │
       │ <───────────────────────────────── │                                      │
       │                                    │                                      │
```

### API Key Flow (Development)

```
┌──────────────────────────────────────────────────────────────────────────────┐
│                           API Key Authentication Flow                         │
└──────────────────────────────────────────────────────────────────────────────┘

┌─────────────┐                    ┌─────────────────┐                    ┌─────────────┐
│  MCP Client │                    │   MCP Server    │                    │  OCI APIs   │
│  (Claude)   │                    │                 │                    │             │
└──────┬──────┘                    └────────┬────────┘                    └──────┬──────┘
       │                                    │                                    │
       │  1. MCP Tool Call                  │                                    │
       │ ─────────────────────────────────> │                                    │
       │                                    │                                    │
       │                                    │  2. Load ~/.oci/config             │
       │                                    │  ┌──────────────────────────────┐  │
       │                                    │  │ [PROFILE]                    │  │
       │                                    │  │ user=[Link to Secure Variable: OCI_USER_OCID]           │  │
       │                                    │  │ tenancy=[Link to Secure Variable: OCI_TENANCY_OCID]     │  │
       │                                    │  │ key_file=~/.oci/key.pem      │  │
       │                                    │  │ fingerprint=xx:xx:xx...      │  │
       │                                    │  └──────────────────────────────┘  │
       │                                    │                                    │
       │                                    │  3. Create Signer                  │
       │                                    │  (cache for 1 hour)                │
       │                                    │                                    │
       │                                    │  4. Sign Request                   │
       │                                    │ ──────────────────────────────────>│
       │                                    │                                    │
       │                                    │  5. API Response                   │
       │                                    │ <──────────────────────────────────│
       │                                    │                                    │
       │  6. Tool Response                  │                                    │
       │ <───────────────────────────────── │                                    │
       │                                    │                                    │
```

---

## Data Flow

### Tool Execution Flow

```
┌─────────────────────────────────────────────────────────────────────────────────────────────┐
│                                    Tool Execution Flow                                       │
└─────────────────────────────────────────────────────────────────────────────────────────────┘

User Query: "Show CPU forecast for database PRODDB01 for next 30 days"
                                        │
                                        ▼
┌───────────────────────────────────────────────────────────────────────────────────────────┐
│                                    LLM (Claude)                                            │
│                                                                                            │
│  1. Parse query → determine tool: opsi_get_database_resource_forecast                     │
│  2. Resolve parameters:                                                                    │
│     - database: PRODDB01 → lookup in cache → [Link to Secure Variable: OCI_DATABASE_OCID]                            │
│     - forecast_days: 30                                                                    │
│     - resource_metric: CPU                                                                 │
└───────────────────────────────────────────────────────────────────────────────────────────┘
                                        │
                                        ▼
┌───────────────────────────────────────────────────────────────────────────────────────────┐
│                                  MCP Protocol Layer                                        │
│                                                                                            │
│  JSON-RPC Request:                                                                         │
│  {                                                                                         │
│    "method": "tools/call",                                                                 │
│    "params": {                                                                             │
│      "name": "opsi_get_database_resource_forecast",                                       │
│      "arguments": {                                                                        │
│        "database_insight_id": "[Link to Secure Variable: OCI_OPSI_DATABASE_INSIGHT_OCID]",                             │
│        "resource_metric": "CPU",                                                           │
│        "forecast_days": 30                                                                 │
│      }                                                                                     │
│    }                                                                                       │
│  }                                                                                         │
└───────────────────────────────────────────────────────────────────────────────────────────┘
                                        │
                                        ▼
┌───────────────────────────────────────────────────────────────────────────────────────────┐
│                                  FastMCP Router                                            │
│                                                                                            │
│  1. Parse tool name: opsi_get_database_resource_forecast                                  │
│  2. Route to sub-server: opsi-tools (prefix: opsi_)                                       │
│  3. Invoke: get_database_resource_forecast()                                              │
└───────────────────────────────────────────────────────────────────────────────────────────┘
                                        │
                                        ▼
┌───────────────────────────────────────────────────────────────────────────────────────────┐
│                                  Tool Implementation                                       │
│                                                                                            │
│  async def get_database_resource_forecast(ctx: Context, ...):                             │
│      # 1. Progress reporting                                                               │
│      await ctx.report_progress(0, 100)                                                    │
│                                                                                            │
│      # 2. Get authenticated client                                                         │
│      signer = get_oci_signer()                                                             │
│      client = get_opsi_client(signer)                                                      │
│                                                                                            │
│      # 3. Make API call                                                                    │
│      response = client.summarize_database_insight_resource_forecast_trend(...)            │
│                                                                                            │
│      # 4. Format response                                                                  │
│      return {"forecast": [...], "recommendations": [...]}                                  │
└───────────────────────────────────────────────────────────────────────────────────────────┘
                                        │
                                        ▼
┌───────────────────────────────────────────────────────────────────────────────────────────┐
│                                  OCI API Layer                                             │
│                                                                                            │
│  Request:                                                                                  │
│  GET https://operationsinsights.us-phoenix-1.oci.oraclecloud.com/                         │
│      20200630/databaseInsights/{id}/resourceForecastTrend                                 │
│                                                                                            │
│  Headers:                                                                                  │
│    Authorization: Signature version="1",keyId="[Link to Secure Variable: OCI_TENANCY_OCID]/[Link to Secure Variable: OCI_USER_OCID]/fingerprint"│
│    Date: Wed, 03 Dec 2025 12:00:00 GMT                                                    │
│    (request-target): get /20200630/databaseInsights/...                                   │
└───────────────────────────────────────────────────────────────────────────────────────────┘
                                        │
                                        ▼
┌───────────────────────────────────────────────────────────────────────────────────────────┐
│                                  Response Processing                                       │
│                                                                                            │
│  {                                                                                         │
│    "forecast": [                                                                           │
│      {"timestamp": "2025-12-03T00:00:00Z", "value": 45.2, "confidence": 0.95},           │
│      {"timestamp": "2025-12-10T00:00:00Z", "value": 52.1, "confidence": 0.90},           │
│      ...                                                                                   │
│    ],                                                                                      │
│    "recommendations": [                                                                    │
│      "CPU usage projected to increase 15% over next 30 days",                             │
│      "Consider scaling up by 2025-12-20 to maintain headroom"                             │
│    ]                                                                                       │
│  }                                                                                         │
└───────────────────────────────────────────────────────────────────────────────────────────┘
```

---

## Caching Architecture

### Cache Structure

```
┌─────────────────────────────────────────────────────────────────────────────────────────────┐
│                                    Cache Architecture                                        │
└─────────────────────────────────────────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────────────────────────────────────┐
│                             Local Cache File (~/.mcp_oci_opsi_cache.json)                 │
│                                                                                           │
│  {                                                                                        │
│    "metadata": {                                                                          │
│      "created": "2025-12-03T10:00:00Z",                                                  │
│      "profile": "DEFAULT",                                                                │
│      "tenancy_ocid": "[Link to Secure Variable: OCI_TENANCY_OCID]"                                         │
│    },                                                                                     │
│    "databases": {                                                                         │
│      "[Link to Secure Variable: OCI_DATABASE_OCID]": {                                                        │
│        "name": "PRODDB01",                                                                │
│        "type": "autonomous",                                                              │
│        "compartment_id": "[Link to Secure Variable: OCI_COMPARTMENT_OCID]",                                         │
│        "compartment_name": "Production",                                                  │
│        "region": "us-phoenix-1",                                                          │
│        "status": "ACTIVE",                                                                │
│        "database_insight_id": "[Link to Secure Variable: OCI_OPSI_DATABASE_INSIGHT_OCID]",                            │
│        "managed_database_id": "[Link to Secure Variable: OCI_MANAGED_DATABASE_OCID]"                                 │
│      },                                                                                   │
│      ...                                                                                  │
│    },                                                                                     │
│    "compartments": {                                                                      │
│      "[Link to Secure Variable: OCI_COMPARTMENT_OCID]": {"name": "Production", "path": "root/Production"},          │
│      ...                                                                                  │
│    },                                                                                     │
│    "hosts": {...},                                                                        │
│    "exadata": {...}                                                                       │
│  }                                                                                        │
└──────────────────────────────────────────────────────────────────────────────────────────┘
                                        │
                      ┌─────────────────┴─────────────────┐
                      │                                   │
                      ▼                                   ▼
         ┌──────────────────────┐            ┌──────────────────────┐
         │   Cache Tools        │            │    OPSI/DBM Tools    │
         │                      │            │                      │
         │  • Zero API calls    │            │  • Real-time data    │
         │  • <50ms response    │            │  • API calls         │
         │  • Inventory data    │            │  • Performance data  │
         │                      │            │                      │
         │  get_fleet_summary   │            │  summarize_sql_stats │
         │  search_databases    │            │  get_awr_report      │
         │  list_compartments   │            │  get_capacity_trend  │
         └──────────────────────┘            └──────────────────────┘
```

### Cache Refresh Strategy

```
┌─────────────────────────────────────────────────────────────────────────────────────────┐
│                                Cache Refresh Strategy                                    │
└─────────────────────────────────────────────────────────────────────────────────────────┘

                    ┌───────────────────────────────────────┐
                    │          Cache Request                │
                    └───────────────────┬───────────────────┘
                                        │
                                        ▼
                    ┌───────────────────────────────────────┐
                    │       Check Cache Validity            │
                    │       (24-hour TTL)                   │
                    └───────────────────┬───────────────────┘
                                        │
                         ┌──────────────┴──────────────┐
                         │                             │
                    Valid│                             │Invalid/Missing
                         ▼                             ▼
          ┌─────────────────────────┐   ┌─────────────────────────┐
          │   Return Cached Data    │   │   Trigger Cache Build   │
          │   (instant response)    │   │   (async background)    │
          └─────────────────────────┘   └───────────┬─────────────┘
                                                    │
                                                    ▼
                                     ┌─────────────────────────────┐
                                     │   Scan Compartments         │
                                     │   (recursive)               │
                                     └───────────────┬─────────────┘
                                                     │
                              ┌───────────────────────┼───────────────────────┐
                              │                       │                       │
                              ▼                       ▼                       ▼
               ┌─────────────────────┐ ┌─────────────────────┐ ┌─────────────────────┐
               │ List Database       │ │ List Host           │ │ List Exadata        │
               │ Insights            │ │ Insights            │ │ Insights            │
               └──────────┬──────────┘ └──────────┬──────────┘ └──────────┬──────────┘
                          │                       │                       │
                          └───────────────────────┼───────────────────────┘
                                                  │
                                                  ▼
                                   ┌─────────────────────────────┐
                                   │   Write Cache File          │
                                   │   (atomic write)            │
                                   └─────────────────────────────┘
```

---

## Skills Architecture

### Skill Structure

```
skills/
├── fleet-overview/
│   └── SKILL.md
├── sql-performance/
│   └── SKILL.md
├── capacity-planning/
│   └── SKILL.md
└── ...

SKILL.md Format:
┌─────────────────────────────────────────────────────────────────────────────────────────────┐
│ ---                                                                                          │
│ skill_name: sql-performance                                                                  │
│ description: Analyze and tune SQL performance                                                │
│ version: 1.0.0                                                                               │
│ tools:                                                                                       │
│   - opsi_summarize_sql_statistics                                                           │
│   - opsi_summarize_sql_insights                                                             │
│   - dbm_get_awr_report                                                                      │
│ triggers:                                                                                    │
│   - slow query                                                                               │
│   - sql performance                                                                          │
│   - execution plan                                                                           │
│ ---                                                                                          │
│                                                                                              │
│ # SQL Performance Analysis Skill                                                             │
│                                                                                              │
│ ## When to Use                                                                               │
│ Use this skill when analyzing slow queries or SQL performance issues.                        │
│                                                                                              │
│ ## Workflow                                                                                  │
│ 1. Get SQL statistics summary                                                                │
│ 2. Identify top SQL by CPU/IO                                                                │
│ 3. Check for plan changes                                                                    │
│ 4. Generate recommendations                                                                  │
└─────────────────────────────────────────────────────────────────────────────────────────────┘
```

### Skill Matching Flow

```
User Query: "My database is slow, help me find the problem"
                                    │
                                    ▼
                  ┌─────────────────────────────────────┐
                  │         Skills Loader               │
                  │                                     │
                  │  get_skill_for_query(query)        │
                  └─────────────────┬───────────────────┘
                                    │
                                    ▼
                  ┌─────────────────────────────────────┐
                  │       Pattern Matching              │
                  │                                     │
                  │  "slow" → sql-performance           │
                  │  "database" → database-diagnostics  │
                  │                                     │
                  │  Best match: sql-performance        │
                  └─────────────────┬───────────────────┘
                                    │
                                    ▼
                  ┌─────────────────────────────────────┐
                  │       Return Skill Context          │
                  │                                     │
                  │  {                                  │
                  │    "skill": "sql-performance",     │
                  │    "tools": [...],                 │
                  │    "workflow": "...",              │
                  │    "instructions": "..."           │
                  │  }                                  │
                  └─────────────────────────────────────┘
```

---

## Deployment Architecture

### OCI VM Deployment

```
┌─────────────────────────────────────────────────────────────────────────────────────────────┐
│                                OCI VM Deployment Architecture                                │
└─────────────────────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────────────────────┐
│                                      OCI Tenancy                                             │
│                                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────────────────────┐   │
│  │                               Virtual Cloud Network                                  │   │
│  │                                                                                      │   │
│  │  ┌────────────────────────────────────────────────────────────────────────────┐    │   │
│  │  │                            Public Subnet                                    │    │   │
│  │  │                            10.0.0.0/24                                      │    │   │
│  │  │                                                                             │    │   │
│  │  │  ┌─────────────────────────────────────────────────────────────────────┐   │    │   │
│  │  │  │                     Compute Instance                                 │   │    │   │
│  │  │  │                     VM.Standard.E4.Flex                              │   │    │   │
│  │  │  │                     2 OCPU, 16 GB RAM                                │   │    │   │
│  │  │  │                                                                      │   │    │   │
│  │  │  │  ┌─────────────────────────────────────────────────────────────┐   │   │    │   │
│  │  │  │  │                  Docker Container                            │   │   │    │   │
│  │  │  │  │                                                              │   │   │    │   │
│  │  │  │  │  ┌──────────────────────────────────────────────────────┐  │   │   │    │   │
│  │  │  │  │  │             MCP OCI OPSI Server v3.0                 │  │   │   │    │   │
│  │  │  │  │  │                                                      │  │   │   │    │   │
│  │  │  │  │  │  • HTTP Transport (port 8000)                       │  │   │   │    │   │
│  │  │  │  │  │  • OAuth or API Key authentication                  │  │   │   │    │   │
│  │  │  │  │  │  • All tools, resources, prompts                    │  │   │   │    │   │
│  │  │  │  │  └──────────────────────────────────────────────────────┘  │   │   │    │   │
│  │  │  │  │                                                              │   │   │    │   │
│  │  │  │  │  Volumes:                                                    │   │   │    │   │
│  │  │  │  │  • /home/mcp/.oci (OCI config, read-only)                   │   │   │    │   │
│  │  │  │  │  • /data (tokens, cache)                                    │   │   │    │   │
│  │  │  │  └─────────────────────────────────────────────────────────────┘   │   │    │   │
│  │  │  │                                                                      │   │    │   │
│  │  │  │  systemd: mcp-oci-opsi.service (auto-restart)                       │   │    │   │
│  │  │  └─────────────────────────────────────────────────────────────────────┘   │    │   │
│  │  │                                                                             │    │   │
│  │  └────────────────────────────────────────────────────────────────────────────┘    │   │
│  │                                     │                                               │   │
│  │                          ┌──────────┴──────────┐                                   │   │
│  │                          │                     │                                   │   │
│  │                  ┌───────┴───────┐    ┌───────┴───────┐                           │   │
│  │                  │ Security List │    │ Internet      │                           │   │
│  │                  │               │    │ Gateway       │                           │   │
│  │                  │ • SSH (22)    │    │               │                           │   │
│  │                  │ • HTTP (8000) │    │               │                           │   │
│  │                  └───────────────┘    └───────────────┘                           │   │
│  │                                                                                    │   │
│  └────────────────────────────────────────────────────────────────────────────────────┘   │
│                                                                                             │
└─────────────────────────────────────────────────────────────────────────────────────────────┘
                                        │
                            Connects to OCI APIs
                                        │
                                        ▼
              ┌─────────────────────────────────────────────────────────┐
              │              OCI Services (All Regions)                 │
              │                                                         │
              │  Operations Insights │ Database Management │ Identity   │
              └─────────────────────────────────────────────────────────┘
```

---

## Security Considerations

### Authentication Security

1. **OAuth Mode**:
   - Tokens encrypted with Fernet (AES-128-CBC)
   - Tokens stored on disk, not in memory long-term
   - Token exchange provides time-limited OCI credentials
   - JWT signing key required for session management

2. **API Key Mode**:
   - Private key never leaves ~/.oci directory
   - Signer cached for 1 hour maximum
   - Profile isolation for multi-tenancy

3. **Resource Principal Mode** (Future):
   - No credentials stored
   - Instance metadata provides auth
   - Automatic credential rotation

### Network Security

1. **VCN Configuration**:
   - Private subnet recommended for production
   - Bastion service for SSH access
   - Security lists with minimal ingress

2. **TLS/SSL**:
   - HTTPS recommended for HTTP transport
   - Load balancer with SSL termination
   - Internal communication can be HTTP

### Data Security

1. **Cache Files**:
   - Stored in user home directory
   - Contains OCIDs and names (not credentials)
   - 24-hour TTL limits data staleness

2. **Token Storage**:
   - Fernet encryption (symmetric)
   - Key must be stored securely
   - Recommend using OCI Vault for key storage

---

## Performance Considerations

### Response Time Targets

| Operation Type | Target | Method |
|----------------|--------|--------|
| Cache queries | <50ms | Local file read |
| Simple API calls | <500ms | Single OCI API |
| Complex analytics | <5s | Multiple API calls |
| Report generation | <30s | Large data processing |

### Optimization Strategies

1. **Client Caching**: OCI clients cached per region (16 max)
2. **Request Batching**: Pagination handled automatically
3. **Parallel Execution**: Multiple API calls where possible
4. **Local Cache**: Zero API calls for inventory queries
5. **Token Caching**: OAuth tokens cached until expiry
