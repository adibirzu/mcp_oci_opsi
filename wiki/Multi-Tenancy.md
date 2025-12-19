# Multi-Tenancy Support

Complete guide to managing multiple OCI accounts and tenancies with MCP OCI OPSI Server.

---

## Overview

MCP OCI OPSI Server v2.0 introduces comprehensive multi-tenancy support, allowing you to:

- ✅ Work with multiple OCI accounts simultaneously
- ✅ Switch between profiles without environment changes
- ✅ Interactive profile selection in build scripts
- ✅ Profile validation and health checks
- ✅ Tenancy-specific caching

---

## Key Features

### 1. Profile Management Tools

Seven new tools for profile operations:

| Tool | Purpose |
|------|---------|
| `list_oci_profiles_enhanced()` | List all profiles with validation |
| `get_oci_profile_details()` | Get detailed profile information |
| `validate_oci_profile()` | Validate profile configuration |
| `get_profile_tenancy_details()` | Get tenancy information |
| `compare_oci_profiles()` | Compare two profiles |
| `refresh_profile_cache()` | Refresh cache for specific profile |
| `get_current_profile_info()` | Get active profile information |

### 2. Interactive Profile Selection

Build cache interactively without modifying environment variables:

```bash
python3 build_cache.py --select-profile
```

### 3. Profile Parameter

All tools accept optional `profile` parameter:

```python
# Use specific profile
result = list_database_insights(
    compartment_id="[Link to Secure Variable: OCI_COMPARTMENT_OCID]",
    profile="production"  # Use production profile
)
```

---

## Setup Multi-Tenancy

### Configure Multiple Profiles

Edit `~/.oci/config`:

```ini
[DEFAULT]
user=[Link to Secure Variable: OCI_USER_OCID]
fingerprint=aa:bb:cc:dd:ee:ff:11:22:33:44:55:66:77:88:99:00
tenancy=[Link to Secure Variable: OCI_TENANCY_OCID]
region=us-phoenix-1
key_file=~/.oci/default_key.pem

[production]
user=[Link to Secure Variable: OCI_USER_OCID]
fingerprint=11:22:33:44:55:66:77:88:99:00:aa:bb:cc:dd:ee:ff
tenancy=[Link to Secure Variable: OCI_TENANCY_OCID]
region=us-ashburn-1
key_file=~/.oci/prod_key.pem

[development]
user=[Link to Secure Variable: OCI_USER_OCID]
fingerprint=ff:ee:dd:cc:bb:aa:99:88:77:66:55:44:33:22:11:00
tenancy=[Link to Secure Variable: OCI_TENANCY_OCID]
region=eu-frankfurt-1
key_file=~/.oci/dev_key.pem

[sandbox]
user=[Link to Secure Variable: OCI_USER_OCID]
fingerprint=99:88:77:66:55:44:33:22:11:00:aa:bb:cc:dd:ee:ff
tenancy=[Link to Secure Variable: OCI_TENANCY_OCID]
region=ap-mumbai-1
key_file=~/.oci/sandbox_key.pem
```

### Validate All Profiles

```python
from mcp_oci_opsi.tools_profile_management import list_oci_profiles_enhanced

# Get all profiles with validation
result = list_oci_profiles_enhanced()

print(f"Total profiles: {result['total_profiles']}")
print(f"Valid profiles: {result['valid_profiles']}")
print(f"Invalid profiles: {result['invalid_profiles']}\n")

for profile in result['profiles']:
    status = "✅" if profile['valid'] else "❌"
    print(f"{status} {profile['name']}")
    print(f"   Region: {profile['region']}")
    print(f"   Tenancy: {profile.get('tenancy_name', 'Unknown')}")
    if not profile['valid']:
        print(f"   Error: {profile.get('error', 'Unknown error')}")
    print()
```

**Expected Output:**
```
Total profiles: 4
Valid profiles: 3
Invalid profiles: 1

✅ DEFAULT
   Region: us-phoenix-1
   Tenancy: CompanyA

✅ production
   Region: us-ashburn-1
   Tenancy: CompanyB

✅ development
   Region: eu-frankfurt-1
   Tenancy: CompanyC

❌ sandbox
   Region: ap-mumbai-1
   Tenancy: Unknown
   Error: Invalid API key fingerprint
```

