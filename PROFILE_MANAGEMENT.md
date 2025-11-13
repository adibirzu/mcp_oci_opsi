# OCI Profile Management Enhancement

## Overview

Enhanced the MCP OCI OPSI server with comprehensive OCI CLI profile management capabilities, making it easy to switch between different OCI credentials.

## What Was Added

### 1. New Configuration Functions (config.py)

**`list_available_profiles()`**
- Lists all profiles from `~/.oci/config`
- Returns: List of profile names

**`get_current_profile()`**
- Returns the currently active profile name
- Reads from `OCI_CLI_PROFILE` environment variable

### 2. New MCP Tools (main.py)

**`list_oci_profiles()`**
- Lists all available OCI CLI profiles
- Shows current active profile
- Displays count of available profiles
- Provides instructions for switching

**`get_profile_info(profile_name)`**
- Get detailed configuration for any profile
- Shows tenancy, user, region, fingerprint, key file
- Can query any profile without switching
- Safely excludes sensitive data

### 3. Configuration Files

**Updated `.env.example`**
- Added clear profile selection examples
- Listed available profiles: DEFAULT, default, emdemo
- Included switching instructions

**Created `.env`**
- Pre-configured with emdemo profile
- Ready for immediate testing

## Available Profiles

Your OCI configuration has the following profiles:

1. **DEFAULT** - Default profile
2. **default** - Alternate default profile
3. **emdemo** - Enterprise Management demo profile ✅ (currently active)

## How to Use

### Via Claude

**List available profiles:**
```
Claude, list all available OCI profiles
```

**Check current profile:**
```
Claude, who am I?
```

**Get info about specific profile:**
```
Claude, get profile info for emdemo
Claude, show me the configuration for DEFAULT profile
```

### Switching Profiles

**Method 1: Edit .env file**
```bash
# Edit /Users/abirzu/dev/mcp_oci_opsi/.env
OCI_CLI_PROFILE=emdemo  # Change to desired profile
```

**Method 2: Environment variable**
```bash
export OCI_CLI_PROFILE=emdemo
# Restart MCP server
```

**Method 3: Claude Desktop/Code config**
```json
{
  "mcpServers": {
    "oci-opsi": {
      "command": "/path/to/python",
      "args": ["-m", "mcp_oci_opsi.main"],
      "env": {
        "OCI_CLI_PROFILE": "emdemo",
        "OCI_REGION": "us-ashburn-1"
      }
    }
  }
}
```

## Testing the emdemo Profile

### Current Status

✅ **emdemo profile is configured and working**

The emdemo profile has been:
- Verified with OCI CLI
- Key file permissions fixed (600)
- Set as default in `.env` file
- Ready for use with MCP server

### Test Commands

**Test with OCI CLI:**
```bash
oci iam region list --profile emdemo
```

**Test with MCP server:**
```bash
cd /Users/abirzu/dev/mcp_oci_opsi
python -m mcp_oci_opsi.main
```

Then in Claude:
```
Claude, who am I?
Claude, list all OCI profiles
Claude, list compartments
```

## Tool Count Update

**Previous:** 46 tools
**Current:** 48 tools (+2)

New tools:
1. `list_oci_profiles()` - Profile discovery
2. `get_profile_info()` - Profile inspection

## Benefits

1. **Easy Profile Discovery** - See all available credentials
2. **Quick Switching** - Change profiles via environment variable
3. **Profile Inspection** - View configuration without switching
4. **Safe Testing** - Test different profiles without affecting others
5. **Clear Documentation** - Instructions in .env.example

## Security Notes

- Private keys remain secure (not exposed through tools)
- Only metadata is shown (user, tenancy, region, fingerprint)
- File permissions automatically checked by OCI CLI
- No passwords or sensitive data exposed

## Next Steps

1. **Test with emdemo profile:**
   ```bash
   # Already configured in .env
   cd /Users/abirzu/dev/mcp_oci_opsi
   python -m mcp_oci_opsi.main
   ```

2. **Use in Claude:**
   - Ask: "Who am I?"
   - Ask: "List all databases"
   - Ask: "Show compartments"

3. **Switch profiles as needed:**
   - Edit `.env` file
   - Change `OCI_CLI_PROFILE` value
   - Restart MCP server

## Technical Details

### Profile Resolution Order

1. `OCI_CLI_PROFILE` environment variable
2. `.env` file value
3. Default to "DEFAULT" profile

### Configuration File Location

`~/.oci/config` - Standard OCI CLI configuration file

### Key File Permissions

Key files must have 600 permissions (owner read/write only):
```bash
chmod 600 ~/.ssh/your-key-file.pem
```

---

**Status: ✅ READY FOR TESTING WITH EMDEMO PROFILE**

The MCP OCI OPSI server now supports easy profile management with 48 tools total!
