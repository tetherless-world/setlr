# Development Scripts

This directory contains scripts for setting up, building, and releasing the setlr project.

## Scripts

### `bootstrap`

Set up a virtual environment suitable for developing and using the project, including all package requirements for build and release.

**Usage:**
```bash
./script/bootstrap
```

This script will:
- Create a Python virtual environment in `venv/`
- Install the project in editable mode with all dependencies
- Install development dependencies (nose2, coverage, flake8, pylint, etc.)
- Install build and release tools (build, wheel, twine)

**After running bootstrap:**
```bash
source venv/bin/activate  # Activate the virtual environment
```

### `build`

Build the project packages and run all tests and checks.

**Usage:**
```bash
./script/build
```

This script will:
- Activate the virtual environment (if it exists)
- Clean previous build artifacts
- Run linting checks with flake8
- Run all tests with nose2
- Build distribution packages (wheel and source tarball)

**Output:**
- `dist/setlr-*.whl` - Wheel distribution
- `dist/setlr-*.tar.gz` - Source distribution

### `release`

Upload the current version of the project to PyPI using twine.

**Usage:**
```bash
./script/release
```

This script will:
- Activate the virtual environment (if it exists)
- Check that distribution files exist
- Validate distribution files with twine
- Prompt for confirmation before uploading
- Upload to PyPI (requires PyPI credentials or API token)

**Prerequisites:**
- Run `./script/build` first to create distribution files
- Have PyPI credentials or API token ready

**Authentication:**
You can provide credentials via:
- Interactive prompt (default)
- Environment variables: `TWINE_USERNAME` and `TWINE_PASSWORD`
- PyPI API token: Set `TWINE_PASSWORD` to your `pypi-...` token

## Typical Workflow

```bash
# 1. Set up development environment (first time only)
./script/bootstrap
source venv/bin/activate

# 2. Make your changes to the code
# ... edit files ...

# 3. Build and test
./script/build

# 4. If all tests pass and you're ready to release
./script/release
```

## Requirements

- Python 3.8 or higher
- Bash shell (Linux/macOS/WSL on Windows)
- Internet connection (for downloading dependencies)

## Notes

- The virtual environment (`venv/`) is automatically excluded from git via `.gitignore`
- All scripts use color output for better readability
- The `build` script will fail if tests don't pass
- The `release` script requires confirmation before uploading to PyPI