---

## Working with Profiles

### Get Profile Details

```python
from mcp_oci_opsi.tools_profile_management import get_oci_profile_details

# Get detailed information
details = get_oci_profile_details("production")

print(f"Profile: {details['profile']}")
print(f"Valid: {details['valid']}")
print(f"\nConfiguration:")
print(f"  User OCID: {details['config']['user']}")
print(f"  Tenancy OCID: {details['config']['tenancy']}")
print(f"  Region: {details['config']['region']}")
print(f"  Key file: {details['config']['key_file']}")

print(f"\nTenancy:")
print(f"  Name: {details['tenancy']['name']}")
print(f"  Home region: {details['tenancy']['home_region_key']}")
```

### Compare Two Profiles

```python
from mcp_oci_opsi.tools_profile_management import compare_oci_profiles

# Compare production and development
comparison = compare_oci_profiles("production", "development")

print("Profile Comparison:\n")
print(f"Profile 1: {comparison['profile1']['name']}")
print(f"  Tenancy: {comparison['profile1']['tenancy_name']}")
print(f"  Region: {comparison['profile1']['region']}")

print(f"\nProfile 2: {comparison['profile2']['name']}")
print(f"  Tenancy: {comparison['profile2']['tenancy_name']}")
print(f"  Region: {comparison['profile2']['region']}")

print(f"\nComparison:")
print(f"  Same tenancy: {comparison['same_tenancy']}")
print(f"  Same region: {comparison['same_region']}")
print(f"  Same user: {comparison['same_user']}")

if comparison['same_tenancy']:
    print("\n  ℹ️ These profiles access the same tenancy")
else:
    print("\n  ℹ️ These profiles access different tenancies")
```

### Get Current Active Profile

```python
from mcp_oci_opsi.tools_profile_management import get_current_profile_info

# Get currently active profile
current = get_current_profile_info()

print(f"Active Profile: {current['profile']}")
print(f"Tenancy: {current['tenancy_name']}")
print(f"Region: {current['region']}")
print(f"User: {current['user_name']}")
```

---

## Building Cache for Multiple Tenancies

### Interactive Selection

```bash
# Interactive profile selection
python3 build_cache.py --select-profile
```

**Interactive Session:**
```
📋 Available OCI Profiles:

  1. ✅ DEFAULT
     Region: us-phoenix-1
     Tenancy: CompanyA ([Link to Secure Variable: OCI_TENANCY_OCID])

  2. ✅ production
     Region: us-ashburn-1
     Tenancy: CompanyB ([Link to Secure Variable: OCI_TENANCY_OCID])

  3. ✅ development
     Region: eu-frankfurt-1
     Tenancy: CompanyC ([Link to Secure Variable: OCI_TENANCY_OCID])

  4. ❌ sandbox [INVALID]
     Error: Invalid API key fingerprint

Select profile (1-3) [or 'q' to quit]: 2

✅ Selected profile: production

🔄 Building cache for your compartments...
   Using profile: production
   Tenancy: CompanyB
   Region: us-ashburn-1
   Scanning 3 root compartments

✅ Cache built successfully!
```

### Specify Profile Directly

```bash
# Build cache for production profile
python3 build_cache.py --profile production

# Build cache for development profile
python3 build_cache.py --profile development
```

### Build Cache for All Profiles

```bash
#!/bin/bash
# build_all_caches.sh - Build cache for all valid profiles

for profile in DEFAULT production development; do
    echo "Building cache for profile: $profile"
    python3 build_cache.py --profile $profile
    echo "---"
done
```

---

## Using Profiles in Code

### Method 1: Profile Parameter

Pass `profile` parameter to any tool:

```python
from mcp_oci_opsi.tools_database_discovery import list_database_insights_by_management_type

# Query production tenancy
prod_result = list_database_insights_by_management_type(
    compartment_id="[Link to Secure Variable: OCI_COMPARTMENT_OCID]",
    profile="production"
)

# Query development tenancy
dev_result = list_database_insights_by_management_type(
    compartment_id="[Link to Secure Variable: OCI_COMPARTMENT_OCID]",
    profile="development"
)

print(f"Production databases: {prod_result['summary']['total_databases']}")
print(f"Development databases: {dev_result['summary']['total_databases']}")
```

