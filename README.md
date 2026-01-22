# setlr: Semantic Extract, Transform and Load

[![Unit Tests](https://github.com/tetherless-world/setlr/actions/workflows/test.yml/badge.svg)](https://github.com/tetherless-world/setlr/actions/workflows/test.yml)
[![Lint](https://github.com/tetherless-world/setlr/actions/workflows/lint.yml/badge.svg)](https://github.com/tetherless-world/setlr/actions/workflows/lint.yml)
[![codecov](https://codecov.io/gh/tetherless-world/setlr/branch/main/graph/badge.svg)](https://codecov.io/gh/tetherless-world/setlr)

**SETLr** is a powerful Python tool for generating RDF graphs from tabular data using declarative SETL (Semantic Extract, Transform, Load) scripts.

## Features

✨ **Multiple Data Sources**: CSV, Excel, JSON, XML, RDF, SAS files  
🔄 **Flexible Transformations**: JSON-LD templates with Jinja2, Python functions, SPARQL  
⚡ **High Performance**: Streaming XML parsing, pandas DataFrames, progress tracking  
🐍 **Python Integration**: Use as library or CLI tool  
✅ **Validation**: Built-in SHACL validation  
📝 **Well Documented**: Comprehensive guides and API reference  

## Quick Start

### Installation

```bash
pip install setlr
```

### Simple Example

Create `data.csv`:
```csv
ID,Name,Email
1,Alice,alice@example.com
2,Bob,bob@example.com
```

Create `transform.setl.ttl`:
```turtle
@prefix setl: <http://purl.org/twc/vocab/setl/> .
@prefix prov: <http://www.w3.org/ns/prov#> .
@prefix csvw: <http://www.w3.org/ns/csvw#> .
@prefix void: <http://rdfs.org/ns/void#> .
@prefix : <http://example.com/> .

:table a csvw:Table, setl:Table ;
    prov:wasGeneratedBy [ a setl:Extract ; prov:used <data.csv> ] .

:output a void:Dataset ;
    prov:wasGeneratedBy [
        a setl:Transform, setl:JSLDT ;
        prov:used :table ;
        prov:value '''[{
            "@id": "http://example.com/person/{{row.ID}}",
            "@type": "http://xmlns.com/foaf/0.1/Person",
            "http://xmlns.com/foaf/0.1/name": "{{row.Name}}",
            "http://xmlns.com/foaf/0.1/mbox": "mailto:{{row.Email}}"
        }]'''
    ] .
```

Run SETLr:
```bash
setlr transform.setl.ttl
```

### Using from Python

```python
from rdflib import Graph, URIRef
import setlr

# Load SETL script
setl_graph = Graph()
setl_graph.parse("transform.setl.ttl", format="turtle")

# Execute ETL pipeline
resources = setlr.run_setl(setl_graph)

# Access generated RDF
output = resources[URIRef('http://example.com/output')]
print(f"Generated {len(output)} RDF triples")
```

## Documentation

📚 **[Complete Documentation](docs/README.md)** - Full guides and references

**Quick Links:**
- [Tutorial](docs/tutorial.md) - Step-by-step guide to SETLr
- [JSLDT Template Language](docs/jsldt.md) - Transform syntax reference
- [Python API](docs/python-api.md) - Using SETLr from Python
- [Quick Start](docs/quickstart.md) - Get started in 5 minutes
- [Examples](docs/examples.md) - Real-world examples

**Advanced Topics:**
- [Streaming XML with XPath](docs/streaming-xml.md) - Efficient large file processing
- [Python Functions](docs/python-functions.md) - Custom Python transforms
- [SPARQL Support](docs/sparql.md) - Query and update endpoints
- [SHACL Validation](docs/shacl.md) - Validate your RDF output

## Key Concepts

SETLr uses RDF (with PROV-O vocabulary) to describe ETL workflows:

1. **Extract**: Load data from sources (CSV, Excel, JSON, XML, RDF, SAS)
2. **Transform**: Apply templates or Python scripts to generate RDF
3. **Load**: Save to files or SPARQL endpoints

## Supported Formats

**Input:**
- Tabular: CSV, TSV, Excel (XLS/XLSX), SAS (XPORT/SAS7BDAT)
- Structured: JSON (with ijson selectors), XML (with XPath streaming)
- Semantic: RDF (Turtle, JSON-LD, RDF/XML, etc.), OWL Ontologies

**Output:**
- RDF: Turtle, TriG, N-Triples, N3, RDF/XML, JSON-LD
- Destinations: Files, SPARQL Update endpoints

## Examples

See the [examples/](example/) directory for complete working examples:

- `social.setl.ttl` - Basic CSV to RDF with conditionals and loops
- `ontology.setl.ttl` - OWL ontology transformation with SHACL shapes

## Development

```bash
# Clone repository
git clone https://github.com/tetherless-world/setlr.git
cd setlr

# Bootstrap (creates venv and installs dependencies)
./script/bootstrap

# Activate virtual environment  
source venv/bin/activate

# Run tests
./script/build

# Run linter
flake8 setlr/
```

## Contributing

Contributions are welcome! Please see our [Contributing Guide](CONTRIBUTING.md) for details on:
- Development setup and workflow
- Code standards and style guidelines
- Testing requirements
- Pull request process

Please note that this project follows a [Code of Conduct](CODE_OF_CONDUCT.md). By participating, you are expected to uphold this code.

## License

Apache License 2.0 - see [LICENSE](LICENSE) file for details.

## Citation

If you use SETLr in your research, please cite:

```bibtex
@software{setlr,
  title = {SETLr: Semantic Extract, Transform and Load},
  author = {McCusker, Jamie},
  year = {2024},
  url = {https://github.com/tetherless-world/setlr}
}
```

## Support

- 📖 [Documentation](docs/README.md)
- 🐛 [Issue Tracker](https://github.com/tetherless-world/setlr/issues)
- 💬 [Discussions](https://github.com/tetherless-world/setlr/discussions)
- 🔒 [Security Policy](SECURITY.md) - Report security vulnerabilities
