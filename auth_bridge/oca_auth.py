"""
OCA Authentication Module
Adapted from ocaider/providers/oca/oca_auth_utils_pkce.py

Provides OAuth PKCE and Device Code authentication flows for Oracle Code Assist.
"""
from __future__ import annotations

import base64
import hashlib
import http.server
import json
import os
import secrets
import socket
import socketserver
import sys
import threading
import time
import urllib.parse
import webbrowser
from typing import Any, Dict, Optional, Tuple

import requests

# Helper function to log to stderr (so stdout only contains JSON)
def log(*args, **kwargs):
    """Log to stderr instead of stdout to avoid breaking JSON output."""
    print(*args, file=sys.stderr, **kwargs)

from .constants import (
    IDCS_AUTHORIZE_ENDPOINT,
    IDCS_BASE_URL,
    IDCS_CLIENT_ID,
    IDCS_CLIENT_SECRET,
    IDCS_DEVICE_CODE_ENDPOINT,
    IDCS_TOKEN_ENDPOINT,
    OCA_AUTH_TIMEOUT,
    OCA_CALLBACK_PORT,
    OCA_DEFAULT_SCOPES,
    OCA_DEVICE_CODE_POLL_INTERVAL,
)
from .token_manager import token_manager


class OCAAuthError(Exception):
    """Custom exception for OCA authentication errors."""
    pass


class PKCEManager:
    """Handles PKCE (Proof Key for Code Exchange) authentication flow."""

    def __init__(self, redirect_uri: str):
        self.redirect_uri = redirect_uri
        self.code_verifier = self._generate_code_verifier()
        self.code_challenge = self._generate_code_challenge(self.code_verifier)
        self.state = secrets.token_urlsafe(32)
        self.nonce = secrets.token_urlsafe(32)  # Add nonce for OIDC compliance
        self.authorization_code: Optional[str] = None

    @staticmethod
    def _generate_code_verifier() -> str:
        """Generate a cryptographically random code verifier."""
        return secrets.token_urlsafe(64)[:128]

    @staticmethod
    def _generate_code_challenge(verifier: str) -> str:
        """Generate code challenge from verifier using S256 method."""
        digest = hashlib.sha256(verifier.encode("utf-8")).digest()
        return base64.urlsafe_b64encode(digest).rstrip(b"=").decode("utf-8")

    def get_authorization_url(self) -> str:
        """Build the authorization URL for browser redirect."""
        params = {
            "response_type": "code",
            "client_id": IDCS_CLIENT_ID,
            "redirect_uri": self.redirect_uri,
            "scope": OCA_DEFAULT_SCOPES,
            "state": self.state,
            "code_challenge": self.code_challenge,
            "code_challenge_method": "S256",
            "nonce": self.nonce,  # Add nonce for OIDC compliance (matches CLINE)
        }
        return f"{IDCS_AUTHORIZE_ENDPOINT}?{urllib.parse.urlencode(params)}"

    def exchange_code_for_token(self, code: str) -> Dict[str, Any]:
        """Exchange authorization code for access token."""
        data = {
            "grant_type": "authorization_code",
            "client_id": IDCS_CLIENT_ID,
            "code": code,
            "redirect_uri": self.redirect_uri,
            "code_verifier": self.code_verifier,
        }

        # Build headers - use Basic Auth if client_secret is configured (confidential client)
        headers = {"Content-Type": "application/x-www-form-urlencoded"}
        if IDCS_CLIENT_SECRET:
            # Confidential client: use Basic Auth with client_id:client_secret
            auth_string = f"{IDCS_CLIENT_ID}:{IDCS_CLIENT_SECRET}"
            auth_header = base64.b64encode(auth_string.encode("utf-8")).decode("utf-8")
            headers["Authorization"] = f"Basic {auth_header}"
            log(f"[OCA Auth] Using Confidential Client authentication (Basic Auth)")
        else:
            # Public client: no Basic Auth, client_id only in form data (PKCE standard)
            log(f"[OCA Auth] Using Public Client authentication (PKCE, no Basic Auth)")

        # Log request details for debugging
        log(f"[OCA Auth] Token exchange request:")
        log(f"  Endpoint: {IDCS_TOKEN_ENDPOINT}")
        log(f"  Client ID: {IDCS_CLIENT_ID}")
        log(f"  Redirect URI: {self.redirect_uri}")
        log(f"  Using Basic Auth: {bool(IDCS_CLIENT_SECRET)}")
        log(f"  Grant Type: authorization_code")
        
        response = requests.post(
            IDCS_TOKEN_ENDPOINT,
            data=data,
            headers=headers,
            timeout=30,
        )

        if not response.ok:
            error_text = response.text
            try:
                error_json = response.json()
                error_msg = error_json.get("error_description", error_json.get("error", error_text))
                error_code = error_json.get("error", "")
            except:
                error_msg = error_text
                error_code = ""
            
            # Log detailed error for debugging
            log(f"[OCA Auth] ❌ Token exchange failed:")
            log(f"  Status: {response.status_code}")
            log(f"  Error Code: {error_code}")
            log(f"  Error Message: {error_msg}")
            log(f"  Full Response: {error_text[:500]}")
            
            # Special handling for invalid_client error
            if error_code == "invalid_client":
                log(f"[OCA Auth] 💡 Troubleshooting 'invalid_client' error:")
                log(f"  1. Verify IDCS endpoint is correct: {IDCS_BASE_URL}")
                log(f"  2. Verify client_id '{IDCS_CLIENT_ID}' is registered in IDCS")
                log(f"  3. Check if client is configured as Public or Confidential")
                log(f"  4. For Public Client: ensure OCA_CLIENT_SECRET is NOT set")
                log(f"  5. For Confidential Client: set OCA_CLIENT_SECRET environment variable")
                log(f"  6. Verify redirect_uri '{self.redirect_uri}' is registered in IDCS")
            
            raise OCAAuthError(f"Token exchange failed: {response.status_code} - {error_msg}")

        return response.json()


