# GitHub Actions Workflows Overview

This repository now includes automated CI/CD workflows using GitHub Actions.

## Workflows

### 1. Unit Tests (test.yml)
**Trigger:** Push or PR to main/master/develop branches

**Python Versions Tested:**
- Python 3.8
- Python 3.9
- Python 3.10
- Python 3.11
- Python 3.12

**Steps:**
1. Checkout code
2. Set up Python environment
3. Install package and test dependencies (nose2, coverage)
4. Create test results directory
5. Run full test suite with nose2
6. Upload test results and coverage reports as artifacts

**Artifacts:**
- `test-results-{python-version}`: JUnit XML test results
- `coverage-{python-version}`: HTML coverage reports

---

### 2. Linting (lint.yml)
**Trigger:** Push or PR to main/master/develop branches

**Linting Tools:**
- flake8: Style guide enforcement
- pycodestyle: PEP 8 style checking
- pylint: Code quality analysis

**Steps:**
1. Checkout code
2. Set up Python 3.11
3. Install linting tools (flake8, pycodestyle, pylint, vulture)
4. Run all linting tools (continues on error)
5. Upload lint results as artifacts

**Artifacts:**
- `lint-results`: Combined output from all linting tools

---

## Status Badges

The README.md now includes workflow status badges that show the current state of the tests and linting:

```markdown
[![Unit Tests](https://github.com/tetherless-world/setlr/actions/workflows/test.yml/badge.svg)](https://github.com/tetherless-world/setlr/actions/workflows/test.yml)
[![Lint](https://github.com/tetherless-world/setlr/actions/workflows/lint.yml/badge.svg)](https://github.com/tetherless-world/setlr/actions/workflows/lint.yml)
```

---

## Manual Workflow Runs

Both workflows can also be triggered manually via the GitHub Actions UI:
1. Go to the "Actions" tab in the repository
2. Select the workflow (Unit Tests or Lint)
3. Click "Run workflow"
4. Choose the branch and click "Run workflow"

---

## Comparison with CircleCI

The new GitHub Actions workflows provide equivalent functionality to the existing CircleCI configuration:

| Feature | CircleCI | GitHub Actions |
|---------|----------|----------------|
| Python Versions | 3.7 | 3.8-3.12 |
| Test Framework | nose2 | nose2 |
| Coverage | ✓ | ✓ |
| Linting | flake8, pycodestyle, pylint | flake8, pycodestyle, pylint |
| Artifacts | ✓ | ✓ |
| Matrix Builds | Single version | Multiple versions |

---

## Benefits

1. **Multiple Python Versions**: Tests run on 5 different Python versions for better compatibility assurance
2. **Native GitHub Integration**: Workflow status visible directly in pull requests
3. **Free for Public Repos**: No additional CI service costs
4. **Artifacts**: Test results and coverage reports easily accessible
