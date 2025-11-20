#!/usr/bin/env python3
"""
Cleanup Script for Non-Working OCI OPSI APIs

This script removes or deprecates the 14 APIs that return 404 errors according to
the API validation results.

Actions:
1. Creates backups of all modified files
2. Deprecates non-working v2.0 resource statistics module
3. Adds deprecation warnings to non-working functions
4. Updates documentation
5. Generates a cleanup report

Based on: API_VALIDATION_SUMMARY.md
Date: November 19, 2025
"""

import os
import shutil
from datetime import datetime
from pathlib import Path

# Define the APIs to deprecate
NON_WORKING_APIS = {
    "tools_opsi_resource_stats.py": {
        "module": "v2.0 Database Resource Statistics",
        "action": "DEPRECATE_ENTIRE_MODULE",
        "reason": "All 4 APIs return 404 - Not available in OCI service",
        "functions": [
            "summarize_database_insight_resource_statistics",
            "summarize_database_insight_resource_usage",
            "summarize_database_insight_resource_utilization_insight",
            "summarize_database_insight_tablespace_usage_trend",
        ],
        "alternatives": [
            "summarize_database_insight_resource_capacity_trend",
            "summarize_database_insight_resource_forecast",
        ]
    },
    "tools_opsi_extended.py": {
        "module": "Host Insights Extended",
        "action": "DEPRECATE_FUNCTIONS",
        "reason": "7 APIs return 404 - May require specific agent versions",
        "functions": [
            "summarize_host_insight_disk_statistics",
            "summarize_host_insight_io_usage_trend",
            "summarize_host_insight_network_usage_trend",
            "summarize_host_insight_storage_usage_trend",
            "summarize_host_insight_top_processes_usage",
            "summarize_host_insight_top_processes_usage_trend",
            "summarize_host_insight_host_recommendation",
        ],
        "alternatives": [
            "summarize_host_insight_resource_usage_trend",
        ]
    },
    "tools_opsi_sql_insights.py": {
        "module": "SQL Insights",
        "action": "DEPRECATE_FUNCTIONS",
        "reason": "2 APIs return 404 - Not available",
        "functions": [
            "summarize_sql_insights",
            "summarize_addm_db_findings",
        ],
        "alternatives": []
    },
    "tools_dbmanagement.py": {
        "module": "Database Management",
        "action": "DEPRECATE_FUNCTIONS",
        "reason": "1 API returns 404 - Not available",
        "functions": [
            "get_database_fleet_health_metrics",
        ],
        "alternatives": [
            "list_managed_databases",
        ]
    }
}


def create_backup(file_path: Path) -> Path:
    """Create a timestamped backup of a file."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_dir = Path("backups") / timestamp
    backup_dir.mkdir(parents=True, exist_ok=True)

    backup_path = backup_dir / file_path.name
    shutil.copy2(file_path, backup_path)

    return backup_path


def add_deprecation_warning(file_path: Path, function_name: str, reason: str, alternatives: list) -> None:
    """Add a deprecation warning to a function."""
    with open(file_path, 'r') as f:
        content = f.read()

    # Find the function definition
    func_pattern = f"def {function_name}("
    if func_pattern not in content:
        print(f"   ⚠️  Function {function_name} not found in {file_path.name}")
        return

    # Add deprecation warning at the start of the docstring
    deprecation_note = f'''
    **DEPRECATED**: This API returns 404 errors and is not available in OCI.

    **Reason**: {reason}

    **Status**: Not deployed to OCI service (as of Nov 2025)
    '''

    if alternatives:
        deprecation_note += f"\n    **Alternatives**: {', '.join(alternatives)}\n    "

    # Find and update the docstring
    lines = content.split('\n')
    new_lines = []
    in_target_function = False
    docstring_start_found = False

    for i, line in enumerate(lines):
        if func_pattern in line:
            in_target_function = True
            new_lines.append(line)
        elif in_target_function and '"""' in line and not docstring_start_found:
            # First docstring quote
            docstring_start_found = True
            new_lines.append(line)
            # Add deprecation warning right after opening """
            for dep_line in deprecation_note.split('\n'):
                new_lines.append(dep_line)
        elif in_target_function and '"""' in line and docstring_start_found:
            # Closing docstring quote
            in_target_function = False
            docstring_start_found = False
            new_lines.append(line)
        else:
            new_lines.append(line)

    # Write back
    with open(file_path, 'w') as f:
        f.write('\n'.join(new_lines))


