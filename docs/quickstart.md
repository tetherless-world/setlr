# Quick Start Guide

Get up and running with SETLr in 5 minutes!

## Installation

```bash
pip install setlr
```

## Your First SETL Script

### 1. Create Sample Data

Save this as `people.csv`:

```csv
ID,Name,Email
1,Alice Smith,alice@example.com
2,Bob Jones,bob@example.com
```

### 2. Create a SETL Script

Save this as `people.setl.ttl`:

```turtle
@prefix setl: <http://purl.org/twc/vocab/setl/> .
@prefix prov: <http://www.w3.org/ns/prov#> .
@prefix csvw: <http://www.w3.org/ns/csvw#> .
@prefix void: <http://rdfs.org/ns/void#> .
@prefix dcterms: <http://purl.org/dc/terms/> .
@prefix pv: <http://purl.org/net/provenance/ns#> .
@prefix : <http://example.com/> .

# Extract: Load the CSV file
:peopleTable a csvw:Table, setl:Table ;
    csvw:delimiter "," ;
    prov:wasGeneratedBy [
        a setl:Extract ;
        prov:used <people.csv> ;
    ] .

# Transform: Convert to RDF using JSON-LD template
:peopleGraph a void:Dataset ;
    prov:wasGeneratedBy [
        a setl:Transform, setl:JSLDT ;
        prov:used :peopleTable ;
        setl:hasContext '''{
            "foaf": "http://xmlns.com/foaf/0.1/"
        }''' ;
        prov:value '''[{
            "@id": "http://example.com/person/{{row.ID}}",
            "@type": "foaf:Person",
            "foaf:name": "{{row.Name}}",
            "foaf:mbox": "mailto:{{row.Email}}"
        }]''' ;
    ] .

# Load: Save to file
<people.ttl> a pv:File ;
    dcterms:format "text/turtle" ;
    prov:wasGeneratedBy [
        a setl:Load ;
        prov:used :peopleGraph ;
    ] .
```

### 3. Run SETLr

```bash
setlr people.setl.ttl
```

This creates `people.ttl` with RDF output:

```turtle
@prefix foaf: <http://xmlns.com/foaf/0.1/> .

<http://example.com/person/1> a foaf:Person ;
    foaf:name "Alice Smith" ;
    foaf:mbox "mailto:alice@example.com" .

<http://example.com/person/2> a foaf:Person ;
    foaf:name "Bob Jones" ;
    foaf:mbox "mailto:bob@example.com" .
```

## Using from Python

```python
from rdflib import Graph, URIRef
import setlr

# Load SETL script
setl_graph = Graph()
setl_graph.parse("people.setl.ttl", format="turtle")

# Execute
resources = setlr.run_setl(setl_graph)

# Access generated RDF
people_graph = resources[URIRef('http://example.com/peopleGraph')]
print(f"Generated {len(people_graph)} triples")

# Query the graph
for person in people_graph.subjects(predicate=URIRef('http://xmlns.com/foaf/0.1/name')):
    print(f"Person: {person}")
```

## Next Steps

- Learn more about [JSLDT Template Language](jsldt.md)
- Explore [Advanced Features](advanced.md)
- See more [Examples](examples.md)
- Read the [Full Tutorial](tutorial.md)
