# Troubleshooting Guide

Common issues and solutions for MCP OCI OPSI Server.

---

## Installation Issues

### Python Version Too Old

**Error:**
```
ERROR: Python 3.8 or higher is required
```

**Solution:**
```bash
# Check current version
python3 --version

# Install Python 3.11 (macOS)
brew install python@3.11

# Install Python 3.11 (Ubuntu)
sudo apt update
sudo apt install python3.11 python3.11-venv

# Verify
python3.11 --version
```

### OCI CLI Not Found

**Error:**
```
bash: oci: command not found
```

**Solution:**
```bash
# Install OCI CLI
bash -c "$(curl -L https://raw.githubusercontent.com/oracle/oci-cli/master/scripts/install/install.sh)"

# Add to PATH (if needed)
export PATH=$PATH:~/bin

# Add to shell profile
echo 'export PATH=$PATH:~/bin' >> ~/.bashrc  # or ~/.zshrc

# Verify
oci --version
```

### Module Import Errors

**Error:**
```
ModuleNotFoundError: No module named 'mcp_oci_opsi'
```

**Solution:**
```bash
# Ensure you're in virtual environment
source .venv/bin/activate  # macOS/Linux
# OR
.venv\Scripts\activate  # Windows

# Reinstall in development mode
pip install -e .

# Verify
python3 -c "import mcp_oci_opsi; print('Success!')"
```

---

## OCI Configuration Issues

### Profile Not Found

**Error:**
```
ProfileNotFound: Profile 'production' not found
```

**Solution:**
```bash
# List available profiles
cat ~/.oci/config | grep "^\["

# Output:
[DEFAULT]
[staging]
[development]

# Fix: Use correct profile name
python3 build_cache.py --profile DEFAULT  # Not 'production'
```

### Invalid API Key

**Error:**
```
ServiceError: 401-NotAuthenticated
Invalid API key fingerprint
```

**Solution:**
```bash
# 1. Verify fingerprint
openssl rsa -pubout -outform DER -in ~/.oci/api_key.pem | \
    openssl md5 -c | \
    awk '{print $2}'

# 2. Compare with OCI Console
# Go to: User Settings → API Keys → Check fingerprint

# 3. Update config if mismatch
vi ~/.oci/config
# Update fingerprint= line

# 4. Verify permissions
chmod 600 ~/.oci/api_key.pem
ls -l ~/.oci/api_key.pem
```

### Permission Denied on Key File

**Error:**
```
PermissionError: [Errno 13] Permission denied: '/Users/xxx/.oci/api_key.pem'
```

**Solution:**
```bash
# Fix permissions
chmod 600 ~/.oci/api_key.pem
chmod 600 ~/.oci/config

# Verify
ls -l ~/.oci/
# Should show: -rw------- for .pem files
```

### Config File Not Found

**Error:**
```
ConfigFileNotFound: ~/.oci/config not found
```

**Solution:**
```bash
# Run OCI CLI setup
oci setup config

# Or create manually
mkdir -p ~/.oci
cat > ~/.oci/config <<EOF
[DEFAULT]
user=ocid1.user.oc1..xxx
fingerprint=xx:xx:xx:xx:xx:xx:xx:xx:xx:xx:xx:xx:xx:xx:xx:xx
tenancy=ocid1.tenancy.oc1..xxx
region=us-phoenix-1
key_file=~/.oci/api_key.pem
EOF

chmod 600 ~/.oci/config
```

---

## Permission and Access Issues

### Compartment Access Denied

**Error:**
```
ServiceError: 404-NotAuthorizedOrNotFound
Authorization failed or requested resource not found
```

**Solution:**

1. **Verify compartment OCID:**
```bash
# List compartments
oci iam compartment list --all

# Verify OCID exists
oci iam compartment get --compartment-id ocid1.compartment.oc1..xxx
```

2. **Check IAM policies:**

Required policies for OPSI:
```
Allow group opsi-users to read database-family in compartment Production
Allow group opsi-users to read opsi-namespace in compartment Production
Allow group opsi-users to use operations-insights-family in compartment Production
```

