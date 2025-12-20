# Configuration Guide

Complete configuration guide for MCP OCI OPSI Server.

---

## OCI CLI Configuration

### Single Profile Setup

The simplest configuration uses a single DEFAULT profile.

#### Create Config File

```bash
# Run interactive setup
oci setup config

# Follow prompts:
# - Config location: ~/.oci/config (default)
# - User OCID: [Link to Secure Variable: OCI_USER_OCID]
# - Tenancy OCID: [Link to Secure Variable: OCI_TENANCY_OCID]
# - Region: us-phoenix-1
# - Generate API key: Y
```

#### Verify Configuration

```bash
# Test connectivity
oci iam region list

# Should return list of OCI regions
```

---

## Multi-Profile Configuration

MCP OCI OPSI Server supports multiple OCI profiles for multi-tenancy scenarios.

### Profile Structure

Edit `~/.oci/config`:

```ini
[DEFAULT]
user=[Link to Secure Variable: OCI_USER_OCID]
fingerprint=aa:bb:cc:dd:ee:ff:11:22:33:44:55:66:77:88:99:00
tenancy=[Link to Secure Variable: OCI_TENANCY_OCID]
region=us-phoenix-1
key_file=~/.oci/default_api_key.pem

[production]
user=[Link to Secure Variable: OCI_USER_OCID]
fingerprint=11:22:33:44:55:66:77:88:99:00:aa:bb:cc:dd:ee:ff
tenancy=[Link to Secure Variable: OCI_TENANCY_OCID]
region=us-ashburn-1
key_file=~/.oci/production_api_key.pem

[development]
user=[Link to Secure Variable: OCI_USER_OCID]
fingerprint=ff:ee:dd:cc:bb:aa:99:88:77:66:55:44:33:22:11:00
tenancy=[Link to Secure Variable: OCI_TENANCY_OCID]
region=eu-frankfurt-1
key_file=~/.oci/dev_api_key.pem
```

### Profile Validation

```bash
# Validate all profiles
python3 -c "
from mcp_oci_opsi.tools_profile_management import list_oci_profiles_enhanced
result = list_oci_profiles_enhanced()
for profile in result['profiles']:
    status = '✅' if profile['valid'] else '❌'
    print(f'{status} {profile[\"name\"]}: {profile[\"region\"]}')
"
```

---

## Environment Variables

### Required Variables

#### CACHE_COMPARTMENT_IDS

Specifies which compartments to scan when building cache.

```bash
# Single compartment
export CACHE_COMPARTMENT_IDS="[Link to Secure Variable: OCI_COMPARTMENT_OCID]"

# Multiple compartments (comma-separated)
export CACHE_COMPARTMENT_IDS="[Link to Secure Variable: OCI_COMPARTMENT_OCID],[Link to Secure Variable: OCI_COMPARTMENT_OCID],[Link to Secure Variable: OCI_COMPARTMENT_OCID]"
```

**How to find compartment OCIDs:**

```bash
# List all compartments
oci iam compartment list --all

# Or in OCI Console:
# Identity & Security → Compartments → Click compartment → Copy OCID
```

### Optional Variables

#### OCI_CLI_PROFILE

Override the default profile for a session.

```bash
# Use production profile for all operations
export OCI_CLI_PROFILE="production"

# Verify
echo $OCI_CLI_PROFILE
```

#### OCI_COMPARTMENT_ID

Set a default compartment for operations.

```bash
export OCI_COMPARTMENT_ID="[Link to Secure Variable: OCI_COMPARTMENT_OCID]"
```

---

## Cache Configuration

### Building Cache

#### Interactive Profile Selection

```bash
# Select profile interactively
python3 build_cache.py --select-profile
```

Output:
```
📋 Available OCI Profiles:

  1. ✅ DEFAULT
     Region: us-phoenix-1
     Tenancy: [Link to Secure Variable: OCI_TENANCY_OCID]

  2. ✅ production
     Region: us-ashburn-1
     Tenancy: [Link to Secure Variable: OCI_TENANCY_OCID]

Select profile (1-2):
```

