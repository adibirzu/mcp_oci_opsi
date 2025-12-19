# Installation Guide

Complete installation guide for MCP OCI OPSI Server.

---

## Prerequisites

### System Requirements

- **Python**: 3.8 or higher
- **OCI CLI**: Latest version
- **Operating System**: macOS, Linux, or Windows
- **Memory**: 512MB minimum, 1GB recommended
- **Disk Space**: 100MB for installation, 500MB for caching

### Required Access

- OCI account with Operations Insights enabled
- IAM permissions for:
  - `OPSI_NAMESPACE_READ`
  - `DATABASE_MANAGEMENT_FAMILY`
  - `DATABASE_MANAGEMENT_READ`

---

## Step 1: Install OCI CLI

### macOS / Linux

```bash
bash -c "$(curl -L https://raw.githubusercontent.com/oracle/oci-cli/master/scripts/install/install.sh)"
```

### Windows

Download and run the installer from:
https://docs.oracle.com/en-us/iaas/Content/API/SDKDocs/cliinstall.htm

### Verify Installation

```bash
oci --version
# Output: 3.x.x or higher
```

---

## Step 2: Configure OCI CLI

### Interactive Configuration

```bash
oci setup config
```

This will prompt for:
1. **Location of config** (~/.oci/config)
2. **User OCID** (from OCI Console → User Settings)
3. **Tenancy OCID** (from OCI Console → Tenancy Details)
4. **Region** (e.g., us-phoenix-1)
5. **Generate new API key** (Y/n)

### Manual Configuration

Create `~/.oci/config`:

```ini
[DEFAULT]
user=[Link to Secure Variable: OCI_USER_OCID]
fingerprint=xx:xx:xx:xx:xx:xx:xx:xx:xx:xx:xx:xx:xx:xx:xx:xx
tenancy=[Link to Secure Variable: OCI_TENANCY_OCID]
region=us-phoenix-1
key_file=~/.oci/oci_api_key.pem
```

### Verify Configuration

```bash
oci iam region list
# Should list OCI regions
```

---

## Step 3: Install MCP OCI OPSI Server

### Clone Repository

```bash
git clone https://github.com/your-org/mcp-oci-opsi.git
cd mcp-oci-opsi
```

### Create Virtual Environment

```bash
# Create venv
python3 -m venv .venv

# Activate venv
source .venv/bin/activate  # macOS/Linux
# OR
.venv\Scripts\activate     # Windows
```

### Install Dependencies

```bash
# Install in development mode
pip install -e .

# Verify installation
python3 -c "import mcp_oci_opsi; print('Success!')"
```

---

## Step 4: Configure Environment

### Set Compartment IDs

```bash
# Add to ~/.bashrc or ~/.zshrc
export CACHE_COMPARTMENT_IDS="[Link to Secure Variable: OCI_COMPARTMENT_OCID],[Link to Secure Variable: OCI_COMPARTMENT_OCID]"

# Or create .env.local file
cat > .env.local <<EOF
CACHE_COMPARTMENT_IDS=[Link to Secure Variable: OCI_COMPARTMENT_OCID],[Link to Secure Variable: OCI_COMPARTMENT_OCID]
EOF
```

### Optional: Set Default Compartment

```bash
export OCI_COMPARTMENT_ID="[Link to Secure Variable: OCI_COMPARTMENT_OCID]"
```

---

## Step 5: Build Initial Cache (Recommended)

### Interactive Profile Selection

```bash
python3 build_cache.py --select-profile
```

This will:
1. List all available OCI profiles
2. Validate each profile
3. Allow you to select which profile to use
4. Build cache for the selected tenancy

### Specify Profile Directly

```bash
python3 build_cache.py --profile production
```

### Use Default Profile

```bash
python3 build_cache.py
```

### Expected Output

