---
name: security-audit
description: |
  Audit database users, roles, privileges, and security configuration.
  Use this skill when the user asks about:
  - Database users and accounts
  - Role assignments
  - System privileges
  - Proxy user configuration
  - Security compliance checks
  This skill helps DBAs maintain database security posture.
allowed-tools:
  - list_users
  - get_user
  - list_roles
  - list_system_privileges
  - list_consumer_group_privileges
  - list_proxy_users
---

# Security Audit Skill

## Purpose
Audit and review database security configuration including users, roles, and privileges.

## When to Use
- User asks about database users
- User needs privilege audit
- User reviews security posture
- User investigates access issues
- Compliance review required

## Security Audit Areas

### User Management
- Account status (open, locked, expired)
- Password expiration
- Profile assignments
- Default tablespaces

### Privilege Analysis
- System privileges (CREATE TABLE, ALTER SESSION, etc.)
- Object privileges
- Role memberships
- Consumer group access

### Proxy Users
- Application accounts using proxy authentication
- Proxy chain analysis

## Recommended Approach

### For User Inventory
Use `list_users()`:
- Returns all database users
- Shows account status
- Includes creation date

### For User Details
Use `get_user(user_name)`:
- Full user configuration
- Profile settings
- Role memberships

### For Privilege Audit
Combine multiple tools:
1. `list_roles()` - All roles in database
2. `list_system_privileges()` - Direct system grants
3. `list_consumer_group_privileges()` - Resource management

## Security Best Practices Checklist
- [ ] No default passwords
- [ ] Lock inactive accounts
- [ ] Remove unnecessary privileges
- [ ] Use roles instead of direct grants
- [ ] Regular privilege review

## Response Format Guidelines
- Highlight security concerns first
- Note accounts with DBA-level privileges
- Flag locked or expired accounts
- Identify overly permissive configurations

## Example Interactions

**User**: "List all database users"
**Approach**:
1. Call `list_users(database_id)`
2. Group by account status
3. Highlight privileged accounts (DBA role)

**User**: "Who has DBA privileges?"
**Approach**:
1. Call `list_roles()` to identify users with DBA role
2. Call `list_system_privileges()` for direct grants
3. Consolidate privileged accounts

**User**: "Show proxy user configuration"
**Approach**:
1. Call `list_proxy_users(database_id)`
2. Map proxy relationships
3. Identify potential security concerns

**User**: "Audit user X's privileges"
**Approach**:
1. Call `get_user(user_name="X")` for user details
2. List assigned roles
3. Enumerate effective privileges

## Token Optimization
- Start with `list_users()` for overview
- Drill down with `get_user()` only for specific users
- Filter results by status or type when possible
