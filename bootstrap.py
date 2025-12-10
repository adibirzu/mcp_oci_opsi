#!/usr/bin/env python3
"""
OPSI MCP Bootstrap & Environment Initialization

Handles:
- Environment variable setup
- Dependency installation
- Cache initialization
- Configuration validation
- Self-contained startup without external dependencies
"""

import os
import sys
import subprocess
import json
from pathlib import Path
from typing import Dict, List, Tuple
from datetime import datetime
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class MCPBootstrap:
    """Bootstrap and initialize OPSI MCP environment."""

    def __init__(self):
        """Initialize bootstrap with paths and configurations."""
        self.project_root = Path(__file__).resolve().parents[1]
        self.mcp_root = Path(__file__).resolve().parent
        self.venv_path = self.project_root / ".venv"
        self.config_dir = Path.home() / ".opsi_mcp"
        self.bootstrap_status_file = self.config_dir / "bootstrap_status.json"
        self.requirements_file = self.mcp_root / "requirements.txt"
        
        # Ensure config directory exists
        self.config_dir.mkdir(parents=True, exist_ok=True)

    def is_venv_active(self) -> bool:
        """Check if virtual environment is active."""
        return hasattr(sys, 'real_prefix') or (
            hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix
        )

    def is_python_venv_available(self) -> bool:
        """Check if a Python venv exists."""
        return (self.venv_path / "bin" / "python").exists() or \
               (self.venv_path / "Scripts" / "python.exe").exists()

    def create_venv(self) -> bool:
        """Create a Python virtual environment."""
        logger.info(f"Creating virtual environment at {self.venv_path}")
        try:
            subprocess.run(
                [sys.executable, "-m", "venv", str(self.venv_path)],
                check=True,
                capture_output=True
            )
            logger.info("✅ Virtual environment created successfully")
            return True
        except subprocess.CalledProcessError as e:
            logger.error(f"❌ Failed to create venv: {e.stderr.decode()}")
            return False

    def get_venv_python(self) -> Path:
        """Get path to Python executable in venv."""
        if sys.platform == "win32":
            return self.venv_path / "Scripts" / "python.exe"
        return self.venv_path / "bin" / "python"

    def install_dependencies(self) -> bool:
        """Install required dependencies."""
        logger.info("Checking and installing dependencies...")
        
        # Get Python executable (use venv if available)
        if self.is_python_venv_available():
            python_exe = self.get_venv_python()
        else:
            python_exe = Path(sys.executable)
        
        # Check if requirements.txt exists
        if not self.requirements_file.exists():
            logger.warning(f"requirements.txt not found at {self.requirements_file}")
            # Use pyproject.toml as fallback
            pyproject_file = self.mcp_root / "pyproject.toml"
            if pyproject_file.exists():
                logger.info("Using pyproject.toml for dependencies")
                try:
                    subprocess.run(
                        [str(python_exe), "-m", "pip", "install", "-e", str(self.mcp_root)],
                        check=True,
                        capture_output=True,
                    )
                    logger.info("✅ Dependencies installed from pyproject.toml")
                    return True
                except subprocess.CalledProcessError as e:
                    logger.error(f"❌ Failed to install dependencies: {e.stderr.decode()}")
                    return False
            return True
        
        # Install from requirements.txt
        try:
            subprocess.run(
                [str(python_exe), "-m", "pip", "install", "-q", "-r", str(self.requirements_file)],
                check=True,
                capture_output=True,
            )
            logger.info("✅ Dependencies installed successfully")
            return True
        except subprocess.CalledProcessError as e:
            logger.error(f"❌ Failed to install dependencies: {e.stderr.decode()}")
            return False

    def setup_environment_variables(self) -> Dict[str, str]:
        """Setup and validate environment variables."""
        logger.info("Setting up environment variables...")
        
        env_vars = dict(os.environ)
        
        # Set PYTHONPATH to include project root
        pythonpath = env_vars.get("PYTHONPATH", "")
        if str(self.project_root) not in pythonpath:
            env_vars["PYTHONPATH"] = f"{self.project_root}:{pythonpath}".strip(":")
            logger.info(f"✅ PYTHONPATH set to include {self.project_root}")
        
        # Set OCI configuration directory
        if "OCI_CONFIG_FILE" not in env_vars:
            oci_config = Path.home() / ".oci" / "config"
            if oci_config.exists():
                env_vars["OCI_CONFIG_FILE"] = str(oci_config)
                logger.info(f"✅ OCI_CONFIG_FILE set to {oci_config}")
        
        # Set default OCI profile
        if "OCI_CLI_PROFILE" not in env_vars:
            env_vars["OCI_CLI_PROFILE"] = "DEFAULT"
            logger.info("✅ OCI_CLI_PROFILE set to DEFAULT")
        
        # Set MCP transport (default: stdio)
        if "FASTMCP_TRANSPORT" not in env_vars:
            env_vars["FASTMCP_TRANSPORT"] = "stdio"
        
        # Apply environment variables
        for key, value in env_vars.items():
            if key.startswith(("OCI_", "FASTMCP_", "PYTHONPATH")):
                os.environ[key] = value
        
        return env_vars

    def validate_oci_config(self) -> bool:
        """Validate OCI configuration is available."""
        logger.info("Validating OCI configuration...")
        
        oci_config = Path.home() / ".oci" / "config"
        if not oci_config.exists():
            logger.warning(f"⚠️  OCI config not found at {oci_config}")
            logger.info("   Run: oci setup config")
            return False
        
        logger.info(f"✅ OCI config found at {oci_config}")
        return True

    def initialize_cache(self) -> bool:
        """Initialize database cache if needed."""
        logger.info("Checking database cache...")
        
        profile = os.getenv("OCI_CLI_PROFILE", "DEFAULT")
        cache_file = Path.home() / f".mcp_oci_opsi_cache_{profile}.json"
        
        if cache_file.exists():
            logger.info(f"✅ Cache file exists: {cache_file}")
            return True
        
        logger.info(f"⚠️  Cache file not found: {cache_file}")
        logger.info("   Run: python3 -m mcp_oci_opsi.scripts.quick_cache_build")
        return True  # Don't fail if cache doesn't exist, it will be built on demand

    def bootstrap_status(self) -> Dict:
        """Get bootstrap status from previous runs."""
        if self.bootstrap_status_file.exists():
            try:
                with open(self.bootstrap_status_file) as f:
                    return json.load(f)
            except Exception as e:
                logger.warning(f"Could not read bootstrap status: {e}")
        
        return {}

    def save_bootstrap_status(self, status: Dict) -> None:
        """Save bootstrap status for future runs."""
        try:
            with open(self.bootstrap_status_file, 'w') as f:
                json.dump(status, f, indent=2)
        except Exception as e:
            logger.warning(f"Could not save bootstrap status: {e}")

    def should_reinstall_deps(self) -> bool:
        """Check if dependencies should be reinstalled."""
        status = self.bootstrap_status()
        
        # Always reinstall if last install was more than 7 days ago
        last_install = status.get("last_install_time")
        if last_install:
            try:
                last_time = datetime.fromisoformat(last_install)
                age_days = (datetime.now() - last_time).days
                if age_days < 7:
                    logger.info(f"✅ Dependencies recently installed ({age_days} days ago)")
                    return False
            except Exception:
                pass
        
        return True

    def run_bootstrap(self, install_deps: bool = True) -> Tuple[bool, str]:
        """
        Run complete bootstrap sequence.
        
        Returns:
            Tuple of (success: bool, message: str)
        """
        logger.info("=" * 80)
        logger.info("OPSI MCP Bootstrap Starting")
        logger.info("=" * 80)
        
        try:
            # Step 1: Check/create venv
            if not self.is_venv_active() and not self.is_python_venv_available():
                logger.info("\nStep 1: Creating virtual environment...")
                if not self.create_venv():
                    return False, "Failed to create virtual environment"
            else:
                logger.info("\n✅ Virtual environment available")
            
            # Step 2: Setup environment variables
            logger.info("\nStep 2: Setting up environment variables...")
            self.setup_environment_variables()
            
            # Step 3: Validate OCI config
            logger.info("\nStep 3: Validating OCI configuration...")
            self.validate_oci_config()
            
            # Step 4: Install/update dependencies
            if install_deps and self.should_reinstall_deps():
                logger.info("\nStep 4: Installing dependencies...")
                if not self.install_dependencies():
                    logger.warning("⚠️  Dependency installation encountered issues")
            else:
                logger.info("\nStep 4: Skipping dependency installation (recently done)")
            
            # Step 5: Initialize cache
            logger.info("\nStep 5: Checking database cache...")
            self.initialize_cache()
            
            # Save bootstrap status
            status = {
                "last_install_time": datetime.now().isoformat(),
                "version": "1.0",
                "status": "success",
            }
            self.save_bootstrap_status(status)
            
            logger.info("\n" + "=" * 80)
            logger.info("✅ Bootstrap Complete - OPSI MCP Ready")
            logger.info("=" * 80)
            
            return True, "Bootstrap successful"
            
        except Exception as e:
            logger.error(f"\n❌ Bootstrap failed: {e}", exc_info=True)
            return False, f"Bootstrap failed: {e}"

    def get_startup_message(self) -> str:
        """Get formatted startup message."""
        return f"""
╔══════════════════════════════════════════════════════════════════════════════╗
║                     OPSI MCP Server Ready                                    ║
╠══════════════════════════════════════════════════════════════════════════════╣
║                                                                              ║
║  Environment Setup:                                                          ║
║  ✅ Virtual Environment: {str(self.venv_path):<47}║
║  ✅ PYTHONPATH: {str(self.project_root):<57}║
║  ✅ OCI Profile: {os.getenv('OCI_CLI_PROFILE', 'DEFAULT'):<61}║
║                                                                              ║
║  Next Steps:                                                                 ║
║  1. Ensure OCI credentials are configured: ~/.oci/config                    ║
║  2. Start the chat server: npm run server                                    ║
║  3. Run the frontend: npm run dev                                            ║
║                                                                              ║
║  For more information:                                                       ║
║  - OPSI_FINAL_EXECUTION_ARCHITECTURE.md                                      ║
║  - OPSI_MCP_AUDIT_REPORT.md                                                  ║
║                                                                              ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""


def main():
    """Run bootstrap when executed as standalone script."""
    bootstrap = MCPBootstrap()
    success, message = bootstrap.run_bootstrap(install_deps=True)
    
    if success:
        print(bootstrap.get_startup_message())
        sys.exit(0)
    else:
        logger.error(message)
        sys.exit(1)


if __name__ == "__main__":
    main()
