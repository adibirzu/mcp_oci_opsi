#!/bin/bash
# Start OPSI MCP Server in HTTP mode for standalone use

export MCP_TRANSPORT=http
export MCP_HTTP_PORT=${MCP_HTTP_PORT:-8000}
export MCP_HTTP_HOST=${MCP_HTTP_HOST:-0.0.0.0}

echo "🚀 Starting OPSI MCP Server in HTTP mode"
echo "   Port: $MCP_HTTP_PORT"
echo "   Host: $MCP_HTTP_HOST"
echo ""
echo "Connect any LLM client to: http://localhost:$MCP_HTTP_PORT"
echo "Press Ctrl+C to stop"
echo ""

cd "$(dirname "$0")"
python -m mcp_oci_opsi