#### Specify Profile Directly

```bash
# Build cache for specific profile
python3 build_cache.py --profile production
```

#### Use Environment Variable

```bash
# Set profile in environment
export OCI_CLI_PROFILE="production"

# Build cache (uses environment profile)
python3 build_cache.py
```

### Cache Location

Default: `~/.mcp-oci/cache/opsi_cache.json`

```bash
# View cache file
cat ~/.mcp-oci/cache/opsi_cache.json | jq '.statistics'

# Output:
{
  "last_updated": "2025-11-18T10:30:00Z",
  "total_databases": 12,
  "total_hosts": 8,
  "profile": "DEFAULT",
  "tenancy_name": "MyCompany",
  "region": "us-phoenix-1"
}
```

### Cache Refresh

Cache is automatically refreshed every 24 hours. Manual refresh:

```bash
# Rebuild cache
python3 build_cache.py --profile production

# Or using tools
python3 -c "
from mcp_oci_opsi.tools_profile_management import refresh_profile_cache
refresh_profile_cache('production')
"
```

---

## API Key Management

### Generate New API Key

```bash
# Generate key pair
openssl genrsa -out ~/.oci/new_api_key.pem 2048

# Generate public key
openssl rsa -pubout -in ~/.oci/new_api_key.pem -out ~/.oci/new_api_key_public.pem

# Fix permissions
chmod 600 ~/.oci/new_api_key.pem
chmod 644 ~/.oci/new_api_key_public.pem
```

### Upload Public Key to OCI

```bash
# Display public key
cat ~/.oci/new_api_key_public.pem

# In OCI Console:
# User Settings → API Keys → Add API Key → Paste public key
# Copy fingerprint
```

### Update Config

```ini
[new-profile]
user=[Link to Secure Variable: OCI_USER_OCID]
fingerprint=<fingerprint-from-console>
tenancy=[Link to Secure Variable: OCI_TENANCY_OCID]
region=us-phoenix-1
key_file=~/.oci/new_api_key.pem
```

---

## Compartment Configuration

### Finding Compartment OCIDs

#### Using OCI CLI

```bash
# List all compartments
oci iam compartment list --all

# Filter by name
oci iam compartment list --all | jq '.data[] | select(.name=="Production")'

# Get root compartment
oci iam compartment list --compartment-id-in-subtree true --all | jq -r '.data[0]."compartment-id"'
```

#### Using Python

```python
from mcp_oci_opsi.tools_cache import list_cached_compartments

# List all compartments
result = list_cached_compartments()
for comp in result['compartments']:
    print(f"{comp['name']}: {comp['id']}")
```

### Configuring Multiple Compartments

```bash
# Method 1: Environment variable
export CACHE_COMPARTMENT_IDS="[Link to Secure Variable: OCI_COMPARTMENT_OCID],[Link to Secure Variable: OCI_COMPARTMENT_OCID]"

# Method 2: .env.local file
cat > .env.local <<EOF
CACHE_COMPARTMENT_IDS=[Link to Secure Variable: OCI_COMPARTMENT_OCID],[Link to Secure Variable: OCI_COMPARTMENT_OCID],[Link to Secure Variable: OCI_COMPARTMENT_OCID]
EOF

# Load .env.local
source .env.local
```

---

## IAM Permissions

### Required Policies

Create these policies in OCI Console (Identity & Security → Policies):

#### For Operations Insights

```
Allow group opsi-users to read database-family in compartment Production
Allow group opsi-users to read opsi-namespace in compartment Production
Allow group opsi-users to use operations-insights-family in compartment Production
```

#### For Database Management

```
Allow group dbm-users to read database-management-family in compartment Production
Allow group dbm-users to use database-management in compartment Production
Allow group dbm-users to inspect database-management-private-endpoints in compartment Production
```

#### For Multi-Compartment Access