class DeviceCodeManager:
    """Handles Device Code authentication flow for headless environments."""

    def start_device_authorization(self) -> Dict[str, Any]:
        """Request device code from IDCS."""
        data = {
            "client_id": IDCS_CLIENT_ID,
            "scope": OCA_DEFAULT_SCOPES,
        }

        response = requests.post(
            IDCS_DEVICE_CODE_ENDPOINT,
            data=data,
            headers={"Content-Type": "application/x-www-form-urlencoded"},
            timeout=30,
        )

        if not response.ok:
            raise OCAAuthError(f"Device authorization failed: {response.status_code} - {response.text}")

        return response.json()

    def poll_for_token(
        self,
        device_code: str,
        expires_in: int,
        interval: Optional[int] = None,
    ) -> Dict[str, Any]:
        """Poll for token after user completes authorization."""
        poll_interval = interval or OCA_DEVICE_CODE_POLL_INTERVAL
        deadline = time.time() + expires_in

        while time.time() < deadline:
            time.sleep(poll_interval)

            data = {
                "grant_type": "urn:ietf:params:oauth:grant-type:device_code",
                "device_code": device_code,
                "client_id": IDCS_CLIENT_ID,
            }

            # Build headers - use Basic Auth if client_secret is configured
            headers = {"Content-Type": "application/x-www-form-urlencoded"}
            if IDCS_CLIENT_SECRET:
                auth_string = f"{IDCS_CLIENT_ID}:{IDCS_CLIENT_SECRET}"
                auth_header = base64.b64encode(auth_string.encode("utf-8")).decode("utf-8")
                headers["Authorization"] = f"Basic {auth_header}"
            
            response = requests.post(
                IDCS_TOKEN_ENDPOINT,
                data=data,
                headers=headers,
                timeout=30,
            )

            if response.ok:
                return response.json()

            error_data = response.json()
            error = error_data.get("error", "")

            if error == "authorization_pending":
                continue
            elif error == "slow_down":
                poll_interval += 5
                continue
            else:
                raise OCAAuthError(f"Device code polling failed: {error}")

        raise OCAAuthError("Device code authorization timed out")


