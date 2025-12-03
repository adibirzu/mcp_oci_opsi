---
name: multi-tenancy
description: |
  Manage multiple OCI tenancies and profiles for cross-tenancy operations.
  Use this skill when the user asks about:
  - Switching between OCI profiles/tenancies
  - Comparing configurations across tenancies
  - Validating profile configurations
  - Cross-tenancy inventory
  This skill enables DBA operations across multiple OCI environments.
allowed-tools:
  - list_oci_profiles
  - list_oci_profiles_enhanced
  - get_oci_profile_details
  - validate_oci_profile
  - get_profile_tenancy_details
  - compare_oci_profiles
  - refresh_profile_cache
  - get_current_profile_info
---

# Multi-Tenancy Management Skill

## Purpose
Manage and operate across multiple OCI tenancies using different profiles.

## What is Multi-Tenancy?
- Different OCI accounts (tenancies)
- Each with its own credentials and regions
- Configured via ~/.oci/config profiles
- Common for MSPs, enterprises with multiple accounts

## When to Use
- User manages multiple OCI accounts
- User needs to switch tenancy context
- User wants to compare across tenancies
- User validates profile configuration

## Profile Management

### List Profiles
```
list_oci_profiles_enhanced()
```
Returns all configured profiles with validation status.

### Validate Profile
```
validate_oci_profile(profile="tenant1")
```
Verifies credentials and connectivity.

### Get Profile Details
```
get_oci_profile_details(profile="tenant1")
```
Returns configuration including region and tenancy info.

## Switching Tenancies
Profile context affects all subsequent tool calls:
1. Most tools accept `profile` parameter
2. Cache is per-profile
3. Region defaults to profile's region

## Best Practices
- Validate profile before operations
- Use descriptive profile names
- Keep credentials current
- Refresh cache when switching profiles

## Response Format Guidelines
- Show current profile context
- List all available profiles
- Indicate validation status
- Note region for each profile

## Example Interactions

**User**: "Which profiles are available?"
**Approach**:
1. Call `list_oci_profiles_enhanced()`
2. Show profile names, regions, and status
3. Highlight current active profile

**User**: "Check if tenant2 profile works"
**Approach**:
1. Call `validate_oci_profile(profile="tenant2")`
2. Report connectivity status
3. Show tenancy name and region if valid
4. Provide troubleshooting if invalid

**User**: "Compare my profiles"
**Approach**:
1. Get list of profiles
2. Call `compare_oci_profiles(profiles=["tenant1", "tenant2"])`
3. Show side-by-side comparison
4. Highlight differences

**User**: "What tenancy am I using?"
**Approach**:
1. Call `get_current_profile_info()`
2. Show profile name, tenancy, region
3. Confirm this is the active context

**User**: "Switch to production tenancy"
**Approach**:
1. Explain profile-based context
2. Most operations accept `profile` parameter
3. For full switch, restart MCP server with OCI_CLI_PROFILE
4. Or pass `profile` parameter to each tool call

## Token Optimization
- Use `list_oci_profiles()` for simple list
- Use enhanced version only when validation needed
- Cache profile validation results
