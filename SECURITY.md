# Security and Privacy Guidelines

## Overview

The MCP OCI OPSI server handles sensitive Oracle Cloud Infrastructure data. This document outlines security best practices and explains which files contain sensitive information.

## 🔒 Files That Contain Sensitive Data (NEVER COMMIT)

### 1. Cache Files

**Location**: `~/.mcp_oci_opsi_cache.json` (user home directory)

**Contains**:
- Database OCIDs
- Database names
- Compartment OCIDs and names
- Host names and OCIDs
- Exadata system details
- Complete tenancy inventory

**Risk**: Exposes your OCI infrastructure topology and resource naming

**Gitignore**: ✅ Already protected by `.gitignore`

### 2. Tenancy Review Reports

**Location**: `~/.mcp_oci_opsi/tenancy_review_*.json` (user home directory)

**Contains**:
- Tenancy OCID and name
- User OCID and email
- Complete compartment hierarchy
- All database, host, and Exadata details
- Statistical analysis of your environment

**Risk**: Complete infrastructure inventory with identifiable information

**Gitignore**: ✅ Already protected by `.gitignore`

### 3. OCI Configuration Files

**Location**: `~/.oci/config` (user home directory)

**Contains**:
- Tenancy OCID
- User OCID
- API key fingerprint
- Private key path
- Region information

**Risk**: Authentication credentials and account identifiers

**Gitignore**: ✅ Already protected by `.gitignore`

### 4. Private Keys

**Files**: `*.pem`, `*.key`, `*_key.pem`

**Contains**:
- OCI API private keys
- SSH private keys

**Risk**: Direct access to your OCI account

**Gitignore**: ✅ Already protected by `.gitignore`

### 5. Wallet Files

**Location**: `wallet/`, `wallet_*/`

**Contains**:
- Autonomous Database wallet files
- Connection strings
- Database credentials

**Risk**: Direct database access

**Gitignore**: ✅ Already protected by `.gitignore`

### 6. Environment Files

**Files**: `.env`, `.env.local`

**Contains**:
- OCI profile names
- Compartment OCIDs
- Region settings
- API keys

**Risk**: Configuration exposure and potential credentials

**Gitignore**: ✅ Already protected by `.gitignore`

### 7. Custom Configuration

**Files**: `claude_desktop_config.json`, `mcp_config.json`

**Contains**:
- File paths (may expose username)
- Profile selections
- Personal configuration

**Risk**: User information disclosure

**Gitignore**: ✅ Already protected by `.gitignore`

### 8. Setup and Build Logs

**Files**: `setup.log`, `cache_build.log`, `*.log`

**Contains**:
- Full output from tenancy scans
- OCIDs, compartment names, database names
- Tenancy structure details

**Risk**: Complete infrastructure disclosure

**Gitignore**: ✅ Already protected by `.gitignore`

### 9. Custom Prompts

**Location**: `prompts/`, `.prompts/`

**Contains**:
- User-specific prompts
- May include database names, OCIDs, or queries
- Personal workflow information

**Risk**: User data and infrastructure details

**Gitignore**: ✅ Already protected by `.gitignore`

### 10. Local Development Files

**Files**: `*_local.py`, `local_config.py`, `test_local*.py`

**Contains**:
- Test data with real OCIDs
- Local configuration
- Development credentials

**Risk**: Credential and OCID exposure

**Gitignore**: ✅ Already protected by `.gitignore`

## ✅ Files Safe to Commit

These files contain NO sensitive data:

- `*.py` (source code) - generic implementation
- `*.md` (documentation) - generic instructions
- `*.sh` (scripts) - generic automation
- `requirements.txt`, `pyproject.toml` - dependencies
- `.gitignore` - exclusion rules
- Example files (`.env.example`) - templates only

## 🛡️ Security Best Practices

### 1. Verify Before Committing

Always check what you're committing:

```bash
# Review changes before commit
git status
git diff

# Never use 'git add .'
# Instead, add files explicitly:
git add specific_file.py

# Review what will be committed
git diff --staged
```

### 2. Check for Leaked Credentials

Before pushing:

```bash
# Search for potential OCIDs
git diff --cached | grep -i "ocid1"

# Search for potential API keys
git diff --cached | grep -i "key"

# Search for potential passwords
git diff --cached | grep -i "password"
```

### 3. Use Environment Variables

Never hardcode sensitive values:

```python
# ❌ WRONG
compartment_id = "ocid1.compartment.oc1..aaa..."

# ✅ CORRECT
import os
compartment_id = os.getenv("OCI_COMPARTMENT_ID")
```

### 4. Keep Cache Files in Home Directory

The cache and review reports are stored in your home directory (`~/`), which is:
- ✅ Outside the git repository
- ✅ User-specific
- ✅ Not accidentally committed

