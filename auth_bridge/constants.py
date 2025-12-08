"""
Constants for OCA Authentication
Adapted from ocaider/providers/oca/constants.py

These are the Oracle IDCS endpoints and client IDs required for
OAuth authentication with Oracle Code Assist.
"""
import os
import re
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Oracle Code Assist LiteLLM Proxy (OpenAI-compatible endpoint)
# Determine from environment or use default
_OCA_LITELLM_URL = os.getenv(
    "OCA_LITELLM_URL",
    "https://api.codeassist.oraclecloud.com/"
)

# Extract region from LiteLLM URL
# Example: https://code-internal.aiservice.us-chicago-1.oci.oraclecloud.com/...
# Extracts: us-chicago-1
def _extract_region_from_url(url: str) -> str:
    """Extract OCI region from URL."""
    # Pattern: aiservice.{region}.oci or code-internal.aiservice.{region}.oci.oraclecloud.com
    # Examples:
    #   - https://code-internal.aiservice.us-chicago-1.oci.oraclecloud.com/
    #   - https://codeassist.aiservice.us-chicago-1.oci.oraclecloud.com/
    match = re.search(r'aiservice\.([a-z0-9\-]+)\.oci', url)
    if match:
        return match.group(1)
    # Fallback to us-chicago-1 if can't parse
    return "us-chicago-1"

_DETECTED_REGION = _extract_region_from_url(_OCA_LITELLM_URL)

# Oracle IDCS (Identity Cloud Service) OAuth endpoints
# IMPORTANT: For Oracle Employee authentication, you MUST set OCA_IDCS_BASE_URL
# to your tenant-specific IDCS URL (e.g., https://idcs-XXXXXXXX.identity.oraclecloud.com)
# The region-based URL will NOT work for employee authentication
IDCS_BASE_URL = os.getenv(
    "OCA_IDCS_BASE_URL",
    f"https://idcs.{_DETECTED_REGION}.oraclecloud.com"  # Fallback, but should be overridden
)

# Log IDCS configuration for debugging (to stderr to avoid breaking JSON output)
import sys
if not os.getenv("OCA_IDCS_BASE_URL"):
    print(f"[OCA Auth] ⚠️  WARNING: OCA_IDCS_BASE_URL not set!", file=sys.stderr)
    print(f"[OCA Auth] Using fallback: {IDCS_BASE_URL}", file=sys.stderr)
    print(f"[OCA Auth] For Oracle Employee auth, set OCA_IDCS_BASE_URL to your tenant-specific URL", file=sys.stderr)
else:
    print(f"[OCA Auth] ✅ IDCS Base URL: {IDCS_BASE_URL}", file=sys.stderr)

# OAuth endpoints
IDCS_AUTHORIZE_ENDPOINT = f"{IDCS_BASE_URL}/oauth2/v1/authorize"
IDCS_TOKEN_ENDPOINT = f"{IDCS_BASE_URL}/oauth2/v1/token"
IDCS_DEVICE_CODE_ENDPOINT = f"{IDCS_BASE_URL}/oauth2/v1/device"
IDCS_USERINFO_ENDPOINT = f"{IDCS_BASE_URL}/oauth2/v1/userinfo"

# Oracle Code Assist Client ID (public client for PKCE flow)
# Default is the Oracle Employee public client ID used by CLINE
IDCS_CLIENT_ID = os.getenv(
    "OCA_CLIENT_ID",
    "a8331954c0cf48ba99b5dd223a14c6ea"  # Oracle Employee public client
)

# Oracle Code Assist Client Secret (optional, for confidential clients)
# If set, Basic Auth will be used for client authentication
IDCS_CLIENT_SECRET = os.getenv("OCA_CLIENT_SECRET", "")

# Oracle Code Assist LiteLLM Proxy (OpenAI-compatible endpoint)
# Note: _OCA_LITELLM_URL is defined above and used for region extraction
# Expose it publicly for other modules
OCA_LITELLM_URL = _OCA_LITELLM_URL

# Model metadata cache filename
OCA_MODEL_METADATA = "oca_model_metadata.json"

# Default scopes for OAuth
OCA_DEFAULT_SCOPES = "openid offline_access"

# Timeout settings
OCA_AUTH_TIMEOUT = 180  # seconds to wait for browser auth (3 minutes)
OCA_DEVICE_CODE_POLL_INTERVAL = 5  # seconds between device code polls

# OAuth callback port (must match IDCS registered redirect URI)
# Default is 48801 to match CLINE's configuration
# Can be overridden with OCA_CALLBACK_PORT environment variable
OCA_CALLBACK_PORT = int(os.getenv("OCA_CALLBACK_PORT", "48801"))
