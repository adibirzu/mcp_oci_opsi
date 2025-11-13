# MCP OCI OPSI Server - Complete Setup Guide

This guide walks you through setting up the MCP OCI OPSI Server on your machine, from OCI configuration to Claude Desktop integration.

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [OCI Configuration](#oci-configuration)
3. [Installation](#installation)
4. [Environment Configuration](#environment-configuration)
5. [Building the Cache](#building-the-cache)
6. [Claude Desktop Integration](#claude-desktop-integration)
7. [Verification](#verification)
8. [Troubleshooting](#troubleshooting)

## Prerequisites

Before you begin, ensure you have:

- **Python 3.10 or higher** installed
- **OCI Account** with access to Operations Insights
- **OCI CLI** configured (or manual configuration file setup)
- **IAM Permissions** for Operations Insights and Database Management
- **Claude Desktop** or **Claude Code** installed (for MCP integration)

### Required IAM Permissions

Your OCI user or instance principal needs these policies:

```
Allow group YourGroup to read operations-insights-family in tenancy
Allow group YourGroup to read database-management-family in tenancy
Allow group YourGroup to read autonomous-databases in tenancy
Allow group YourGroup to read compartments in tenancy
```

## OCI Configuration

### Option 1: Using OCI CLI (Recommended)

1. Install OCI CLI:
   ```bash
   bash -c "$(curl -L https://raw.githubusercontent.com/oracle/oci-cli/master/scripts/install/install.sh)"
   ```

2. Configure OCI CLI:
   ```bash
   oci setup config
   ```

   This will create `~/.oci/config` and generate an API key pair.

3. Upload the public key to OCI:
   - Log into OCI Console
   - Navigate to your user profile → API Keys
   - Click "Add API Key" and paste the public key contents

### Option 2: Manual Configuration

1. Create the configuration directory:
   ```bash
   mkdir -p ~/.oci
   ```

2. Generate API key pair:
   ```bash
   openssl genrsa -out ~/.oci/oci_api_key.pem 2048
   openssl rsa -pubout -in ~/.oci/oci_api_key.pem -out ~/.oci/oci_api_key_public.pem
   chmod 600 ~/.oci/oci_api_key.pem
   ```

3. Upload the public key to OCI (see Option 1, step 3)

4. Create `~/.oci/config`:
   ```ini
   [DEFAULT]
   user=ocid1.user.oc1..aaaaaa...
   fingerprint=xx:xx:xx:xx:xx:xx:xx:xx:xx:xx:xx:xx:xx:xx:xx:xx
   tenancy=ocid1.tenancy.oc1..aaaaaa...
   region=us-ashburn-1
   key_file=~/.oci/oci_api_key.pem
   ```

   Replace the values with your actual OCI details.

### Multiple Profiles (Optional)

You can configure multiple profiles in `~/.oci/config`:

```ini
[DEFAULT]
user=ocid1.user.oc1..aaaaaa...
fingerprint=...
tenancy=ocid1.tenancy.oc1..aaaaaa...
region=us-ashburn-1
key_file=~/.oci/oci_api_key.pem

[PRODUCTION]
user=ocid1.user.oc1..bbbbbb...
fingerprint=...
tenancy=ocid1.tenancy.oc1..bbbbbb...
region=us-phoenix-1
key_file=~/.oci/oci_api_key_prod.pem

[DEVELOPMENT]
user=ocid1.user.oc1..cccccc...
fingerprint=...
tenancy=ocid1.tenancy.oc1..cccccc...
region=eu-frankfurt-1
key_file=~/.oci/oci_api_key_dev.pem
```

## Installation

### Step 1: Clone or Download the Repository

```bash
cd ~/dev  # or your preferred location
git clone https://github.com/YOUR_USERNAME/mcp_oci_opsi.git
cd mcp_oci_opsi
```

### Step 2: Create Virtual Environment

**Using uv (recommended):**
```bash
# Install uv if not already installed
curl -LsSf https://astral.sh/uv/install.sh | sh

# Create and activate virtual environment
uv venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
uv pip install -e .

# Optional: Install with Oracle Database support
uv pip install -e ".[database]"
```

**Using pip:**
```bash
# Create virtual environment
python3 -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
pip install -e .

# Optional: Install with Oracle Database support
pip install -e ".[database]"
```

## Environment Configuration

### Step 1: Create .env File

```bash
cp .env.example .env
```

### Step 2: Edit .env File

Open `.env` in your text editor and configure:

```bash
# OCI Profile (from ~/.oci/config)
OCI_CLI_PROFILE=DEFAULT

# OCI Region (optional, overrides config file)
OCI_REGION=us-ashburn-1

# Default Compartment ID (optional)
# OCI_COMPARTMENT_ID=ocid1.compartment.oc1..aaaaaaaxxxxx

# Cache Compartment IDs (comma-separated, for fast cache system)
# List the root compartment OCIDs you want to cache
# The system will recursively scan all child compartments
CACHE_COMPARTMENT_IDS=ocid1.compartment.oc1..aaa,ocid1.compartment.oc1..bbb
```

### Step 3: Find Your Compartment OCIDs

**Using OCI CLI:**
```bash
# List all compartments
oci iam compartment list --compartment-id-in-subtree true --all

# Or list specific compartment by name
oci iam compartment list --name "Production" --all
```

**Using OCI Console:**
1. Navigate to Identity & Security → Compartments
2. Click on your compartment
3. Copy the OCID from the compartment details

### Configuration Examples

**Single compartment:**
```bash
CACHE_COMPARTMENT_IDS=ocid1.compartment.oc1..aaaaaaaxxxxx
```

**Multiple compartments:**
```bash
CACHE_COMPARTMENT_IDS=ocid1.compartment.oc1..aaa,ocid1.compartment.oc1..bbb,ocid1.compartment.oc1..ccc
```

**Different profile:**
```bash
OCI_CLI_PROFILE=PRODUCTION
OCI_REGION=us-phoenix-1
CACHE_COMPARTMENT_IDS=ocid1.compartment.oc1..prod_compartment
```

## Building the Cache

The fast cache system provides instant responses with zero API calls for database inventory queries.

### Step 1: Configure Cache Compartments

Ensure you've set `CACHE_COMPARTMENT_IDS` in your `.env` file (see above).

### Step 2: Build the Cache

```bash
# Activate virtual environment if not already active
source .venv/bin/activate

# Build cache
python3 build_cache.py
```

Expected output:
```
🔄 Building cache for your compartments...
   Scanning 3 root compartments

✅ Cache built successfully!

📊 Statistics:
   Compartments scanned: 3
   Total databases: N
   Total hosts: N

📁 Databases by compartment:
   Production: X databases
   Development: Y databases
   Test: Z databases

💾 Cache saved to: /Users/your_username/.mcp_oci_opsi_cache.json
⏰ Last updated: 2024-11-13T14:00:00Z

🚀 Cache ready! Use fast cache tools for instant responses.
```

### Step 3: Verify Cache

```bash
# Check cache file exists
ls -lh ~/.mcp_oci_opsi_cache.json

# Optional: View cache contents (JSON format)
cat ~/.mcp_oci_opsi_cache.json | python3 -m json.tool | head -50
```

## Claude Desktop Integration

### Step 1: Find Python Path

Get the full path to your virtual environment's Python:

```bash
# From your project directory with venv activated
which python
```

Copy this path. Example: `/Users/your_username/dev/mcp_oci_opsi/.venv/bin/python`

### Step 2: Locate Claude Desktop Config

Find your Claude Desktop configuration file:

- **macOS**: `~/Library/Application Support/Claude/claude_desktop_config.json`
- **Windows**: `%APPDATA%\Claude\claude_desktop_config.json`
- **Linux**: `~/.config/Claude/claude_desktop_config.json`

### Step 3: Edit Configuration

Open `claude_desktop_config.json` and add the MCP server:

```json
{
  "mcpServers": {
    "oci-opsi": {
      "command": "/Users/your_username/dev/mcp_oci_opsi/.venv/bin/python",
      "args": [
        "-m",
        "mcp_oci_opsi.main"
      ],
      "env": {
        "OCI_CLI_PROFILE": "DEFAULT",
        "OCI_REGION": "us-ashburn-1"
      }
    }
  }
}
```

**Important**: Replace:
- `/Users/your_username/dev/mcp_oci_opsi/.venv/bin/python` with your actual Python path
- `DEFAULT` with your OCI profile name
- `us-ashburn-1` with your region

### Step 4: Restart Claude Desktop

1. Quit Claude Desktop completely
2. Relaunch Claude Desktop
3. The OCI OPSI tools should now be available

## Verification

### Test 1: Basic Connectivity

In Claude Desktop, try:
```
Claude, ping the OCI OPSI server
```

Expected: Positive response confirming server is running.

### Test 2: Check Current Profile

```
Claude, who am I in OCI?
```

Expected: Your OCI user OCID, tenancy, and region information.

### Test 3: List Profiles

```
Claude, list all available OCI profiles
```

Expected: List of profiles from your `~/.oci/config` file.

### Test 4: Fast Cache Queries

```
Claude, show me fleet summary
```

Expected: Instant response (<50ms) with your cached database count.

```
Claude, how many databases do I have?
```

Expected: Instant count from cache.

### Test 5: Live API Query

```
Claude, list database insights in compartment [YOUR_COMPARTMENT_OCID]
```

Expected: List of databases with Operations Insights enabled (takes 2-5 seconds).

## Troubleshooting

### Error: "ModuleNotFoundError: No module named 'mcp_oci_opsi'"

**Solution**: Install the package in editable mode:
```bash
cd /path/to/mcp_oci_opsi
source .venv/bin/activate
pip install -e .
```

### Error: "ConfigFileNotFound" or "ProfileNotFound"

**Solution**: Verify OCI configuration:
```bash
# Check config file exists
cat ~/.oci/config

# Check profile name matches
grep "\[" ~/.oci/config

# Test OCI CLI
oci iam region list
```

### Error: "CACHE_COMPARTMENT_IDS environment variable not set"

**Solution**: Add compartment IDs to your `.env` file:
```bash
echo "CACHE_COMPARTMENT_IDS=ocid1.compartment.oc1..your_ocid" >> .env
```

### Error: "ServiceError: NotAuthenticated"

**Solutions**:
1. Verify API key uploaded to OCI Console
2. Check key file permissions:
   ```bash
   chmod 600 ~/.oci/oci_api_key.pem
   ```
3. Verify fingerprint matches in OCI Console
4. Check user has required IAM permissions

### Cache Not Updating

**Solution**: Rebuild cache manually:
```bash
python3 build_cache.py
```

Or in Claude:
```
Claude, rebuild database cache
```

### Claude Desktop Not Showing Tools

**Solutions**:
1. Check Claude Desktop config JSON is valid:
   ```bash
   # macOS
   cat ~/Library/Application\ Support/Claude/claude_desktop_config.json | python3 -m json.tool
   ```
2. Verify Python path is correct
3. Restart Claude Desktop completely
4. Check Claude Desktop logs (if available)

## Advanced Configuration

### Using Instance Principal Authentication

For OCI Compute instances with instance principals:

1. Remove/comment out key_file in `~/.oci/config`
2. Set authentication type:
   ```ini
   [DEFAULT]
   region=us-ashburn-1
   tenancy=ocid1.tenancy.oc1..aaaaaa...
   # Instance principal will be used automatically
   ```

### Custom Cache Location

Set environment variable:
```bash
export MCP_OCI_OPSI_CACHE_FILE=/custom/path/cache.json
```

### Cache Refresh Schedule

The cache is valid for 24 hours by default. To refresh:

**Manual:**
```bash
python3 build_cache.py
```

**Automated (cron):**
```bash
# Edit crontab
crontab -e

# Add daily refresh at 2 AM
0 2 * * * cd /path/to/mcp_oci_opsi && /path/to/.venv/bin/python3 build_cache.py
```

## Next Steps

1. **Explore Tools**: Ask Claude "What OCI OPSI tools are available?"
2. **Read Documentation**: Check [README.md](README.md) for tool details
3. **Cache System**: Read [CACHE_SYSTEM.md](CACHE_SYSTEM.md) for optimization tips
4. **Demo Questions**: See [DBA_DEMO_QUESTIONS.md](DBA_DEMO_QUESTIONS.md) for example queries

## Getting Help

- **GitHub Issues**: Report bugs or request features
- **Documentation**: Check all `.md` files in the repository
- **OCI Documentation**: [Operations Insights Docs](https://docs.oracle.com/en-us/iaas/operations-insights/)

---

**Ready to use the MCP OCI OPSI Server!** 🚀
