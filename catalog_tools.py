#!/usr/bin/env python3
"""Catalog all MCP tools and their functions."""

import os
import re
from pathlib import Path

def extract_functions(file_path):
    """Extract public function names from a Python file."""
    functions = []
    with open(file_path, 'r') as f:
        content = f.read()
        # Find all function definitions
        pattern = r'^def ([a-zA-Z_][a-zA-Z0-9_]*)\('
        matches = re.finditer(pattern, content, re.MULTILINE)
        for match in matches:
            func_name = match.group(1)
            # Skip private functions
            if not func_name.startswith('_'):
                functions.append(func_name)
    return functions

def main():
    """Catalog all tools."""
    tools_dir = Path('mcp_oci_opsi')
    tool_files = sorted(tools_dir.glob('tools_*.py'))

    print("=" * 80)
    print("MCP OCI OPSI - COMPLETE TOOL CATALOG")
    print("=" * 80)
    print()

    total_tools = 0
    by_category = {}

    for tool_file in tool_files:
        category = tool_file.stem.replace('tools_', '')
        functions = extract_functions(tool_file)

        if functions:
            by_category[category] = functions
            total_tools += len(functions)

            print(f"### {category.upper().replace('_', ' ')} ({len(functions)} tools)")
            print(f"File: {tool_file.name}")
            print()
            for func in functions:
                print(f"  - {func}()")
            print()

    print("=" * 80)
    print(f"SUMMARY: {total_tools} tools across {len(by_category)} categories")
    print("=" * 80)
    print()

    # Group by functionality
    print("BY FUNCTIONALITY:")
    print()
    print(f"Database Management: {len(by_category.get('dbmanagement', [])) + len(by_category.get('dbmanagement_monitoring', [])) + len(by_category.get('dbmanagement_sql_plans', []))}")
    print(f"Operations Insights: {len(by_category.get('opsi', [])) + len(by_category.get('opsi_extended', [])) + len(by_category.get('opsi_sql_insights', [])) + len(by_category.get('opsi_diagnostics', []))}")
    print(f"SQL Watch: {len(by_category.get('sqlwatch', [])) + len(by_category.get('sqlwatch_bulk', []))}")
    print(f"Discovery & Registration: {len(by_category.get('database_discovery', [])) + len(by_category.get('database_registration', []))}")
    print(f"Cache: {len(by_category.get('cache', []))}")
    print(f"Profile Management: {len(by_category.get('profile_management', []))}")
    print(f"Visualization: {len(by_category.get('visualization', []))}")
    print(f"Oracle Database: {len(by_category.get('oracle_database', []))}")

if __name__ == '__main__':
    main()
