#!/usr/bin/env python3
"""
PII Cleanup Script for OPSI MCP

Scans the codebase for hardcoded OCIDs and sensitive information.
Replaces them with:
1. Environment variable lookups for functional code
2. Generic placeholders for comments/docstrings

Usage:
    python3 clean_pii.py
"""

import re
import os
from pathlib import Path
import shutil
from datetime import datetime

# Patterns to identify PII
OCID_PATTERNS = [
    # Compartment OCIDs
    (r'["\']ocid1\.compartment\.oc1\.\.[a-z0-9]+["\']', 'os.getenv("OCI_COMPARTMENT_ID", "ocid1.compartment.oc1..example")'),
    # Tenancy OCIDs
    (r'["\']ocid1\.tenancy\.oc1\.\.[a-z0-9]+["\']', 'os.getenv("OCI_TENANCY_ID", "ocid1.tenancy.oc1..example")'),
    # User OCIDs
    (r'["\']ocid1\.user\.oc1\.\.[a-z0-9]+["\']', 'os.getenv("OCI_USER_ID", "ocid1.user.oc1..example")'),
    # Database Insight OCIDs
    (r'["\']ocid1\.opsidatabaseinsight\.oc1\.\.[a-z0-9]+["\']', 'os.getenv("OPSI_DATABASE_ID", "ocid1.opsidatabaseinsight.oc1..example")'),
    # Autonomous Database OCIDs
    (r'["\']ocid1\.autonomousdatabase\.oc1\.\.[a-z0-9]+["\']', 'os.getenv("ADB_ID", "ocid1.autonomousdatabase.oc1..example")'),
]

# Patterns for Docstrings/Comments (simpler replacement)
DOC_OCID_PATTERNS = [
    (r'ocid1\.compartment\.oc1\.\.[a-z0-9]+', 'ocid1.compartment.oc1..example'),
    (r'ocid1\.tenancy\.oc1\.\.[a-z0-9]+', 'ocid1.tenancy.oc1..example'),
    (r'ocid1\.user\.oc1\.\.[a-z0-9]+', 'ocid1.user.oc1..example'),
    (r'ocid1\.opsidatabaseinsight\.oc1\.\.[a-z0-9]+', 'ocid1.opsidatabaseinsight.oc1..example'),
    (r'ocid1\.autonomousdatabase\.oc1\.\.[a-z0-9]+', 'ocid1.autonomousdatabase.oc1..example'),
]

ROOT_DIR = Path(__file__).parent

def clean_file(filepath: Path):
    """Clean PII from a single file."""
    try:
        content = filepath.read_text(encoding='utf-8')
        original_content = content
        
        # 1. Handle assignments and function calls (code)
        # We look for specific variable assignments commonly used in the codebase
        
        # Special handling for COMPARTMENT_ID constants
        if filepath.suffix == '.py':
            # Replace COMPARTMENT_ID = "..." with os.getenv
            content = re.sub(
                r'COMPARTMENT_ID\s*=\s*["\']ocid1\.compartment\.oc1\.\.[a-z0-9]+["\']',
                'COMPARTMENT_ID = os.getenv("OCI_COMPARTMENT_ID", "ocid1.compartment.oc1..example")',
                content
            )
            
            # Replace DATABASE_ID = "..."
            content = re.sub(
                r'(DATABASE_ID|DATABASE_INSIGHT_ID)\s*=\s*["\']ocid1\.[a-z]+\.oc1\.\.[a-z0-9]+["\']',
                r'\1 = os.getenv("OPSI_DATABASE_ID", "ocid1.opsidatabaseinsight.oc1..example")',
                content
            )

            # Ensure os is imported if we introduced os.getenv
            if 'os.getenv' in content and 'import os' not in content:
                content = 'import os\n' + content

        # 2. General replacements for strings in code
        for pattern, replacement in OCID_PATTERNS:
            # This is risky as it might replace inside docstrings incorrectly if not careful
            # So we rely more on specific variable assignment replacements above for code,
            # and use this for remaining hardcoded strings in function calls
            
            # Look for function calls: param="ocid1..."
            content = re.sub(
                r'=\s*["\'](ocid1\.[a-z]+\.oc1\.\.[a-z0-9]+)["\']',
                lambda m: f'= os.getenv("OCI_ID", "{m.group(1)}")' if "example" not in m.group(1) else m.group(0),
                content
            )

        # 3. Clean Docstrings and Comments
        for pattern, replacement in DOC_OCID_PATTERNS:
            content = re.sub(pattern, replacement, content)

        if content != original_content:
            print(f"Cleaning {filepath.relative_to(ROOT_DIR)}")
            filepath.write_text(content, encoding='utf-8')
            return True
            
    except Exception as e:
        print(f"Error processing {filepath}: {e}")
    
    return False

def main():
    print("Starting PII Cleanup...")
    count = 0
    for filepath in ROOT_DIR.rglob("*.py"):
        if filepath.name == "clean_pii.py":
            continue
            
        if clean_file(filepath):
            count += 1
            
    print(f"\nCleanup complete. Modified {count} files.")

if __name__ == "__main__":
    main()
