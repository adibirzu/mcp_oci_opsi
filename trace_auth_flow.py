#!/usr/bin/env python3
"""
Trace the OCA authentication flow without actually authenticating.
This shows what auth URL would be used and what domain redirect would occur.

Usage:
    python3 trace_auth_flow.py
"""

import os
import sys
import urllib.parse

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from auth_bridge.constants import (
    IDCS_AUTHORIZE_ENDPOINT,
    IDCS_TOKEN_ENDPOINT,
    IDCS_CLIENT_ID,
    OCA_DEFAULT_SCOPES,
    _DETECTED_REGION,
    IDCS_BASE_URL,
    _OCA_LITELLM_URL,
)
from auth_bridge.oca_auth import PKCEManager, OAuthCallbackServer

def print_section(title):
    print("\n" + "█" * 70)
    print(f"█  {title}")
    print("█" * 70)

def main():
    print_section("OCA AUTHENTICATION FLOW TRACE")

    print("\n1️⃣  CONFIGURATION")
    print(f"\n   OCA LiteLLM URL:")
    print(f"   → {_OCA_LITELLM_URL}")

    print(f"\n   Detected Region:")
    print(f"   → {_DETECTED_REGION}")

    print(f"\n   IDCS Base URL:")
    print(f"   → {IDCS_BASE_URL}")

    print_section("STEP 1: CREATE PKCE MANAGER")

    # Find an available port
    port = OAuthCallbackServer.find_available_port()
    redirect_uri = f"http://localhost:{port}/callback"

    print(f"\n   Redirect URI (callback address):")
    print(f"   → {redirect_uri}")

    # Create PKCE manager
    pkce_manager = PKCEManager(redirect_uri)

    print(f"\n   Code Verifier (PKCE):")
    print(f"   → {pkce_manager.code_verifier[:20]}... (truncated)")

    print(f"\n   Code Challenge:")
    print(f"   → {pkce_manager.code_challenge[:20]}... (truncated)")

    print(f"\n   State (CSRF protection):")
    print(f"   → {pkce_manager.state[:20]}... (truncated)")

    print_section("STEP 2: BUILD AUTHORIZATION URL")

    auth_url = pkce_manager.get_authorization_url()

    print(f"\n   Authorization Endpoint:")
    print(f"   → {IDCS_AUTHORIZE_ENDPOINT}")

    # Parse the full URL for display
    parsed = urllib.parse.urlparse(auth_url)
    params = urllib.parse.parse_qs(parsed.query)

    print(f"\n   Full Authorization URL (to open in browser):")
    print(f"   → {auth_url[:100]}...")

    print(f"\n   URL Parameters:")
    for key, value in params.items():
        if isinstance(value, list):
            value = value[0]
        if len(str(value)) > 50:
            print(f"      {key}: {str(value)[:50]}...")
        else:
            print(f"      {key}: {value}")

    print_section("STEP 3: USER AUTHENTICATION")

    print(f"\n   When user opens the authorization URL, they are redirected to:")

    # Extract domain from IDCS_AUTHORIZE_ENDPOINT
    idcs_domain = IDCS_AUTHORIZE_ENDPOINT.replace("https://", "").split("/")[0]
    print(f"   → {idcs_domain}/oauth2/v1/authorize?...")

    print(f"\n   The IDCS server then authenticates the user and redirects back to:")
    print(f"   → {redirect_uri}?code=AUTH_CODE&state=STATE")

    print_section("STEP 4: TOKEN EXCHANGE")

    print(f"\n   After getting authorization code, server exchanges it for token:")
    print(f"   → POST {IDCS_TOKEN_ENDPOINT}")
    print(f"      Parameters:")
    print(f"         grant_type: authorization_code")
    print(f"         code: [auth_code_from_redirect]")
    print(f"         client_id: {IDCS_CLIENT_ID}")
    print(f"         redirect_uri: {redirect_uri}")
    print(f"         code_verifier: [pkce_verifier]")

    print_section("CRITICAL DOMAIN INFORMATION")

    print(f"\n   ✓ IDCS Auth Domain:")
    print(f"     {IDCS_AUTHORIZE_ENDPOINT.split('/oauth2')[0]}")

    print(f"\n   ✓ IDCS Token Domain:")
    print(f"     {IDCS_TOKEN_ENDPOINT.split('/oauth2')[0]}")

    print(f"\n   ✓ OCA LiteLLM Domain:")
    llm_domain = _OCA_LITELLM_URL.replace("https://", "").replace("http://", "").split("/")[0]
    print(f"     {llm_domain}")

    print_section("EXPECTED REDIRECT FLOW")

    print(f"\n   1. Browser opens auth URL to IDCS domain")
    print(f"      → {idcs_domain}")

    print(f"\n   2. User authenticates on IDCS page")

    print(f"\n   3. IDCS redirects back to:")
    print(f"      → http://localhost:{port}/callback?code=...&state=...")

    print(f"\n   4. Server receives authorization code")

    print(f"\n   5. Server exchanges code for token with IDCS token endpoint")
    print(f"      → {IDCS_TOKEN_ENDPOINT.split('/oauth2')[0]}")

    print(f"\n   6. Token is stored in session")

    print(f"\n   7. Authentication complete! ✅")

    print_section("⚠️  TROUBLESHOOTING GUIDE")

    print(f"\n   If you're getting redirected to WRONG domain:")
    print(f"")
    print(f"   Current IDCS Domain: {idcs_domain}")
    print(f"")
    print(f"   This domain should match your OCA region: {_DETECTED_REGION}")
    print(f"")
    print(f"   If it doesn't, set OCA_IDCS_BASE_URL explicitly:")
    print(f"   ")
    print(f"   Example for different regions:")
    print(f"   - US Chicago:    OCA_IDCS_BASE_URL=https://idcs.us-chicago-1.oraclecloud.com")
    print(f"   - US Phoenix:    OCA_IDCS_BASE_URL=https://idcs.us-phoenix-1.oraclecloud.com")
    print(f"   - US Ashburn:    OCA_IDCS_BASE_URL=https://idcs.us-ashburn-1.oraclecloud.com")
    print(f"   - EU Frankfurt:  OCA_IDCS_BASE_URL=https://idcs.eu-frankfurt-1.oraclecloud.com")
    print(f"   - EU Zurich:     OCA_IDCS_BASE_URL=https://idcs.eu-zurich-1.oraclecloud.com")
    print(f"   - AP Sydney:     OCA_IDCS_BASE_URL=https://idcs.ap-sydney-1.oraclecloud.com")
    print(f"   - AP Tokyo:      OCA_IDCS_BASE_URL=https://idcs.ap-tokyo-1.oraclecloud.com")

    print("\n" + "█" * 70 + "\n")

if __name__ == "__main__":
    main()
