"""MCP server entrypoint for running as a module.

This allows the server to be run as:
    python -m mcp_oci_opsi
    python3 -m mcp_oci_opsi

Version Selection:
    Set MCP_VERSION environment variable to choose version:
    - MCP_VERSION=v2: Original server (main.py)
    - MCP_VERSION=v3: Enhanced FastMCP 2.0 server (main_v3.py) [default]

Compatible with all LLM clients:
- Claude Desktop
- Claude Code (Cline)
- ChatGPT
- Gemini
- Any MCP-compatible client
"""

import os

# Allow version selection via environment variable
# Default to v2 (FastMCP server) so the MCP server starts correctly when launched by clients.
version = os.getenv("MCP_VERSION", "v2").lower()

if version == "v2":
    from .main import main
else:
    from .main_v3 import main

if __name__ == "__main__":
    main()