Required policies for Database Management:
```
Allow group dbm-users to read database-management-family in compartment Production
Allow group dbm-users to use database-management in compartment Production
```

3. **Verify user group membership:**
```bash
# List groups for user
oci iam user list-groups --user-id ocid1.user.oc1..xxx
```

### Diagnose Permissions

```python
from mcp_oci_opsi.tools_diagnostics import diagnose_opsi_permissions

# Run diagnostics
result = diagnose_opsi_permissions(
    compartment_id="ocid1.compartment.oc1..xxx"
)

print(result['summary']['status'])
print("\nDetails:")
for check in result['checks']:
    status = "✅" if check['success'] else "❌"
    print(f"{status} {check['name']}: {check['message']}")

# Get recommendations
if result['summary']['issues_found'] > 0:
    print("\nRecommendations:")
    for rec in result['recommendations']:
        print(f"  • {rec}")
```

---

## API and Data Issues

### SQL Statistics Returns 404

**Error:**
```
ServiceError: 404-NotFound
SQL statistics API not supported for this database
```

**Cause:** EM-managed databases don't support SQL statistics API.

**Solution:**

1. **Check database type:**
```python
from mcp_oci_opsi.tools_database_discovery import get_database_api_compatibility

compat = get_database_api_compatibility(
    database_insight_id="ocid1.databaseinsight.oc1..xxx"
)

print(f"Entity source: {compat['entity_source']}")
print(f"SQL stats supported: {compat['api_compatibility']['summarize_sql_statistics']['supported']}")
```

2. **Use warehouse queries instead:**
```python
from mcp_oci_opsi.tools_opsi import query_warehouse_standard

# For EM-managed databases, use warehouse
result = query_warehouse_standard(
    compartment_id="ocid1.compartment.oc1..xxx",
    warehouse_query="SELECT * FROM SQL_STATS WHERE ..."
)
```

3. **Or migrate to MACS:**
- See [Agent Detection](./Agent-Detection) for migration guide

### Cache Empty or Stale

**Error:**
```
CacheError: No databases found in cache
```

**Solution:**
```bash
# Rebuild cache
python3 build_cache.py --select-profile

# Verify cache
cat ~/.mcp_oci_opsi_cache.json | jq '.statistics'

# Check last update time
cat ~/.mcp_oci_opsi_cache.json | jq '.statistics.last_updated'
```

### Database Not Found in Cache

**Error:**
```
Database 'PRODDB' not found in cache
```

**Solution:**
```python
# 1. Search with different criteria
from mcp_oci_opsi.tools_cache import search_cached_databases

# Try partial name match
result = search_cached_databases(database_name="PROD")

# 2. Check if database is in different compartment
result = search_cached_databases()  # Get all
print(f"Total databases: {result['count']}")

# 3. Rebuild cache
import subprocess
subprocess.run(["python3", "build_cache.py", "--select-profile"])
```

---

## Performance Issues

### Slow API Responses

**Issue:** API calls taking > 5 seconds

**Solution:**

1. **Use cache for fast queries:**
```python
# ✅ FAST (cached)
from mcp_oci_opsi.tools_cache import get_cached_database
db = get_cached_database("ocid1.databaseinsight.oc1..xxx")  # <50ms

# ❌ SLOW (API call)
from mcp_oci_opsi.tools_database_discovery import get_database_insight
db = get_database_insight("ocid1.databaseinsight.oc1..xxx")  # 1-2s
```

2. **Batch operations:**
```python
# ✅ GOOD - Single API call
database_ids = ["id1", "id2", "id3"]
stats = summarize_database_insight_resource_statistics(
    compartment_id="xxx",
    database_id=database_ids
)

# ❌ BAD - Multiple API calls
for db_id in database_ids:
    stats = summarize_database_insight_resource_statistics(
        compartment_id="xxx",
        database_id=[db_id]
    )
```

3. **Enable debug logging to identify bottlenecks:**
```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

### High Memory Usage

**Issue:** Process using excessive memory

**Solution:**
```python
# 1. Limit result sets
result = summarize_sql_statistics(
    compartment_id="xxx",
    limit=100  # Don't fetch all results
)

