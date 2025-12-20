# OCI VM Deployment Guide

This guide provides step-by-step instructions for deploying the MCP OCI OPSI Server to an OCI Compute instance using Terraform.

---

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Quick Start](#quick-start)
3. [Detailed Setup](#detailed-setup)
4. [Configuration Options](#configuration-options)
5. [Network Architecture](#network-architecture)
6. [Security Configuration](#security-configuration)
7. [OAuth Setup](#oauth-setup)
8. [Post-Deployment](#post-deployment)
9. [Maintenance](#maintenance)
10. [Troubleshooting](#troubleshooting)

---

## Prerequisites

### Required Tools

| Tool | Version | Installation |
|------|---------|--------------|
| Terraform | >= 1.0.0 | [terraform.io/downloads](https://www.terraform.io/downloads) |
| OCI CLI | >= 3.0.0 | [docs.oracle.com](https://docs.oracle.com/en-us/iaas/Content/API/SDKDocs/cliinstall.htm) |
| SSH Key | RSA/Ed25519 | `ssh-keygen -t rsa -b 4096` |

### OCI Requirements

1. **OCI Account** with appropriate permissions
2. **API Key** configured in OCI Console
3. **Compartment** for resource deployment
4. **IAM Policies** (see below)

### Required IAM Policies

Create these policies in your tenancy:

```hcl
# Allow user/group to manage compute instances
Allow group MCPAdmins to manage instance-family in compartment <compartment-name>

# Allow user/group to manage networking
Allow group MCPAdmins to manage virtual-network-family in compartment <compartment-name>

# Allow user/group to read images
Allow group MCPAdmins to read app-catalog-listing in tenancy

# Allow user/group to access Operations Insights (for MCP server)
Allow group MCPAdmins to read operations-insights-family in tenancy
Allow group MCPAdmins to read database-management-family in tenancy
Allow group MCPAdmins to read compartments in tenancy
```

---

## Quick Start

### 1. Clone the Repository

```bash
git clone https://github.com/adibirzu/mcp_oci_opsi.git
cd mcp_oci_opsi/terraform/oci-vm
```

### 2. Configure Variables

```bash
# Copy example variables file
cp terraform.tfvars.example terraform.tfvars

# Edit with your values
vim terraform.tfvars
```

**Minimum required variables:**

```hcl
tenancy_ocid     = "[Link to Secure Variable: OCI_TENANCY_OCID]"
user_ocid        = "[Link to Secure Variable: OCI_USER_OCID]"
fingerprint      = "xx:xx:xx:xx:xx:xx:xx:xx:xx:xx:xx:xx:xx:xx:xx:xx"
private_key_path = "~/.oci/oci_api_key.pem"
region           = "us-phoenix-1"
compartment_ocid = "[Link to Secure Variable: OCI_COMPARTMENT_OCID]"
```

### 3. Deploy

```bash
# Initialize Terraform
terraform init

# Preview changes
terraform plan

# Deploy
terraform apply
```

### 4. Verify Deployment

```bash
# Get outputs
terraform output

# SSH into instance
ssh opc@<public-ip>

# Check service status
sudo systemctl status mcp-oci-opsi
```

---

## Detailed Setup

### Step 1: Prepare OCI Credentials

1. **Generate API Key** (if you don't have one):

```bash
# Generate key pair
openssl genrsa -out ~/.oci/oci_api_key.pem 2048
chmod 600 ~/.oci/oci_api_key.pem

# Generate public key
openssl rsa -pubout -in ~/.oci/oci_api_key.pem -out ~/.oci/oci_api_key_public.pem
```

2. **Upload Public Key to OCI Console**:
   - Go to OCI Console → Identity → Users → Your User
   - Click "API Keys" → "Add API Key"
   - Upload `~/.oci/oci_api_key_public.pem`
   - Copy the fingerprint

3. **Configure OCI CLI**:

```bash
# Run OCI CLI setup
oci setup config

# Or manually create ~/.oci/config:
cat > ~/.oci/config << EOF
[DEFAULT]
user=[Link to Secure Variable: OCI_USER_OCID]
tenancy=[Link to Secure Variable: OCI_TENANCY_OCID]
region=us-phoenix-1
fingerprint=xx:xx:xx:xx:xx:xx:xx:xx:xx:xx:xx:xx:xx:xx:xx:xx
key_file=~/.oci/oci_api_key.pem
EOF

chmod 600 ~/.oci/config
```

### Step 2: Generate SSH Key (if needed)

```bash
# Generate new SSH key
ssh-keygen -t rsa -b 4096 -f ~/.ssh/id_rsa_oci -N ""

# Use this path in terraform.tfvars
ssh_public_key_path = "~/.ssh/id_rsa_oci.pub"
```

### Step 3: Configure Terraform Variables

Create your `terraform.tfvars`:

```hcl
# =============================================================================
# OCI Provider Configuration
# =============================================================================
tenancy_ocid     = "[Link to Secure Variable: OCI_TENANCY_OCID]"
user_ocid        = "[Link to Secure Variable: OCI_USER_OCID]"
fingerprint      = "12:34:56:78:90:ab:cd:ef:12:34:56:78:90:ab:cd:ef"
private_key_path = "~/.oci/oci_api_key.pem"
region           = "us-phoenix-1"

# =============================================================================
# Compartment
# =============================================================================
compartment_ocid = "[Link to Secure Variable: OCI_COMPARTMENT_OCID]"

# =============================================================================
# Network Configuration
# =============================================================================
create_vcn        = true          # Create new VCN
use_public_subnet = true          # Use public subnet (recommended for initial setup)
vcn_cidr_block    = "10.0.0.0/16"
subnet_cidr_block = "10.0.1.0/24"

# =============================================================================
# Compute Instance
# =============================================================================
instance_display_name  = "mcp-oci-opsi-server"
instance_shape         = "VM.Standard.E4.Flex"
instance_ocpus         = 2
instance_memory_in_gbs = 16
ssh_public_key_path    = "~/.ssh/id_rsa.pub"

# =============================================================================
# MCP Server
# =============================================================================
mcp_version   = "v3"
mcp_transport = "http"
mcp_http_port = 8000

# =============================================================================
# OCI CLI on Server (Optional - for API Key auth)
# =============================================================================
# Pre-configure OCI CLI on the server for API key authentication
# Generate base64: base64 -i ~/.oci/config | tr -d '\n'
# oci_config_content = "W0RFRkFVTFRdCnVzZXI9Li4uCg=="
# oci_key_content    = "LS0tLS1CRUdJTiBSU0EgUFJJVkFURSBLRVktLS0tLQo..."

# =============================================================================
# Tags
# =============================================================================
freeform_tags = {
  "Project"     = "mcp-oci-opsi"
  "Environment" = "production"
  "Owner"       = "dba-team"
}
```

### Step 4: Deploy Infrastructure

```bash
# Navigate to terraform directory
cd terraform/oci-vm

# Initialize providers
terraform init

# Validate configuration
terraform validate

# Preview changes
terraform plan -out=tfplan

# Apply changes
terraform apply tfplan
```

### Step 5: Verify Deployment

After `terraform apply` completes:

```bash
# View outputs
terraform output

# Expected output:
# instance_id = "[Link to Secure Variable: OCI_INSTANCE_OCID]"
# instance_public_ip = "129.146.xxx.xxx"
# mcp_server_url = "http://129.146.xxx.xxx:8000"
# ssh_command = "ssh opc@129.146.xxx.xxx"
```

### Step 6: Configure OCI CLI on Server

If you didn't pre-configure OCI credentials, do it now:

```bash
# SSH into instance
ssh opc@<public-ip>

# Switch to mcp user
sudo su - mcp

# Configure OCI CLI
mkdir -p ~/.oci

# Edit config file
cat > ~/.oci/config << 'EOF'
[DEFAULT]
user=[Link to Secure Variable: OCI_USER_OCID]
tenancy=[Link to Secure Variable: OCI_TENANCY_OCID]
region=us-phoenix-1
fingerprint=xx:xx:xx:xx:xx:xx:xx:xx:xx:xx:xx:xx:xx:xx:xx:xx
key_file=/home/mcp/.oci/oci_api_key.pem
EOF

chmod 600 ~/.oci/config

# Upload your private key
# From your local machine:
scp ~/.oci/oci_api_key.pem opc@<public-ip>:/tmp/
# On server:
sudo mv /tmp/oci_api_key.pem /home/mcp/.oci/
sudo chown mcp:mcp /home/mcp/.oci/oci_api_key.pem
sudo chmod 600 /home/mcp/.oci/oci_api_key.pem

# Restart MCP service
sudo systemctl restart mcp-oci-opsi

# Verify
sudo systemctl status mcp-oci-opsi
```

---

## Configuration Options

### Network Options

#### Option A: Public Subnet (Default)

```hcl
create_vcn        = true
use_public_subnet = true  # VM gets public IP, accessible from internet
```

**Pros:**
- Direct HTTP access to MCP server
- Easy to set up
- SSH access without bastion

**Cons:**
- VM exposed to internet
- Requires security list rules

#### Option B: Private Subnet

```hcl
create_vcn        = true
use_public_subnet = false  # VM only has private IP
```

**Pros:**
- More secure
- No direct internet exposure

**Cons:**
- Requires bastion host for SSH
- Requires load balancer for HTTP

#### Option C: Existing VCN

```hcl
create_vcn  = false
vcn_ocid    = "[Link to Secure Variable: OCI_VCN_OCID]"
subnet_ocid = "[Link to Secure Variable: OCI_SUBNET_OCID]"
```

### Instance Sizing

| Workload | OCPUs | Memory | Shape |
|----------|-------|--------|-------|
| Development | 1 | 8 GB | VM.Standard.E4.Flex |
| Production (Small) | 2 | 16 GB | VM.Standard.E4.Flex |
| Production (Large) | 4 | 32 GB | VM.Standard.E4.Flex |

```hcl
instance_shape         = "VM.Standard.E4.Flex"
instance_ocpus         = 2
instance_memory_in_gbs = 16
```

---

## Network Architecture

### Public Subnet Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                            Internet                                  │
└──────────────────────────────────┬──────────────────────────────────┘
                                   │
                          ┌────────┴────────┐
                          │ Internet Gateway │
                          └────────┬────────┘
                                   │
┌──────────────────────────────────┴──────────────────────────────────┐
│                         Virtual Cloud Network                        │
│                            10.0.0.0/16                               │
│                                                                      │
│  ┌────────────────────────────────────────────────────────────────┐ │
│  │                      Public Subnet                              │ │
│  │                       10.0.1.0/24                               │ │
│  │                                                                 │ │
│  │  ┌─────────────────────────────────────────────────────────┐  │ │
│  │  │              MCP OCI OPSI Server                         │  │ │
│  │  │              Public IP: 129.146.x.x                      │  │ │
│  │  │              Private IP: 10.0.1.x                        │  │ │
│  │  │                                                          │  │ │
│  │  │  Security List:                                          │  │ │
│  │  │  - SSH (22) from 0.0.0.0/0                              │  │ │
│  │  │  - HTTP (8000) from 0.0.0.0/0                           │  │ │
│  │  └─────────────────────────────────────────────────────────┘  │ │
│  └────────────────────────────────────────────────────────────────┘ │
│                                                                      │
│                          ┌────────────────┐                          │
│                          │ Service Gateway│                          │
│                          └───────┬────────┘                          │
│                                  │                                   │
└──────────────────────────────────┼───────────────────────────────────┘
                                   │
                    ┌──────────────┴──────────────┐
                    │    OCI Services Network     │
                    │  (Operations Insights, DBM) │
                    └─────────────────────────────┘
```

### Private Subnet Architecture (Recommended for Production)

```
┌─────────────────────────────────────────────────────────────────────┐
│                            Internet                                  │
└───────────────────────────────┬──────────────────────────────────────┘
                                │
                       ┌────────┴────────┐
                       │  Load Balancer   │
                       │  (HTTPS:443)     │
                       └────────┬────────┘
                                │
┌───────────────────────────────┴──────────────────────────────────────┐
│                         Virtual Cloud Network                         │
│                            10.0.0.0/16                                │
│                                                                       │
│  ┌────────────────────────┐  ┌────────────────────────────────────┐  │
│  │    Public Subnet       │  │        Private Subnet               │  │
│  │    10.0.0.0/24         │  │        10.0.1.0/24                  │  │
│  │                        │  │                                     │  │
│  │  ┌──────────────────┐  │  │  ┌─────────────────────────────┐   │  │
│  │  │  Bastion Host    │──┼──┼─>│   MCP OCI OPSI Server       │   │  │
│  │  │  (SSH Jump)      │  │  │  │   Private IP: 10.0.1.x      │   │  │
│  │  └──────────────────┘  │  │  │   HTTP: 8000                │   │  │
│  │                        │  │  └─────────────────────────────┘   │  │
│  └────────────────────────┘  └────────────────────────────────────┘  │
│                                      │                                │
│                             ┌────────┴────────┐                       │
│                             │   NAT Gateway    │                       │
│                             └────────┬────────┘                       │
│                                      │                                │
│                             ┌────────┴────────┐                       │
│                             │ Service Gateway │                       │
│                             └─────────────────┘                       │
└───────────────────────────────────────────────────────────────────────┘
```

---

## Security Configuration

### Restrict SSH Access

Modify `terraform.tfvars` or update security list after deployment:

```hcl
# In security list, restrict SSH to specific IPs
ingress_security_rules {
  protocol = "6"  # TCP
  source   = "YOUR_IP/32"  # Your office/home IP
  tcp_options {
    min = 22
    max = 22
  }
}
```

### Enable HTTPS

For production, add a load balancer with SSL:

1. Create OCI Load Balancer
2. Add SSL certificate (Let's Encrypt or OCI Certificate Service)
3. Configure backend set pointing to MCP server port 8000
4. Update security list to only allow load balancer traffic

### Use Instance Principal (No API Keys)

For better security, use instance principal authentication:

1. Create Dynamic Group:

```hcl
# In OCI Console: Identity → Dynamic Groups
Name: MCPServerDynamicGroup
Rule: ALL {instance.compartment.id = '[Link to Secure Variable: OCI_COMPARTMENT_OCID]'}
```

2. Create Policy:

```hcl
Allow dynamic-group MCPServerDynamicGroup to read operations-insights-family in tenancy
Allow dynamic-group MCPServerDynamicGroup to read database-management-family in tenancy
Allow dynamic-group MCPServerDynamicGroup to read compartments in tenancy
```

3. Update MCP server to use resource principal authentication (built-in support in future version)

---

## OAuth Setup

For production multi-user deployments:

### Step 1: Create OAuth Application in OCI

1. Go to OCI Console → Identity → Domains → Your Domain
2. Click "Integrated Applications" → "Add Application"
3. Select "Confidential Application"
4. Configure:
   - **Name**: MCP OCI OPSI Server
   - **Client Type**: Confidential
   - **Grant Types**: Authorization Code
   - **Redirect URL**: `https://your-domain.com/oauth/callback`

5. Save and note the Client ID and Client Secret

### Step 2: Update Terraform Variables

```hcl
enable_oauth        = true
oauth_config_url    = "https://idcs-xxx.identity.oraclecloud.com/.well-known/openid-configuration"
oauth_client_id     = "your-client-id"
oauth_client_secret = "your-client-secret"
server_base_url     = "https://your-public-domain.com"
```

### Step 3: Redeploy

```bash
terraform plan
terraform apply
```

---

## Post-Deployment

### Build Initial Cache

```bash
# SSH into server
ssh opc@<public-ip>

# Switch to mcp user
sudo su - mcp
cd /opt/mcp-oci-opsi

# Activate virtual environment
source .venv/bin/activate

# Build cache
python scripts/tenancy_review.py

# Or use the script
./scripts/quick_cache_build.sh
```

### Test MCP Server

```bash
# Check server health
curl http://<public-ip>:8000/health

# List available tools (MCP protocol)
curl -X POST http://<public-ip>:8000 \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc": "2.0", "method": "tools/list", "id": 1}'
```

### Configure Claude Desktop (Remote)

For HTTP transport, configure Claude Desktop to connect remotely:

```json
{
  "mcpServers": {
    "oci-opsi-remote": {
      "url": "http://129.146.xxx.xxx:8000",
      "transport": "http"
    }
  }
}
```

---

## Maintenance

### Update MCP Server

```bash
# SSH into server
ssh opc@<public-ip>

# Stop service
sudo systemctl stop mcp-oci-opsi

# Update code
sudo su - mcp
cd /opt/mcp-oci-opsi
git pull

# Update dependencies
source .venv/bin/activate
pip install -e .

# Restart service
exit
sudo systemctl start mcp-oci-opsi
```

### View Logs

```bash
# Service logs
sudo journalctl -u mcp-oci-opsi -f

# Last 100 lines
sudo journalctl -u mcp-oci-opsi -n 100

# Since specific time
sudo journalctl -u mcp-oci-opsi --since "1 hour ago"
```

### Backup Configuration

```bash
# On server
sudo tar -czvf /tmp/mcp-backup.tar.gz \
  /opt/mcp-oci-opsi/.env.local \
  /home/mcp/.oci \
  /home/mcp/.mcp-oci/cache

# Download backup
scp opc@<public-ip>:/tmp/mcp-backup.tar.gz ./
```

### Destroy Infrastructure

```bash
# Remove all resources
terraform destroy

# Confirm by typing 'yes'
```

---

## Troubleshooting

### Cloud-Init Issues

```bash
# Check cloud-init status
sudo cloud-init status --long

# View cloud-init logs
sudo cat /var/log/cloud-init-output.log
sudo cat /var/log/cloud-init.log
```

### Service Won't Start

```bash
# Check service status
sudo systemctl status mcp-oci-opsi

# Check logs
sudo journalctl -u mcp-oci-opsi -n 50

# Common issues:
# 1. OCI config not found - configure /home/mcp/.oci/config
# 2. Python dependencies - run pip install -e . again
# 3. Port conflict - check if port 8000 is in use
```

### OCI Authentication Errors

```bash
# Test OCI CLI
sudo su - mcp
oci iam region list

# Common fixes:
# 1. Check fingerprint matches key
# 2. Verify key permissions: chmod 600 ~/.oci/*
# 3. Ensure user has correct policies
```

### Network Connectivity

```bash
# Test outbound connectivity
curl -I https://operationsinsights.us-phoenix-1.oci.oraclecloud.com

# Test inbound (from your machine)
curl http://<public-ip>:8000/health

# Check security list allows traffic
oci network security-list get --security-list-id <sl-ocid>
```

### Memory Issues

```bash
# Check memory usage
free -h
top

# If running out of memory, increase instance size:
# Update terraform.tfvars and run terraform apply
instance_memory_in_gbs = 32
```

---

## Additional Resources

- [OCI Compute Documentation](https://docs.oracle.com/en-us/iaas/Content/Compute/home.htm)
- [OCI Terraform Provider](https://registry.terraform.io/providers/oracle/oci/latest/docs)
- [FastMCP Documentation](https://gofastmcp.com/)
- [MCP Protocol Specification](https://modelcontextprotocol.io/)
