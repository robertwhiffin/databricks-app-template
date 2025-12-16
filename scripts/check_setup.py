#!/usr/bin/env python3
"""Setup validation script for Databricks Chat App Template.

This script checks your local development environment setup and helps identify
configuration issues before you run the app.

Usage:
    python scripts/check_setup.py

    Or make it executable:
    chmod +x scripts/check_setup.py
    ./scripts/check_setup.py
"""
import os
import sys
import subprocess
from pathlib import Path
from typing import Tuple, List, Dict
import re

# Color codes for terminal output
GREEN = '\033[92m'
RED = '\033[91m'
YELLOW = '\033[93m'
BLUE = '\033[94m'
BOLD = '\033[1m'
RESET = '\033[0m'


class SetupChecker:
    """Validates the development environment setup."""

    def __init__(self):
        self.project_root = Path(__file__).parent.parent
        self.checks_passed = 0
        self.checks_failed = 0
        self.warnings = 0
        self.issues: List[Dict[str, str]] = []

    def print_header(self, text: str):
        """Print a formatted header."""
        print(f"\n{BOLD}{BLUE}{'=' * 70}{RESET}")
        print(f"{BOLD}{BLUE}{text}{RESET}")
        print(f"{BOLD}{BLUE}{'=' * 70}{RESET}\n")

    def print_check(self, name: str):
        """Print check name."""
        print(f"{BOLD}Checking: {name}...{RESET}", end=" ")

    def print_success(self, message: str = "OK"):
        """Print success message."""
        print(f"{GREEN}✓ {message}{RESET}")
        self.checks_passed += 1

    def print_failure(self, message: str):
        """Print failure message."""
        print(f"{RED}✗ {message}{RESET}")
        self.checks_failed += 1

    def print_warning(self, message: str):
        """Print warning message."""
        print(f"{YELLOW}⚠ {message}{RESET}")
        self.warnings += 1

    def print_info(self, message: str):
        """Print info message."""
        print(f"  {message}")

    def add_issue(self, check: str, problem: str, solution: str):
        """Record an issue for summary."""
        self.issues.append({
            "check": check,
            "problem": problem,
            "solution": solution
        })

    def check_python_version(self) -> bool:
        """Check if Python version is 3.10+."""
        self.print_check("Python version")
        version = sys.version_info
        if version.major == 3 and version.minor >= 10:
            self.print_success(f"Python {version.major}.{version.minor}.{version.micro}")
            return True
        else:
            self.print_failure(f"Python {version.major}.{version.minor}.{version.micro} (need 3.10+)")
            self.add_issue(
                "Python Version",
                f"Found Python {version.major}.{version.minor}, need 3.10+",
                "Install Python 3.10 or higher: https://www.python.org/downloads/"
            )
            return False

    def check_env_file(self) -> Tuple[bool, Dict[str, str]]:
        """Check if .env file exists and has required variables."""
        self.print_check(".env file")
        env_path = self.project_root / ".env"

        if not env_path.exists():
            self.print_failure("Not found")
            self.add_issue(
                ".env File",
                ".env file doesn't exist",
                "Run: cp .env.example .env\nThen edit .env with your credentials"
            )
            return False, {}

        self.print_success("Found")

        # Parse .env file
        env_vars = {}
        with open(env_path) as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    env_vars[key.strip()] = value.strip()

        return True, env_vars

    def check_databricks_host(self, env_vars: Dict[str, str]) -> bool:
        """Check DATABRICKS_HOST format."""
        self.print_check("DATABRICKS_HOST")

        if "DATABRICKS_HOST" not in env_vars:
            self.print_failure("Not set in .env")
            self.add_issue(
                "DATABRICKS_HOST",
                "DATABRICKS_HOST not found in .env file",
                "Add to .env: DATABRICKS_HOST=https://your-workspace.cloud.databricks.com"
            )
            return False

        host = env_vars["DATABRICKS_HOST"]

        # Check if it's a placeholder
        if "your-workspace" in host or host == "https://your-workspace.cloud.databricks.com":
            self.print_failure("Still has placeholder value")
            self.add_issue(
                "DATABRICKS_HOST",
                "DATABRICKS_HOST still has example placeholder",
                "Replace with your actual workspace URL from Databricks browser address bar"
            )
            return False

        # Check format
        if not host.startswith("https://"):
            self.print_failure("Must start with https://")
            self.add_issue(
                "DATABRICKS_HOST",
                f"Invalid format: {host}",
                f"Change to: https://{host.replace('http://', '')}"
            )
            return False

        if host.endswith("/"):
            self.print_warning("Has trailing slash (will be removed)")
            self.print_info(f"Current: {host}")
            self.print_info(f"Should be: {host.rstrip('/')}")

        self.print_success(f"{host}")
        return True

    def check_databricks_token(self, env_vars: Dict[str, str]) -> bool:
        """Check DATABRICKS_TOKEN format."""
        self.print_check("DATABRICKS_TOKEN")

        if "DATABRICKS_TOKEN" not in env_vars:
            self.print_failure("Not set in .env")
            self.add_issue(
                "DATABRICKS_TOKEN",
                "DATABRICKS_TOKEN not found in .env file",
                "Generate token: Databricks UI → Settings → Developer → Access Tokens"
            )
            return False

        token = env_vars["DATABRICKS_TOKEN"]

        # Check if placeholder
        if "paste-your-token-here" in token or "dapi..." in token:
            self.print_failure("Still has placeholder value")
            self.add_issue(
                "DATABRICKS_TOKEN",
                "Token still has example placeholder",
                "Generate a real token from Databricks and paste it in .env"
            )
            return False

        # Check format
        if not token.startswith("dapi"):
            self.print_failure("Must start with 'dapi'")
            self.add_issue(
                "DATABRICKS_TOKEN",
                "Token doesn't start with 'dapi' (invalid format)",
                "Generate a new token from Databricks UI"
            )
            return False

        if len(token) < 20:
            self.print_failure("Token too short (likely invalid)")
            self.add_issue(
                "DATABRICKS_TOKEN",
                "Token is suspiciously short",
                "Generate a new token from Databricks UI"
            )
            return False

        # Don't print actual token, just show it exists
        self.print_success(f"Set (starts with {token[:8]}...)")
        return True

    def check_database_url(self, env_vars: Dict[str, str]) -> bool:
        """Check DATABASE_URL format."""
        self.print_check("DATABASE_URL")

        if "DATABASE_URL" not in env_vars:
            self.print_failure("Not set in .env")
            self.add_issue(
                "DATABASE_URL",
                "DATABASE_URL not found in .env file",
                "Add to .env: DATABASE_URL=postgresql://localhost:5432/chat_template"
            )
            return False

        url = env_vars["DATABASE_URL"]

        if not url.startswith("postgresql://"):
            self.print_failure("Must start with postgresql://")
            self.add_issue(
                "DATABASE_URL",
                f"Invalid format: {url}",
                "Change to: postgresql://localhost:5432/chat_template"
            )
            return False

        self.print_success(f"{url}")
        return True

    def check_postgresql_installed(self) -> bool:
        """Check if PostgreSQL is installed."""
        self.print_check("PostgreSQL installation")

        try:
            result = subprocess.run(
                ["psql", "--version"],
                capture_output=True,
                text=True,
                timeout=5
            )
            if result.returncode == 0:
                version = result.stdout.strip()
                self.print_success(version)
                return True
            else:
                self.print_failure("Not found")
                self.add_issue(
                    "PostgreSQL",
                    "PostgreSQL not installed",
                    "macOS: brew install postgresql@14\nLinux: sudo apt install postgresql"
                )
                return False
        except FileNotFoundError:
            self.print_failure("psql command not found")
            self.add_issue(
                "PostgreSQL",
                "PostgreSQL not installed or not in PATH",
                "macOS: brew install postgresql@14\nLinux: sudo apt install postgresql"
            )
            return False
        except subprocess.TimeoutExpired:
            self.print_failure("Command timed out")
            return False

    def check_postgresql_running(self) -> bool:
        """Check if PostgreSQL service is running."""
        self.print_check("PostgreSQL service")

        try:
            # Try to connect to default postgres database
            result = subprocess.run(
                ["psql", "-d", "postgres", "-c", "SELECT 1;"],
                capture_output=True,
                text=True,
                timeout=5
            )
            if result.returncode == 0:
                self.print_success("Running")
                return True
            else:
                self.print_failure("Not running or not accessible")
                self.add_issue(
                    "PostgreSQL Service",
                    "PostgreSQL is not running",
                    "macOS: brew services start postgresql@14\nLinux: sudo systemctl start postgresql"
                )
                return False
        except FileNotFoundError:
            self.print_failure("Cannot check (psql not found)")
            return False
        except subprocess.TimeoutExpired:
            self.print_failure("Connection timeout")
            return False

    def check_database_exists(self) -> bool:
        """Check if chat_template database exists."""
        self.print_check("Database 'chat_template'")

        try:
            result = subprocess.run(
                ["psql", "-lqt"],
                capture_output=True,
                text=True,
                timeout=5
            )
            if result.returncode == 0:
                databases = result.stdout
                if "chat_template" in databases:
                    self.print_success("Exists")
                    return True
                else:
                    self.print_failure("Not found")
                    self.add_issue(
                        "Database",
                        "chat_template database doesn't exist",
                        "Run: createdb chat_template\nThen: python scripts/init_database.py"
                    )
                    return False
            else:
                self.print_failure("Cannot check")
                return False
        except (FileNotFoundError, subprocess.TimeoutExpired):
            self.print_failure("Cannot check")
            return False

    def check_virtual_environment(self) -> bool:
        """Check if running in virtual environment."""
        self.print_check("Virtual environment")

        in_venv = hasattr(sys, 'real_prefix') or (
            hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix
        )

        if in_venv:
            venv_path = sys.prefix
            self.print_success(f"Active: {venv_path}")
            return True
        else:
            self.print_warning("Not activated")
            self.print_info("It's recommended to use a virtual environment")
            self.print_info("Run: source .venv/bin/activate")
            return False

    def check_dependencies(self) -> bool:
        """Check if required Python packages are installed."""
        self.print_check("Python dependencies")

        required_packages = [
            "fastapi",
            "uvicorn",
            "databricks-sdk",
            "sqlalchemy",
            "psycopg2-binary",
            "pydantic"
        ]

        try:
            import importlib
            missing = []
            for package in required_packages:
                # Handle package name differences
                import_name = package.replace("-", "_")
                try:
                    importlib.import_module(import_name)
                except ImportError:
                    missing.append(package)

            if not missing:
                self.print_success(f"All {len(required_packages)} packages installed")
                return True
            else:
                self.print_failure(f"Missing: {', '.join(missing)}")
                self.add_issue(
                    "Dependencies",
                    f"Missing packages: {', '.join(missing)}",
                    "Run: pip install -r requirements.txt"
                )
                return False
        except Exception as e:
            self.print_failure(f"Check failed: {e}")
            return False

    def check_databricks_connection(self, env_vars: Dict[str, str]) -> bool:
        """Check if can connect to Databricks."""
        self.print_check("Databricks connection")

        if "DATABRICKS_HOST" not in env_vars or "DATABRICKS_TOKEN" not in env_vars:
            self.print_warning("Skipped (credentials not set)")
            return False

        try:
            # Set environment variables for SDK
            os.environ["DATABRICKS_HOST"] = env_vars["DATABRICKS_HOST"]
            os.environ["DATABRICKS_TOKEN"] = env_vars["DATABRICKS_TOKEN"]

            from databricks.sdk import WorkspaceClient
            client = WorkspaceClient()

            # Try to get current user (lightweight API call)
            user = client.current_user.me()
            self.print_success(f"Connected as {user.user_name}")
            return True

        except ImportError:
            self.print_warning("Skipped (databricks-sdk not installed)")
            return False
        except Exception as e:
            error_str = str(e)
            if "401" in error_str or "Unauthorized" in error_str:
                self.print_failure("Authentication failed (401)")
                self.add_issue(
                    "Databricks Authentication",
                    "Token is invalid or expired",
                    "Generate a new token from Databricks UI"
                )
            elif "403" in error_str or "Forbidden" in error_str:
                self.print_failure("Permission denied (403)")
                self.add_issue(
                    "Databricks Permissions",
                    "Token doesn't have required permissions",
                    "Check token permissions in Databricks UI"
                )
            elif "404" in error_str:
                self.print_failure("Workspace not found (404)")
                self.add_issue(
                    "Databricks Workspace",
                    "DATABRICKS_HOST URL is incorrect",
                    "Check workspace URL in browser and update .env"
                )
            else:
                self.print_failure(f"Connection failed: {error_str}")
                self.add_issue(
                    "Databricks Connection",
                    f"Cannot connect: {error_str}",
                    "Check DATABRICKS_HOST and DATABRICKS_TOKEN in .env"
                )
            return False

    def check_port_availability(self, port: int, service: str) -> bool:
        """Check if port is available."""
        self.print_check(f"Port {port} ({service})")

        try:
            import socket
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(1)
            result = sock.connect_ex(('localhost', port))
            sock.close()

            if result == 0:
                self.print_warning("Already in use")
                self.print_info(f"Port {port} is already occupied")
                self.print_info(f"Run ./stop_app.sh or kill process using: lsof -i :{port}")
                return False
            else:
                self.print_success("Available")
                return True
        except Exception as e:
            self.print_warning(f"Cannot check: {e}")
            return False

    def print_summary(self):
        """Print summary of all checks."""
        self.print_header("SUMMARY")

        total = self.checks_passed + self.checks_failed
        print(f"{GREEN}✓ Passed: {self.checks_passed}{RESET}")
        print(f"{RED}✗ Failed: {self.checks_failed}{RESET}")
        print(f"{YELLOW}⚠ Warnings: {self.warnings}{RESET}")
        print(f"Total checks: {total}\n")

        if self.checks_failed == 0:
            print(f"{GREEN}{BOLD}🎉 All critical checks passed!{RESET}")
            print(f"\n{BOLD}Ready to start the app:{RESET}")
            print(f"  ./start_app.sh\n")
        else:
            print(f"{RED}{BOLD}❌ Some checks failed. Please fix the issues below.{RESET}\n")

            self.print_header("ISSUES FOUND")
            for i, issue in enumerate(self.issues, 1):
                print(f"{BOLD}{i}. {issue['check']}{RESET}")
                print(f"   {RED}Problem:{RESET} {issue['problem']}")
                print(f"   {GREEN}Solution:{RESET} {issue['solution']}")
                print()

            print(f"{BOLD}After fixing issues, run this script again:{RESET}")
            print(f"  python scripts/check_setup.py\n")

    def run_all_checks(self):
        """Run all validation checks."""
        self.print_header("DATABRICKS CHAT APP - SETUP VALIDATION")

        # Basic checks
        self.print_header("1. Basic Environment")
        self.check_python_version()
        self.check_virtual_environment()

        # Environment file checks
        self.print_header("2. Configuration Files")
        env_exists, env_vars = self.check_env_file()
        if env_exists:
            self.check_databricks_host(env_vars)
            self.check_databricks_token(env_vars)
            self.check_database_url(env_vars)
        else:
            env_vars = {}

        # Database checks
        self.print_header("3. Database")
        pg_installed = self.check_postgresql_installed()
        if pg_installed:
            pg_running = self.check_postgresql_running()
            if pg_running:
                self.check_database_exists()

        # Python dependencies
        self.print_header("4. Dependencies")
        self.check_dependencies()

        # Databricks connection
        self.print_header("5. Databricks Connection")
        self.check_databricks_connection(env_vars)

        # Port availability
        self.print_header("6. Port Availability")
        self.check_port_availability(8000, "Backend")
        self.check_port_availability(3000, "Frontend")

        # Summary
        self.print_summary()

        # Exit code
        sys.exit(0 if self.checks_failed == 0 else 1)


def main():
    """Main entry point."""
    checker = SetupChecker()
    checker.run_all_checks()


if __name__ == "__main__":
    main()