class OAuthCallbackHandler(http.server.BaseHTTPRequestHandler):
    """HTTP handler for OAuth callback."""

    def log_message(self, format: str, *args) -> None:
        """Suppress logging."""
        pass

    def do_GET(self) -> None:
        """Handle OAuth callback GET request."""
        parsed = urllib.parse.urlparse(self.path)
        
        # Log all incoming requests for debugging
        log(f"[OCA Auth] Received callback request: {self.path}")

        # Support both /callback and /auth/oca paths for compatibility
        if parsed.path == "/callback" or parsed.path == "/auth/oca":
            query = urllib.parse.parse_qs(parsed.query)

            if "code" in query:
                log("[OCA Auth] ✅ Authorization code received!")
                self.server.auth_code = query["code"][0]  # type: ignore
                self.server.auth_state = query.get("state", [None])[0]  # type: ignore
                self._send_success_response()
            elif "error" in query:
                error = query["error"][0]  # type: ignore
                error_desc = query.get("error_description", ["Unknown error"])[0]  # type: ignore
                log(f"[OCA Auth] ❌ OAuth error received: {error} - {error_desc}")
                self.server.auth_error = error  # type: ignore
                self._send_error_response(error_desc)
            else:
                log("[OCA Auth] ⚠️ Callback received but no code or error parameter")
                self._send_error_response("No authorization code received")
        else:
            log(f"[OCA Auth] ⚠️ Unexpected callback path: {parsed.path}")
            self.send_error(404)

    def _send_success_response(self) -> None:
        """Send success HTML page."""
        self.send_response(200)
        self.send_header("Content-type", "text/html")
        self.end_headers()
        html = """
        <!DOCTYPE html>
        <html>
        <head><title>Authentication Successful</title></head>
        <body style="font-family: sans-serif; text-align: center; padding: 50px;">
            <h1 style="color: #28a745;">✅ Authentication Successful!</h1>
            <p>You can close this window and return to the application.</p>
        </body>
        </html>
        """
        self.wfile.write(html.encode())

    def _send_error_response(self, error: str) -> None:
        """Send error HTML page."""
        self.send_response(400)
        self.send_header("Content-type", "text/html")
        self.end_headers()
        html = f"""
        <!DOCTYPE html>
        <html>
        <head><title>Authentication Failed</title></head>
        <body style="font-family: sans-serif; text-align: center; padding: 50px;">
            <h1 style="color: #dc3545;">❌ Authentication Failed</h1>
            <p>{error}</p>
        </body>
        </html>
        """
        self.wfile.write(html.encode())


