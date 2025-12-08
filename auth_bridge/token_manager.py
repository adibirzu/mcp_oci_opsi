"""
Token Manager for OCA Authentication
Adapted from ocaider/_token_manager.py for the Oracle DB Autonomous Agent.

Handles secure storage, caching, and refresh of OAuth tokens.
"""
from __future__ import annotations

import json
import os
import sys
import time
from pathlib import Path
from typing import Any, Dict, Optional

# Helper function to log to stderr (so stdout only contains JSON)
def log(*args, **kwargs):
    """Log to stderr instead of stdout to avoid breaking JSON output."""
    print(*args, file=sys.stderr, **kwargs)

# Token cache location
_TOKEN_CACHE_DIR = Path.home() / ".oracle-db-agent" / "auth"
_TOKEN_CACHE_FILE = _TOKEN_CACHE_DIR / "oca_tokens.json"

# Buffer time before expiry to trigger refresh (5 minutes)
_REFRESH_BUFFER_SECONDS = 300


class TokenManager:
    """
    Manages OAuth tokens for Oracle Code Assist.
    Provides caching, validation, and refresh capabilities.
    """

    def __init__(self):
        self._tokens: Dict[str, Any] = {}
        self._load_from_cache()

    def _load_from_cache(self) -> None:
        """Load tokens from disk cache if available."""
        if _TOKEN_CACHE_FILE.exists():
            try:
                with open(_TOKEN_CACHE_FILE, "r") as f:
                    self._tokens = json.load(f)
            except (json.JSONDecodeError, IOError) as e:
                log(f"[TokenManager] Warning: Could not load token cache: {e}")
                self._tokens = {}

    def _save_to_cache(self) -> None:
        """Persist tokens to disk cache."""
        try:
            _TOKEN_CACHE_DIR.mkdir(parents=True, exist_ok=True)
            # Secure file permissions (owner read/write only)
            with open(_TOKEN_CACHE_FILE, "w") as f:
                json.dump(self._tokens, f, indent=2)
            os.chmod(_TOKEN_CACHE_FILE, 0o600)
        except IOError as e:
            log(f"[TokenManager] Warning: Could not save token cache: {e}")

    def has_valid_token(self, now: Optional[float] = None) -> bool:
        """Check if we have a valid (non-expired) access token."""
        if now is None:
            now = time.time()
        
        access_token = self._tokens.get("access_token")
        expires_at = self._tokens.get("expires_at", 0)
        
        if not access_token:
            return False
        
        # Consider token invalid if within refresh buffer of expiry
        return expires_at > (now + _REFRESH_BUFFER_SECONDS)

    def can_refresh(self, now: Optional[float] = None) -> bool:
        """Check if we have a refresh token that can be used."""
        if now is None:
            now = time.time()
        
        refresh_token = self._tokens.get("refresh_token")
        refresh_expires_at = self._tokens.get("refresh_expires_at", float("inf"))
        
        if not refresh_token:
            return False
        
        return refresh_expires_at > now

    def access_token(self) -> str:
        """Return the current access token."""
        return self._tokens.get("access_token", "")

    def refresh_token_value(self) -> str:
        """Return the current refresh token."""
        return self._tokens.get("refresh_token", "")

    def cache_token(self, token_response: Dict[str, Any]) -> None:
        """
        Store a new token response from OAuth flow.
        
        Args:
            token_response: OAuth token response containing access_token,
                          refresh_token, expires_in, etc.
        """
        now = time.time()
        
        self._tokens = {
            "access_token": token_response.get("access_token", ""),
            "refresh_token": token_response.get("refresh_token", ""),
            "token_type": token_response.get("token_type", "Bearer"),
            "expires_at": now + token_response.get("expires_in", 3600),
            "refresh_expires_at": now + token_response.get("refresh_expires_in", 86400 * 30),
            "scope": token_response.get("scope", ""),
            "cached_at": now,
        }
        
        self._save_to_cache()

    def refresh_token(self, oauth_client: Any) -> str:
        """
        Refresh the access token using the refresh token.
        
        Args:
            oauth_client: An OAuth2Session client configured for the provider.
            
        Returns:
            The new access token.
        """
        from .constants import IDCS_TOKEN_ENDPOINT
        
        refresh_tok = self.refresh_token_value()
        if not refresh_tok:
            raise ValueError("No refresh token available")
        
        try:
            token_response = oauth_client.refresh_token(
                IDCS_TOKEN_ENDPOINT,
                refresh_token=refresh_tok,
            )
            self.cache_token(token_response)
            return self.access_token()
        except Exception as e:
            log(f"[TokenManager] Token refresh failed: {e}")
            # Clear tokens on refresh failure
            self._tokens = {}
            self._save_to_cache()
            raise

    def clear(self) -> None:
        """Clear all cached tokens."""
        self._tokens = {}
        self._save_to_cache()

    def get_token_info(self) -> Dict[str, Any]:
        """Return non-sensitive token metadata for debugging."""
        return {
            "has_access_token": bool(self._tokens.get("access_token")),
            "has_refresh_token": bool(self._tokens.get("refresh_token")),
            "expires_at": self._tokens.get("expires_at", 0),
            "is_valid": self.has_valid_token(),
            "can_refresh": self.can_refresh(),
        }


# Global singleton instance
token_manager = TokenManager()
