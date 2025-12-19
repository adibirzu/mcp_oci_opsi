# MCP OCI OPSI Server Architecture

## Overview

This is a **standalone, public MCP server** for Oracle Cloud Infrastructure Operations Insights (OPSI). It is designed to be used independently or integrated with the DB OPS Agent.

## Authentication Architecture

### MCP Server Authentication (Public)

The MCP OCI OPSI server uses **standard OCI SDK authentication** via:
- `~/.oci/config` file with API key authentication
- OCI profiles (DEFAULT, or custom via `OCI_CLI_PROFILE` environment variable)
- Standard OCI SDK credential methods

**The MCP server does NOT use:**
- ❌ OCA (Oracle Code Assist) authentication
- ❌ IDCS OAuth flows
- ❌ The `auth_bridge` module

### Auth Bridge Module (Internal - Not Used by MCP Server)

The `auth_bridge/` directory contains OCA-specific authentication code that is:
- **NOT imported by the MCP server** (`main.py` does not use it)
- Present in the codebase for potential use by the parent DB OPS Agent
- Contains internal Oracle-specific OAuth flows and IDCS integration

## Directory Structure

```
mcp_oci_opsi/
├── main.py                 # MCP server entry point (uses OCI SDK auth only)
├── __main__.py            # Module entry point
├── config.py              # OCI config reader (~/.oci/config)
├── oci_clients.py         # OCI SDK client factories
├── tools_*.py             # MCP tool implementations
│
├── auth_bridge/           # ⚠️ NOT USED BY MCP SERVER
│   ├── constants.py       # OCA-specific constants (IGNORED)
│   ├── oca_auth.py        # OCA OAuth flows (IGNORED)
│   └── token_manager.py   # OCA token management (IGNORED)
│
└── scripts/               # Utility scripts
```

## How to Use the MCP Server

### 1. Prerequisites
```bash
# Install the MCP server
pip install -e ".[dev,database]"

# Configure OCI credentials
vi ~/.oci/config
```

### 2. OCI Configuration Example
```ini
[DEFAULT]
user=[Link to Secure Variable: OCI_USER_OCID]
fingerprint=aa:bb:cc:...
tenancy=[Link to Secure Variable: OCI_TENANCY_OCID]
region=us-ashburn-1
key_file=~/.oci/oci_api_key.pem
```

### 3. Run the Server
```bash
# Use default profile
python -m mcp_oci_opsi

# Use specific profile
OCI_CLI_PROFILE=myprofile python -m mcp_oci_opsi
```

### 4. Integration with Cline
Configure in Cline MCP settings:
```json
{
  "mcpServers": {
    "oci-opsi": {
      "type": "stdio",
      "command": "/path/to/.venv/bin/python",
      "args": ["-m", "mcp_oci_opsi"],
      "cwd": "/path/to/oracle-db-autonomous-agent",
      "env": {
        "OCI_CONFIG_FILE": "/Users/username/.oci/config",
        "OCI_PROFILE": "DEFAULT"
      }
    }
  }
}
```

## Available MCP Tools

The server exposes tools for:
- **Operations Insights (OPSI)**: Database performance metrics, SQL insights
- **Database Management**: SQL Watch, AWR reports, tablespaces
- **Database Discovery**: Fleet discovery, caching
- **Profile Management**: Multi-tenancy support
- **Skills**: DBA guidance and best practices

All tools use standard OCI SDK authentication - no OCA authentication required.

## Security & Public Distribution

✅ **Safe for public distribution:**
- Uses standard OCI API key authentication
- No hardcoded credentials or internal URLs
- No OCA-specific code in execution path
- Environment-based configuration

❌ **Do NOT include:**
- Your `.env.local` file (contains IDCS URLs if OCA is configured elsewhere)
- Your `~/.oci/config` file
- Cache files with tenant-specific data

## Environment Variables

### Required (MCP Server)
- `OCI_CONFIG_FILE` - Path to OCI config (default: `~/.oci/config`)
- `OCI_CLI_PROFILE` - OCI profile name (default: `DEFAULT`)

### Not Used (OCA-related - for parent agent only)
- `OCA_LITELLM_URL` - Ignored by MCP server
- `OCA_IDCS_BASE_URL` - Ignored by MCP server
- `OCA_CLIENT_ID` - Ignored by MCP server
- `OCA_CLIENT_SECRET` - Ignored by MCP server

## Development vs Integration

### Standalone Development
- Run directly: `python -m mcp_oci_opsi`
- Standard OCI authentication
- No OCA dependencies

### Integration with DB OPS Agent
- Agent may use `auth_bridge` for its own OCA authentication
- MCP server still uses OCI SDK authentication independently
- Two separate authentication paths: Agent (OCA) + MCP (OCI)

## Troubleshooting

### "Module not found: mcp_oci_opsi"
```bash
pip install -e ".[dev,database]"
```

### "Invalid OCI credentials"
```bash
# Check your OCI config
cat ~/.oci/config

# Test OCI authentication
oci iam region list --profile DEFAULT
```

### "No such profile"
```bash
# List available profiles
grep '^\[' ~/.oci/config

# Set correct profile
export OCI_CLI_PROFILE=your_profile_name
```

## License & Distribution

This MCP server is designed for public distribution and community use. It contains no proprietary Oracle internal code or credentials when properly configured.
