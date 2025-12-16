# Quickstart Folder

This folder contains everything a new developer needs to get the Databricks Chat Template running quickly.

## Contents

### Documentation

- **[QUICKSTART.md](./QUICKSTART.md)** - Get running in 5 minutes (start here!)
- **[PREREQUISITES.md](./PREREQUISITES.md)** - Detailed installation guide for all prerequisites
- **[TROUBLESHOOTING.md](./TROUBLESHOOTING.md)** - Solutions to common issues

### Scripts

- **[setup.sh](./setup.sh)** - Master automated setup script
- **[check_system_dependencies.sh](./check_system_dependencies.sh)** - Verify system dependencies
- **[create_python_environment.sh](./create_python_environment.sh)** - Python environment setup
- **[setup_database.sh](./setup_database.sh)** - Database initialization

### Configuration Templates

- **[../.env.example](../.env.example)** - Environment configuration template

## Quick Navigation

### I'm brand new - Start here:
1. [PREREQUISITES.md](./PREREQUISITES.md) - Install Python, PostgreSQL, Node.js
2. [QUICKSTART.md](./QUICKSTART.md) - Set up and run the application
3. [TROUBLESHOOTING.md](./TROUBLESHOOTING.md) - If you hit issues

### I have prerequisites installed - Skip to:
1. [QUICKSTART.md](./QUICKSTART.md) - Steps 2-5 only

### Something's broken - Go to:
1. [TROUBLESHOOTING.md](./TROUBLESHOOTING.md) - Find your error message

## Usage

### Automated Setup (Recommended)
```bash
# 1. Copy environment template
cp .env.example .env

# 2. Edit with your credentials
nano .env

# 3. Run automated setup
./quickstart/setup.sh

# 4. Start application
./start_app.sh
```

### Manual Setup
If you prefer manual control, see [QUICKSTART.md](./QUICKSTART.md) for step-by-step instructions.

## Support

- **Questions about installation?** - [PREREQUISITES.md](./PREREQUISITES.md)
- **Application not working?** - [TROUBLESHOOTING.md](./TROUBLESHOOTING.md)
- **Want to understand the system?** - [../README.md](../README.md)

## Contributing

Found an issue or have a suggestion for the quickstart guides?
1. Check [TROUBLESHOOTING.md](./TROUBLESHOOTING.md) first
2. Review the main [README.md](../README.md) for detailed documentation
3. Open an issue or PR with your feedback

---

**Time to first chat: 5 minutes**
