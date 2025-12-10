# OPSI MCP Server - Standalone Usage Guide

The OPSI MCP Server can work as a **standalone server** that any MCP-compatible LLM client can connect to.

## Quick Start

### Option 1: Stdio Mode (Default - for MCP config)

```bash
# Use in mcp-config.json
{
  "oci-opsi": {
    "command": "python",
    "args": ["-m", "mcp_oci_opsi"],
    "env": {
      "OCI_CONFIG_FILE": "/path/to/.oci/config",
      "OCI_PROFILE": "DEFAULT"
    }
  }
}
```

### Option 2: HTTP Mode (Standalone - any LLM)

```bash
# Start HTTP server on port 8000
./start_http.sh

# Or with custom port
MCP_HTTP_PORT=9000 ./start_http.sh
```

Then connect any MCP client to: `http://localhost:8000`

## Connecting Different LLMs

### Claude Desktop

Add to `~/Library/Application Support/Claude/claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "oci-opsi": {
      "command": "python",
      "args": ["-m", "mcp_oci_opsi"],
      "cwd": "/path/to/mcp_oci_opsi"
    }
  }
}
```

### ChatGPT with MCP

```bash
# Start HTTP mode
./start_http.sh

# Connect via MCP Bridge
# URL: http://localhost:8000
```

### Any LLM with HTTP MCP Support

1. Start the server: `./start_http.sh`
2. Configure your LLM client to connect to `http://localhost:8000`
3. Available tools will be automatically discovered

## Docker Deployment

```bash
# Build image
docker build -t mcp-oci-opsi .

# Run container
docker run -p 8000:8000 \
  -v ~/.oci:/root/.oci:ro \
  -e MCP_TRANSPORT=http \
  mcp-oci-opsi
```

## Available Tools

The server exposes 100+ tools for:
- Database discovery and monitoring (OPSI)
- SQL performance analysis
- AWR report generation
- Cache management
- Profile management
- Resource forecasting

## Authentication

The server uses your OCI CLI configuration:

```bash
# Default location
~/.oci/config

# Specify profile
export OCI_PROFILE=my-profile

# Or custom config file
export OCI_CONFIG_FILE=/path/to/config
```

## Testing

```bash
# Test imports
python -c "from mcp_oci_opsi.tools import opsi, cache; print('✅ OK')"

# Test server startup (stdio)
python -m mcp_oci_opsi

# Test HTTP mode
./start_http.sh
```

## Troubleshooting

**Import errors**: Run `./comprehensive_fix.sh` to fix all imports

**Connection issues**: Check OCI config file permissions and profile settings

**Port conflicts**: Change port with `MCP_HTTP_PORT=9000 ./start_http.sh`

## More Information

- Full documentation: See `README.md`
- Cache system: See `CACHE_SYSTEM.md`
- Skills/prompts: See `SKILLS_GUIDE.md`
