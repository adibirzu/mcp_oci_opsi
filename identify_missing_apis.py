#!/usr/bin/env python3
"""Identify missing OCI API calls that should be implemented."""

import oci
from pathlib import Path
import re

def get_implemented_apis():
    """Get all implemented API calls from tool files."""
    implemented = set()
    tools_dir = Path('mcp_oci_opsi')

    for tool_file in tools_dir.glob('tools_*.py'):
        with open(tool_file, 'r') as f:
            content = f.read()
            # Find all client method calls
            patterns = [
                r'client\.(\w+)\(',
                r'opsi_client\.(\w+)\(',
                r'dbm_client\.(\w+)\(',
            ]
            for pattern in patterns:
                matches = re.finditer(pattern, content)
                for match in matches:
                    implemented.add(match.group(1))

    return implemented

def get_opsi_client_methods():
    """Get all available OPSI client methods."""
    try:
        config = oci.config.from_file()
        client = oci.opsi.OperationsInsightsClient(config)

        methods = [m for m in dir(client) if not m.startswith('_') and callable(getattr(client, m))]
        # Filter to just API methods (not helpers)
        api_methods = [m for m in methods if not m in [
            'base_client', 'endpoint', 'service_endpoint', 'timeout',
            'get_endpoint', 'set_endpoint', 'set_region'
        ]]
        return set(api_methods)
    except Exception as e:
        print(f"Warning: Could not load OPSI client: {e}")
        return set()

def get_dbm_client_methods():
    """Get all available Database Management client methods."""
    try:
        config = oci.config.from_file()
        client = oci.database_management.DbManagementClient(config)

        methods = [m for m in dir(client) if not m.startswith('_') and callable(getattr(client, m))]
        api_methods = [m for m in methods if not m in [
            'base_client', 'endpoint', 'service_endpoint', 'timeout',
            'get_endpoint', 'set_endpoint', 'set_region'
        ]]
        return set(api_methods)
    except Exception as e:
        print(f"Warning: Could not load DBM client: {e}")
        return set()

def main():
    """Identify missing APIs."""
    print("=" * 80)
    print("OCI API COVERAGE ANALYSIS")
    print("=" * 80)
    print()

    implemented = get_implemented_apis()
    print(f"Implemented API calls: {len(implemented)}")
    print()

    print("=" * 80)
    print("OPERATIONS INSIGHTS API COVERAGE")
    print("=" * 80)
    print()

    opsi_methods = get_opsi_client_methods()
    print(f"Total OPSI API methods: {len(opsi_methods)}")

    # Check for commonly needed missing APIs
    needed_opsi_apis = [
        'summarize_database_insight_resource_statistics',
        'summarize_database_insight_resource_usage',
        'summarize_database_insight_resource_utilization_insight',
        'summarize_awr_database_sysstat_reports',
        'ingest_sql_stats',
        'ingest_host_metrics',
        'get_news_report',
        'summarize_configuration_items',
        'summarize_database_insight_tablespace_usage_trend',
        'list_warehouse_data_objects',
        'query_opsi_data_object_data',
        'summarize_exadata_insight_resource_statistics',
        'summarize_exadata_insight_resource_usage',
        'summarize_exadata_insight_resource_usage_aggregated',
        'summarize_exadata_members',
        'list_database_configurations',
        'list_host_configurations',
        'list_sql_searches',
        'search_sql_texts',
    ]

    print("\nMissing High-Value OPSI APIs:")
    missing_opsi = []
    for api in needed_opsi_apis:
        if api in opsi_methods and api not in implemented:
            missing_opsi.append(api)
            print(f"  - {api}")

    print()
    print("=" * 80)
    print("DATABASE MANAGEMENT API COVERAGE")
    print("=" * 80)
    print()

    dbm_methods = get_dbm_client_methods()
    print(f"Total DBM API methods: {len(dbm_methods)}")

    needed_dbm_apis = [
        'list_users',
        'get_user',
        'list_roles',
        'list_system_privileges',
        'list_tablespaces',
        'get_tablespace',
        'create_tablespace_managed_database',
        'drop_tablespace_managed_database',
        'get_optimizer_statistics_advisor_execution',
        'implement_optimizer_statistics_advisor_recommendations',
        'summarize_awr_db_metrics',
        'summarize_awr_db_cpu_usages',
        'summarize_awr_db_wait_events',
        'summarize_awr_db_wait_event_buckets',
        'summarize_awr_db_sysstats',
        'summarize_awr_db_top_wait_events',
        'summarize_awr_db_parameter_changes',
        'list_consumer_group_privileges',
        'list_proxy_users',
        'list_data_access_containers',
        'get_pdb_metrics',
        'get_database_storage_usage',
        'list_sql_tuning_sets',
        'get_sql_execution_plan',
        'list_object_privileges',
        'list_table_statistics',
        'change_database_parameters',
        'reset_database_parameters',
    ]

    print("\nMissing High-Value DBM APIs:")
    missing_dbm = []
    for api in needed_dbm_apis:
        if api in dbm_methods and api not in implemented:
            missing_dbm.append(api)
            print(f"  - {api}")

    print()
    print("=" * 80)
    print("SUMMARY")
    print("=" * 80)
    print()
    print(f"Missing OPSI APIs: {len(missing_opsi)}")
    print(f"Missing DBM APIs: {len(missing_dbm)}")
    print(f"Total Missing High-Value APIs: {len(missing_opsi) + len(missing_dbm)}")
    print()

    # Save to file
    with open('missing_apis.txt', 'w') as f:
        f.write("MISSING OPERATIONS INSIGHTS APIs\n")
        f.write("=" * 80 + "\n\n")
        for api in sorted(missing_opsi):
            f.write(f"{api}\n")
        f.write("\n")

        f.write("MISSING DATABASE MANAGEMENT APIs\n")
        f.write("=" * 80 + "\n\n")
        for api in sorted(missing_dbm):
            f.write(f"{api}\n")

    print(f"✅ Full list saved to missing_apis.txt")
    print()

    return missing_opsi, missing_dbm

if __name__ == '__main__':
    main()
