# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [1.0.2] - 2026-01-18

### Changed
- Version bump for package release

## [1.0.1] - 2026-01-18

### Changed
- Migrated from `setup.py` to `pyproject.toml` following PEP 517/518 standards for modern Python packaging
- Restructured codebase: moved implementation from `setlr/__init__.py` to `setlr/core.py` (~916 lines)
- `setlr/__init__.py` now serves as a clean public API interface (~90 lines)

### Added
- New public API function `run_setl()` with comprehensive documentation and type hints
- Proper deprecation warning for `_setl()` function (still available for backward compatibility)
- Improved error messages for NaN/missing values (now displays `<empty/missing>` instead of `nan`)
- Extended JSON error context from 4 to 8 lines before error for better debugging
- Comprehensive API documentation with usage examples

### Fixed
- Improved error reporting for missing data scenarios
- Better context display for JSON syntax errors in templates

## [1.0.0] - 2026-01-18

### Added
- Initial stable release of setlr
- Core SETL (Semantic Extract, Transform, Load) functionality
- Support for generating RDF graphs from tabular data
- CLI tool via `setlr` command
- Data source readers: CSV, Excel, JSON, XML, and RDF graphs
- Template-based transformation using Jinja2
- Named graph support via ConjunctiveGraph
- RDF namespaces: csvw, ov, setl, prov, pv, sp, sd, dc, void, shacl
- Utility functions: `extract()`, `transform()`, `load()`, `hash()`, `camelcase()`
- Python 3.8+ support
- Comprehensive test suite

### Dependencies
- rdflib >= 6.0.0
- pandas >= 0.23.0
- jinja2
- click (CLI support)
- tqdm (progress bars)
- pyshacl[js] (validation)
- beautifulsoup4, lxml (XML/HTML parsing)
- requests (HTTP support)
- toposort (dependency ordering)
- Other utility libraries: numpy, xlrd, ijson, python-slugify

[Unreleased]: https://github.com/tetherless-world/setlr/compare/v1.0.2...HEAD
[1.0.2]: https://github.com/tetherless-world/setlr/compare/v1.0.1...v1.0.2
[1.0.1]: https://github.com/tetherless-world/setlr/compare/v1.0.0...v1.0.1
[1.0.0]: https://github.com/tetherless-world/setlr/releases/tag/v1.0.0
