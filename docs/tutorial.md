# SETLr Tutorial

Learn the fundamentals of SETLr by building a complete ETL pipeline from CSV to RDF.

## Overview

SETLr uses declarative SETL (Semantic Extract, Transform, and Load) workflows described in RDF to transform tabular data into semantic RDF graphs. This tutorial teaches you the core concepts step-by-step.

## Sample Data

Create a file named `social.csv` with this content:

```csv
ID,Name,MarriedTo,Knows,DOB
Alice,Alice Smith,Bob,Bob; Charles,1/12/1983
Bob,Bob Smith,Alice,Alice; Charles,3/23/1985
Charles,Charles Brown,,Alice; Bob,12/15/1955
Dave,Dave Jones,,,4/25/1967
```

## Step 1: Starting Your SETL File

Create `social.setl.ttl` with namespace prefixes:

```turtle
@prefix prov:    <http://www.w3.org/ns/prov#> .
@prefix dcat:    <http://www.w3.org/ns/dcat#> .
@prefix dcterms: <http://purl.org/dc/terms/> .
@prefix void:    <http://rdfs.org/ns/void#> .
@prefix setl:    <http://purl.org/twc/vocab/setl/> .
@prefix csvw:    <http://www.w3.org/ns/csvw#> .
@prefix pv:      <http://purl.org/net/provenance/ns#> .
@prefix :        <http://example.com/setl/> .
```

## Step 2: Extracting Data

Add an Extract activity to load the CSV:

```turtle
:table a csvw:Table, setl:Table ;
    csvw:delimiter "," ;
    prov:wasGeneratedBy [
        a setl:Extract ;
        prov:used <social.csv> ;
    ] .
```

**Key Points:**
- `csvw:Table` indicates CSV format
- `setl:Table` marks it as a SETL table resource
- `csvw:delimiter` specifies the delimiter (default is comma)
- `csvw:skipRows` can skip header rows if needed

### Supported Extract Formats

| Type | Format | Options |
|------|--------|---------|
| `csvw:Table, setl:Table` | CSV/TSV | `csvw:delimiter`, `csvw:skipRows` |
| `setl:Excel, setl:Table` | Excel (XLS/XLSX) | None |
| `setl:XPORT, setl:Table` | SAS XPORT | None |
| `setl:SAS7BDAT, setl:Table` | SAS Dataset | None |
| `void:Dataset` | RDF (Turtle, JSON-LD, etc.) | None |
| `owl:Ontology` | OWL Ontology | None |

## Step 3: Transforming with JSLDT

JSLDT (JSON-LD Templates) transform tables into RDF using Jinja2 templating:

```turtle
<http://example.com/social> a void:Dataset ;
    prov:wasGeneratedBy [
        a setl:Transform, setl:JSLDT ;
        prov:used :table ;
        setl:hasContext '''{
            "foaf": "http://xmlns.com/foaf/0.1/"
        }''' ;
        prov:value '''[{
            "@id": "https://example.com/social/{{row.ID}}",
            "@type": "foaf:Person",
            "foaf:name": "{{row.Name}}"
        }]''' ;
    ] .
```

This generates RDF for each row:

```turtle
<https://example.com/social/Alice> a foaf:Person ;
    foaf:name "Alice Smith" .

<https://example.com/social/Bob> a foaf:Person ;
    foaf:name "Bob Smith" .

# ... etc
```

### Template Variables

Inside JSLDT templates, you have access to:

- `row` - Current row as pandas.Series
- `table` - Full table as pandas.DataFrame
- `name` - Row index
- `isempty()` - Function to check for empty/NaN values
- `hash()` - Generate UUIDs
- `re` - Python regex module
- `resources` - All generated SETL resources

## Step 4: Conditional Elements

Use `@if` to conditionally include elements:

```turtle
prov:value '''[{
    "@id": "https://example.com/social/{{row.ID}}",
    "@type": "foaf:Person",
    "foaf:name": "{{row.Name}}",
    "http://schema.org/spouse": [{
        "@if": "not isempty(row.MarriedTo)",
        "@id": "https://example.com/social/{{row.MarriedTo}}"
    }]
}]''' ;
```

Now only Alice and Bob have `schema:spouse` properties.

**Key Points:**
- `@if` value is a Python expression
- Wrap in array `[{...}]` for valid JSON-LD
- Use `isempty()` to safely check for NaN/None

## Step 5: Iterating with @for

Split delimited values with `@for`:

