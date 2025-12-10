#!/usr/bin/env python3
"""
OPSI MCP - Configuration Manager
Supports local OCI config and remote SSE OAuth token authentication.
"""

import os
import logging
from typing import Dict, Any, Optional

import oci

# Configure logging
logger = logging.getLogger(__name__)

class AuthConfig:
    """Manages OCI authentication configuration."""
    
    @staticmethod
    def get_config() -> Dict[str, Any]:
        """
        Get OCI configuration with priority:
        1. OCI_AUTH_TOKEN (SSE/Remote)
        2. Instance Principal (OCI VM)
        3. Resource Principal (Functions)
        4. Local Config (~/.oci/config)
        """
        # 1. Check for SSE/Remote Auth Token
        auth_token = os.getenv("OCI_AUTH_TOKEN")
        if auth_token:
            logger.info("Using OCI_AUTH_TOKEN for authentication")
            return {
                "authentication_type": "token_auth",
                "token": auth_token,
                "region": os.getenv("OCI_REGION", "us-ashburn-1")
            }
            
        # 2. Check for Local Config
        try:
            profile = os.getenv("OCI_CLI_PROFILE", "DEFAULT")
            config = oci.config.from_file(profile_name=profile)
            logger.info(f"Using local OCI config (profile: {profile})")
            return config
        except Exception as e:
            logger.warning(f"Failed to load local config: {e}")
            
        # 3. Fallback to Instance/Resource Principal (simplified check)
        if os.getenv("OCI_RESOURCE_PRINCIPAL_VERSION"):
            logger.info("Using Resource Principal")
            return {"authentication_type": "resource_principal"}
            
        raise RuntimeError("No valid OCI authentication method found")

    @staticmethod
    def create_signer(config: Dict[str, Any]) -> Any:
        """Create OCI signer based on config type."""
        auth_type = config.get("authentication_type")
        
        if auth_type == "token_auth":
            # For remote SSE, we expect a valid token that can be used
            # This is a placeholder for actual OCI IAM token handling
            # In a real scenario, this would use oci.auth.signers.SecurityTokenSigner
            token = config["token"]
            # return oci.auth.signers.SecurityTokenSigner(token)
            raise NotImplementedError("SSE Token Auth not fully implemented yet")
            
        elif auth_type == "resource_principal":
            return oci.auth.signers.get_resource_principals_signer()
            
        else:
            # Standard API Key Signer from config dict
            return oci.signer.Signer(
                tenancy=config["tenancy"],
                user=config["user"],
                fingerprint=config["fingerprint"],
                private_key_file_location=config.get("key_file"),
                pass_phrase=config.get("pass_phrase")
            )

def get_oci_config() -> Dict[str, Any]:
    """Helper to get config compatible with existing code."""
    return AuthConfig.get_config()
