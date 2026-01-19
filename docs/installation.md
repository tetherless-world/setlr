# Installation Guide

How to install and set up SETLr.

## Requirements

- **Python**: 3.8 or higher
- **Operating System**: Linux, macOS, or Windows
- **Disk Space**: ~100 MB (including dependencies)

## Installation Methods

### 1. Install from PyPI (Recommended)

```bash
pip install setlr
```

This installs the latest stable release from the Python Package Index.

### 2. Install from Source

For the latest development version:

```bash
# Clone repository
git clone https://github.com/tetherless-world/setlr.git
cd setlr

# Install
pip install .
```

### 3. Development Installation

For contributing or development:

```bash
# Clone repository
git clone https://github.com/tetherless-world/setlr.git
cd setlr

# Bootstrap (creates venv, installs dependencies)
./script/bootstrap

# Activate virtual environment
source venv/bin/activate

# Install in editable mode
pip install -e .
```

## Verify Installation

Check that setlr is installed:

```bash
# Check CLI tool
setlr --help

# Check Python module
python -c "import setlr; print(setlr.__version__)"
```

Expected output:
```
Usage: setlr [OPTIONS] SCRIPT
...

1.0.2
```

## Dependencies

SETLr automatically installs these dependencies:

### Core Dependencies

- **rdflib** (>=6.0.0) - RDF processing
- **pandas** (>=0.23.0) - DataFrame operations
- **jinja2** - Template rendering
- **click** - CLI interface
- **tqdm** - Progress bars

### Data Format Support

- **beautifulsoup4**, **lxml** - XML/HTML parsing
- **xlrd** - Excel files
- **ijson** - Streaming JSON

### Additional Features

- **pyshacl[js]** - SHACL validation
- **requests** - HTTP data sources
- **toposort** - Dependency ordering
- **python-slugify** - String slugification

## Virtual Environment (Recommended)

Using a virtual environment isolates setlr from system Python:

```bash
# Create virtual environment
python3 -m venv setlr-env

# Activate (Linux/macOS)
source setlr-env/bin/activate

# Activate (Windows)
setlr-env\\Scripts\\activate

# Install setlr
pip install setlr

# When done
deactivate
```

## Troubleshooting

### Issue: `ModuleNotFoundError: No module named 'rdflib'`

**Solution**: Dependencies weren't installed. Try:

```bash
pip install --upgrade pip
pip install setlr --force-reinstall
```

### Issue: `setlr: command not found`

**Solution**: pip's bin directory not in PATH:

```bash
# Find where pip installs scripts
python -m site --user-base

# Add to PATH (Linux/macOS)
export PATH="$HOME/.local/bin:$PATH"

# Or use full path
python -m setlr script.setl.ttl
```

### Issue: Permission denied on Linux

**Solution**: Install for user only:

```bash
pip install --user setlr
```

### Issue: SSL Certificate Error

**Solution**: Update certificates or use --trusted-host:

```bash
pip install --trusted-host pypi.org --trusted-host files.pythonhosted.org setlr
```

## Upgrading

Upgrade to the latest version:

```bash
pip install --upgrade setlr
```

Check current version:

```bash
pip show setlr
```

## Uninstalling

Remove setlr:

```bash
pip uninstall setlr
```

## Docker

Use setlr in Docker:

```dockerfile
FROM python:3.11-slim

# Install setlr
RUN pip install setlr

# Copy your scripts
COPY transform.setl.ttl data.csv /app/

WORKDIR /app

# Run setlr
CMD ["setlr", "transform.setl.ttl"]
```

Build and run:

```bash
docker build -t my-setlr-app .
docker run my-setlr-app
```

## Next Steps

- Follow the [Quick Start Guide](quickstart.md)
- Read the [Tutorial](tutorial.md)
- See [Examples](examples.md)
- Check the [CLI Reference](cli.md)