```turtle
prov:value '''[{
    "@id": "https://example.com/social/{{row.ID}}",
    "@type": "foaf:Person",
    "foaf:name": "{{row.Name}}",
    "foaf:knows": [{
        "@if": "not isempty(row.Knows)",
        "@for": "friend in row.Knows.split('; ')",
        "@do": { "@id": "https://example.com/social/{{friend}}" }
    }]
}]''' ;
```

This creates multiple `foaf:knows` links:

```turtle
<https://example.com/social/Alice> a foaf:Person ;
    foaf:knows <https://example.com/social/Bob>,
               <https://example.com/social/Charles> ;
    foaf:name "Alice Smith" .
```

**Key Points:**
- `@for` iterates over Python iterable
- `@do` is repeated for each item
- Variable (e.g., `friend`) is scoped to the loop

## Step 6: Loading Results

Save to a file:

```turtle
<social.ttl> a pv:File ;
    dcterms:format "text/turtle" ;
    prov:wasGeneratedBy [
        a setl:Load ;
        prov:used <http://example.com/social> ;
    ] .
```

### Supported Formats

- **RDF/XML**: `application/rdf+xml`, `text/rdf` (default)
- **Turtle**: `text/turtle`, `application/turtle`
- **N-Triples**: `text/plain`
- **N3**: `text/n3`
- **TriG**: `application/trig`
- **JSON-LD**: `application/json`

### Load to SPARQL Endpoint

```turtle
@prefix sd: <http://www.w3.org/ns/sparql-service-description#> .

:sparql_load a setl:Load, sd:Service ;
    sd:endpoint <http://localhost:3030/dataset/update> ;
    prov:used <http://example.com/social> .
```

## Complete Example

Here's the full `social.setl.ttl`:

```turtle
@prefix prov:    <http://www.w3.org/ns/prov#> .
@prefix dcterms: <http://purl.org/dc/terms/> .
@prefix void:    <http://rdfs.org/ns/void#> .
@prefix setl:    <http://purl.org/twc/vocab/setl/> .
@prefix csvw:    <http://www.w3.org/ns/csvw#> .
@prefix pv:      <http://purl.org/net/provenance/ns#> .
@prefix :        <http://example.com/setl/> .

# Extract
:table a csvw:Table, setl:Table ;
    csvw:delimiter "," ;
    prov:wasGeneratedBy [
        a setl:Extract ;
        prov:used <social.csv> ;
    ] .

# Transform
<http://example.com/social> a void:Dataset ;
    prov:wasGeneratedBy [
        a setl:Transform, setl:JSLDT ;
        prov:used :table ;
        setl:hasContext '''{
            "foaf": "http://xmlns.com/foaf/0.1/",
            "schema": "http://schema.org/"
        }''' ;
        prov:value '''[{
            "@id": "https://example.com/social/{{row.ID}}",
            "@type": "foaf:Person",
            "foaf:name": "{{row.Name}}",
            "schema:spouse": [{
                "@if": "not isempty(row.MarriedTo)",
                "@id": "https://example.com/social/{{row.MarriedTo}}"
            }],
            "foaf:knows": [{
                "@if": "not isempty(row.Knows)",
                "@for": "friend in row.Knows.split('; ')",
                "@do": { "@id": "https://example.com/social/{{friend}}" }
            }]
        }]''' ;
    ] .

# Load
<social.ttl> a pv:File ;
    dcterms:format "text/turtle" ;
    prov:wasGeneratedBy [
        a setl:Load ;
        prov:used <http://example.com/social> ;
    ] .
```

## Running Your SETL Script

### Command Line

```bash
setlr social.setl.ttl
```

This creates `social.ttl` with the RDF output.

### From Python

```python
from rdflib import Graph, URIRef
import setlr

# Load script
setl_graph = Graph()
setl_graph.parse("social.setl.ttl", format="turtle")

# Execute
resources = setlr.run_setl(setl_graph)

# Access results
social_graph = resources[URIRef('http://example.com/social')]
print(f"Generated {len(social_graph)} triples")
```

## Next Steps

- Learn more about [JSLDT Template Language](jsldt.md)
- Explore [Advanced Features](advanced.md):
  - [Streaming XML](streaming-xml.md)
  - [Python Functions](python-functions.md)
  - [SPARQL Support](sparql.md)
  - [SHACL Validation](shacl.md)
- See more [Examples](examples.md)
- Check the [Python API Reference](python-api.md)
