# Command-Line Interface (CLI) Reference

Complete reference for the `setlr` command-line tool.

## Synopsis

```bash
setlr [OPTIONS] SCRIPT
```

## Description

Execute a SETL script to perform Extract, Transform, and Load operations on data sources.

## Arguments

### SCRIPT

Path to the SETL script file (Turtle format).

```bash
setlr my_transform.setl.ttl
```

## Options

### `--rdf-validation FILE`

Validate output RDF against SHACL shapes.

```bash
setlr transform.setl.ttl --rdf-validation shapes.ttl
```

**Details:**
- `FILE` should contain SHACL shapes in Turtle format
- Validation runs after transform but before load
- Non-conforming output generates warnings

### `--text-validation FILE`

Validate output against text-based validation rules.

```bash
setlr transform.setl.ttl --text-validation rules.txt
```

### `--quiet, -q`

Suppress progress bars and informational output.

```bash
setlr transform.setl.ttl --quiet
```

Useful for:
- Running in scripts/automation
- Cleaner log output
- CI/CD pipelines

### `-n, --samples N`

Process only the first N rows of each table (for testing).

```bash
setlr transform.setl.ttl -n 10
```

Process first 10 rows only:
- Faster execution for testing
- Verify template logic
- Debug issues with specific rows

Use `-n -1` to process all rows (default).

### `--help`

Show help message and exit.

```bash
setlr --help
```

## Exit Codes

| Code | Meaning |
|------|---------|
| 0 | Success |
| 1 | Error (invalid script, transform failure, etc.) |

## Examples

### Basic Usage

```bash
# Run SETL script
setlr social.setl.ttl
```

### Test with Sample Data

```bash
# Process only first 5 rows
setlr large_dataset.setl.ttl -n 5
```

### Quiet Mode for Scripts

```bash
#!/bin/bash
# automation script
if setlr --quiet transform.setl.ttl; then
    echo "Transform successful"
else
    echo "Transform failed"
    exit 1
fi
```

### With SHACL Validation

```bash
# Validate output against shapes
setlr transform.setl.ttl --rdf-validation shapes.ttl
```

## Input Files

### SETL Script Format

SETL scripts must be valid RDF in Turtle format:

```turtle
@prefix setl: <http://purl.org/twc/vocab/setl/> .
@prefix prov: <http://www.w3.org/ns/prov#> .

# Extract, Transform, Load definitions...
```

### Data Files

Data files are referenced in the SETL script:

```turtle
:table a setl:Table ;
    prov:wasGeneratedBy [
        a setl:Extract ;
        prov:used <data.csv> ;  # Relative or absolute path
    ] .
```

Paths can be:
- **Relative**: `<data.csv>` (relative to SETL script)
- **Absolute**: `</full/path/to/data.csv>`
- **File URL**: `<file:///full/path/to/data.csv>`
- **HTTP URL**: `<http://example.com/data.csv>`

## Output Files

Output files are defined in Load activities:

```turtle
<output.ttl> a pv:File ;
    dcterms:format "text/turtle" ;
    prov:wasGeneratedBy [
        a setl:Load ;
        prov:used :graph ;
    ] .
```

## Environment Variables

### `SETLR_LOG_LEVEL`

Set logging level:

```bash
export SETLR_LOG_LEVEL=DEBUG
setlr transform.setl.ttl
```

Valid levels: DEBUG, INFO, WARNING, ERROR, CRITICAL

## Logging

SETLr logs to stderr with the following levels:

- **INFO**: Progress messages, row counts
- **WARNING**: Non-fatal issues (empty results, etc.)
- **ERROR**: Transform failures, template errors

### Example Log Output

```
INFO:setlr:Extracting data from data.csv
100%|██████████| 1000/1000 [00:02<00:00, 456.78it/s]
INFO:setlr:Transforming table with 1000 rows
INFO:setlr:Generated 5000 triples
INFO:setlr:Loading to output.ttl
```

## Error Messages

SETLr provides detailed error messages for common issues:

### Template Error

```
ERROR:setlr:Error rendering template: 'NoneType' object has no attribute 'split'
ERROR:setlr:Row data: {'ID': '3', 'Name': 'Alice', 'Friends': '<empty/missing>'}
ERROR:setlr:Template context:
ERROR:setlr:>>> 5:     "@for": "f in row.Friends.split(';')",
```

### File Not Found

```
ERROR:setlr:Cannot read file: data.csv (No such file or directory)
```

### Invalid RDF

```
ERROR:setlr:Failed to parse JSON-LD: Expecting property name enclosed in double quotes
```

## Performance Tips

### 1. Use Quiet Mode

```bash
setlr --quiet script.setl.ttl  # Faster without progress bars
```

### 2. Test with Samples

```bash
setlr -n 100 script.setl.ttl  # Test with 100 rows first
```

### 3. Use Persisted Datasets

For large outputs, use `setl:Persisted` in your script:

```turtle
:largeGraph a void:Dataset, setl:Persisted ;
    prov:wasGeneratedBy [ ... ] .
```

### 4. Profile Performance

```bash
time setlr script.setl.ttl  # Measure execution time
```

## Integration Examples

### Shell Script

```bash
#!/bin/bash
set -e  # Exit on error

echo "Running ETL pipeline..."

# Extract and transform
setlr --quiet extract.setl.ttl

# Validate
if setlr --quiet --rdf-validation shapes.ttl transform.setl.ttl; then
    echo "✓ Validation passed"
else
    echo "✗ Validation failed"
    exit 1
fi

echo "Pipeline complete"
```

### Makefile

```makefile
.PHONY: all clean test

all: output.ttl

output.ttl: transform.setl.ttl data.csv
	setlr transform.setl.ttl

test:
	setlr -n 10 transform.setl.ttl

clean:
	rm -f output.ttl
```

### Python Subprocess

```python
import subprocess
import sys

try:
    result = subprocess.run(
        ['setlr', 'transform.setl.ttl'],
        check=True,
        capture_output=True,
        text=True
    )
    print("Success:", result.stdout)
except subprocess.CalledProcessError as e:
    print("Error:", e.stderr, file=sys.stderr)
    sys.exit(1)
```

## See Also

- [Python API](python-api.md) - Using setlr as a library
- [Tutorial](tutorial.md) - Writing SETL scripts
- [Examples](examples.md) - Complete examples
