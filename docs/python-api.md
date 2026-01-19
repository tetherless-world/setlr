# Python API Reference

Complete guide to using SETLr programmatically from Python.

## Main Entry Point

### `run_setl(setl_graph)`

Execute a SETL script and return all generated resources.

**Parameters:**
- `setl_graph` (rdflib.Graph): An RDF graph containing the SETL script description

**Returns:**
- `dict`: Dictionary mapping resource URIs (as URIRef objects) to their generated content:
  - Tables → pandas DataFrame
  - RDF Graphs → rdflib.Graph
  - Functions → Python functions

**Example:**

```python
from rdflib import Graph, URIRef
import setlr

# Load SETL script
setl_graph = Graph()
setl_graph.parse("transform.setl.ttl", format="turtle")

# Execute
resources = setlr.run_setl(setl_graph)

# Access resources by URI
table_uri = URIRef('http://example.com/myTable')
if table_uri in resources:
    df = resources[table_uri]
    print(f"Loaded table with {len(df)} rows")

output_uri = URIRef('http://example.com/output')
if output_uri in resources:
    graph = resources[output_uri]
    print(f"Generated {len(graph)} triples")
```

## Complete Python Example

Here's a complete example building a SETL script programmatically:

```python
from rdflib import Graph, Namespace, Literal, URIRef
from rdflib.namespace import RDF, PROV
import setlr
import tempfile

# Define namespaces
setl = Namespace('http://purl.org/twc/vocab/setl/')
void = Namespace('http://rdfs.org/ns/void#')
csvw = Namespace('http://www.w3.org/ns/csvw#')
dcterms = Namespace('http://purl.org/dc/terms/')
ex = Namespace('http://example.com/')

# Create CSV file
with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
    f.write('Name,Age\\n')
    f.write('Alice,30\\n')
    f.write('Bob,25\\n')
    csv_file = f.name

# Build SETL graph
setl_graph = Graph()
setl_graph.bind('setl', setl)
setl_graph.bind('prov', PROV)
setl_graph.bind('void', void)
setl_graph.bind('csvw', csvw)

# Extract: Define table
table = ex.myTable
setl_graph.add((table, RDF.type, setl.Table))
setl_graph.add((table, RDF.type, csvw.Table))
setl_graph.add((table, csvw.delimiter, Literal(',')))

extract = setl_graph.resource(setl_graph.skolemize())
extract.add(RDF.type, setl.Extract)
extract.add(PROV.used, URIRef('file://' + csv_file))
setl_graph.add((table, PROV.wasGeneratedBy, extract.identifier))

# Transform: Define JSON-LD template
output = ex.output
setl_graph.add((output, RDF.type, void.Dataset))

transform = setl_graph.resource(setl_graph.skolemize())
transform.add(RDF.type, setl.Transform)
transform.add(RDF.type, setl.JSLDT)
transform.add(PROV.used, table)

template = '''[{
    "@id": "http://example.com/person/{{row.Name}}",
    "@type": "http://xmlns.com/foaf/0.1/Person",
    "http://xmlns.com/foaf/0.1/name": "{{row.Name}}",
    "http://xmlns.com/foaf/0.1/age": "{{row.Age}}"
}]'''
transform.add(PROV.value, Literal(template))
setl_graph.add((output, PROV.wasGeneratedBy, transform.identifier))

# Execute
resources = setlr.run_setl(setl_graph)

# Access results
output_graph = resources[output]
print(f"Generated {len(output_graph)} RDF triples")

# Query the graph
from rdflib import URIRef as U
foaf_name = U('http://xmlns.com/foaf/0.1/name')
for s, p, o in output_graph.triples((None, foaf_name, None)):
    print(f"{s} has name: {o}")
```

## Utility Functions

SETLr exports several utility functions that can be used independently:

### Data Reading Functions

