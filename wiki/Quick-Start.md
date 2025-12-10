# Quick Start Guide

## Prereqs
- Python 3.10+
- OCI CLI profile configured

## Install
```bash
git clone https://github.com/your-org/mcp-oci-opsi.git
cd mcp-oci-opsi
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev,database]"
```

## Build cache (recommended)
```bash
./scripts/setup_and_build.sh --profile DEFAULT
```

## Run (stdio)
```bash
python -m mcp_oci_opsi
```

### MCP config (stdio)
```json
{
  "mcpServers": {
    "oci-opsi": {
      "command": "/path/to/.venv/bin/python",
      "args": ["-m", "mcp_oci_opsi"],
      "env": {
        "MCP_VERSION": "v3",
        "OCI_CLI_PROFILE": "DEFAULT"
      }
    }
  }
}
```

## Run (HTTP)
```bash
export MCP_TRANSPORT=http
export MCP_HTTP_PORT=8000
python -m mcp_oci_opsi
```

### MCP config (HTTP)
```json
{
  "mcpServers": {
    "oci-opsi": {
      "url": "http://127.0.0.1:8000"
    }
  }
}
```

## First queries
- "Show fleet summary" (cache)
- "Find database PROD" (cache)
- "Analyze SQL performance for database X" (OPSI)
- "Generate AWR report for database Y" (DBM)
