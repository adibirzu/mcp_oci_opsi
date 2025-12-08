#!/usr/bin/env python3
"""
Debug script to inspect OCA authentication configuration.
Run this to see what domains and endpoints are being used.

Usage:
    python3 debug_oca_config.py
"""

import os
import sys

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from auth_bridge.constants import (
    _OCA_LITELLM_URL,
    _DETECTED_REGION,
    IDCS_BASE_URL,
    IDCS_AUTHORIZE_ENDPOINT,
    IDCS_TOKEN_ENDPOINT,
    IDCS_DEVICE_CODE_ENDPOINT,
    IDCS_USERINFO_ENDPOINT,
    IDCS_CLIENT_ID,
    OCA_LITELLM_URL,
)

def print_header(title):
    """Print a formatted header."""
    print("\n" + "=" * 70)
    print(f"  {title}")
    print("=" * 70)

def main():
    print_header("OCA Authentication Configuration Debug")

    print("\n📌 CONFIGURATION SOURCES:")
    print(f"  OCA_LITELLM_URL env var:     {os.getenv('OCA_LITELLM_URL', '(not set)')}")
    print(f"  OCA_IDCS_BASE_URL env var:   {os.getenv('OCA_IDCS_BASE_URL', '(not set)')}")

    print_header("DETECTED VALUES")
    print(f"\n🔍 LiteLLM URL (used for region extraction):")
    print(f"   {_OCA_LITELLM_URL}")

    print(f"\n📍 Detected Region:")
    print(f"   {_DETECTED_REGION}")

    print(f"\n🌐 IDCS Base URL:")
    print(f"   {IDCS_BASE_URL}")

    print_header("OAUTH ENDPOINTS")

    print(f"\n🔐 Authorization Endpoint:")
    print(f"   {IDCS_AUTHORIZE_ENDPOINT}")

    print(f"\n🔑 Token Endpoint:")
    print(f"   {IDCS_TOKEN_ENDPOINT}")

    print(f"\n📱 Device Code Endpoint:")
    print(f"   {IDCS_DEVICE_CODE_ENDPOINT}")

    print(f"\n👤 User Info Endpoint:")
    print(f"   {IDCS_USERINFO_ENDPOINT}")

    print_header("CLIENT CONFIGURATION")

    print(f"\n🆔 OCA Client ID:")
    print(f"   {IDCS_CLIENT_ID}")

    print(f"\n🔗 OCA LiteLLM URL (public constant):")
    print(f"   {OCA_LITELLM_URL}")

    print_header("DOMAIN MAPPING")

    # Extract domain from IDCS_BASE_URL
    idcs_domain = IDCS_BASE_URL.replace("https://", "").replace("http://", "").rstrip("/")
    llm_domain = _OCA_LITELLM_URL.replace("https://", "").replace("http://", "").split("/")[0]

    print(f"\n🌍 IDCS Domain (for auth):")
    print(f"   {idcs_domain}")

    print(f"\n🌍 LiteLLM Domain (for API):")
    print(f"   {llm_domain}")

    print_header("VERIFICATION")

    print(f"\n✅ Region Detection:")
    if _DETECTED_REGION != "us-chicago-1":
        print(f"   ✓ Custom region detected: {_DETECTED_REGION}")
    else:
        print(f"   ✓ Using default region: {_DETECTED_REGION}")

    print(f"\n✅ IDCS Endpoint:")
    if IDCS_BASE_URL == f"https://idcs.{_DETECTED_REGION}.oraclecloud.com":
        print(f"   ✓ Correctly constructed from region")
    else:
        print(f"   ✓ Manually overridden")

    print(f"\n✅ Domain Format:")
    if "idcs." in IDCS_BASE_URL and ".oraclecloud.com" in IDCS_BASE_URL:
        print(f"   ✓ Valid IDCS domain format")
    else:
        print(f"   ⚠️  WARNING: Non-standard IDCS domain format!")

    print("\n" + "=" * 70)
    print("\n✨ Use these endpoints for OCA authentication flow:")
    print(f"   Authorization URL: {IDCS_AUTHORIZE_ENDPOINT}")
    print(f"   Token URL: {IDCS_TOKEN_ENDPOINT}")
    print("\n" + "=" * 70 + "\n")

if __name__ == "__main__":
    main()
