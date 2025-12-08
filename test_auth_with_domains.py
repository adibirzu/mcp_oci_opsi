#!/usr/bin/env python3
"""
Test which IDCS domain actually works for OAuth token exchange.
"""

import requests
import json

def test_token_endpoint(domain_base):
    """Test token endpoint with a dummy authorization code."""
    token_url = f"https://{domain_base}/oauth2/v1/token"

    # This will obviously fail (invalid code) but we want to see if the endpoint exists
    data = {
        "grant_type": "authorization_code",
        "client_id": "oca-cli",
        "code": "invalid-test-code",
        "redirect_uri": "http://localhost:8400/callback",
        "code_verifier": "test",
    }

    print(f"\nTesting token endpoint: {token_url}")
    print("=" * 70)

    try:
        response = requests.post(
            token_url,
            data=data,
            headers={"Content-Type": "application/x-www-form-urlencoded"},
            timeout=5,
        )

        print(f"Status Code: {response.status_code}")
        print(f"Response Headers:")
        for key, value in response.headers.items():
            if key.lower() in ['content-type', 'server', 'x-frame-options']:
                print(f"  {key}: {value}")

        if response.text:
            try:
                body = json.loads(response.text)
                print(f"\nResponse Body:")
                print(f"  {json.dumps(body, indent=2)}")
            except:
                print(f"\nResponse Body (raw):")
                print(f"  {response.text[:200]}")

        # Analyze the response
        if response.status_code == 404:
            print("\n❌ Endpoint does NOT exist (404)")
            return False

        elif response.status_code == 400:
            # 400 Bad Request is good! It means the endpoint exists but our request was invalid
            if "error" in response.text:
                print("\n✅ Endpoint EXISTS - rejected our test request (as expected)")
                return True
            else:
                print("\n⚠️  Unclear response")
                return None

        elif response.status_code == 401:
            # Unauthorized is also good - endpoint exists
            print("\n✅ Endpoint EXISTS - authentication failed (as expected)")
            return True

        elif response.status_code in [200, 201]:
            print("\n⚠️  Unexpected success response")
            return True

        else:
            print(f"\n⚠️  Unexpected status: {response.status_code}")
            return None

    except requests.exceptions.ConnectionError as e:
        print(f"\n❌ Connection error - domain not reachable")
        print(f"   Error: {str(e)[:100]}")
        return False

    except requests.exceptions.Timeout:
        print(f"\n⏱️  Timeout - domain may not be accessible")
        return None

    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        return None

def main():
    print("\n" + "=" * 70)
    print("  TOKEN ENDPOINT REACHABILITY TEST")
    print("=" * 70)

    candidates = [
        # The domain that should work based on region
        "identity.us-chicago-1.oraclecloud.com",
        "auth.us-chicago-1.oraclecloud.com",
        "login.us-chicago-1.oraclecloud.com",

        # Try some other patterns for IDCS
        "idcs.us-chicago-1.oraclecloud.com",
        "iam.us-chicago-1.oraclecloud.com",
    ]

    results = {}
    for domain in candidates:
        result = test_token_endpoint(domain)
        results[domain] = result

    # Summary
    print("\n" + "=" * 70)
    print("SUMMARY")
    print("=" * 70)

    working = [d for d, r in results.items() if r is True]
    maybe = [d for d, r in results.items() if r is None]
    failed = [d for d, r in results.items() if r is False]

    if working:
        print(f"\n✅ Endpoints that EXIST:\n")
        for domain in working:
            print(f"   https://{domain}/oauth2/v1/token")

    if maybe:
        print(f"\n⚠️  Unclear (may need closer inspection):\n")
        for domain in maybe:
            print(f"   https://{domain}/oauth2/v1/token")

    if failed:
        print(f"\n❌ Endpoints that DON'T exist:\n")
        for domain in failed:
            print(f"   https://{domain}/oauth2/v1/token")

    print("\n" + "=" * 70 + "\n")

if __name__ == "__main__":
    main()
