# Contributing to SETLr

Thank you for your interest in contributing to SETLr! We welcome contributions from the community.

## Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Getting Started](#getting-started)
- [Development Setup](#development-setup)
- [Code Standards](#code-standards)
- [Testing Guidelines](#testing-guidelines)
- [Commit Message Conventions](#commit-message-conventions)
- [Pull Request Process](#pull-request-process)
- [Pre-commit Hooks](#pre-commit-hooks)

## Code of Conduct

This project and everyone participating in it is governed by our [Code of Conduct](CODE_OF_CONDUCT.md). By participating, you are expected to uphold this code. Please report unacceptable behavior to [mccusj@cs.rpi.edu](mailto:mccusj@cs.rpi.edu).

## Getting Started

1. Fork the repository on GitHub
2. Clone your fork locally
3. Create a new branch for your feature or bug fix
4. Make your changes
5. Test your changes
6. Submit a pull request

## Development Setup

SETLr includes scripts to help you set up your development environment quickly.

### Prerequisites

- Python 3.8 or higher
- Git

### Bootstrap Your Environment

The `bootstrap` script will create a virtual environment and install all dependencies:

```bash
# Clone the repository
git clone https://github.com/YOUR_USERNAME/setlr.git
cd setlr

# Run the bootstrap script
./script/bootstrap

# Activate the virtual environment
source venv/bin/activate
```

The bootstrap script will:
- Create a Python virtual environment in `venv/`
- Install setlr in editable mode
- Install all development dependencies (nose2, coverage, flake8, pylint, vulture)
- Install build tools (build, wheel, twine)

### Building and Testing

Use the provided scripts for common development tasks:

```bash
# Run linting checks and tests (full build)
./script/build

# Run tests only
nose2 --verbose

# Run tests with coverage
nose2 --with-coverage --coverage-report html

# Run linting
flake8 setlr/ tests/
```

## Code Standards

SETLr follows Python best practices and PEP 8 style guidelines (with some project-specific exceptions defined in `setup.cfg`).

### Style Guidelines

- **PEP 8**: Follow [PEP 8](https://pep8.org/) style guidelines for Python code
- **Docstrings**: Use [PEP 257](https://pep.org/pep-0257/) docstring conventions
  - All public modules, functions, classes, and methods should have docstrings
  - Use triple quotes (`"""`) for docstrings
  - Start with a one-line summary, followed by a blank line if more detail is needed
- **Type Hints**: Use type hints for function parameters and return values where appropriate
- **Import Order**: Organize imports in the following order:
  1. Standard library imports
  2. Related third-party imports
  3. Local application/library specific imports
- **Line Length**: Keep lines under 120 characters when practical (some flexibility given)

### Naming Conventions

- **Variables and Functions**: `lowercase_with_underscores`
- **Classes**: `CapitalizedWords` (PascalCase)
- **Constants**: `UPPERCASE_WITH_UNDERSCORES`
- **Private**: Prefix with single underscore `_private_function`

### Example Code Style

```python
from typing import Dict, Optional
import pandas as pd
from rdflib import Graph

def process_data(input_file: str, options: Optional[Dict] = None) -> Graph:
    """
    Process tabular data and generate an RDF graph.
    
    Args:
        input_file: Path to the input data file
        options: Optional configuration dictionary
        
    Returns:
        An RDFlib Graph containing the processed data
        
    Raises:
        ValueError: If input_file does not exist
    """
    if options is None:
        options = {}
    
    # Implementation here
    pass
```

## Testing Guidelines

SETLr uses `nose2` as the test runner. All new features and bug fixes should include tests.

### Writing Tests

- Place tests in the `tests/` directory
- Test files should be named `test_*.py`
- Test functions should be named `test_*`
- Use descriptive test names that explain what is being tested
- Include both positive and negative test cases
- Mock external dependencies when appropriate

### Running Tests

```bash
# Run all tests
nose2 --verbose

# Run specific test file
nose2 tests.test_module

# Run specific test
nose2 tests.test_module.TestClass.test_method

# Run with coverage
nose2 --with-coverage --coverage setlr/
```

### Test Coverage

- Aim for high test coverage of new code
- The project uses `coverage` to track test coverage
- Run `nose2 --with-coverage` to generate coverage reports

## Commit Message Conventions

Write clear and descriptive commit messages:

### Format

```
Short summary (50 chars or less)

More detailed explanation if necessary. Wrap at 72 characters.
Explain the problem that this commit is solving. Focus on why you
are making this change rather than how.

- Bullet points are okay
- Use present tense ("Add feature" not "Added feature")
- Reference issues and pull requests

Fixes #123
```

### Examples

Good commit messages:
- `Add support for streaming JSON parsing`
- `Fix memory leak in XML processing`
- `Update documentation for JSLDT templates`
- `Refactor SPARQL query builder for clarity`

## Pull Request Process

1. **Create a Branch**: Create a feature branch from `develop` (or `main` if no develop branch exists)
   ```bash
   git checkout -b feature/my-new-feature
   ```

2. **Make Your Changes**: Implement your feature or bug fix

3. **Test Your Changes**: Ensure all tests pass
   ```bash
   ./script/build
   ```

4. **Update Documentation**: Update relevant documentation in the `docs/` directory

5. **Update CHANGELOG**: Add an entry to the `[Unreleased]` section of `CHANGELOG.md`

6. **Commit Your Changes**: Use clear commit messages

7. **Push to Your Fork**:
   ```bash
   git push origin feature/my-new-feature
   ```

8. **Open a Pull Request**: Open a PR against the main repository
   - Use the PR template
   - Provide a clear description of the changes
   - Link to any related issues
   - Ensure CI checks pass

9. **Code Review**: Address any feedback from maintainers

10. **Merge**: Once approved, a maintainer will merge your PR

### Pull Request Checklist

Before submitting your pull request, ensure:

- [ ] Code follows the project's style guidelines
- [ ] All tests pass (`./script/build`)
- [ ] New tests are added for new features
- [ ] Documentation is updated
- [ ] CHANGELOG.md is updated
- [ ] Commit messages are clear and descriptive
- [ ] No unnecessary files are included (check `.gitignore`)

## Pre-commit Hooks

SETLr uses pre-commit hooks to automatically check code quality before commits.

### Setup Pre-commit

```bash
# Install pre-commit (if not already installed)
pip install pre-commit

# Install the git hooks
pre-commit install
```

### Using Pre-commit

Once installed, pre-commit will run automatically on `git commit`. You can also run it manually:

```bash
# Run on all files
pre-commit run --all-files

# Run on staged files only
pre-commit run
```

The pre-commit hooks will:
- Remove trailing whitespace
- Fix end of file
- Check YAML syntax
- Check for large files
- Check for merge conflicts
- Format code with Black
- Lint code with Flake8
- Sort imports with isort

## Questions?

If you have questions about contributing, please:

- Check the [documentation](docs/README.md)
- Open a [discussion](https://github.com/tetherless-world/setlr/discussions)
- Contact the maintainer at [mccusj@cs.rpi.edu](mailto:mccusj@cs.rpi.edu)

Thank you for contributing to SETLr!
