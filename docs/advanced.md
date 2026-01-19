# Advanced Features

SETLr provides several advanced capabilities beyond basic CSV-to-RDF transformation. This guide covers specialized features for working with large XML files, custom Python code, SPARQL endpoints, and SHACL validation.

## Overview

- **[Streaming XML with XPath](#streaming-xml)** - Efficiently process large XML files with XPath filtering
- **[Python Functions in Transforms](#python-functions)** - Execute custom Python code within transforms
- **[SPARQL Support](#sparql-support)** - Load RDF to SPARQL endpoints
- **[SHACL Validation](#shacl-validation)** - Validate output RDF against SHACL shapes

## Streaming XML with XPath {#streaming-xml}

For large XML files that don't fit in memory, SETLr provides streaming XML parsing with XPath filtering.

### Key Features

- **Memory Efficient**: Uses incremental parsing (iterparse) to process one element at a time
- **XPath Filtering**: Extract only the elements you need
- **Progress Tracking**: Shows progress bar for long-running operations
- **DTD Validation**: Optional validation against document DTD

### Quick Example

```turtle
@prefix setl: <http://purl.org/twc/vocab/setl/> .
@prefix prov: <http://www.w3.org/ns/prov#> .
@prefix : <http://example.com/> .

:xmlTable a setl:Table ;
    setl:xpath "//book" ;  # Extract only <book> elements
    prov:wasGeneratedBy [
        a setl:Extract ;
        prov:used <catalog.xml> ;
    ] .
```

This extracts only `<book>` elements from the XML, ignoring all other elements and reducing memory usage.

### When to Use

- XML files larger than 100 MB
- Files with thousands of elements
- Limited memory environments
- Need to extract specific elements from complex XML

**→ [Full Streaming XML Documentation](streaming-xml.md)**

## Python Functions in Transforms {#python-functions}

Execute custom Python code within JSLDT transforms for complex processing, graph manipulation, and post-processing.

### Key Features

- **Graph Access**: Direct access to the RDF graph being generated
- **Post-Processing**: Add computed triples, aggregates, and statistics
- **Validation**: Check generated RDF for correctness
- **Custom Logic**: Execute arbitrary Python code

### Quick Example

```turtle
@prefix setl: <http://purl.org/twc/vocab/setl/> .
@prefix prov: <http://www.w3.org/ns/prov#> .
@prefix void: <http://rdfs.org/ns/void#> .
@prefix : <http://example.com/> .

:enrichedGraph a void:Dataset ;
    prov:wasGeneratedBy [
        a setl:Transform, setl:JSLDT ;
        prov:used :dataTable ;
        prov:used [
            a setl:PythonScript ;
            prov:value '''
# Variables available: graph, setl_graph
from rdflib.namespace import RDF

# Count triples by type
types = {}
for s, p, o in graph.triples((None, RDF.type, None)):
    types[str(o)] = types.get(str(o), 0) + 1

print("Generated triples by type:")
for t, count in sorted(types.items()):
    print(f"  {t}: {count}")
''' 
        ] ;
        prov:value '''[{
            "@id": "http://example.com/{{row.ID}}",
            "@type": "http://example.com/Item"
        }]''' ;
    ] .
```

### When to Use

- Computing aggregates or statistics after transformation
- Adding cross-references between generated entities
- Validating generated RDF structure
- Complex logic not easily expressed in JSLDT templates

⚠️ **Security Warning**: Python scripts execute with full system access. Only run trusted SETL scripts.

**→ [Full Python Functions Documentation](python-functions.md)**

## SPARQL Support {#sparql-support}

Load transformed RDF directly to SPARQL endpoints for integration with triple stores and semantic web applications.

### Key Features

- **Direct Loading**: Send RDF to SPARQL UPDATE endpoints
- **Integration**: Works with Fuseki, GraphDB, Blazegraph, etc.
- **SPARQL Service Description**: Uses standard W3C vocabulary

### Quick Example

```turtle
@prefix setl: <http://purl.org/twc/vocab/setl/> .
@prefix prov: <http://www.w3.org/ns/prov#> .
@prefix void: <http://rdfs.org/ns/void#> .
@prefix sd: <http://www.w3.org/ns/sparql-service-description#> .
@prefix : <http://example.com/> .

# Transform data (see previous examples)
:myGraph a void:Dataset ;
    prov:wasGeneratedBy [
        a setl:Transform, setl:JSLDT ;
        # ... transform details ...
    ] .

# Load to SPARQL endpoint
:sparql_load a setl:Load, sd:Service ;
    sd:endpoint <http://localhost:3030/dataset/update> ;
    prov:used :myGraph .
```

### Configuration

The SPARQL endpoint URL should point to the UPDATE endpoint:

- **Fuseki**: `http://localhost:3030/dataset/update`
- **GraphDB**: `http://localhost:7200/repositories/repo/statements`
- **Blazegraph**: `http://localhost:9999/blazegraph/namespace/kb/sparql`

### When to Use

- Loading data into semantic web applications
- Integration with existing triple stores
- Building knowledge graphs
- Creating linked data services

### Authentication

For endpoints requiring authentication, use HTTP authentication in the URL or configure credentials in your environment.

## SHACL Validation {#shacl-validation}

Validate transformed RDF against SHACL (Shapes Constraint Language) shapes to ensure data quality and conformance to schemas.

### Key Features

- **W3C Standard**: Uses SHACL specification for validation
- **Pre-Load Validation**: Checks RDF before loading to files or endpoints
- **Detailed Reports**: Shows which constraints failed
- **Schema Enforcement**: Ensure data meets required structure

### Quick Example

Create SHACL shapes file (`shapes.ttl`):

```turtle
@prefix sh: <http://www.w3.org/ns/shacl#> .
@prefix xsd: <http://www.w3.org/2001/XMLSchema#> .
@prefix ex: <http://example.com/> .
@prefix foaf: <http://xmlns.com/foaf/0.1/> .

ex:PersonShape
    a sh:NodeShape ;
    sh:targetClass foaf:Person ;
    sh:property [
        sh:path foaf:name ;
        sh:minCount 1 ;
        sh:datatype xsd:string ;
    ] ;
    sh:property [
        sh:path foaf:mbox ;
        sh:maxCount 1 ;
        sh:nodeKind sh:IRI ;
    ] .
```

Run SETLr with validation:

```bash
setlr transform.setl.ttl --rdf-validation shapes.ttl
```

### Validation Process

1. SETL transform executes and generates RDF
2. Generated RDF is validated against SHACL shapes
3. Validation report is generated
4. If validation passes, RDF is loaded
5. If validation fails, warnings are shown but loading continues

### When to Use

- Enforcing data quality standards
- Ensuring schema conformance
- Catching transformation errors early
- Documenting expected RDF structure

### Common Shape Constraints

**Required Properties:**
```turtle
@prefix sh: <http://www.w3.org/ns/shacl#> .
@prefix foaf: <http://xmlns.com/foaf/0.1/> .

sh:property [
    sh:path foaf:name ;
    sh:minCount 1 ;  # Required
] ;
```

**Data Types:**
```turtle
@prefix sh: <http://www.w3.org/ns/shacl#> .
@prefix schema: <http://schema.org/> .
@prefix xsd: <http://www.w3.org/2001/XMLSchema#> .

sh:property [
    sh:path schema:age ;
    sh:datatype xsd:integer ;
] ;
```

**Value Ranges:**
```turtle
@prefix sh: <http://www.w3.org/ns/shacl#> .
@prefix schema: <http://schema.org/> .

sh:property [
    sh:path schema:age ;
    sh:minInclusive 0 ;
    sh:maxInclusive 150 ;
] ;
```

**Pattern Matching:**
```turtle
@prefix sh: <http://www.w3.org/ns/shacl#> .
@prefix foaf: <http://xmlns.com/foaf/0.1/> .

sh:property [
    sh:path foaf:mbox ;
    sh:pattern "^mailto:" ;
] ;
```

### Installation

SHACL validation requires the `pyshacl` package:

```bash
pip install setlr[validation]
# or
pip install pyshacl[js]
```

## See Also

- [Tutorial](tutorial.md) - Step-by-step guide to SETLr basics
- [JSLDT Template Language](jsldt.md) - Template syntax reference
- [Python API](python-api.md) - Using SETLr from Python code
- [CLI Reference](cli.md) - Command-line options and usage
- [Examples](examples.md) - Complete working examples