### Method 2: Environment Variable

```python
import os

# Set profile for all operations
os.environ['OCI_CLI_PROFILE'] = 'production'

# All subsequent operations use production profile
from mcp_oci_opsi.tools_cache import search_cached_databases

result = search_cached_databases()  # Uses production profile
```

### Method 3: Context Manager (Custom)

```python
class OCIProfileContext:
    """Context manager for temporary profile switching."""

    def __init__(self, profile):
        self.profile = profile
        self.previous_profile = None

    def __enter__(self):
        self.previous_profile = os.environ.get('OCI_CLI_PROFILE')
        os.environ['OCI_CLI_PROFILE'] = self.profile
        return self

    def __exit__(self, *args):
        if self.previous_profile:
            os.environ['OCI_CLI_PROFILE'] = self.previous_profile
        else:
            os.environ.pop('OCI_CLI_PROFILE', None)

# Usage
with OCIProfileContext('production'):
    # All operations use production profile
    result = search_cached_databases()

# Profile reverts to previous value
```

---

## Multi-Tenancy Use Cases

### Use Case 1: Multi-Environment Management

Manage production, staging, and development separately:

```python
from mcp_oci_opsi.tools_database_discovery import list_database_insights_by_management_type

environments = {
    'production': '[Link to Secure Variable: OCI_COMPARTMENT_OCID]',
    'staging': '[Link to Secure Variable: OCI_COMPARTMENT_OCID]',
    'development': '[Link to Secure Variable: OCI_COMPARTMENT_OCID]'
}

for env_name, compartment in environments.items():
    result = list_database_insights_by_management_type(
        compartment_id=compartment,
        profile=env_name
    )

    print(f"\n{env_name.upper()} Environment:")
    print(f"  Databases: {result['summary']['total_databases']}")
    print(f"  Agent adoption: {result['summary']['agent_based_percentage']}%")
```

### Use Case 2: Multi-Customer Management (MSP)

Manage multiple customer tenancies:

```python
customers = {
    'customer-a': {
        'profile': 'customer_a_profile',
        'compartment': '[Link to Secure Variable: OCI_COMPARTMENT_OCID]'
    },
    'customer-b': {
        'profile': 'customer_b_profile',
        'compartment': '[Link to Secure Variable: OCI_COMPARTMENT_OCID]'
    },
    'customer-c': {
        'profile': 'customer_c_profile',
        'compartment': '[Link to Secure Variable: OCI_COMPARTMENT_OCID]'
    }
}

for customer_name, config in customers.items():
    result = list_database_insights_by_management_type(
        compartment_id=config['compartment'],
        profile=config['profile']
    )

    print(f"\n{customer_name}:")
    print(f"  Total databases: {result['summary']['total_databases']}")
    print(f"  MACS databases: {len(result['databases_by_type'].get('MACS_MANAGED_EXTERNAL_DATABASE', []))}")
```

### Use Case 3: Regional Comparison

Compare databases across regions:

```python
regions = {
    'us-phoenix-1': 'profile_phoenix',
    'us-ashburn-1': 'profile_ashburn',
    'eu-frankfurt-1': 'profile_frankfurt'
}

compartment_id = "[Link to Secure Variable: OCI_COMPARTMENT_OCID]"

for region, profile in regions.items():
    result = list_database_insights_by_management_type(
        compartment_id=compartment_id,
        profile=profile
    )

    print(f"\nRegion: {region}")
    print(f"  Databases: {result['summary']['total_databases']}")
    print(f"  Agent-based: {result['summary']['agent_based_percentage']}%")
```

---

## Best Practices

### 1. Profile Naming Convention

Use descriptive, consistent profile names:

```ini
# ✅ GOOD
[prod-tenancy-a]
[stage-tenancy-a]
[dev-tenancy-a]

[customer-abc-prod]
[customer-abc-dev]

# ❌ BAD
[profile1]
[config2]
[temp]
```

### 2. Validate Before Use

Always validate profiles before operations:

```python
from mcp_oci_opsi.tools_profile_management import validate_oci_profile

# Validate before using
validation = validate_oci_profile("production")

if validation['valid']:
    # Proceed with operations
    result = list_database_insights(
        compartment_id="[Link to Secure Variable: OCI_COMPARTMENT_OCID]",
        profile="production"
    )
else:
    print(f"❌ Profile invalid: {validation['error']}")
```

