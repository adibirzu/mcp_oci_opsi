"""OCI configuration and authentication helpers."""

import os
from pathlib import Path
from typing import Any, List, Tuple

import oci
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


def list_available_profiles() -> List[str]:
    """
    List all available OCI profiles from the config file.

    Returns:
        List[str]: List of profile names available in ~/.oci/config

    Raises:
        FileNotFoundError: If OCI config file doesn't exist
    """
    config_path = Path.home() / ".oci" / "config"

    if not config_path.exists():
        raise FileNotFoundError(f"OCI config file not found at {config_path}")

    profiles = []
    with open(config_path, 'r') as f:
        for line in f:
            line = line.strip()
            if line.startswith('[') and line.endswith(']'):
                profile_name = line[1:-1]  # Remove brackets
                profiles.append(profile_name)

    return profiles


def get_current_profile() -> str:
    """
    Get the currently active OCI profile name.

    Returns:
        str: The profile name from OCI_CLI_PROFILE env var or 'DEFAULT'
    """
    return os.getenv("OCI_CLI_PROFILE", "DEFAULT")


def get_oci_config() -> dict[str, Any]:
    """
    Get OCI configuration from environment or default config file.

    Reads configuration from ~/.oci/config using the profile specified in
    OCI_CLI_PROFILE environment variable (defaults to 'DEFAULT').

    If OCI_REGION is set, it will override the region in the config file.

    Returns:
        dict: OCI configuration dictionary with keys like 'user', 'key_file',
              'fingerprint', 'tenancy', 'region', etc.

    Raises:
        oci.exceptions.ConfigFileNotFound: If config file doesn't exist
        oci.exceptions.InvalidConfig: If config file is invalid
    """
    profile = os.getenv("OCI_CLI_PROFILE", "DEFAULT")
    region_override = os.getenv("OCI_REGION")

    # Load config from file
    config = oci.config.from_file(profile_name=profile)

    # Override region if specified in environment
    if region_override:
        config["region"] = region_override

    # Validate the config
    oci.config.validate_config(config)

    return config


def get_signer_and_region(
    use_resource_principal: bool = False,
) -> Tuple[oci.signer.Signer, str]:
    """
    Get OCI signer and region for API authentication.

    This function provides a signer that can be used with OCI service clients
    for authentication. Currently supports user principal authentication.

    Args:
        use_resource_principal: If True, use Resource Principal authentication
                              (for OCI Functions/Container Instances).
                              Currently not implemented - reserved for future use.

    Returns:
        Tuple[oci.signer.Signer, str]: A tuple containing:
            - signer: OCI signer object for authentication
            - region: OCI region string

    Raises:
        NotImplementedError: If use_resource_principal=True (not yet supported)
        oci.exceptions.ConfigFileNotFound: If config file doesn't exist
        oci.exceptions.InvalidConfig: If config file is invalid

    Example:
        >>> signer, region = get_signer_and_region()
        >>> client = oci.identity.IdentityClient(config={}, signer=signer)
        >>> client.base_client.set_region(region)
    """
    if use_resource_principal:
        # Future implementation for OCI Functions/Container Instances
        # signer = oci.auth.signers.get_resource_principals_signer()
        # region = os.getenv("OCI_REGION") or signer.region
        # return signer, region
        raise NotImplementedError(
            "Resource Principal authentication is not yet implemented. "
            "Set use_resource_principal=False to use user principal authentication."
        )

    # User principal authentication (standard API key)
    config = get_oci_config()
    region = config["region"]

    # Create signer from config
    signer = oci.signer.Signer(
        tenancy=config["tenancy"],
        user=config["user"],
        fingerprint=config["fingerprint"],
        private_key_file_location=config.get("key_file"),
        pass_phrase=config.get("pass_phrase"),
    )

    return signer, region


def get_compartment_id() -> str:
    """
    Get the default compartment ID from environment or use tenancy root.

    Returns:
        str: Compartment OCID. Defaults to tenancy OCID if OCI_COMPARTMENT_ID
             is not set in environment variables.

    Example:
        >>> compartment_id = get_compartment_id()
        >>> # Use in API calls
        >>> client.list_resources(compartment_id=compartment_id)
    """
    compartment_id = os.getenv("OCI_COMPARTMENT_ID")

    if compartment_id:
        return compartment_id

    # Fall back to tenancy root
    config = get_oci_config()
    return config["tenancy"]


# Future: Resource Principal support
# When implementing, add these environment variable checks:
# - OCI_RESOURCE_PRINCIPAL_VERSION
# - OCI_RESOURCE_PRINCIPAL_REGION
# - OCI_RESOURCE_PRINCIPAL_RPST
# - OCI_RESOURCE_PRINCIPAL_PRIVATE_PEM
#
# Example implementation:
# def _get_resource_principal_signer():
#     """Get signer using Resource Principal authentication."""
#     try:
#         signer = oci.auth.signers.get_resource_principals_signer()
#         return signer
#     except Exception as e:
#         raise RuntimeError(
#             f"Failed to get Resource Principal signer: {e}. "
#             "Ensure this is running in an OCI Function or Container Instance "
#             "with proper IAM policies configured."
#         ) from e
