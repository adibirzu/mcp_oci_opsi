# =============================================================================
# MCP OCI OPSI Server - Main Terraform Configuration
# =============================================================================

terraform {
  required_version = ">= 1.0.0"

  required_providers {
    oci = {
      source  = "oracle/oci"
      version = ">= 5.0.0"
    }
    tls = {
      source  = "hashicorp/tls"
      version = ">= 4.0.0"
    }
  }
}

# -----------------------------------------------------------------------------
# OCI Provider Configuration
# -----------------------------------------------------------------------------

provider "oci" {
  tenancy_ocid     = var.tenancy_ocid
  user_ocid        = var.user_ocid != "" ? var.user_ocid : null
  fingerprint      = var.fingerprint != "" ? var.fingerprint : null
  private_key_path = var.private_key_path != "" ? var.private_key_path : null
  region           = var.region
}

# -----------------------------------------------------------------------------
# Data Sources
# -----------------------------------------------------------------------------

# Get availability domains
data "oci_identity_availability_domains" "ads" {
  compartment_id = var.tenancy_ocid
}

# Get latest Oracle Linux 8 image
data "oci_core_images" "ol8" {
  compartment_id           = var.compartment_ocid
  operating_system         = "Oracle Linux"
  operating_system_version = "8"
  shape                    = var.instance_shape
  sort_by                  = "TIMECREATED"
  sort_order               = "DESC"
}

# Get current tenancy details
data "oci_identity_tenancy" "tenancy" {
  tenancy_id = var.tenancy_ocid
}

# -----------------------------------------------------------------------------
# Local Values
# -----------------------------------------------------------------------------

locals {
  # Use provided image or latest Oracle Linux 8
  instance_image_ocid = var.instance_image_ocid != "" ? var.instance_image_ocid : data.oci_core_images.ol8.images[0].id

  # SSH public key
  ssh_public_key = var.ssh_public_key != "" ? var.ssh_public_key : file(pathexpand(var.ssh_public_key_path))

  # First availability domain
  availability_domain = data.oci_identity_availability_domains.ads.availability_domains[0].name

  # VCN and subnet OCIDs
  vcn_id    = var.create_vcn ? oci_core_vcn.mcp_vcn[0].id : var.vcn_ocid
  subnet_id = var.create_vcn ? oci_core_subnet.mcp_subnet[0].id : var.subnet_ocid

  # Common tags
  common_tags = merge(var.freeform_tags, {
    "CreatedAt" = timestamp()
  })
}

# -----------------------------------------------------------------------------
# VCN (Optional - only if create_vcn = true)
# -----------------------------------------------------------------------------

resource "oci_core_vcn" "mcp_vcn" {
  count = var.create_vcn ? 1 : 0

  compartment_id = var.compartment_ocid
  cidr_blocks    = [var.vcn_cidr_block]
  display_name   = "mcp-oci-opsi-vcn"
  dns_label      = "mcpopsi"

  freeform_tags = local.common_tags
}

# Internet Gateway (for public subnet)
resource "oci_core_internet_gateway" "mcp_igw" {
  count = var.create_vcn && var.use_public_subnet ? 1 : 0

  compartment_id = var.compartment_ocid
  vcn_id         = oci_core_vcn.mcp_vcn[0].id
  display_name   = "mcp-oci-opsi-igw"
  enabled        = true

  freeform_tags = local.common_tags
}

# NAT Gateway (for private subnet)
resource "oci_core_nat_gateway" "mcp_nat" {
  count = var.create_vcn && !var.use_public_subnet ? 1 : 0

  compartment_id = var.compartment_ocid
  vcn_id         = oci_core_vcn.mcp_vcn[0].id
  display_name   = "mcp-oci-opsi-nat"

  freeform_tags = local.common_tags
}

# Service Gateway (for OCI services access)
data "oci_core_services" "all_services" {
  filter {
    name   = "name"
    values = ["All .* Services In Oracle Services Network"]
    regex  = true
  }
}

resource "oci_core_service_gateway" "mcp_sgw" {
  count = var.create_vcn ? 1 : 0

  compartment_id = var.compartment_ocid
  vcn_id         = oci_core_vcn.mcp_vcn[0].id
  display_name   = "mcp-oci-opsi-sgw"

  services {
    service_id = data.oci_core_services.all_services.services[0].id
  }

  freeform_tags = local.common_tags
}

# Route Table
resource "oci_core_route_table" "mcp_rt" {
  count = var.create_vcn ? 1 : 0

  compartment_id = var.compartment_ocid
  vcn_id         = oci_core_vcn.mcp_vcn[0].id
  display_name   = "mcp-oci-opsi-rt"

  # Internet route (public) or NAT route (private)
  dynamic "route_rules" {
    for_each = var.use_public_subnet ? [1] : []
    content {
      destination       = "0.0.0.0/0"
      destination_type  = "CIDR_BLOCK"
      network_entity_id = oci_core_internet_gateway.mcp_igw[0].id
    }
  }

  dynamic "route_rules" {
    for_each = var.use_public_subnet ? [] : [1]
    content {
      destination       = "0.0.0.0/0"
      destination_type  = "CIDR_BLOCK"
      network_entity_id = oci_core_nat_gateway.mcp_nat[0].id
    }
  }

  # Service gateway route for OCI services
  route_rules {
    destination       = data.oci_core_services.all_services.services[0].cidr_block
    destination_type  = "SERVICE_CIDR_BLOCK"
    network_entity_id = oci_core_service_gateway.mcp_sgw[0].id
  }

  freeform_tags = local.common_tags
}