### 3. Cache Per Profile

Build separate cache for each profile:

```bash
# Build production cache
python3 build_cache.py --profile production

# Build development cache
python3 build_cache.py --profile development
```

### 4. Document Profile Usage

Document which profiles are used for what:

```python
# profiles.py - Profile configuration

PROFILES = {
    'production': {
        'description': 'Production environment - Company A',
        'region': 'us-phoenix-1',
        'use_for': ['monitoring', 'reporting', 'alerts']
    },
    'development': {
        'description': 'Development environment - Company A',
        'region': 'us-ashburn-1',
        'use_for': ['testing', 'development']
    }
}
```

---

## Troubleshooting Multi-Tenancy

### Profile Not Found

```python
# Error: ProfileNotFound: production
# Solution: List available profiles
from mcp_oci_opsi.tools_profile_management import list_oci_profiles_enhanced

profiles = list_oci_profiles_enhanced()
print("Available profiles:")
for p in profiles['profiles']:
    print(f"  - {p['name']}")
```

### Invalid Profile Configuration

```python
# Error: Invalid configuration for profile
# Solution: Validate and check details
from mcp_oci_opsi.tools_profile_management import get_oci_profile_details

details = get_oci_profile_details("production")
if not details['valid']:
    print(f"Error: {details.get('error', 'Unknown')}")
    print("Check:")
    print("  - API key file exists and is readable")
    print("  - Fingerprint matches OCI Console")
    print("  - User/Tenancy OCIDs are correct")
```

### Wrong Tenancy Access

```python
# Error: Accessing wrong tenancy
# Solution: Compare profiles and verify
from mcp_oci_opsi.tools_profile_management import get_current_profile_info

current = get_current_profile_info()
print(f"Currently using: {current['profile']}")
print(f"Tenancy: {current['tenancy_name']}")
print(f"Region: {current['region']}")

# Verify it's the correct tenancy before proceeding
```

---

## Advanced Topics

### Programmatic Profile Switching

```python
class MultiTenancyManager:
    """Manage operations across multiple profiles."""

    def __init__(self, profiles):
        self.profiles = profiles

    def execute_on_all(self, func, *args, **kwargs):
        """Execute function on all profiles."""
        results = {}

        for profile in self.profiles:
            try:
                kwargs['profile'] = profile
                result = func(*args, **kwargs)
                results[profile] = {'success': True, 'data': result}
            except Exception as e:
                results[profile] = {'success': False, 'error': str(e)}

        return results

# Usage
manager = MultiTenancyManager(['production', 'development', 'staging'])

results = manager.execute_on_all(
    list_database_insights_by_management_type,
    compartment_id="[Link to Secure Variable: OCI_COMPARTMENT_OCID]"
)

for profile, result in results.items():
    if result['success']:
        print(f"{profile}: {result['data']['summary']['total_databases']} databases")
    else:
        print(f"{profile}: Error - {result['error']}")
```

### Automated Profile Health Checks

```python
from mcp_oci_opsi.tools_profile_management import list_oci_profiles_enhanced
from datetime import datetime

def check_all_profiles():
    """Daily profile health check."""
    result = list_oci_profiles_enhanced()

    report = {
        'timestamp': datetime.utcnow().isoformat(),
        'total': result['total_profiles'],
        'valid': result['valid_profiles'],
        'invalid': result['invalid_profiles'],
        'profiles': []
    }

    for profile in result['profiles']:
        report['profiles'].append({
            'name': profile['name'],
            'valid': profile['valid'],
            'region': profile['region'],
            'error': profile.get('error')
        })

    # Send alert if any invalid
    if report['invalid'] > 0:
        send_alert(f"⚠️ {report['invalid']} invalid OCI profiles detected")

    return report

# Schedule daily
# 0 6 * * * /path/to/check_profiles.py
```

---

## Related Pages

- [Configuration](./Configuration) - OCI CLI configuration
- [Agent Detection](./Agent-Detection) - Agent type detection
- [Installation](./Installation) - Installation guide

---

**Last Updated**: 2025-11-18
**Version**: 2.0.0
**Feature**: Multi-Tenancy Support
