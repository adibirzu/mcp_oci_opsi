#!/usr/bin/env python3
"""
Script to find the actual IDCS domain being used by your OCA setup.

This script tests various IDCS domain patterns to find which one resolves.
"""

import socket
import sys
from urllib.parse import urlparse

def test_domain(domain):
    """Test if a domain resolves via DNS."""
    try:
        ip = socket.gethostbyname(domain)
        return True, ip
    except socket.gaierror:
        return False, None

def main():
    # OCA region extracted from your LiteLLM URL
    region = "us-chicago-1"

    print("\n" + "=" * 70)
    print("  IDCS DOMAIN FINDER")
    print("=" * 70)

    print(f"\nSearching for IDCS domain patterns for region: {region}")
    print("\nTesting domain patterns:\n")

    # Common IDCS domain patterns for Oracle Cloud
    domain_patterns = [
        # Standard OCI IDCS pattern
        f"idcs.{region}.oraclecloud.com",

        # Regional IDCS pattern (without 'idcs' prefix)
        f"{region}.identity.oraclecloud.com",

        # Oracle Identity Cloud Service standard pattern
        f"identity.{region}.oraclecloud.com",

        # Older deprecated patterns
        f"idcs-{region}.identity.oraclecloud.com",
        f"{region}.idcs.oraclecloud.com",

        # Possible custom domain (if using non-standard setup)
        f"auth.{region}.oraclecloud.com",
        f"login.{region}.oraclecloud.com",
        f"oauth.{region}.oraclecloud.com",
    ]

    found_domains = []

    for domain in domain_patterns:
        print(f"Testing: {domain:<50}", end=" ... ")
        sys.stdout.flush()

        reachable, ip = test_domain(domain)
        if reachable:
            print(f"✓ FOUND! (resolves to {ip})")
            found_domains.append((domain, ip))
        else:
            print("✗ Not found")

    print("\n" + "=" * 70)

    if found_domains:
        print("\n✅ FOUND WORKING IDCS DOMAINS:\n")
        for domain, ip in found_domains:
            print(f"   Domain: {domain}")
            print(f"   IP: {ip}")
            print(f"   URL: https://{domain}\n")

        print("=" * 70)
        print("\n📋 RECOMMENDED NEXT STEPS:\n")
        print("1. Try authenticating with one of the found domains")
        print("2. Use environment variable to set the correct domain:")
        print(f"   OCA_IDCS_BASE_URL=https://{found_domains[0][0]}")
        print("\n3. Add to .env.local file and restart the application")

    else:
        print("\n❌ NO WORKING IDCS DOMAINS FOUND\n")
        print("The IDCS domain may be:")
        print("  1. In a different region than us-chicago-1")
        print("  2. Using a custom/non-standard domain")
        print("  3. Not publicly accessible from your network")
        print("\nTroubleshooting:")
        print("  - Check your OCA documentation for the correct IDCS endpoint")
        print("  - Ask your OCA administrator for the IDCS domain")
        print("  - Try setting OCA_IDCS_BASE_URL manually in .env.local")

    print("\n" + "=" * 70 + "\n")

if __name__ == "__main__":
    main()
