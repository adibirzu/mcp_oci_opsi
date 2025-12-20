"""OCI IAM OAuth integration for FastMCP.

This module provides:
1. OCI IAM OAuth provider configuration
2. Token exchange for OCI API access
3. Encrypted disk-based token storage (no Redis required)

Reference: https://gofastmcp.com/integrations/oci
"""

import os
from pathlib import Path
from typing import Any, Dict, Optional, Tuple
from functools import lru_cache

import oci


# Token cache for performance
_token_signer_cache: Dict[str, Any] = {}


def create_oci_auth_provider(
    base_url: str,
    storage_path: Optional[str] = None,
) -> Any:
    """
    Create OCI IAM OAuth provider for FastMCP.

    This uses the OIDC Proxy pattern since OCI doesn't support
    Dynamic Client Registration.

    Args:
        base_url: Public URL of the server (for OAuth callbacks)
        storage_path: Path for encrypted token storage (default: ~/.mcp-oci/cache/oauth)

    Returns:
        Configured OCIProvider instance

    Environment Variables Required:
        FASTMCP_SERVER_AUTH_OCI_IAM_GUID: Identity domain identifier
        FASTMCP_SERVER_AUTH_OCI_CONFIG_URL: OIDC configuration endpoint
        FASTMCP_SERVER_AUTH_OCI_CLIENT_ID: OAuth application client ID
        FASTMCP_SERVER_AUTH_OCI_CLIENT_SECRET: OAuth application secret
        JWT_SIGNING_KEY: Key for signing internal JWTs
        STORAGE_ENCRYPTION_KEY: Fernet key for encrypting stored tokens
    """
    try:
        from fastmcp.server.auth.providers.oci import OCIProvider
        from key_value.aio.stores.disk import DiskStore
        from key_value.aio.wrappers.encryption import FernetEncryptionWrapper
        from cryptography.fernet import Fernet
    except ImportError as e:
        raise ImportError(
            f"Missing OAuth dependencies: {e}. "
            "Install with: pip install 'fastmcp[auth]' cryptography key-value-aio"
        ) from e

    # Get required environment variables
    config_url = os.environ.get("FASTMCP_SERVER_AUTH_OCI_CONFIG_URL")
    client_id = os.environ.get("FASTMCP_SERVER_AUTH_OCI_CLIENT_ID")
    client_secret = os.environ.get("FASTMCP_SERVER_AUTH_OCI_CLIENT_SECRET")
    jwt_signing_key = os.environ.get("JWT_SIGNING_KEY")
    encryption_key = os.environ.get("STORAGE_ENCRYPTION_KEY")

    # Validate required vars
    missing = []
    if not config_url:
        missing.append("FASTMCP_SERVER_AUTH_OCI_CONFIG_URL")
    if not client_id:
        missing.append("FASTMCP_SERVER_AUTH_OCI_CLIENT_ID")
    if not client_secret:
        missing.append("FASTMCP_SERVER_AUTH_OCI_CLIENT_SECRET")
    if not jwt_signing_key:
        missing.append("JWT_SIGNING_KEY")

    if missing:
        raise ValueError(
            f"Missing required environment variables for OAuth: {', '.join(missing)}"
        )

    # Set up encrypted disk storage for tokens
    if storage_path is None:
        base_cache = os.path.expanduser(os.getenv("MCP_CACHE_DIR") or os.getenv("OCI_MCP_CACHE_DIR") or "~/.mcp-oci/cache")
        storage_path = str(Path(base_cache) / "oauth")

    # Create storage directory
    Path(storage_path).mkdir(parents=True, exist_ok=True)

    # Configure storage with optional encryption
    disk_store = DiskStore(directory=storage_path)

    if encryption_key:
        client_storage = FernetEncryptionWrapper(
            key_value=disk_store,
            fernet=Fernet(encryption_key.encode() if isinstance(encryption_key, str) else encryption_key)
        )
    else:
        # Warning: tokens stored unencrypted
        print("WARNING: STORAGE_ENCRYPTION_KEY not set. OAuth tokens will be stored unencrypted.")
        client_storage = disk_store

    # Create OCI provider
    return OCIProvider(
        config_url=config_url,
        client_id=client_id,
        client_secret=client_secret,
        base_url=base_url,
        jwt_signing_key=jwt_signing_key,
        client_storage=client_storage,
    )


