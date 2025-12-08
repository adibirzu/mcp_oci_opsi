#!/usr/bin/env python3
"""
Test OAuth endpoints on the found IDCS domains to find the correct one.
"""

import requests

def test_oauth_endpoint(domain_base):
    """Test if OAuth endpoints exist on a domain."""
    endpoints = [
        (f"https://{domain_base}/oauth2/v1/authorize", "Authorization"),
        (f"https://{domain_base}/oauth2/v1/token", "Token"),
        (f"https://{domain_base}/.well-known/openid-configuration", "OpenID Config"),
    ]

    print(f"\n{'=' * 70}")
    print(f"Testing: {domain_base}")
    print('=' * 70)

    working_endpoints = 0

    for endpoint, name in endpoints:
        try:
            response = requests.head(endpoint, timeout=5, allow_redirects=False)
            status = response.status_code
            reason = response.reason

            # Check if endpoint exists
            if status == 404:
                print(f"  {name:<20} → ✗ Not found (404)")
            elif status == 401 or status == 400:
                print(f"  {name:<20} → ✓ Exists ({status} - needs auth)")
                working_endpoints += 1
            elif 200 <= status < 300:
                print(f"  {name:<20} → ✓ OK ({status})")
                working_endpoints += 1
            else:
                print(f"  {name:<20} → ? ({status} {reason})")

        except requests.exceptions.ConnectionError:
            print(f"  {name:<20} → ✗ Connection error")
        except requests.exceptions.Timeout:
            print(f"  {name:<20} → ✗ Timeout")
        except Exception as e:
            print(f"  {name:<20} → ✗ Error: {str(e)[:40]}")

    return working_endpoints > 0

def main():
    print("\n" + "=" * 70)
    print("  OAUTH ENDPOINT TESTER")
    print("=" * 70)

    candidates = [
        "identity.us-chicago-1.oraclecloud.com",
        "auth.us-chicago-1.oraclecloud.com",
        "login.us-chicago-1.oraclecloud.com",
    ]

    print("\nTesting OAuth endpoints on each candidate domain:\n")

    working_domains = []
    for domain in candidates:
        if test_oauth_endpoint(domain):
            working_domains.append(domain)

    print("\n" + "=" * 70)
    print("RESULTS")
    print("=" * 70)

    if working_domains:
        print(f"\n✅ Found {len(working_domains)} domain(s) with OAuth endpoints:\n")
        for domain in working_domains:
            print(f"   https://{domain}")
            print(f"   Authorization: https://{domain}/oauth2/v1/authorize")
            print(f"   Token: https://{domain}/oauth2/v1/token\n")

        print("=" * 70)
        print("\n📋 RECOMMENDED ACTION:\n")
        print(f"Update your .env file with:")
        print(f"   OCA_IDCS_BASE_URL=https://{working_domains[0]}\n")

    else:
        print("\n❌ No domains with OAuth endpoints found")
        print("The IDCS domain may use a different OAuth endpoint structure")

    print("=" * 70 + "\n")

if __name__ == "__main__":
    main()