class OAuthCallbackServer:
    """HTTP server to handle OAuth callback."""

    def __init__(self, port: int, pkce_manager: PKCEManager):
        self.port = port
        self.pkce_manager = pkce_manager
        self.server: Optional[socketserver.TCPServer] = None
        self.thread: Optional[threading.Thread] = None

    @staticmethod
    def find_available_port(start: int = 8400, end: int = 8500) -> int:
        """Find an available port in the given range."""
        import socket
        for port in range(start, end):
            try:
                with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                    s.bind(("127.0.0.1", port))
                    return port
            except OSError:
                continue
        raise OCAAuthError(f"No available port found in range {start}-{end}")

    def start(self) -> None:
        """Start the callback server in a background thread."""
        class CallbackServer(socketserver.TCPServer):
            allow_reuse_address = True
            auth_code: Optional[str] = None
            auth_state: Optional[str] = None
            auth_error: Optional[str] = None

        self.server = CallbackServer(("localhost", self.port), OAuthCallbackHandler)
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()
        
        # Give the server a moment to start listening
        time.sleep(0.1)
        
        # Verify server is actually listening
        try:
            test_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            test_socket.settimeout(1)
            result = test_socket.connect_ex(("localhost", self.port))
            test_socket.close()
            if result == 0:
                log(f"[OCA Auth] ✅ Callback server listening on http://127.0.0.1:{self.port}/auth/oca")
            else:
                log(f"[OCA Auth] ⚠️ Warning: Callback server may not be listening properly")
        except Exception as e:
            log(f"[OCA Auth] ⚠️ Warning: Could not verify callback server: {e}")

    def wait_for_token(self, timeout: int = OCA_AUTH_TIMEOUT) -> Dict[str, Any]:
        """Wait for user to complete authorization and return token."""
        deadline = time.time() + timeout
        last_status_time = time.time()
        status_interval = 30  # Print status every 30 seconds

        while time.time() < deadline:
            if self.server and self.server.auth_code:  # type: ignore
                # Validate state
                if self.server.auth_state != self.pkce_manager.state:  # type: ignore
                    raise OCAAuthError("OAuth state mismatch - possible CSRF attack")

                # Exchange code for token
                return self.pkce_manager.exchange_code_for_token(self.server.auth_code)  # type: ignore

            if self.server and self.server.auth_error:  # type: ignore
                raise OCAAuthError(f"OAuth error: {self.server.auth_error}")  # type: ignore

            # Print status periodically
            now = time.time()
            if now - last_status_time >= status_interval:
                remaining = int(deadline - now)
                log(f"[OCA Auth] Waiting for authentication... ({remaining}s remaining)")
                log(f"[OCA Auth] Make sure you complete login in the browser and are redirected to: http://127.0.0.1:{self.port}/auth/oca")
                last_status_time = now

            time.sleep(0.5)

        raise OCAAuthError(
            f"Authorization timed out after {timeout} seconds. "
            f"Please ensure:\n"
            f"  1. The browser opened and you completed login\n"
            f"  2. You were redirected to: http://127.0.0.1:{self.port}/auth/oca\n"
            f"  3. The redirect URI matches your IDCS application configuration"
        )

    def shutdown(self) -> None:
        """Shutdown the callback server."""
        if self.server:
            self.server.shutdown()


def fetch_oca_token(flow: Optional[str] = None) -> str:
    """
    Fetch a valid OCA access token.

    Attempts to use cached token, refresh if possible, or initiate new OAuth flow.

    Args:
        flow: Authentication flow type - "pc" for browser PKCE, "headless" for device code.
              Defaults to OCA_AUTH_FLOW environment variable or "pc".

    Returns:
        Valid access token string.

    Raises:
        OCAAuthError: If authentication fails.
    """
    now = time.time()

    # Check for valid cached token
    if token_manager.has_valid_token(now):
        return token_manager.access_token()

    # Try to refresh existing token
    if token_manager.can_refresh(now):
        try:
            # Simple refresh using requests (no authlib session needed for refresh)
            refresh_tok = token_manager.refresh_token_value()
            data = {
                "grant_type": "refresh_token",
                "client_id": IDCS_CLIENT_ID,
                "refresh_token": refresh_tok,
            }
            
            # Build headers - use Basic Auth if client_secret is configured
            headers = {"Content-Type": "application/x-www-form-urlencoded"}
            if IDCS_CLIENT_SECRET:
                auth_string = f"{IDCS_CLIENT_ID}:{IDCS_CLIENT_SECRET}"
                auth_header = base64.b64encode(auth_string.encode("utf-8")).decode("utf-8")
                headers["Authorization"] = f"Basic {auth_header}"
            
            response = requests.post(
                IDCS_TOKEN_ENDPOINT,
                data=data,
                headers=headers,
                timeout=30,
            )
            if response.ok:
                token_manager.cache_token(response.json())
                return token_manager.access_token()
        except Exception as e:
            log(f"[OCA Auth] Token refresh failed: {e}")

    # Determine flow type
    auth_flow = (flow or os.getenv("OCA_AUTH_FLOW", "pc")).lower()

    if auth_flow == "headless":
        return _authenticate_device_code()
    else:
        return _authenticate_pkce()


