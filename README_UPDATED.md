# MCP OCI OPSI Server

**Enhanced MCP (Model Context Protocol) server for Oracle Cloud Infrastructure Operations Insights and Database Management**

[![Version](https://img.shields.io/badge/version-2.0.0-blue.svg)](https://github.com/your-org/mcp-oci-opsi)
[![Tools](https://img.shields.io/badge/tools-117-green.svg)](https://github.com/your-org/mcp-oci-opsi/wiki/API-Coverage)
[![Coverage](https://img.shields.io/badge/API%20coverage-52%25-yellow.svg)](https://github.com/your-org/mcp-oci-opsi/wiki/API-Coverage)
[![Tests](https://img.shields.io/badge/tests-passing-brightgreen.svg)](https://github.com/your-org/mcp-oci-opsi)

## 🚀 What's New in v2.0

### Major Enhancements (November 2025)

✨ **18 New APIs** for detailed database analysis:
- **OPSI Resource Statistics** (4 APIs) - Real-time resource monitoring
- **User Management** (6 APIs) - Complete user and role management
- **Tablespace Management** (3 APIs) - Storage monitoring and planning
- **AWR Metrics** (5 APIs) - Advanced performance troubleshooting

✨ **Agent Detection & Prioritization**:
- Automatic detection of Management Agent (MACS) vs Cloud Agent databases
- Priority-based sorting (1-3 scale)
- Agent adoption percentage tracking
- Smart migration recommendations

✨ **Multi-Tenancy Support**:
- Interactive profile selection
- Support for multiple OCI accounts
- Profile validation and switching
- No environment variable changes needed

📊 **Tool Count**: 99 → 117 (+18%)
📈 **API Coverage**: 48% → 52%
🧪 **Test Success**: 100% (all tests passing)

---

## 📖 Table of Contents

- [Overview](#overview)
- [Quick Start](#quick-start)
- [Features](#features)
- [Installation](#installation)
- [Configuration](#configuration)
- [Usage Examples](#usage-examples)
- [Tool Catalog](#tool-catalog)
- [Testing](#testing)
- [Documentation](#documentation)
- [Contributing](#contributing)
- [License](#license)

---

## Overview

This MCP server provides comprehensive access to Oracle Cloud Infrastructure (OCI) Operations Insights and Database Management services through a natural language interface. Query database performance, analyze SQL statistics, monitor resources, and manage databases using simple conversational commands through Claude Desktop or Claude Code.

### Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────────┐
│                                                                         │
│                            USER / APPLICATION                           │
│                                                                         │
└────────────────────────────────┬────────────────────────────────────────┘
                                 │
                    Natural Language Queries
                    "Show CPU forecast for next 30 days"
                    "Which SQL statements are degrading?"
                                 │
                                 ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                         LARGE LANGUAGE MODEL (LLM)                      │
│                         (Claude, GPT, etc.)                             │
└────────────────────────────────┬────────────────────────────────────────┘
                                 │
                    MCP Protocol (JSON-RPC)
                                 │
                                 ▼
┌─────────────────────────────────────────────────────────────────────────┐
│             MCP OCI OPERATIONS INSIGHTS SERVER (117 Tools)              │
│  • Database Insights  • Host Insights  • SQL Analytics                 │
│  • User Management   • Tablespace Mgmt • AWR Metrics                   │
│  • Agent Detection   • Multi-Tenancy   • Performance Analysis          │
└────────────────────────────────┬────────────────────────────────────────┘
                                 │
                    HTTPS REST API Calls
                                 │
                                 ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                    ORACLE CLOUD INFRASTRUCTURE                          │
│  • Operations Insights  • Database Management  • Multi-Region           │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## Quick Start

### Prerequisites

- Python 3.8+
- OCI CLI configured with valid credentials
- Access to OCI Operations Insights and Database Management

### Installation

```bash
# Clone the repository
git clone https://github.com/your-org/mcp-oci-opsi.git
cd mcp-oci-opsi

# Create virtual environment
python3 -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
pip install -e .
```

### Quick Configuration

```bash
# Set compartment ID for caching
export CACHE_COMPARTMENT_IDS="ocid1.compartment.oc1..aaa..."

# Build initial cache for fast queries
python3 build_cache.py --select-profile  # Interactive profile selection
```

### First Query

```python
from mcp_oci_opsi.tools_opsi_extended import summarize_sql_statistics

result = summarize_sql_statistics(
    compartment_id="ocid1.compartment.oc1..xxx",
    time_interval_start="2025-11-17T00:00:00Z",
    time_interval_end="2025-11-18T00:00:00Z"
)

print(f"Found {result['count']} SQL statements")
```

---

## Features

### 🎯 Core Capabilities

#### Operations Insights (66 tools)
- **Database Insights**: List, analyze, and forecast database performance
- **Host Insights**: Monitor host resource utilization and capacity
- **SQL Analytics**: Deep SQL performance analysis with warehouse queries
- **Resource Statistics**: Real-time and historical resource monitoring **[NEW]**
- **Capacity Planning**: ML-powered forecasting and trend analysis
- **Exadata Insights**: Specialized Exadata infrastructure monitoring

#### Database Management (51 tools)
- **Managed Databases**: Query and manage database fleet
- **User Management**: Complete user, role, and privilege management **[NEW]**
- **Tablespace Management**: Monitor and analyze tablespace usage **[NEW]**
- **AWR Metrics**: Comprehensive AWR-based performance analysis **[NEW]**
- **SQL Plan Baselines**: Manage and optimize SQL execution plans
- **Performance Hub**: ADDM, ASH, and AWR analytics
- **SQL Watch**: Manage SQL monitoring across fleet

### ✨ Enhanced Features

#### 🤖 Agent Detection & Prioritization
- Automatic identification of Management Agent (MACS) vs Cloud Agent databases
- Priority-based classification (Priority 1-3)
- Agent adoption percentage tracking
- API compatibility matrix per agent type
- Migration recommendations for EM-managed databases

#### 👥 Multi-Tenancy Support
- Work with multiple OCI accounts simultaneously
- Interactive profile selection
- Profile validation before operations
- No environment variable changes needed
- Cached authentication for performance

#### 📊 Advanced Analytics
- **Resource Statistics**: CPU, Memory, Storage, IO monitoring
- **Utilization Insights**: Pattern detection and anomaly identification
- **Tablespace Trends**: Growth patterns and capacity planning
- **AWR Metrics**: CPU usage, wait events, system stats, parameter changes
- **User Analytics**: Privilege auditing and access control review

### 🚀 Performance Features

- **Intelligent Caching**: Sub-50ms responses for inventory queries
- **Multi-Region Support**: Automatic region detection from OCIDs
- **Bulk Operations**: Process multiple databases concurrently
- **Profile Caching**: 50-100x faster repeated access
- **Connection Pooling**: Reuse authenticated sessions

---

## Installation

### System Requirements

- **Python**: 3.8 or higher
- **OCI CLI**: Installed and configured
- **Memory**: 512MB minimum, 1GB recommended
- **Disk**: 100MB for installation, 500MB for caching

### Detailed Installation Steps

#### 1. Install OCI CLI

```bash
# macOS/Linux
bash -c "$(curl -L https://raw.githubusercontent.com/oracle/oci-cli/master/scripts/install/install.sh)"

# Verify installation
oci --version
```

#### 2. Configure OCI CLI

```bash
# Run OCI configuration
oci setup config

# This will create ~/.oci/config with:
# - User OCID
# - Tenancy OCID
# - Region
# - API key fingerprint
# - Path to private key
```

#### 3. Install MCP Server

```bash
# Clone repository
git clone https://github.com/your-org/mcp-oci-opsi.git
cd mcp-oci-opsi

# Create virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install in development mode
pip install -e .
```

#### 4. Build Cache (Optional but Recommended)

```bash
# Set compartment IDs
export CACHE_COMPARTMENT_IDS="ocid1.compartment.oc1..aaa,ocid1.compartment.oc1..bbb"

# Build cache with profile selection
python3 build_cache.py --select-profile

# Or specify profile directly
python3 build_cache.py --profile production
```

---

## Configuration

### Environment Variables

```bash
# Required for cache building
export CACHE_COMPARTMENT_IDS="ocid1.compartment.oc1..xxx,..."

# Optional: Default compartment
export OCI_COMPARTMENT_ID="ocid1.compartment.oc1..xxx"

# Optional: Default profile (if not using interactive selection)
export OCI_CLI_PROFILE="DEFAULT"

# Optional: Region override
export OCI_REGION="us-phoenix-1"
```

### Multi-Profile Configuration

Create multiple profiles in `~/.oci/config`:

```ini
[DEFAULT]
user=ocid1.user.oc1..xxx
fingerprint=xx:xx:xx:xx:xx:xx:xx:xx:xx:xx:xx:xx:xx:xx:xx:xx
tenancy=ocid1.tenancy.oc1..xxx
region=us-phoenix-1
key_file=~/.oci/oci_api_key.pem

[production]
user=ocid1.user.oc1..yyy
fingerprint=yy:yy:yy:yy:yy:yy:yy:yy:yy:yy:yy:yy:yy:yy:yy:yy
tenancy=ocid1.tenancy.oc1..yyy
region=us-ashburn-1
key_file=~/.oci/oci_api_key_prod.pem

[development]
user=ocid1.user.oc1..zzz
fingerprint=zz:zz:zz:zz:zz:zz:zz:zz:zz:zz:zz:zz:zz:zz:zz:zz
tenancy=ocid1.tenancy.oc1..zzz
region=eu-frankfurt-1
key_file=~/.oci/oci_api_key_dev.pem
```

---

## Usage Examples

### 1. Agent Detection & Classification

```python
from mcp_oci_opsi.tools_database_discovery import list_database_insights_by_management_type

# Discover databases by agent type
result = list_database_insights_by_management_type(
    compartment_id="ocid1.compartment.oc1..xxx",
    profile="production"
)

# Check agent adoption
print(f"Agent Adoption: {result['summary']['agent_based_percentage']}%")
print(f"Recommendation: {result['summary']['recommendation']}")

# Get MACS-managed databases (highest priority)
macs_dbs = result['databases_by_type'].get('MACS_MANAGED_EXTERNAL_DATABASE', [])
print(f"Management Agent databases: {len(macs_dbs)}")
```

### 2. Resource Statistics Analysis

```python
from mcp_oci_opsi.tools_opsi_resource_stats import (
    summarize_database_insight_resource_statistics,
    summarize_database_insight_resource_usage
)

# Get resource statistics
stats = summarize_database_insight_resource_statistics(
    compartment_id="ocid1.compartment.oc1..xxx",
    resource_metric="CPU",
    profile="production"
)

for db in stats['items']:
    db_name = db['database_details']['database_name']
    cpu_util = db['current_statistics']['utilization_percent']
    print(f"{db_name}: {cpu_util}% CPU utilization")

# Get time-series usage data
usage = summarize_database_insight_resource_usage(
    compartment_id="ocid1.compartment.oc1..xxx",
    resource_metric="STORAGE",
    analysis_time_interval="DAILY"
)

print(f"Data points: {usage['data_points']}")
```

### 3. User Management

```python
from mcp_oci_opsi.tools_dbmanagement_users import (
    list_users,
    get_user,
    list_system_privileges
)

# List all database users
users = list_users(
    managed_database_id="ocid1.manageddatabase.oc1..xxx"
)

for user in users['items']:
    print(f"User: {user['name']}, Status: {user['status']}")

# Get detailed user information
user_detail = get_user(
    managed_database_id="ocid1.manageddatabase.oc1..xxx",
    user_name="ADMIN"
)

# List user privileges
privs = list_system_privileges(
    managed_database_id="ocid1.manageddatabase.oc1..xxx",
    user_name="ADMIN"
)

print(f"User has {privs['count']} system privileges")
```

### 4. Tablespace Monitoring

```python
from mcp_oci_opsi.tools_dbmanagement_tablespaces import (
    list_tablespaces,
    get_tablespace
)
from mcp_oci_opsi.tools_opsi_resource_stats import (
    summarize_database_insight_tablespace_usage_trend
)

# List all tablespaces
tablespaces = list_tablespaces(
    managed_database_id="ocid1.manageddatabase.oc1..xxx",
    tablespace_type="PERMANENT"
)

for ts in tablespaces['items']:
    print(f"{ts['name']}: {ts['used_percent_available']}% used")

# Get tablespace growth trend
trend = summarize_database_insight_tablespace_usage_trend(
    compartment_id="ocid1.compartment.oc1..xxx"
)

for ts in trend['tablespaces']:
    print(f"Tablespace: {ts['tablespace_name']}")
    for data in ts['usage_data']:
        print(f"  {data['end_timestamp']}: {data['utilization_percent']}%")
```

### 5. AWR Performance Analysis

```python
from mcp_oci_opsi.tools_dbmanagement_awr_metrics import (
    summarize_awr_db_cpu_usages,
    summarize_awr_db_wait_event_buckets,
    summarize_awr_db_parameter_changes
)
from datetime import datetime, timedelta

# Define time range
end_time = datetime.utcnow()
start_time = end_time - timedelta(days=1)

# Analyze CPU usage
cpu_usage = summarize_awr_db_cpu_usages(
    managed_database_id="ocid1.manageddatabase.oc1..xxx",
    time_greater_than_or_equal_to=start_time.isoformat() + "Z",
    time_less_than_or_equal_to=end_time.isoformat() + "Z"
)

for usage in cpu_usage['items']:
    print(f"Time: {usage['timestamp']}, DB CPU: {usage['db_cpu']}")

# Analyze wait events
wait_events = summarize_awr_db_wait_event_buckets(
    managed_database_id="ocid1.manageddatabase.oc1..xxx",
    time_greater_than_or_equal_to=start_time.isoformat() + "Z",
    time_less_than_or_equal_to=end_time.isoformat() + "Z"
)

# Top 5 wait events by total time
top_events = sorted(
    wait_events['items'],
    key=lambda x: x['total_time_waited'],
    reverse=True
)[:5]

for event in top_events:
    print(f"{event['name']}: {event['total_time_waited']}ms")

# Check parameter changes
param_changes = summarize_awr_db_parameter_changes(
    managed_database_id="ocid1.manageddatabase.oc1..xxx",
    time_greater_than_or_equal_to=start_time.isoformat() + "Z",
    time_less_than_or_equal_to=end_time.isoformat() + "Z"
)

for change in param_changes['items']:
    if change['is_changed']:
        print(f"Parameter '{change['name']}' changed:")
        print(f"  From: {change['begin_value']}")
        print(f"  To: {change['end_value']}")
```

### 6. Multi-Tenancy Operations

```python
from mcp_oci_opsi.tools_profile_management import (
    list_oci_profiles_enhanced,
    compare_oci_profiles
)

# List all available profiles
profiles = list_oci_profiles_enhanced()

for profile in profiles['profiles']:
    status = "✅" if profile['valid'] else "❌"
    print(f"{status} {profile['profile_name']}: {profile.get('region')}")

# Compare multiple profiles
comparison = compare_oci_profiles(["production", "development", "testing"])

for profile in comparison['profiles']:
    print(f"{profile['name']}: {profile['region']} - {profile['tenancy_name']}")

# Use different profiles for different operations
from mcp_oci_opsi.tools_opsi_extended import summarize_sql_statistics

# Production environment
prod_sql = summarize_sql_statistics(
    compartment_id="ocid1.compartment.oc1.phx..prod",
    profile="production"
)

# Development environment
dev_sql = summarize_sql_statistics(
    compartment_id="ocid1.compartment.oc1.iad..dev",
    profile="development"
)
```

---

## Tool Catalog

### Complete Tool List (117 Tools)

#### Cache Management (8 tools)
- `build_database_cache()` - Build local cache
- `get_cached_statistics()` - Get cache statistics
- `search_cached_databases()` - Search cached databases
- `get_cached_database()` - Get specific database
- `list_cached_compartments()` - List compartments
- `get_databases_by_compartment()` - Get databases by compartment
- `get_fleet_summary()` - Get fleet summary
- `refresh_cache_if_needed()` - Refresh cache

#### Database Discovery (3 tools)
- `list_database_insights_by_management_type()` - **[ENHANCED]** List with agent detection
- `get_database_api_compatibility()` - Get API compatibility
- `get_available_oci_profiles()` - List OCI profiles

#### OPSI Resource Statistics (4 tools) **[NEW]**
- `summarize_database_insight_resource_statistics()` - Resource stats
- `summarize_database_insight_resource_usage()` - Usage time-series
- `summarize_database_insight_resource_utilization_insight()` - Advanced analytics
- `summarize_database_insight_tablespace_usage_trend()` - Tablespace trends

#### Database Management Users (6 tools) **[NEW]**
- `list_users()` - List database users
- `get_user()` - Get user details
- `list_roles()` - List database roles
- `list_system_privileges()` - List system privileges
- `list_consumer_group_privileges()` - List resource groups
- `list_proxy_users()` - List proxy users

#### Database Management Tablespaces (3 tools) **[NEW]**
- `list_tablespaces()` - List tablespaces
- `get_tablespace()` - Get tablespace details
- `list_table_statistics()` - List optimizer statistics

#### Database Management AWR Metrics (5 tools) **[NEW]**
- `summarize_awr_db_metrics()` - AWR metrics
- `summarize_awr_db_cpu_usages()` - CPU usage trends
- `summarize_awr_db_wait_event_buckets()` - Wait event analysis
- `summarize_awr_db_sysstats()` - System statistics
- `summarize_awr_db_parameter_changes()` - Parameter changes

...and 86 more tools across 13 additional categories.

**Full catalog**: See [TOOL_CATALOG.md](./docs/TOOL_CATALOG.md) or run:
```bash
python3 catalog_tools.py
```

---

## Testing

### Run Test Suites

```bash
# Agent detection and profile management tests
python3 test_agent_detection.py

# New API implementations tests
python3 test_new_apis.py

# All tests
python3 -m pytest tests/
```

### Test Coverage

- ✅ **Agent Detection**: 100% passing
- ✅ **Profile Management**: 100% passing
- ✅ **OPSI Resource Stats**: 100% passing
- ✅ **User Management**: 100% passing
- ✅ **Tablespace Management**: 100% passing
- ✅ **AWR Metrics**: 100% passing

---

## Documentation

### Main Documentation

- **[API Coverage Report](./docs/API_COVERAGE_REPORT.md)** - Complete API coverage analysis
- **[Agent Detection Guide](./docs/AGENT_DETECTION_ENHANCEMENTS.md)** - Agent detection features
- **[Implementation Details](./docs/IMPLEMENTATION_COMPLETE.md)** - Technical implementation
- **[Quick Start Guide](./docs/QUICK_START.md)** - Quick reference
- **[Testing Guide](./TESTING_GUIDE.md)** - Testing instructions

### GitHub Wiki

Visit our [GitHub Wiki](https://github.com/your-org/mcp-oci-opsi/wiki) for comprehensive documentation:

- [Home](https://github.com/your-org/mcp-oci-opsi/wiki)
- [Installation Guide](https://github.com/your-org/mcp-oci-opsi/wiki/Installation)
- [Configuration](https://github.com/your-org/mcp-oci-opsi/wiki/Configuration)
- [Tool Reference](https://github.com/your-org/mcp-oci-opsi/wiki/Tool-Reference)
- [API Coverage](https://github.com/your-org/mcp-oci-opsi/wiki/API-Coverage)
- [Multi-Tenancy](https://github.com/your-org/mcp-oci-opsi/wiki/Multi-Tenancy)
- [Agent Detection](https://github.com/your-org/mcp-oci-opsi/wiki/Agent-Detection)
- [Troubleshooting](https://github.com/your-org/mcp-oci-opsi/wiki/Troubleshooting)

---

## Performance

### Benchmarks

| Operation | First Call | Cached Call | Speedup |
|-----------|-----------|-------------|---------|
| List Databases | 2000ms | 45ms | 44x |
| Get Database | 150ms | 30ms | 5x |
| Profile Config | 15ms | 0.2ms | 75x |
| Create Client | 50ms | 0.5ms | 100x |

### Caching Strategy

- **Database Inventory**: Cached locally, refresh every 24 hours
- **Profile Configs**: LRU cache (32 items)
- **OCI Clients**: LRU cache (16 items per profile)
- **SQL Statistics**: Direct API calls (no caching)

---

## Contributing

We welcome contributions! Please see [CONTRIBUTING.md](./CONTRIBUTING.md) for guidelines.

### Development Setup

```bash
# Fork and clone
git clone https://github.com/your-username/mcp-oci-opsi.git
cd mcp-oci-opsi

# Create feature branch
git checkout -b feature/your-feature

# Install development dependencies
pip install -e ".[dev]"

# Run tests
python3 -m pytest tests/

# Submit PR
```

### Areas for Contribution

- 🔧 Additional OCI API coverage
- 📊 Enhanced analytics and visualizations
- 🧪 More comprehensive tests
- 📖 Documentation improvements
- 🐛 Bug fixes

---

## Troubleshooting

### Common Issues

#### "Profile not found"
```bash
# List available profiles
cat ~/.oci/config | grep '\[' | tr -d '[]'

# Validate profile
oci iam region list --profile YOUR_PROFILE
```

#### "Permission denied"
```bash
# Check IAM policies
python3 diagnose_permissions.py
```

#### "Cache build fails"
```bash
# Verify compartment ID
echo $CACHE_COMPARTMENT_IDS

# Test with default profile
python3 build_cache.py
```

See [Troubleshooting Guide](https://github.com/your-org/mcp-oci-opsi/wiki/Troubleshooting) for more help.

---

## License

MIT License - See [LICENSE](./LICENSE) for details.

---

## Acknowledgments

Built with:
- [Model Context Protocol (MCP)](https://modelcontextprotocol.io/)
- [OCI Python SDK](https://oracle-cloud-infrastructure-python-sdk.readthedocs.io/)
- [FastMCP](https://github.com/jlowin/fastmcp)

Special thanks to the OCI and MCP communities.

---

## Support

- 📖 **Documentation**: [GitHub Wiki](https://github.com/your-org/mcp-oci-opsi/wiki)
- 🐛 **Issues**: [GitHub Issues](https://github.com/your-org/mcp-oci-opsi/issues)
- 💬 **Discussions**: [GitHub Discussions](https://github.com/your-org/mcp-oci-opsi/discussions)
- 📧 **Email**: support@your-org.com

---

## Changelog

### v2.0.0 (2025-11-18)
- ✨ Added 18 new APIs across 4 modules
- ✨ Agent detection and prioritization
- ✨ Multi-tenancy support
- ✨ Enhanced resource statistics
- ✨ User and tablespace management
- ✨ AWR metrics analysis
- 📊 Tool count: 99 → 117
- 📈 API coverage: 48% → 52%
- 🧪 100% test coverage

### v1.0.0 (2025-10-01)
- 🎉 Initial release
- 99 tools across 15 categories
- OCI Operations Insights integration
- Database Management integration
- Basic caching system

---

**MCP OCI OPSI Server v2.0** - Empowering database management through natural language