```
📋 Available OCI Profiles:

  1. ✅ DEFAULT
     Region: us-phoenix-1
     Tenancy: [Link to Secure Variable: OCI_TENANCY_OCID]

  2. ✅ production
     Region: us-ashburn-1
     Tenancy: [Link to Secure Variable: OCI_TENANCY_OCID]

Select profile (1-2): 1

🔄 Building cache for your compartments...
   Scanning 3 root compartments

✅ Cache built successfully!

📊 Statistics:
   Tenancy: MyCompany
   Profile: DEFAULT
   Region: us-phoenix-1
   Compartments scanned: 5
   Total databases: 12
   Total hosts: 8

💾 Cache saved to: ~/.mcp_oci_opsi_cache.json
⏰ Last updated: 2025-11-18T10:30:00Z

🚀 Cache ready! Use fast cache tools for instant responses.
```

---

## Step 6: Verify Installation

### Run Test Suite

```bash
# Test agent detection and profiles
python3 test_agent_detection.py

# Test new APIs
python3 test_new_apis.py
```

### Expected Test Results

```
🧪 MCP OCI OPSI - Agent Detection & Multi-Profile Enhancement Tests
================================================================================

TEST 1: Profile Management - ✅ PASSED
TEST 2: Agent Detection - ✅ PASSED
TEST 3: MCP Tool - ✅ PASSED

Overall: 3/3 tests passed

🎉 All tests PASSED!
```

### Quick Functionality Test

```python
# Test basic functionality
from mcp_oci_opsi.tools_cache import get_cached_statistics

stats = get_cached_statistics()
print(f"Total databases: {stats['statistics']['total_databases']}")
print(f"Total hosts: {stats['statistics']['total_hosts']}")
```

---

## Step 7: Configure for Production (Optional)

### Claude Desktop Integration

Add to `~/Library/Application Support/Claude/claude_desktop_config.json` (macOS):

```json
{
  "mcpServers": {
    "oci-opsi": {
      "command": "/path/to/mcp_oci_opsi/.venv/bin/python",
      "args": ["-m", "mcp_oci_opsi"],
      "env": {
        "OCI_CLI_PROFILE": "DEFAULT",
        "CACHE_COMPARTMENT_IDS": "[Link to Secure Variable: OCI_COMPARTMENT_OCID]"
      }
    }
  }
}
```

### Claude Code Integration

Add to `.claude/mcp-config.json`:

```json
{
  "servers": {
    "oci-opsi": {
      "command": "python",
      "args": ["-m", "mcp_oci_opsi"],
      "cwd": "/path/to/mcp_oci_opsi"
    }
  }
}
```

---

## Troubleshooting Installation

### Python Version Issues

```bash
# Check Python version
python3 --version

# If < 3.8, install newer version
brew install python@3.11  # macOS
sudo apt install python3.11  # Ubuntu
```

### OCI CLI Not Found

```bash
# Check if OCI CLI is in PATH
which oci

# If not found, add to PATH
export PATH=$PATH:~/bin  # Adjust based on installation location
```

### Permission Errors

```bash
# Fix key file permissions
chmod 600 ~/.oci/oci_api_key.pem

# Fix config file permissions
chmod 600 ~/.oci/config
```

### Module Import Errors

```bash
# Reinstall dependencies
pip install --force-reinstall -e .

# Or clear cache and reinstall
pip cache purge
pip install -e .
```

### Cache Build Failures

```bash
# Verify compartment IDs
echo $CACHE_COMPARTMENT_IDS

# Test OCI connectivity
oci iam region list --profile DEFAULT

# Check permissions
python3 diagnose_permissions.py
```

---

## Uninstallation

### Remove MCP Server

```bash
# Deactivate venv
deactivate

# Remove installation
cd ..
rm -rf mcp_oci_opsi

# Remove cache
rm ~/.mcp_oci_opsi_cache.json
```

### Keep OCI CLI

OCI CLI can be used by other applications. To remove:

```bash
# Remove OCI CLI (optional)
rm -rf ~/bin/oci
rm -rf ~/lib/oracle-cli
```

---

## Next Steps

1. **[Configuration](./Configuration)** - Configure multi-tenancy and profiles
2. **[Quick Start](./Quick-Start)** - Learn basic usage
3. **[Tool Reference](./Tool-Reference)** - Explore available tools

---

**Installation Complete!** 🎉

You now have a fully functional MCP OCI OPSI Server with 117 tools ready to use.