# 2. Use pagination
offset = 0
limit = 100

while True:
    result = list_database_insights(
        compartment_id="xxx",
        limit=limit,
        page=offset
    )
    # Process batch
    if len(result['items']) < limit:
        break
    offset += limit
```

---

## Agent Detection Issues

### Agent Type Not Detected

**Issue:** Database shows "Unknown" agent type

**Solution:**
```python
from mcp_oci_opsi.oci_clients import get_opsi_client

# Manual check
client = get_opsi_client()
response = client.get_database_insight("ocid1.databaseinsight.oc1..xxx")

db_insight = response.data
print(f"Entity source: {db_insight.entity_source}")
print(f"Database type: {db_insight.database_type}")

# Expected values:
# - MACS_MANAGED_EXTERNAL_DATABASE
# - AUTONOMOUS_DATABASE
# - EM_MANAGED_EXTERNAL_DATABASE
# - PE_COMANAGED_DATABASE
```

### Low Agent Adoption Reported

**Issue:** `agent_based_percentage` is unexpectedly low

**Solution:**
```python
from mcp_oci_opsi.tools_database_discovery import list_database_insights_by_management_type

# Get detailed breakdown
result = list_database_insights_by_management_type(
    compartment_id="ocid1.compartment.oc1..xxx"
)

# Check distribution
print("Database Distribution:")
for entity_type, info in result['summary']['by_management_type'].items():
    agent_status = "🤖 Agent" if info['agent_based'] else "📋 Non-agent"
    print(f"{agent_status} - {info['display_name']}: {info['count']}")

# Identify migration candidates
em_databases = result['databases_by_type'].get('EM_MANAGED_EXTERNAL_DATABASE', [])
if em_databases:
    print(f"\n⚠️ {len(em_databases)} databases should migrate to MACS")
```

---

## Multi-Profile Issues

### Wrong Profile Being Used

**Issue:** Operations executing on wrong tenancy

**Solution:**
```python
# Check current profile
from mcp_oci_opsi.tools_profile_management import get_current_profile_info

current = get_current_profile_info()
print(f"Active profile: {current['profile']}")
print(f"Tenancy: {current['tenancy_name']}")

# Verify before proceeding
if current['tenancy_name'] != 'ExpectedTenancy':
    print("⚠️ WARNING: Using wrong tenancy!")

# Explicitly specify profile
result = list_database_insights(
    compartment_id="xxx",
    profile="production"  # Force specific profile
)
```

### Profile Validation Fails

**Issue:** Profile marked as invalid

**Solution:**
```python
from mcp_oci_opsi.tools_profile_management import get_oci_profile_details

# Get detailed error
details = get_oci_profile_details("production")

if not details['valid']:
    print(f"❌ Profile invalid")
    print(f"Error: {details.get('error', 'Unknown')}")
    print("\nChecklist:")
    print("  1. API key file exists:", details['config'].get('key_file'))
    print("  2. Fingerprint correct:", details['config'].get('fingerprint'))
    print("  3. User OCID valid:", details['config'].get('user'))
    print("  4. Tenancy OCID valid:", details['config'].get('tenancy'))
```

---

## Testing and Validation Issues

### Tests Failing

**Error:**
```
pytest: command not found
```

**Solution:**
```bash
# Install test dependencies
pip install pytest

# Run tests
python3 test_agent_detection.py
python3 test_new_apis.py
```

### Import Errors in Tests

**Error:**
```
ImportError: cannot import name 'list_database_insights_by_management_type'
```

**Solution:**
```bash
# Ensure package is installed in development mode
pip install -e .

