# Contributing to MCP OCI OPSI Server

Thank you for your interest in contributing to the MCP OCI OPSI Server! This document provides guidelines and instructions for contributing.

## Table of Contents

1. [Code of Conduct](#code-of-conduct)
2. [Getting Started](#getting-started)
3. [Development Setup](#development-setup)
4. [Making Changes](#making-changes)
5. [Testing](#testing)
6. [Submitting Changes](#submitting-changes)
7. [Coding Standards](#coding-standards)
8. [Documentation](#documentation)

## Code of Conduct

This project adheres to a code of conduct that all contributors are expected to follow:

- Be respectful and inclusive
- Welcome newcomers and help them get started
- Focus on what is best for the community
- Show empathy towards other community members

## Getting Started

### Prerequisites

- Python 3.10 or higher
- OCI account with Operations Insights access
- Git for version control
- Basic understanding of:
  - Model Context Protocol (MCP)
  - OCI SDK for Python
  - Oracle Cloud Infrastructure services

### Areas for Contribution

We welcome contributions in several areas:

- **New Tools**: Add new MCP tools for additional OCI services
- **Bug Fixes**: Fix reported issues
- **Documentation**: Improve or add documentation
- **Performance**: Optimize existing tools
- **Testing**: Add test coverage
- **Examples**: Create usage examples and demos

## Development Setup

### 1. Fork and Clone

```bash
# Fork the repository on GitHub first, then:
git clone https://github.com/YOUR_USERNAME/mcp_oci_opsi.git
cd mcp_oci_opsi
```

### 2. Create Virtual Environment

```bash
# Using uv (recommended)
uv venv
source .venv/bin/activate

# Using pip
python3 -m venv .venv
source .venv/bin/activate
```

### 3. Install Development Dependencies

```bash
# Install package in editable mode with dev dependencies
uv pip install -e ".[dev,database]"

# Or with pip
pip install -e ".[dev,database]"
```

### 4. Configure OCI

Follow the [SETUP.md](SETUP.md) guide to configure your OCI credentials and environment.

### 5. Build Cache (Optional)

```bash
# Set up your compartment IDs in .env.local
cp .env.example .env.local
# Edit .env.local with your compartments

# Build cache
python3 build_cache.py
```

## Making Changes

### 1. Create a Branch

```bash
git checkout -b feature/your-feature-name
# or
git checkout -b fix/issue-description
```

Branch naming conventions:
- `feature/` - New features or enhancements
- `fix/` - Bug fixes
- `docs/` - Documentation changes
- `refactor/` - Code refactoring
- `test/` - Test additions or changes

### 2. Make Your Changes

Follow these guidelines:

**Adding a New Tool:**

1. Add the tool function to the appropriate module:
   - API tools: `mcp_oci_opsi/tools_*.py`
   - Cache tools: `mcp_oci_opsi/tools_cache.py`
   - Database tools: `mcp_oci_opsi/tools_database.py`

2. Register the tool in `mcp_oci_opsi/main.py`:
   ```python
   @mcp.tool()
   def your_new_tool(param1: str, param2: int = 10) -> Dict[str, Any]:
       """
       Brief description of what the tool does.

       Args:
           param1: Description of parameter 1
           param2: Description of parameter 2 (default: 10)

       Returns:
           Dictionary containing the results

       Example:
           your_new_tool("value", 20)
       """
       # Implementation
       pass
   ```

3. Add documentation to README.md

**Fixing a Bug:**

1. Reference the issue number in your commit
2. Add a test case if applicable
3. Ensure the fix doesn't break existing functionality

### 3. Follow Coding Standards

See [Coding Standards](#coding-standards) section below.

## Testing

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=mcp_oci_opsi

# Run specific test file
pytest tests/test_cache.py

# Run with verbose output
pytest -v
```

### Writing Tests

Create test files in the `tests/` directory:

```python
# tests/test_your_feature.py
import pytest
from mcp_oci_opsi.your_module import your_function


def test_your_function():
    """Test description."""
    result = your_function("test_input")
    assert result == expected_value


def test_your_function_error():
    """Test error handling."""
    with pytest.raises(ValueError):
        your_function(invalid_input)
```

### Manual Testing

Test your changes with Claude Desktop:

1. Install your modified version:
   ```bash
   pip install -e .
   ```

2. Restart Claude Desktop

3. Test the new functionality:
   ```
   Claude, [test your new tool]
   ```

## Submitting Changes

### 1. Commit Your Changes

Follow conventional commit format:

```bash
git add .
git commit -m "feat: add new tool for listing Exadata insights"
git commit -m "fix: correct cache expiry calculation"
git commit -m "docs: update SETUP.md with troubleshooting"
```

Commit types:
- `feat:` - New feature
- `fix:` - Bug fix
- `docs:` - Documentation change
- `refactor:` - Code refactoring
- `test:` - Test addition or modification
- `chore:` - Maintenance tasks

### 2. Push to Your Fork

```bash
git push origin feature/your-feature-name
```

### 3. Create Pull Request

1. Go to the original repository on GitHub
2. Click "New Pull Request"
3. Select your fork and branch
4. Fill out the PR template:

```markdown
## Description
Brief description of changes

## Type of Change
- [ ] Bug fix
- [ ] New feature
- [ ] Documentation update
- [ ] Performance improvement

## Testing
How has this been tested?

## Checklist
- [ ] Code follows project style guidelines
- [ ] Tests added/updated
- [ ] Documentation updated
- [ ] No sensitive data included
- [ ] All tests pass
```

### 4. Review Process

- Maintainers will review your PR
- Address any feedback or requested changes
- Once approved, your PR will be merged

## Coding Standards

### Python Style

Follow PEP 8 with these specifics:

```python
# Use type hints
def function_name(param: str, optional: int = 10) -> Dict[str, Any]:
    """Docstring following Google style."""
    pass

# Use meaningful variable names
database_insights = []  # Good
di = []  # Bad

# Keep functions focused and small
# One function, one responsibility

# Use list comprehensions when appropriate
squares = [x**2 for x in range(10)]

# Format with Black
# Run: black mcp_oci_opsi/
```

### Documentation Strings

Use Google-style docstrings:

```python
def complex_function(param1: str, param2: int, param3: bool = False) -> Dict:
    """
    Brief one-line description.

    Longer description explaining what the function does,
    any important details, edge cases, etc.

    Args:
        param1: Description of param1
        param2: Description of param2
        param3: Description of param3 (default: False)

    Returns:
        Dictionary containing:
            - key1: description
            - key2: description

    Raises:
        ValueError: When param2 is negative
        OciException: When OCI API call fails

    Example:
        >>> result = complex_function("test", 42, True)
        >>> print(result['key1'])
        'value'
    """
    pass
```

### Error Handling

```python
# Good error handling
try:
    result = oci_client.some_operation()
    return {"success": True, "data": result}
except oci.exceptions.ServiceError as e:
    logger.error(f"OCI API error: {e}")
    return {"success": False, "error": str(e)}
except Exception as e:
    logger.error(f"Unexpected error: {e}")
    return {"success": False, "error": "Internal error"}
```

### Sensitive Data

**NEVER commit:**
- API keys or passwords
- OCIDs from your tenancy
- Database connection strings
- Wallet files
- Real compartment/database names from your environment
- User-specific paths (use placeholders)

**Always:**
- Use environment variables for configuration
- Add sensitive files to `.gitignore`
- Use placeholder values in examples
- Document what users need to configure

## Documentation

### Update Documentation When:

- Adding new tools → Update README.md
- Changing configuration → Update SETUP.md
- Adding features → Update relevant .md files
- Finding bugs → Add to troubleshooting sections

### Documentation Style

- Use clear, concise language
- Include code examples
- Use markdown formatting
- Add screenshots for UI-related changes
- Keep examples generic (no real tenant data)

### Example Documentation

````markdown
## New Tool: list_exadata_insights

Lists Exadata infrastructure insights in a compartment.

**Usage:**

```
Claude, list Exadata insights in compartment [COMPARTMENT_OCID]
```

**Parameters:**
- `compartment_id` (required): The compartment OCID
- `limit` (optional): Maximum number of results (default: 100)

**Returns:**
Dictionary with Exadata insight details including:
- Name and OCID
- Status and lifecycle state
- Resource statistics

**Example Response:**
```json
{
  "count": 2,
  "items": [
    {
      "name": "exadata-system-01",
      "id": "[Link to Secure Variable: OCI_RESOURCE_OCID]",
      "status": "ACTIVE"
    }
  ]
}
```
````

## Questions?

- **General Questions**: Open a GitHub Discussion
- **Bug Reports**: Create a GitHub Issue
- **Feature Requests**: Create a GitHub Issue with "enhancement" label
- **Security Issues**: Email maintainers directly (see SECURITY.md)

## License

By contributing, you agree that your contributions will be licensed under the same license as the project (MIT License).

---

Thank you for contributing to MCP OCI OPSI Server! 🙏
