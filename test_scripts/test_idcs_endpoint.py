#!/usr/bin/env python3
"""
Test if the IDCS endpoint is reachable and working.

Usage:
    python3 test_idcs_endpoint.py
"""

import os
import sys
import requests
from urllib.parse import urlparse

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from auth_bridge.constants import (
    IDCS_AUTHORIZE_ENDPOINT,
    IDCS_TOKEN_ENDPOINT,
    IDCS_BASE_URL,
    _DETECTED_REGION,
    _OCA_LITELLM_URL,
)

def test_endpoint(url, method="GET", name="Endpoint"):
    """Test if an endpoint is reachable."""
    try:
        if method == "GET":
            response = requests.head(url, timeout=5, allow_redirects=False)
        else:
            response = requests.options(url, timeout=5, allow_redirects=False)

        status = response.status_code
        reason = response.reason

        # 4xx/5xx with meaningful message = endpoint exists but needs auth/params
        # 404 = endpoint doesn't exist
        # Connection error = domain doesn't exist

        if status == 404:
            return (False, f"❌ Not found (404)")
        elif status == 401 or status == 400:
            return (True, f"✓ Reachable ({status} {reason}) - needs auth/params")
        elif 200 <= status < 300:
            return (True, f"✓ OK ({status})")
        else:
            return (True, f"✓ Reachable ({status} {reason})")

    except requests.exceptions.ConnectionError as e:
        return (False, f"❌ DNS/Connection error - domain not reachable")
    except requests.exceptions.Timeout:
        return (False, f"❌ Timeout - endpoint not responding")
    except Exception as e:
        return (False, f"❌ Error: {str(e)[:60]}")

def print_header(title):
    print("\n" + "=" * 70)
    print(f"  {title}")
    print("=" * 70)

def main():
    print_header("IDCS ENDPOINT REACHABILITY TEST")

    print(f"\n📍 Configuration:")
    print(f"   Detected Region: {_DETECTED_REGION}")
    print(f"   IDCS Base URL: {IDCS_BASE_URL}")
    print(f"   OCA LiteLLM URL: {_OCA_LITELLM_URL}")

    print_header("Testing Endpoints")

    # Test IDCS Base URL
    print(f"\n1. IDCS Base URL")
    print(f"   URL: {IDCS_BASE_URL}")
    reachable, msg = test_endpoint(IDCS_BASE_URL)
    print(f"   Result: {msg}")

    # Test Authorization Endpoint
    print(f"\n2. Authorization Endpoint")
    print(f"   URL: {IDCS_AUTHORIZE_ENDPOINT}")
    reachable, msg = test_endpoint(IDCS_AUTHORIZE_ENDPOINT)
    print(f"   Result: {msg}")

    # Test Token Endpoint
    print(f"\n3. Token Endpoint")
    print(f"   URL: {IDCS_TOKEN_ENDPOINT}")
    reachable, msg = test_endpoint(IDCS_TOKEN_ENDPOINT, method="POST")
    print(f"   Result: {msg}")

    # Extract and test domain
    print_header("Domain Analysis")

    idcs_domain = urlparse(IDCS_BASE_URL).netloc
    print(f"\n   IDCS Domain: {idcs_domain}")
    print(f"   Expected pattern: idcs.<region>.oraclecloud.com")

    if "idcs." in idcs_domain and ".oraclecloud.com" in idcs_domain:
        print(f"   ✓ Correct IDCS domain format")
    else:
        print(f"   ⚠️  WARNING: Non-standard IDCS domain")

    # DNS test
    print_header("DNS Validation")

    import socket
    try:
        ip = socket.gethostbyname(idcs_domain)
        print(f"\n   Domain: {idcs_domain}")
        print(f"   ✓ DNS resolves to: {ip}")
    except socket.gaierror:
        print(f"\n   Domain: {idcs_domain}")
        print(f"   ❌ DNS DOES NOT RESOLVE - DOMAIN NOT FOUND!")
        print(f"")
        print(f"   This is the problem! The IDCS domain is incorrect.")
        print(f"")
        print(f"   Solution: Check what domain is actually used in your OCA setup.")
        print(f"   ")
        print(f"   Options:")
        print(f"   1. Use environment variable: OCA_IDCS_BASE_URL=https://idcs.<correct-region>.oraclecloud.com")
        print(f"   2. Check OCA documentation for your region's IDCS endpoint")

    print_header("Recommended Next Steps")

    print(f"\n   If endpoints are NOT reachable:")
    print(f"")
    print(f"   1. Run: python3 debug_oca_config.py")
    print(f"      → Shows current configuration")
    print(f"")
    print(f"   2. Run: python3 trace_auth_flow.py")
    print(f"      → Shows the auth flow without authenticating")
    print(f"")
    print(f"   3. Check which IDCS domain your OCA actually uses:")
    print(f"      → Look at OCA setup/documentation")
    print(f"      → Or check logs when OCA redirects you")
    print(f"")
    print(f"   4. Set OCA_IDCS_BASE_URL if different from detected region:")
    print(f"      → Add to .env.local: OCA_IDCS_BASE_URL=https://idcs.<correct-region>.oraclecloud.com")

    print("\n" + "=" * 70 + "\n")

if __name__ == "__main__":
    main()