# Verify imports
python3 -c "from mcp_oci_opsi.tools_database_discovery import list_database_insights_by_management_type; print('OK')"
```

---

## Common Error Messages

### "Invalid value for `lifecycle_state`"

**Error:**
```
ValueError: Invalid value for `lifecycle_state` ('ACTIVE'), must be None
```

**Solution:**
```python
# Don't pass lifecycle_state parameter
# Or pass None
result = list_database_insights_by_management_type(
    compartment_id="xxx",
    lifecycle_state=None  # Or omit entirely
)
```

### "Tenancy OCID mismatch"

**Error:**
```
TenancyMismatchError: Resource belongs to different tenancy
```

**Solution:**
```bash
# Verify you're using correct profile
echo $OCI_CLI_PROFILE

# Check compartment tenancy
oci iam compartment get --compartment-id ocid1.compartment.oc1..xxx | jq -r '.data."compartment-id"'

# Use correct profile
export OCI_CLI_PROFILE="correct-profile"
```

---

## Debug Mode

### Enable Verbose Logging

```python
import logging

# Enable debug logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# Run operations - will show detailed logs
from mcp_oci_opsi.tools_database_discovery import list_database_insights

result = list_database_insights(compartment_id="xxx")
```

### OCI SDK Debug Mode

```python
import oci

# Enable OCI SDK logging
oci.base_client.is_http_log_enabled(True)

# Now all HTTP requests/responses are logged
```

### Capture Request/Response

```python
import logging
import http.client

# Enable HTTP debug
http.client.HTTPConnection.debuglevel = 1

# Configure logging
logging.basicConfig()
logging.getLogger().setLevel(logging.DEBUG)
requests_log = logging.getLogger("requests.packages.urllib3")
requests_log.setLevel(logging.DEBUG)
requests_log.propagate = True
```

---

## Getting Help

### Diagnostic Report

Run comprehensive diagnostics:

```python
from mcp_oci_opsi.tools_diagnostics import get_comprehensive_diagnostics

# Generate full diagnostic report
report = get_comprehensive_diagnostics(
    compartment_id="ocid1.compartment.oc1..xxx"
)

print("=" * 80)
print("COMPREHENSIVE DIAGNOSTICS REPORT")
print("=" * 80)

print(f"\nOPSI Permissions: {report['opsi_permissions']['summary']['status']}")
print(f"SQLWatch Status: {report['sqlwatch_status']['summary']['enabled_count']} enabled")
print(f"Database Insights: {report['insights_config']['summary']['total_databases']}")

print("\nIssues Found:")
for category, data in report.items():
    if 'issues_found' in data.get('summary', {}):
        issues = data['summary']['issues_found']
        if issues > 0:
            print(f"  • {category}: {issues} issues")

print("\nRecommendations:")
for category, data in report.items():
    if 'recommendations' in data:
        for rec in data['recommendations']:
            print(f"  • {rec}")
```

### Where to Get Support

1. **Documentation**
   - [Installation](./Installation)
   - [Configuration](./Configuration)
   - [Quick Start](./Quick-Start)
   - [Agent Detection](./Agent-Detection)

2. **GitHub**
   - Issues: Report bugs and request features
   - Discussions: Ask questions and share knowledge

3. **OCI Support**
   - For OCI-specific issues (permissions, services, etc.)
   - Open support ticket in OCI Console

---

## FAQ Quick Answers

**Q: Why is my cache empty?**
A: Run `python3 build_cache.py --select-profile`

**Q: SQL statistics returns 404?**
A: EM-managed databases don't support it. Use warehouse queries or migrate to MACS.

**Q: How do I switch profiles?**
A: Pass `profile="name"` parameter or set `OCI_CLI_PROFILE` environment variable

**Q: Agent detection not working?**
A: Verify with `get_database_api_compatibility(database_insight_id="xxx")`

**Q: Cache is stale?**
A: Rebuild with `python3 build_cache.py` or wait 24 hours for auto-refresh

---

## Related Pages

- [Configuration](./Configuration) - Configuration guide
- [Installation](./Installation) - Installation guide
- [Quick Start](./Quick-Start) - Getting started
- [Agent Detection](./Agent-Detection) - Agent features
- [Multi-Tenancy](./Multi-Tenancy) - Multi-profile support

---

**Last Updated**: 2025-11-18
**Version**: 2.0.0
**Coverage**: Common Issues
