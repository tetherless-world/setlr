# SETLr Documentation

Welcome to the SETLr (Semantic Extract, Transform and Load-er) documentation!

## Table of Contents

1. [Quick Start](quickstart.md)
2. [Installation](installation.md)
3. [Tutorial](tutorial.md)
4. [JSLDT Template Language](jsldt.md)
5. [Python API](python-api.md)
6. [Advanced Features](advanced.md)
   - [Streaming XML with XPath](streaming-xml.md)
   - [Python Functions in Transforms](python-functions.md)
   - [SPARQL Support](sparql.md)
   - [SHACL Validation](shacl.md)
7. [Examples](examples.md)
8. [CLI Reference](cli.md)

## What is SETLr?

SETLr is a powerful tool for generating RDF graphs from tabular data sources. It uses declarative SETL (Semantic Extract, Transform, Load) scripts to:

- **Extract** data from CSV, Excel, JSON, XML, and RDF sources
- **Transform** data using JSON-LD templates with Jinja2 templating  
- **Load** results to files or SPARQL endpoints

## Key Features

- 📊 **Multiple Data Formats**: CSV, Excel, JSON, XML, RDF, SAS files
- 🔄 **Powerful Transformations**: JSON-LD templates with @if, @for, @with control structures
- 🐍 **Python Integration**: Call from Python code or use custom Python functions
- ⚡ **Streaming**: Efficient XML parsing for large files with XPath filtering
- ✅ **Validation**: Built-in SHACL validation support
- 🎯 **SPARQL**: Execute SPARQL queries and load to endpoints

## Quick Example

```python
from rdflib import Graph
import setlr

# Load your SETL script
setl_graph = Graph()
setl_graph.parse("my_script.setl.ttl", format="turtle")

# Execute the ETL pipeline
resources = setlr.run_setl(setl_graph)

# Access generated RDF
output_graph = resources[URIRef('http://example.com/output')]
```

## Learn More

- New to SETLr? Start with the [Quick Start Guide](quickstart.md)
- Want to learn the basics? Follow the [Tutorial](tutorial.md)
- Need to write transforms? Check the [JSLDT Template Language](jsldt.md)
- Using Python? See the [Python API Documentation](python-api.md)
