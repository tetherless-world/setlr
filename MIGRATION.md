# Migration to pyproject.toml and API Improvements

This document describes the changes made to migrate the project to modern Python packaging standards and improve the API.

## Changes Made

### 1. Migration to pyproject.toml

The project has been migrated from `setup.py` to `pyproject.toml`, following PEP 517/518 standards for modern Python packaging.

- **New file**: `pyproject.toml` - Contains all project metadata, dependencies, and build configuration
- **Status of setup.py**: The old `setup.py` file is still present for compatibility but is no longer the primary packaging configuration

### 2. Code Restructuring

The implementation code has been moved from `setlr/__init__.py` to `setlr/core.py` following best practices:

- **setlr/core.py**: Contains all implementation code (916+ lines)
- **setlr/__init__.py**: Now serves as a clean public API interface (~90 lines)

This separation provides:
- Better code organization
- Clearer public API surface
- Easier maintenance
- Improved IDE support and code navigation

### 3. New Public API: `run_setl()`

A new, well-documented public function `run_setl()` has been introduced:

```python
from rdflib import ConjunctiveGraph
from setlr import run_setl

# Load a SETL script
setl_graph = ConjunctiveGraph()
setl_graph.parse("my_script.setl.ttl", format="turtle")

# Execute the script
resources = run_setl(setl_graph)

# Access generated resources
output_graph = resources['http://example.com/output']
```

**Features:**
- Comprehensive docstring with examples
- Proper type hints in documentation
- Clear description of parameters and return values
- Usage examples

### 4. Backward Compatibility

The old `_setl()` function is still available for backward compatibility:

```python
from setlr import _setl  # Still works, but deprecated

# Old code continues to work
resources = _setl(setl_graph)
```

**Deprecation Warning:**
- Using `_setl()` will emit a `DeprecationWarning`
- The warning suggests using `run_setl()` instead
- No breaking changes - existing code continues to work

### 5. Exported API

The following are now officially exported from the `setlr` package:

**Main Functions:**
- `run_setl()` - Primary API function (recommended)
- `_setl()` - Deprecated, use `run_setl()` instead
- `main()` - CLI entry point

**Utility Functions:**
- `read_csv()`, `read_excel()`, `read_json()`, `read_xml()`, `read_graph()`
- `extract()`, `json_transform()`, `transform()`, `load()`
- `isempty()`, `hash()`, `camelcase()`, `get_content()`

**Namespaces:**
- `csvw`, `ov`, `setl`, `prov`, `pv`, `sp`, `sd`, `dc`, `void`, `shacl`, `api_vocab`

## Migration Guide for Users

### If you were using `_setl()`:

**Before:**
```python
from setlr import _setl

resources = _setl(setl_graph)
```

**After (recommended):**
```python
from setlr import run_setl

resources = run_setl(setl_graph)
```

**Note:** Your old code will continue to work, but you'll see a deprecation warning. Update at your convenience.

### If you were importing internal functions:

**Before:**
```python
from setlr import read_csv, extract
```

**After:**
```python
from setlr import read_csv, extract  # Still works!
```

No changes needed - all utility functions are properly exported.

## For Package Maintainers

### Building the Package

With pyproject.toml, you can now build the package using modern tools:

```bash
# Install build tool
pip install build

# Build the package
python -m build
```

This creates both wheel and source distributions in the `dist/` directory.

### Installing from Source

```bash
# Development installation
pip install -e .

# Regular installation
pip install .
```

### Running Tests

```bash
# Install test dependencies
pip install nose2 coverage

# Run tests
nose2 --verbose
```

## Benefits of This Migration

1. **Modern Standards**: Uses PEP 517/518 standards for Python packaging
2. **Better Documentation**: Clear, comprehensive API documentation
3. **Improved Structure**: Cleaner separation between public API and implementation
4. **Backward Compatible**: No breaking changes for existing users
5. **Future-Proof**: Follows current Python best practices
6. **Better IDE Support**: Clearer module structure aids code completion and navigation

## Questions or Issues?

If you encounter any issues with the migration or have questions about the new API, please open an issue on GitHub.
