"""Authentication module for MCP OCI OPSI server.

Supports:
- OCI IAM OAuth for production multi-user access
- API Key authentication via ~/.oci/config for development
- Hybrid authentication with automatic fallback
"""

from .hybrid_auth import (
    get_oci_signer,
    get_authenticated_user,
    detect_auth_mode,
    clear_signer_cache,
    AuthMode,
    AuthenticatedUser,
)
from .oci_oauth import (
    create_oci_auth_provider,
    get_token_exchange_signer,
    is_oauth_configured,
    get_oauth_config_status,
    generate_encryption_key,
    generate_jwt_signing_key,
    clear_token_cache,
)

__all__ = [
    "get_oci_signer",
    "get_authenticated_user",
    "detect_auth_mode",
    "clear_signer_cache",
    "AuthMode",
    "AuthenticatedUser",
    "create_oci_auth_provider",
    "get_token_exchange_signer",
    "is_oauth_configured",
    "get_oauth_config_status",
    "generate_encryption_key",
    "generate_jwt_signing_key",
    "clear_token_cache",
]
