# =============================================================================
# MCP OCI OPSI Server - Terraform Variables
# =============================================================================

# -----------------------------------------------------------------------------
# OCI Provider Configuration
# -----------------------------------------------------------------------------

variable "tenancy_ocid" {
  description = "OCID of the OCI tenancy"
  type        = string
}

variable "user_ocid" {
  description = "OCID of the OCI user (for API key auth)"
  type        = string
  default     = ""
}

variable "fingerprint" {
  description = "Fingerprint of the OCI API key"
  type        = string
  default     = ""
}

variable "private_key_path" {
  description = "Path to the OCI API private key file"
  type        = string
  default     = ""
}

variable "region" {
  description = "OCI region (e.g., us-phoenix-1)"
  type        = string
}

# -----------------------------------------------------------------------------
# Compartment Configuration
# -----------------------------------------------------------------------------

variable "compartment_ocid" {
  description = "OCID of the compartment where resources will be created"
  type        = string
}

# -----------------------------------------------------------------------------
# Network Configuration
# -----------------------------------------------------------------------------

variable "create_vcn" {
  description = "Whether to create a new VCN or use existing"
  type        = bool
  default     = true
}

variable "vcn_ocid" {
  description = "OCID of existing VCN (if create_vcn = false)"
  type        = string
  default     = ""
}

variable "subnet_ocid" {
  description = "OCID of existing subnet (if create_vcn = false)"
  type        = string
  default     = ""
}

variable "vcn_cidr_block" {
  description = "CIDR block for the VCN"
  type        = string
  default     = "10.0.0.0/16"
}

variable "subnet_cidr_block" {
  description = "CIDR block for the subnet"
  type        = string
  default     = "10.0.1.0/24"
}

variable "use_public_subnet" {
  description = "Whether to use a public subnet (with internet gateway)"
  type        = bool
  default     = true
}

# -----------------------------------------------------------------------------
# Compute Instance Configuration
# -----------------------------------------------------------------------------

variable "instance_display_name" {
  description = "Display name for the compute instance"
  type        = string
  default     = "mcp-oci-opsi-server"
}

variable "instance_shape" {
  description = "Shape of the compute instance"
  type        = string
  default     = "VM.Standard.E4.Flex"
}

variable "instance_ocpus" {
  description = "Number of OCPUs for flex shape"
  type        = number
  default     = 2
}

variable "instance_memory_in_gbs" {
  description = "Memory in GBs for flex shape"
  type        = number
  default     = 16
}

variable "instance_image_ocid" {
  description = "OCID of the OS image (default: Oracle Linux 8)"
  type        = string
  default     = ""
}

variable "ssh_public_key_path" {
  description = "Path to SSH public key file for instance access"
  type        = string
  default     = "~/.ssh/id_rsa.pub"
}

variable "ssh_public_key" {
  description = "SSH public key content (alternative to path)"
  type        = string
  default     = ""
}

# -----------------------------------------------------------------------------
# MCP Server Configuration
# -----------------------------------------------------------------------------

variable "mcp_version" {
  description = "MCP server version (v2 or v3)"
  type        = string
  default     = "v3"
}

variable "mcp_transport" {
  description = "MCP transport mode (stdio or http)"
  type        = string
  default     = "http"
}

variable "mcp_http_port" {
  description = "HTTP port for MCP server"
  type        = number
  default     = 8000
}

variable "enable_oauth" {
  description = "Enable OAuth authentication"
  type        = bool
  default     = false
}

variable "oauth_config_url" {
  description = "OIDC configuration URL for OAuth"
  type        = string
  default     = ""
  sensitive   = true
}

variable "oauth_client_id" {
  description = "OAuth client ID"
  type        = string
  default     = ""
  sensitive   = true
}

variable "oauth_client_secret" {
  description = "OAuth client secret"
  type        = string
  default     = ""
  sensitive   = true
}

variable "server_base_url" {
  description = "Public URL of the MCP server (for OAuth callbacks)"
  type        = string
  default     = ""
}

# -----------------------------------------------------------------------------
# OCI CLI Configuration for the MCP Server
# -----------------------------------------------------------------------------

variable "oci_cli_profile" {
  description = "OCI CLI profile to use on the server"
  type        = string
  default     = "DEFAULT"
}

variable "oci_config_content" {
  description = "Content of OCI config file to deploy (base64 encoded)"
  type        = string
  default     = ""
  sensitive   = true
}

variable "oci_key_content" {
  description = "Content of OCI API key file to deploy (base64 encoded)"
  type        = string
  default     = ""
  sensitive   = true
}

# -----------------------------------------------------------------------------
# Tags
# -----------------------------------------------------------------------------

variable "freeform_tags" {
  description = "Freeform tags to apply to resources"
  type        = map(string)
  default = {
    "Project"     = "mcp-oci-opsi"
    "Environment" = "production"
    "ManagedBy"   = "terraform"
  }
}

# -----------------------------------------------------------------------------
# GitHub Repository (for deployment)
# -----------------------------------------------------------------------------

variable "github_repo_url" {
  description = "GitHub repository URL for MCP OCI OPSI server"
  type        = string
  default     = "https://github.com/adibirzu/mcp_oci_opsi.git"
}

variable "github_branch" {
  description = "Git branch to deploy"
  type        = string
  default     = "main"
}
