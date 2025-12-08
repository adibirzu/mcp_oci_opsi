"""Hybrid authentication supporting both OAuth and API Key modes.

This module provides a unified authentication interface that:
1. Uses OCI IAM OAuth when available (production, multi-user)
2. Falls back to API Key authentication (development, single-user)
"""

import os
from enum import Enum
from typing import Any, Dict, Optional, Tuple
from dataclasses import dataclass

import oci

from ..config import get_oci_config, get_current_profile


class AuthMode(Enum):
    """Authentication mode for OCI API access."""
    OAUTH = "oauth"          # OCI IAM OAuth (production)
    API_KEY = "api_key"      # Config file API key (development)
    RESOURCE_PRINCIPAL = "resource_principal"  # OCI Functions/Container Instances


@dataclass
class AuthenticatedUser:
    """Represents an authenticated user."""
    user_id: str
    tenancy_id: str
    region: str
    auth_mode: AuthMode
    profile: Optional[str] = None
    email: Optional[str] = None
    display_name: Optional[str] = None


# Global cache for signers to avoid recreation
_signer_cache: Dict[str, Any] = {}


def detect_auth_mode() -> AuthMode:
    """
    Detect the appropriate authentication mode based on environment.

    Returns:
        AuthMode: The detected authentication mode
    """
    # Check for OAuth token in context (set during OAuth flow)
    if os.getenv("FASTMCP_OAUTH_ENABLED") == "1":
        return AuthMode.OAUTH

    # Check for Resource Principal (OCI Functions/Container Instances)
    if os.getenv("OCI_RESOURCE_PRINCIPAL_VERSION"):
        return AuthMode.RESOURCE_PRINCIPAL

    # Default to API Key
    return AuthMode.API_KEY


def get_oci_signer(
    auth_mode: Optional[AuthMode] = None,
    profile: Optional[str] = None,
    oauth_token: Optional[str] = None,
) -> Tuple[Any, str, AuthMode]:
    """
    Get OCI signer based on authentication mode.

    Args:
        auth_mode: Force a specific auth mode (auto-detect if None)
        profile: OCI profile name for API Key mode
        oauth_token: OAuth token for OAuth mode

    Returns:
        Tuple of (signer, region, auth_mode)

    Raises:
        ValueError: If authentication fails
    """
    if auth_mode is None:
        auth_mode = detect_auth_mode()

    if auth_mode == AuthMode.OAUTH and oauth_token:
        return _get_oauth_signer(oauth_token)
    elif auth_mode == AuthMode.RESOURCE_PRINCIPAL:
        return _get_resource_principal_signer()
    else:
        return _get_api_key_signer(profile)


def _get_api_key_signer(profile: Optional[str] = None) -> Tuple[Any, str, AuthMode]:
    """
    Get signer using API Key from ~/.oci/config.

    Args:
        profile: OCI profile name (uses OCI_CLI_PROFILE or DEFAULT if None)

    Returns:
        Tuple of (signer, region, AuthMode.API_KEY)
    """
    cache_key = f"api_key:{profile or get_current_profile()}"

    if cache_key in _signer_cache:
        return _signer_cache[cache_key]

    # Save and restore profile if specified
    original_profile = os.getenv("OCI_CLI_PROFILE")
    if profile:
        os.environ["OCI_CLI_PROFILE"] = profile

    try:
        config = get_oci_config()
        region = config["region"]

        signer = oci.signer.Signer(
            tenancy=config["tenancy"],
            user=config["user"],
            fingerprint=config["fingerprint"],
            private_key_file_location=config.get("key_file"),
            pass_phrase=config.get("pass_phrase"),
        )

        result = (signer, region, AuthMode.API_KEY)
        _signer_cache[cache_key] = result
        return result

    finally:
        # Restore original profile
        if profile and original_profile:
            os.environ["OCI_CLI_PROFILE"] = original_profile
        elif profile and not original_profile:
            os.environ.pop("OCI_CLI_PROFILE", None)


def _get_resource_principal_signer() -> Tuple[Any, str, AuthMode]:
    """
    Get signer using Resource Principal (for OCI Functions/Container Instances).

    Returns:
        Tuple of (signer, region, AuthMode.RESOURCE_PRINCIPAL)
    """
    cache_key = "resource_principal"

    if cache_key in _signer_cache:
        return _signer_cache[cache_key]

    try:
        signer = oci.auth.signers.get_resource_principals_signer()
        region = os.getenv("OCI_REGION") or signer.region

        result = (signer, region, AuthMode.RESOURCE_PRINCIPAL)
        _signer_cache[cache_key] = result
        return result

    except Exception as e:
        raise ValueError(
            f"Failed to get Resource Principal signer: {e}. "
            "Ensure running in OCI Functions/Container Instance with proper IAM policies."
        ) from e


def _get_oauth_signer(oauth_token: str) -> Tuple[Any, str, AuthMode]:
    """
    Get signer using OAuth token exchange.

    Args:
        oauth_token: The OAuth access token

    Returns:
        Tuple of (signer, region, AuthMode.OAUTH)
    """
    # Import here to avoid circular dependency
    from .oci_oauth import get_token_exchange_signer

    signer, region = get_token_exchange_signer(oauth_token)
    return (signer, region, AuthMode.OAUTH)


def get_authenticated_user(
    auth_mode: Optional[AuthMode] = None,
    profile: Optional[str] = None,
    oauth_claims: Optional[Dict[str, Any]] = None,
) -> AuthenticatedUser:
    """
    Get information about the authenticated user.

    Args:
        auth_mode: Authentication mode
        profile: OCI profile for API Key mode
        oauth_claims: JWT claims for OAuth mode

    Returns:
        AuthenticatedUser with user details
    """
    if auth_mode is None:
        auth_mode = detect_auth_mode()

    if auth_mode == AuthMode.OAUTH and oauth_claims:
        return AuthenticatedUser(
            user_id=oauth_claims.get("sub", "unknown"),
            tenancy_id=oauth_claims.get("tenant", "unknown"),
            region=oauth_claims.get("region", os.getenv("OCI_REGION", "unknown")),
            auth_mode=AuthMode.OAUTH,
            email=oauth_claims.get("email"),
            display_name=oauth_claims.get("name"),
        )

    elif auth_mode == AuthMode.RESOURCE_PRINCIPAL:
        signer = oci.auth.signers.get_resource_principals_signer()
        return AuthenticatedUser(
            user_id="resource_principal",
            tenancy_id=signer.tenancy_id,
            region=os.getenv("OCI_REGION") or signer.region,
            auth_mode=AuthMode.RESOURCE_PRINCIPAL,
        )

    else:  # API_KEY
        config = get_oci_config()
        return AuthenticatedUser(
            user_id=config.get("user", "unknown"),
            tenancy_id=config.get("tenancy", "unknown"),
            region=config.get("region", "unknown"),
            auth_mode=AuthMode.API_KEY,
            profile=profile or get_current_profile(),
        )


def clear_signer_cache():
    """Clear the signer cache (useful for testing or profile switching)."""
    global _signer_cache
    _signer_cache = {}
