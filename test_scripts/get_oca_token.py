#!/usr/bin/env python3
"""
OCA Token CLI
Command-line interface for the Node.js server to fetch OCA tokens.

Usage:
    python3 get_oca_token.py              # Get token (JSON output)
    python3 get_oca_token.py --info       # Get token status info
    python3 get_oca_token.py --clear      # Clear cached tokens
    python3 get_oca_token.py --headless   # Force headless device code flow
"""
from __future__ import annotations

import argparse
import json
import os
import sys

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from auth_bridge.oca_auth import fetch_oca_token, get_token_info, clear_tokens, OCAAuthError
from auth_bridge.constants import OCA_LITELLM_URL


def main():
    parser = argparse.ArgumentParser(description="OCA Token Management CLI")
    parser.add_argument("--info", action="store_true", help="Show token status info")
    parser.add_argument("--clear", action="store_true", help="Clear cached tokens")
    parser.add_argument("--headless", action="store_true", help="Use headless device code flow")
    parser.add_argument("--json", action="store_true", help="Output as JSON (default)")
    parser.add_argument("--raw", action="store_true", help="Output raw token only")

    args = parser.parse_args()

    try:
        if args.clear:
            clear_tokens()
            output = {"success": True, "message": "Tokens cleared"}
            print(json.dumps(output))
            return 0

        if args.info:
            info = get_token_info()
            info["base_url"] = OCA_LITELLM_URL
            print(json.dumps(info, indent=2))
            return 0

        # Fetch token
        flow = "headless" if args.headless else None
        token = fetch_oca_token(flow=flow)

        if args.raw:
            print(token)
        else:
            output = {
                "success": True,
                "access_token": token,
                "base_url": OCA_LITELLM_URL,
                "token_info": get_token_info()
            }
            print(json.dumps(output))

        return 0

    except OCAAuthError as e:
        error_output = {
            "success": False,
            "error": str(e),
            "error_type": "OCAAuthError"
        }
        print(json.dumps(error_output), file=sys.stderr)
        return 1

    except Exception as e:
        error_output = {
            "success": False,
            "error": str(e),
            "error_type": type(e).__name__
        }
        print(json.dumps(error_output), file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