def _authenticate_pkce() -> str:
    """Authenticate using browser-based PKCE flow."""
    # Use fixed port from config (default 48801 to match CLINE)
    # This must match the redirect URI registered in IDCS
    port = OCA_CALLBACK_PORT
    
    # Try to bind to the configured port first
    try:
        import socket
        test_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        test_socket.settimeout(1)
        result = test_socket.connect_ex(("127.0.0.1", port))
        test_socket.close()
        if result == 0:
            # Port is in use, try to find another one
            log(f"[OCA Auth] ⚠️  Port {port} is in use, trying to find available port...")
            port = OAuthCallbackServer.find_available_port(start=8400, end=8500)
            log(f"[OCA Auth] ⚠️  WARNING: Using port {port} instead of {OCA_CALLBACK_PORT}")
            log(f"[OCA Auth] ⚠️  This may cause redirect_uri mismatch if IDCS expects port {OCA_CALLBACK_PORT}")
    except Exception:
        # If check fails, just use the configured port
        pass
    
    # Use 127.0.0.1 and /auth/oca path to match CLINE's redirect URI pattern
    redirect_uri = f"http://127.0.0.1:{port}/auth/oca"
    log(f"[OCA Auth] Using redirect URI: {redirect_uri}")

    pkce_manager = PKCEManager(redirect_uri)
    callback_server = OAuthCallbackServer(port, pkce_manager)

    try:
        callback_server.start()
        auth_url = pkce_manager.get_authorization_url()

        log("\n" + "=" * 70)
        log("[OCA Auth] Starting PKCE Authentication Flow")
        log("=" * 70)
        log(f"[OCA Auth] Callback URL: {redirect_uri}")
        log(f"[OCA Auth] Opening browser for authentication...")
        log(f"[OCA Auth] If browser doesn't open, visit this URL manually:")
        log(f"[OCA Auth] {auth_url}")
        log(f"[OCA Auth] Waiting up to {OCA_AUTH_TIMEOUT} seconds for authentication...")
        log("=" * 70 + "\n")

        # Open browser in background thread
        try:
            webbrowser.open_new_tab(auth_url)
        except Exception as e:
            log(f"[OCA Auth] Warning: Could not open browser automatically: {e}")
            log(f"[OCA Auth] Please open this URL manually: {auth_url}")

        # Wait for callback
        token_response = callback_server.wait_for_token()
        token_manager.cache_token(token_response)

        log("\n[OCA Auth] ✅ Authentication successful!")
        return token_manager.access_token()

    except OCAAuthError as e:
        log(f"\n[OCA Auth] ❌ Authentication failed: {e}")
        raise
    except Exception as e:
        log(f"\n[OCA Auth] ❌ Unexpected error: {e}")
        raise OCAAuthError(f"Authentication failed: {e}")
    finally:
        callback_server.shutdown()


def _authenticate_device_code() -> str:
    """Authenticate using device code flow (for headless environments)."""
    device_mgr = DeviceCodeManager()

    auth = device_mgr.start_device_authorization()

    log("\n" + "=" * 60)
    log("[OCA Auth] Device Code Authentication")
    log("=" * 60)
    log(f"\n📱 Open this URL: {auth.get('verification_uri', auth.get('verification_uri_complete', ''))}")
    log(f"🔑 Enter code: {auth.get('user_code', 'N/A')}")
    log("\nWaiting for authorization...")
    log("=" * 60 + "\n")

    token_response = device_mgr.poll_for_token(
        device_code=auth["device_code"],
        expires_in=auth.get("expires_in", 600),
        interval=auth.get("interval"),
    )

    token_manager.cache_token(token_response)
    log("[OCA Auth] ✅ Authentication successful!")
    return token_manager.access_token()


def get_token_info() -> Dict[str, Any]:
    """Get current token status information."""
    return token_manager.get_token_info()


def clear_tokens() -> None:
    """Clear all cached tokens (logout)."""
    token_manager.clear()
    log("[OCA Auth] Tokens cleared.")
