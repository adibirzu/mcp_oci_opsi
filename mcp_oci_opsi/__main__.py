"""MCP server entrypoint for running as a module.

This allows the server to be run as:
    python -m mcp_oci_opsi
    python3 -m mcp_oci_opsi

Compatible with all LLM clients:
- Claude Desktop
- Claude Code (Cline)
- ChatGPT
- Gemini
- Any MCP-compatible client
"""

from .main import main

if __name__ == "__main__":
    main()