```python
from rdflib import Graph
import setlr

# Read CSV
csv_graph = Graph()
df = setlr.read_csv('data.csv', csv_graph)

# Read Excel
excel_graph = Graph()
df = setlr.read_excel('data.xlsx', excel_graph)

# Read JSON
json_graph = Graph()
data = setlr.read_json('data.json', json_graph)

# Read XML
xml_graph = Graph()
data = setlr.read_xml('data.xml', xml_graph)

# Read RDF graph
rdf_graph = Graph()
graph = setlr.read_graph('data.ttl', rdf_graph)
```

### Helper Functions

```python
import setlr

# Check if value is empty/NaN
if setlr.isempty(value):
    print("Value is empty")

# Generate hash
hash_value = setlr.hash("some text")  # SHA-256 hash

# Convert to camelCase
name = setlr.camelcase("hello-world")  # Returns "HelloWorld"

# Get content from URL or file
content = setlr.get_content('http://example.com/data.csv', result_graph)
```

## Working with Multiple Tables

You can process multiple tables in a single script:

```python
from rdflib import Graph, Namespace, Literal, URIRef
from rdflib.namespace import RDF, PROV
import setlr

setl = Namespace('http://purl.org/twc/vocab/setl/')
ex = Namespace('http://example.com/')

setl_graph = Graph()
setl_graph.bind('setl', setl)
setl_graph.bind('prov', PROV)

# Extract table 1
table1 = ex.employees
setl_graph.add((table1, RDF.type, setl.Table))
extract1 = setl_graph.resource(setl_graph.skolemize())
extract1.add(RDF.type, setl.Extract)
extract1.add(PROV.used, URIRef('file:///path/to/employees.csv'))
setl_graph.add((table1, PROV.wasGeneratedBy, extract1.identifier))

# Extract table 2
table2 = ex.departments
setl_graph.add((table2, RDF.type, setl.Table))
extract2 = setl_graph.resource(setl_graph.skolemize())
extract2.add(RDF.type, setl.Extract)
extract2.add(PROV.used, URIRef('file:///path/to/departments.csv'))
setl_graph.add((table2, PROV.wasGeneratedBy, extract2.identifier))

# Transform using both tables
# (use prov:qualifiedUsage to reference secondary tables)

# Execute
resources = setlr.run_setl(setl_graph)

# Access both tables
employees_df = resources[table1]
departments_df = resources[table2]
```

## Configuration

### Logging

SETLr uses Python's logging module:

```python
import logging
import setlr

# Set log level
setlr.logger.setLevel(logging.DEBUG)

# Add custom handler
handler = logging.StreamHandler()
handler.setLevel(logging.INFO)
setlr.logger.addHandler(handler)
```

### Processing Options

Control which rows are processed:

```python
# Process only first N rows (for testing)
setlr.core.run_samples = 10  # Process only first 10 rows

# Process all rows
setlr.core.run_samples = -1  # Default: process all
```

## Error Handling

SETLr provides detailed error messages when templates fail:

```python
from rdflib import Graph
import setlr

try:
    setl_graph = Graph()
    setl_graph.parse("script.setl.ttl", format="turtle")
    resources = setlr.run_setl(setl_graph)
except Exception as e:
    print(f"SETL execution failed: {e}")
    # Error includes:
    # - Row data with <empty/missing> markers
    # - Template context (8 lines before error)
    # - Line number in template
    # - Python stack trace
```

## Deprecated API

### `_setl(setl_graph)` [DEPRECATED]

**Note:** Use `run_setl()` instead. This function is kept for backward compatibility but will emit a DeprecationWarning.

```python
import setlr
import warnings

# Old way (deprecated)
with warnings.catch_warnings():
    warnings.simplefilter("ignore", DeprecationWarning)
    resources = setlr._setl(setl_graph)

# New way (recommended)
resources = setlr.run_setl(setl_graph)
```

## Next Steps

- Learn about [JSLDT Template Language](jsldt.md)
- Explore [Advanced Features](advanced.md)
- See [Examples](examples.md)
