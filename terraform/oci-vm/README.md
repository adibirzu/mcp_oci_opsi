# MCP OCI OPSI Server - Terraform Deployment

This directory contains Terraform configurations for deploying the MCP OCI OPSI Server to OCI Compute.

## Quick Start

```bash
# 1. Configure variables
cp terraform.tfvars.example terraform.tfvars
# Edit terraform.tfvars with your OCI credentials

# 2. Deploy
terraform init
terraform plan
terraform apply

# 3. Get connection info
terraform output
```

## Files

| File | Description |
|------|-------------|
| `main.tf` | Main Terraform configuration (VCN, subnet, instance) |
| `variables.tf` | Input variable definitions |
| `cloud-init.yaml` | Cloud-init template for instance provisioning |
| `terraform.tfvars.example` | Example variables file |

## Requirements

- Terraform >= 1.0.0
- OCI Provider >= 5.0.0
- OCI CLI configured (`~/.oci/config`)
- SSH key pair

## What Gets Created

- VCN with public/private subnet (optional)
- Internet Gateway or NAT Gateway
- Service Gateway for OCI services
- Security List (SSH + HTTP)
- Compute Instance (VM.Standard.E4.Flex)
- MCP OCI OPSI Server (auto-configured)

## Configuration

See `terraform.tfvars.example` for all available options.

### Minimum Required Variables

```hcl
tenancy_ocid     = "ocid1.tenancy.oc1..aaa..."
user_ocid        = "ocid1.user.oc1..aaa..."
fingerprint      = "xx:xx:xx:xx:xx:xx:xx:xx:xx:xx:xx:xx:xx:xx:xx:xx"
private_key_path = "~/.oci/oci_api_key.pem"
region           = "us-phoenix-1"
compartment_ocid = "ocid1.compartment.oc1..aaa..."
```

## Outputs

After `terraform apply`:

```
instance_id          = "ocid1.instance.oc1..."
instance_public_ip   = "129.146.xxx.xxx"
mcp_server_url       = "http://129.146.xxx.xxx:8000"
ssh_command          = "ssh opc@129.146.xxx.xxx"
```

## Documentation

- [Full Deployment Guide](../../docs/OCI_VM_DEPLOYMENT.md)
- [Architecture Overview](../../docs/ARCHITECTURE.md)
- [Main README](../../README.md)