# Security List
resource "oci_core_security_list" "mcp_sl" {
  count = var.create_vcn ? 1 : 0

  compartment_id = var.compartment_ocid
  vcn_id         = oci_core_vcn.mcp_vcn[0].id
  display_name   = "mcp-oci-opsi-sl"

  # Egress: Allow all outbound
  egress_security_rules {
    destination = "0.0.0.0/0"
    protocol    = "all"
    stateless   = false
  }

  # Ingress: SSH (22)
  ingress_security_rules {
    protocol    = "6" # TCP
    source      = "0.0.0.0/0"
    stateless   = false
    description = "SSH access"

    tcp_options {
      min = 22
      max = 22
    }
  }

  # Ingress: MCP HTTP (8000) - only if public subnet
  dynamic "ingress_security_rules" {
    for_each = var.use_public_subnet ? [1] : []
    content {
      protocol    = "6" # TCP
      source      = "0.0.0.0/0"
      stateless   = false
      description = "MCP HTTP access"

      tcp_options {
        min = var.mcp_http_port
        max = var.mcp_http_port
      }
    }
  }

  # Ingress: ICMP for path MTU discovery
  ingress_security_rules {
    protocol    = "1" # ICMP
    source      = var.vcn_cidr_block
    stateless   = false
    description = "ICMP for path MTU discovery"

    icmp_options {
      type = 3
      code = 4
    }
  }

  freeform_tags = local.common_tags
}

# Subnet
resource "oci_core_subnet" "mcp_subnet" {
  count = var.create_vcn ? 1 : 0

  compartment_id             = var.compartment_ocid
  vcn_id                     = oci_core_vcn.mcp_vcn[0].id
  cidr_block                 = var.subnet_cidr_block
  display_name               = "mcp-oci-opsi-subnet"
  dns_label                  = "mcpsubnet"
  prohibit_public_ip_on_vnic = !var.use_public_subnet
  route_table_id             = oci_core_route_table.mcp_rt[0].id
  security_list_ids          = [oci_core_security_list.mcp_sl[0].id]

  freeform_tags = local.common_tags
}

# -----------------------------------------------------------------------------
# Compute Instance
# -----------------------------------------------------------------------------

resource "oci_core_instance" "mcp_server" {
  compartment_id      = var.compartment_ocid
  availability_domain = local.availability_domain
  display_name        = var.instance_display_name
  shape               = var.instance_shape

  shape_config {
    ocpus         = var.instance_ocpus
    memory_in_gbs = var.instance_memory_in_gbs
  }

  source_details {
    source_type = "image"
    source_id   = local.instance_image_ocid
  }

  create_vnic_details {
    subnet_id        = local.subnet_id
    display_name     = "mcp-oci-opsi-vnic"
    assign_public_ip = var.use_public_subnet
    hostname_label   = "mcpopsi"
  }

  metadata = {
    ssh_authorized_keys = local.ssh_public_key
    user_data = base64encode(templatefile("${path.module}/cloud-init.yaml", {
      mcp_version         = var.mcp_version
      mcp_transport       = var.mcp_transport
      mcp_http_port       = var.mcp_http_port
      enable_oauth        = var.enable_oauth
      oauth_config_url    = var.oauth_config_url
      oauth_client_id     = var.oauth_client_id
      oauth_client_secret = var.oauth_client_secret
      server_base_url     = var.server_base_url
      oci_cli_profile     = var.oci_cli_profile
      oci_config_content  = var.oci_config_content
      oci_key_content     = var.oci_key_content
      github_repo_url     = var.github_repo_url
      github_branch       = var.github_branch
      region              = var.region
    }))
  }

  freeform_tags = local.common_tags

  # Preserve boot volume on destroy
  preserve_boot_volume = false
}

# -----------------------------------------------------------------------------
# Outputs
# -----------------------------------------------------------------------------

output "instance_id" {
  description = "OCID of the compute instance"
  value       = oci_core_instance.mcp_server.id
}

output "instance_public_ip" {
  description = "Public IP address of the instance (if public subnet)"
  value       = var.use_public_subnet ? oci_core_instance.mcp_server.public_ip : null
}

output "instance_private_ip" {
  description = "Private IP address of the instance"
  value       = oci_core_instance.mcp_server.private_ip
}

output "mcp_server_url" {
  description = "URL to access the MCP server (HTTP transport)"
  value       = var.use_public_subnet && var.mcp_transport == "http" ? "http://${oci_core_instance.mcp_server.public_ip}:${var.mcp_http_port}" : null
}

output "ssh_command" {
  description = "SSH command to connect to the instance"
  value       = var.use_public_subnet ? "ssh opc@${oci_core_instance.mcp_server.public_ip}" : "ssh opc@${oci_core_instance.mcp_server.private_ip} (via bastion)"
}

output "vcn_id" {
  description = "OCID of the VCN"
  value       = local.vcn_id
}

output "subnet_id" {
  description = "OCID of the subnet"
  value       = local.subnet_id
}

output "availability_domain" {
  description = "Availability domain where instance is created"
  value       = local.availability_domain
}

output "cloud_init_status_command" {
  description = "Command to check cloud-init status"
  value       = "ssh opc@${var.use_public_subnet ? oci_core_instance.mcp_server.public_ip : oci_core_instance.mcp_server.private_ip} 'sudo cloud-init status --wait'"
}

output "mcp_service_status_command" {
  description = "Command to check MCP service status"
  value       = "ssh opc@${var.use_public_subnet ? oci_core_instance.mcp_server.public_ip : oci_core_instance.mcp_server.private_ip} 'sudo systemctl status mcp-oci-opsi'"
}