def deprecate_module(file_path: Path, module_name: str, reason: str) -> None:
    """Add a module-level deprecation notice."""
    with open(file_path, 'r') as f:
        lines = f.readlines()

    # Create deprecation notice
    deprecation_notice = f'''
# ============================================================================
# DEPRECATION NOTICE
# ============================================================================
#
# MODULE DEPRECATED: {module_name}
#
# All APIs in this module return 404 errors and are not available in OCI.
#
# Reason: {reason}
#
# Status: APIs exist in SDK but not deployed to OCI service (as of Nov 2025)
#
# Validation: Tested across multiple regions and database types
# - Phoenix (us-phoenix-1): 404
# - London (uk-london-1): 404
# - Autonomous Databases: 404
# - MACS-Managed Databases: 404
# - Agent-Based Databases: 404
#
# Recommendation: Do not use these APIs until Oracle confirms deployment.
#
# See: API_VALIDATION_SUMMARY.md for details and alternatives
# ============================================================================

'''

    # Find where to insert (after imports, before first function)
    insert_index = 0
    for i, line in enumerate(lines):
        if line.strip() and not line.strip().startswith('#') and not line.strip().startswith('"""') and not line.startswith('from') and not line.startswith('import'):
            insert_index = i
            break

    # Insert the notice
    lines.insert(insert_index, deprecation_notice)

    # Write back
    with open(file_path, 'w') as f:
        f.writelines(lines)


def main():
    """Main cleanup execution."""
    print("=" * 80)
    print("MCP OCI OPSI - Non-Working API Cleanup Script")
    print("=" * 80)
    print()

    base_path = Path("mcp_oci_opsi")
    backup_files = []
    deprecated_count = 0

    # Process each file
    for filename, info in NON_WORKING_APIS.items():
        file_path = base_path / filename

        if not file_path.exists():
            print(f"⚠️  File not found: {filename}")
            continue

        print(f"\n📄 Processing: {filename}")
        print(f"   Module: {info['module']}")
        print(f"   Action: {info['action']}")
        print(f"   Reason: {info['reason']}")

        # Create backup
        backup_path = create_backup(file_path)
        backup_files.append(backup_path)
        print(f"   ✅ Backup created: {backup_path}")

        # Deprecate entire module or specific functions
        if info['action'] == "DEPRECATE_ENTIRE_MODULE":
            deprecate_module(file_path, info['module'], info['reason'])
            print(f"   ✅ Added module deprecation notice")
            deprecated_count += len(info['functions'])

        # Add deprecation warnings to individual functions
        for func in info['functions']:
            add_deprecation_warning(
                file_path,
                func,
                info['reason'],
                info.get('alternatives', [])
            )
            deprecated_count += 1

        print(f"   ✅ Deprecated {len(info['functions'])} function(s)")

    # Generate cleanup report
    print("\n" + "=" * 80)
    print("CLEANUP SUMMARY")
    print("=" * 80)
    print(f"\n✅ Files processed: {len(NON_WORKING_APIS)}")
    print(f"✅ Functions deprecated: {deprecated_count}")
    print(f"✅ Backups created: {len(backup_files)}")

    print("\n📂 Backup locations:")
    for backup in backup_files:
        print(f"   {backup}")

    print("\n📊 Deprecated APIs by module:")
    for filename, info in NON_WORKING_APIS.items():
        print(f"\n   {info['module']} ({filename}):")
        for func in info['functions']:
            print(f"      ❌ {func}")
        if info.get('alternatives'):
            print(f"      ✅ Alternatives: {', '.join(info['alternatives'])}")

    print("\n" + "=" * 80)
    print("Next Steps:")
    print("=" * 80)
    print("""
1. Review the deprecated functions in each file
2. Test that non-deprecated APIs still work
3. Update README.md with deprecation notices
4. Update MCP tool descriptions if needed
5. Consider removing from exports if not auto-discovered

Files modified:
""")
    for filename in NON_WORKING_APIS.keys():
        print(f"   - mcp_oci_opsi/{filename}")

    print("\nTo restore from backup:")
    print("   cp backups/<timestamp>/<filename> mcp_oci_opsi/<filename>")

    print("\n✅ Cleanup complete!")
    print()


if __name__ == "__main__":
    main()