**Cache location**: `~/.mcp_oci_opsi_cache.json`
**Reports location**: `~/.mcp_oci_opsi/tenancy_review_*.json`

### 5. Review .gitignore Regularly

Ensure `.gitignore` is comprehensive:

```bash
# Check if sensitive files are ignored
git check-ignore ~/.mcp_oci_opsi_cache.json
git check-ignore tenancy_review_*.json
git check-ignore .env
```

### 6. Use Example Files for Documentation

Provide templates without real data:

```bash
# Create example files
cp .env .env.example

# Edit to remove real values
# Replace with placeholders:
OCI_CLI_PROFILE=DEFAULT
OCI_COMPARTMENT_ID=ocid1.compartment.oc1..YOUR_COMPARTMENT_OCID
```

### 7. Secure Your Development Environment

```bash
# Set proper file permissions
chmod 600 ~/.oci/config
chmod 600 ~/.oci/*.pem
chmod 600 .env

# Don't share your home directory
# Don't sync sensitive files to cloud storage
# Use encrypted disk for development
```

## 🚨 If You Accidentally Commit Sensitive Data

### Immediate Actions

1. **DO NOT** continue pushing
2. **Remove from history** immediately:

```bash
# If not yet pushed
git reset HEAD~1
git rm --cached sensitive_file.json

# If already pushed (requires force push)
git filter-branch --force --index-filter \
  "git rm --cached --ignore-unmatch sensitive_file.json" \
  --prune-empty --tag-name-filter cat -- --all

# Force push (WARNING: coordinate with team)
git push origin --force --all
```

3. **Rotate credentials** immediately:
   - Generate new OCI API keys
   - Update `~/.oci/config`
   - Revoke old keys in OCI Console

4. **Rebuild cache** with new credentials:
```bash
./scripts/quick_cache_build.sh
```

### Prevention Going Forward

- Enable GitHub secret scanning
- Use pre-commit hooks to check for secrets
- Regular security audits

## 🔍 Audit Your Repository

### Check Current Status

```bash
# List all tracked files
git ls-tree -r HEAD --name-only

# Check if any sensitive files are tracked
git ls-files | grep -E "(cache|\.env|\.oci|\.pem|\.key)"
```

### Scan for Secrets

```bash
# Install git-secrets
brew install git-secrets  # macOS
# or
apt-get install git-secrets  # Linux

# Scan repository
git secrets --scan-history
```

## 📋 Pre-Commit Checklist

Before every commit:

- [ ] No cache files (`*_cache.json`)
- [ ] No tenancy reports (`tenancy_review_*.json`)
- [ ] No credentials (`.env`, `*.pem`, `*.key`)
- [ ] No OCIDs in code (use environment variables)
- [ ] No real database names in examples
- [ ] No log files (`*.log`)
- [ ] No wallet files (`wallet*/`)
- [ ] No custom prompts (`prompts/`)
- [ ] Reviewed with `git diff --staged`

## 📝 Reporting Security Issues

If you discover a security vulnerability:

1. **DO NOT** open a public GitHub issue
2. Email security concerns to: [your-email]
3. Include:
   - Description of the vulnerability
   - Steps to reproduce
   - Potential impact
   - Suggested fix (if any)

## 🔐 Encryption Recommendations

For additional security:

### 1. Encrypt Your Cache

```bash
# Encrypt cache file
gpg -c ~/.mcp_oci_opsi_cache.json

# Decrypt when needed
gpg ~/.mcp_oci_opsi_cache.json.gpg
```

### 2. Use Encrypted Volumes

Store sensitive files on encrypted volumes:
- macOS: FileVault
- Linux: LUKS
- Windows: BitLocker

### 3. Secure Deletion

When removing sensitive files:

```bash
# Secure delete (macOS)
rm -P sensitive_file.json

# Secure delete (Linux)
shred -u sensitive_file.json
```

## 📚 Additional Resources

- [OCI Security Best Practices](https://docs.oracle.com/en-us/iaas/Content/Security/Reference/security_guide.htm)
- [Git Security](https://git-scm.com/book/en/v2/GitHub-Maintaining-a-Project)
- [Managing Secrets in Git](https://docs.github.com/en/code-security/secret-scanning)

---

## Summary

**Key Principles**:
1. ✅ Cache files are stored in home directory (outside repo)
2. ✅ All sensitive files are in `.gitignore`
3. ✅ Use environment variables for configuration
4. ✅ Never commit credentials or OCIDs
5. ✅ Review changes before committing
6. ✅ Rotate credentials if exposed

**Safe Repository**:
- Source code ✅
- Documentation ✅
- Scripts ✅
- Dependencies ✅
- Templates ✅

**Protected Data**:
- Cache files 🔒
- Review reports 🔒
- Credentials 🔒
- OCIDs 🔒
- Logs 🔒

Stay secure! 🔐