def get_token_exchange_signer(oauth_token: str) -> Tuple[Any, str]:
    """
    Exchange OAuth token for OCI API signer using Token Exchange.

    This enables the authenticated user's identity to flow through to
    OCI Control Plane APIs.

    Args:
        oauth_token: The OAuth access token from authentication

    Returns:
        Tuple of (TokenExchangeSigner, region)

    Environment Variables Required:
        FASTMCP_SERVER_AUTH_OCI_IAM_GUID: Identity domain GUID
        FASTMCP_SERVER_AUTH_OCI_CLIENT_ID: OAuth client ID
        FASTMCP_SERVER_AUTH_OCI_CLIENT_SECRET: OAuth client secret
        OCI_REGION: Default OCI region
    """
    # Check cache first (tokens are cached by their JTI)
    import jwt
    try:
        decoded = jwt.decode(oauth_token, options={"verify_signature": False})
        token_id = decoded.get("jti", oauth_token[:32])
    except Exception:
        token_id = oauth_token[:32]

    if token_id in _token_signer_cache:
        return _token_signer_cache[token_id]

    # Get configuration
    iam_guid = os.environ.get("FASTMCP_SERVER_AUTH_OCI_IAM_GUID", "")
    client_id = os.environ.get("FASTMCP_SERVER_AUTH_OCI_CLIENT_ID")
    client_secret = os.environ.get("FASTMCP_SERVER_AUTH_OCI_CLIENT_SECRET")
    region = os.environ.get("OCI_REGION", "us-phoenix-1")

    if not all([iam_guid, client_id, client_secret]):
        raise ValueError(
            "Token exchange requires: FASTMCP_SERVER_AUTH_OCI_IAM_GUID, "
            "FASTMCP_SERVER_AUTH_OCI_CLIENT_ID, FASTMCP_SERVER_AUTH_OCI_CLIENT_SECRET"
        )

    # Extract domain ID from GUID (format: idcs-xxx.identity.oraclecloud.com)
    domain_id = iam_guid.split(".")[0] if "." in iam_guid else iam_guid

    try:
        from oci.auth.signers import TokenExchangeSigner

        signer = TokenExchangeSigner(
            jwt_or_func=oauth_token,
            oci_domain_id=domain_id,
            client_id=client_id,
            client_secret=client_secret,
        )

        # Cache the signer
        _token_signer_cache[token_id] = (signer, region)

        return signer, region

    except Exception as e:
        raise ValueError(
            f"Token exchange failed: {e}. "
            "Ensure Identity Propagation Trust is configured in OCI IAM."
        ) from e


def generate_encryption_key() -> str:
    """
    Generate a new Fernet encryption key for token storage.

    Returns:
        Base64-encoded Fernet key string

    Usage:
        key = generate_encryption_key()
        # Set as environment variable: STORAGE_ENCRYPTION_KEY=key
    """
    from cryptography.fernet import Fernet
    return Fernet.generate_key().decode()


def generate_jwt_signing_key() -> str:
    """
    Generate a new JWT signing key.

    Returns:
        Random 32-byte hex string

    Usage:
        key = generate_jwt_signing_key()
        # Set as environment variable: JWT_SIGNING_KEY=key
    """
    import secrets
    return secrets.token_hex(32)


def clear_token_cache():
    """Clear the token signer cache."""
    global _token_signer_cache
    _token_signer_cache = {}


def is_oauth_configured() -> bool:
    """
    Check if OAuth is properly configured.

    Returns:
        True if all required OAuth environment variables are set
    """
    required = [
        "FASTMCP_SERVER_AUTH_OCI_CONFIG_URL",
        "FASTMCP_SERVER_AUTH_OCI_CLIENT_ID",
        "FASTMCP_SERVER_AUTH_OCI_CLIENT_SECRET",
        "JWT_SIGNING_KEY",
    ]
    return all(os.environ.get(var) for var in required)


def get_oauth_config_status() -> Dict[str, Any]:
    """
    Get OAuth configuration status for diagnostics.

    Returns:
        Dict with configuration status and missing variables
    """
    vars_status = {
        "FASTMCP_SERVER_AUTH_OCI_CONFIG_URL": bool(os.environ.get("FASTMCP_SERVER_AUTH_OCI_CONFIG_URL")),
        "FASTMCP_SERVER_AUTH_OCI_CLIENT_ID": bool(os.environ.get("FASTMCP_SERVER_AUTH_OCI_CLIENT_ID")),
        "FASTMCP_SERVER_AUTH_OCI_CLIENT_SECRET": bool(os.environ.get("FASTMCP_SERVER_AUTH_OCI_CLIENT_SECRET")),
        "FASTMCP_SERVER_AUTH_OCI_IAM_GUID": bool(os.environ.get("FASTMCP_SERVER_AUTH_OCI_IAM_GUID")),
        "JWT_SIGNING_KEY": bool(os.environ.get("JWT_SIGNING_KEY")),
        "STORAGE_ENCRYPTION_KEY": bool(os.environ.get("STORAGE_ENCRYPTION_KEY")),
        "OCI_REGION": bool(os.environ.get("OCI_REGION")),
    }

    missing = [k for k, v in vars_status.items() if not v]
    required_missing = [
        k for k in missing
        if k in ["FASTMCP_SERVER_AUTH_OCI_CONFIG_URL", "FASTMCP_SERVER_AUTH_OCI_CLIENT_ID",
                 "FASTMCP_SERVER_AUTH_OCI_CLIENT_SECRET", "JWT_SIGNING_KEY"]
    ]

    return {
        "oauth_configured": len(required_missing) == 0,
        "variables": vars_status,
        "missing_required": required_missing,
        "missing_optional": [k for k in missing if k not in required_missing],
        "storage_encrypted": bool(os.environ.get("STORAGE_ENCRYPTION_KEY")),
    }