```
Allow group opsi-users to read database-family in tenancy
Allow group opsi-users to read opsi-namespace in tenancy
Allow group opsi-users to use operations-insights-family in tenancy
```

### Verify Permissions

```python
from mcp_oci_opsi.tools_diagnostics import diagnose_opsi_permissions

# Check permissions for a compartment
result = diagnose_opsi_permissions(
    compartment_id="[Link to Secure Variable: OCI_COMPARTMENT_OCID]"
)

print(result['summary']['status'])
# Output: "All required permissions available" or error details
```

---

## Advanced Configuration

### Custom Cache Location

```bash
# Set custom cache path (not recommended)
# Modify cache.py:
CACHE_FILE = "/custom/path/cache.json"
```

### Logging Configuration

```python
import logging

# Enable debug logging
logging.basicConfig(level=logging.DEBUG)

# Or in code:
import oci
oci.config.validate_config = True
```

### Timeout Configuration

```python
# Adjust client timeouts
from oci.config import DEFAULT_LOCATION

config = oci.config.from_file(DEFAULT_LOCATION, "DEFAULT")
config["timeout"] = 60  # seconds
```

---

## Configuration Validation

### Complete Validation Script

```python
#!/usr/bin/env python3
"""Validate complete MCP OCI OPSI configuration."""

from mcp_oci_opsi.tools_profile_management import (
    list_oci_profiles_enhanced,
    validate_oci_profile,
)
from mcp_oci_opsi.tools_cache import get_cached_statistics
import os

print("=" * 80)
print("MCP OCI OPSI Configuration Validation")
print("=" * 80)

# 1. Check environment variables
print("\n1. Environment Variables:")
cache_comps = os.getenv("CACHE_COMPARTMENT_IDS")
print(f"   CACHE_COMPARTMENT_IDS: {'✅' if cache_comps else '❌'} {cache_comps or 'Not set'}")

# 2. Check profiles
print("\n2. OCI Profiles:")
profiles_result = list_oci_profiles_enhanced()
for profile in profiles_result['profiles']:
    status = "✅" if profile['valid'] else "❌"
    print(f"   {status} {profile['name']}: {profile['region']}")

# 3. Check cache
print("\n3. Cache Status:")
try:
    stats = get_cached_statistics()
    print(f"   ✅ Cache loaded")
    print(f"   Profile: {stats['statistics']['profile']}")
    print(f"   Databases: {stats['statistics']['total_databases']}")
    print(f"   Last updated: {stats['statistics']['last_updated']}")
except Exception as e:
    print(f"   ❌ Cache error: {e}")

print("\n" + "=" * 80)
print("Validation Complete")
print("=" * 80)
```

Save as `validate_config.py` and run:

```bash
python3 validate_config.py
```

---

## Troubleshooting Configuration

### Profile Not Found

```bash
# Error: ProfileNotFound
# Fix: Check profile name in ~/.oci/config
cat ~/.oci/config | grep "\["

# Verify profile exists
oci iam region list --profile YOUR_PROFILE
```

### Permission Denied on Key File

```bash
# Error: Permission denied: ~/.oci/api_key.pem
# Fix: Set correct permissions
chmod 600 ~/.oci/*.pem
```

### Invalid Fingerprint

```bash
# Get fingerprint from key file
openssl rsa -pubout -outform DER -in ~/.oci/api_key.pem | \
    openssl md5 -c | \
    awk '{print $2}'

# Compare with fingerprint in config
grep fingerprint ~/.oci/config
```

### Compartment Access Denied

```bash
# Test compartment access
oci iam compartment get --compartment-id [Link to Secure Variable: OCI_COMPARTMENT_OCID]

# If error, check IAM policies
```

---

## Related Pages

- [Installation](./Installation) - Installation guide
- [Multi-Tenancy](./Multi-Tenancy) - Multi-account management
- [Troubleshooting](./Troubleshooting) - Common issues

---

**Last Updated**: 2025-11-18
**Version**: 2.0.0
