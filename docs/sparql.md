# SPARQL Support

SETLr provides comprehensive support for SPARQL, allowing you to query RDF data sources and load results to SPARQL Update endpoints.

## Overview

SPARQL integration enables:
- Querying SPARQL endpoints as data sources
- Loading transformed data to SPARQL Update endpoints
- Executing SPARQL queries within transforms
- Combining SPARQL with other data sources

## SPARQL Queries as Data Sources

Use SPARQL SELECT queries to extract data from RDF sources.

### Basic SPARQL Query

```turtle
@prefix setl: <http://purl.org/twc/vocab/setl/> .
@prefix prov: <http://www.w3.org/ns/prov#> .
@prefix : <http://example.com/> .

:sparql_data a setl:Table ;
    prov:wasGeneratedBy [
        a setl:Extract ;
        setl:query '''
            PREFIX foaf: <http://xmlns.com/foaf/0.1/>
            
            SELECT ?name ?email ?homepage
            WHERE {
                ?person a foaf:Person ;
                    foaf:name ?name ;
                    foaf:mbox ?email .
                OPTIONAL { ?person foaf:homepage ?homepage }
            }
        '''
    ] .

:output prov:wasGeneratedBy [
    a setl:Transform, setl:JSLDT ;
    prov:used :sparql_data ;
    prov:value '''[{
        "@for": "row in sparql_data",
        "@do": {
            "@id": "http://example.com/enriched/{{row.name | slugify}}",
            "@type": "EnrichedPerson",
            "originalName": "{{row.name}}",
            "email": "{{row.email}}",
            "homepage": {
                "@if": "row.homepage",
                "@do": "{{row.homepage}}"
            }
        }
    }]'''
] .
```

### Querying Remote Endpoints

Query external SPARQL endpoints:

```turtle
:dbpedia_data a setl:Table ;
    prov:wasGeneratedBy [
        a setl:Extract ;
        setl:endpoint <http://dbpedia.org/sparql> ;
        setl:query '''
            PREFIX dbo: <http://dbpedia.org/ontology/>
            PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
            
            SELECT ?city ?name ?population ?country
            WHERE {
                ?city a dbo:City ;
                    rdfs:label ?name ;
                    dbo:populationTotal ?population ;
                    dbo:country ?country .
                FILTER (lang(?name) = "en")
                FILTER (?population > 1000000)
            }
            LIMIT 100
        '''
    ] .
```

### Authenticated Endpoints

For endpoints requiring authentication:

```turtle
:protected_data a setl:Table ;
    prov:wasGeneratedBy [
        a setl:Extract ;
        setl:endpoint <http://example.com/sparql> ;
        setl:username "user" ;
        setl:password "pass" ;
        setl:query '''
            SELECT ?s ?p ?o
            WHERE { ?s ?p ?o }
            LIMIT 100
        '''
    ] .
```

**Security Note**: For production use, load credentials from environment variables:

```python
import os
from rdflib import Graph, Literal
import setlr

# Load SETL script
setl_graph = Graph()
setl_graph.parse('transform.setl.ttl', format='turtle')

# Add credentials from environment
for extract in setl_graph.subjects(RDF.type, setl.Extract):
    if (extract, setl.endpoint, None) in setl_graph:
        username = os.getenv('SPARQL_USERNAME')
        password = os.getenv('SPARQL_PASSWORD')
        if username:
            setl_graph.add((extract, setl.username, Literal(username)))
        if password:
            setl_graph.add((extract, setl.password, Literal(password)))

# Run transform
resources = setlr.run_setl(setl_graph)
```

## Loading to SPARQL Endpoints

Write transformed data to SPARQL Update endpoints.

### Basic SPARQL Update

```turtle
:output a void:Dataset ;
    prov:wasGeneratedBy [
        a setl:Transform, setl:JSLDT ;
        prov:used :input_table ;
        prov:value '''[{
            "@for": "row in input_table",
            "@do": {
                "@id": "http://example.com/entity/{{row.ID}}",
                "@type": "Entity",
                "name": "{{row.Name}}"
            }
        }]'''
    ] ;
    prov:wasAttributedTo [
        a setl:Load ;
        setl:endpoint <http://localhost:3030/dataset/update> ;
        setl:graphName <http://example.com/graph/transformed>
    ] .
```

### Loading to Named Graphs

Specify which named graph to load data into:

```turtle
:load_config a setl:Load ;
    setl:endpoint <http://localhost:3030/mydata/update> ;
    setl:graphName <http://example.com/graph/batch-20240101> ;
    prov:used :output .
```

### Update Operations

Perform custom SPARQL Update operations:

```turtle
:update_operation a setl:Load ;
    setl:endpoint <http://localhost:3030/dataset/update> ;
    setl:updateQuery '''
        PREFIX ex: <http://example.com/>
        
        DELETE { ?s ex:oldProperty ?o }
        INSERT { ?s ex:newProperty ?o }
        WHERE { ?s ex:oldProperty ?o }
    ''' ;
    prov:used :output .
```

### Batch Loading

For large datasets, load in batches:

```python
from rdflib import Graph, URIRef, Namespace
import setlr

SETL = Namespace('http://purl.org/twc/vocab/setl/')

# Process in batches
batch_size = 10000
output_graph = Graph()

# Load and transform data in batches
# Then load each batch to endpoint
for batch_num, batch_data in enumerate(data_batches):
    # Create batch-specific SETL script
    setl_graph = create_batch_setl(batch_data, batch_num)
    
    # Process
    resources = setlr.run_setl(setl_graph)
    
    # Batch is automatically loaded to endpoint by SETL script
    print(f"Loaded batch {batch_num}")
```

## Combining SPARQL with Other Sources

Mix SPARQL data with CSV, JSON, or other sources.

### Join SPARQL with CSV Data

```turtle
# Load CSV data
:csv_table a csvw:Table, setl:Table ;
    prov:wasGeneratedBy [ 
        a setl:Extract ; 
        prov:used <people.csv> 
    ] .

# Query related RDF data
:rdf_enrichment a setl:Table ;
    prov:wasGeneratedBy [
        a setl:Extract ;
        setl:endpoint <http://example.com/sparql> ;
        setl:query '''
            SELECT ?id ?category ?score
            WHERE {
                ?entity ex:id ?id ;
                    ex:category ?category ;
                    ex:score ?score .
            }
        '''
    ] .

# Combine in transform
:output prov:wasGeneratedBy [
    a setl:Transform, setl:JSLDT ;
    prov:used :csv_table, :rdf_enrichment ;
    prov:value '''[{
        "@for": "person in csv_table",
        "@do": {
            "@id": "http://example.com/person/{{person.ID}}",
            "@type": "Person",
            "name": "{{person.Name}}",
            "enrichment": [{
                "@for": "data in rdf_enrichment",
                "@if": "data.id == person.ID",
                "@do": {
                    "category": "{{data.category}}",
                    "score": "{{data.score}}"
                }
            }]
        }
    }]'''
] .
```

## SPARQL in Python API

Use SPARQL programmatically with the Python API.

### Query Execution

```python
from rdflib import Graph
from SPARQLWrapper import SPARQLWrapper, JSON

# Query a SPARQL endpoint
sparql = SPARQLWrapper("http://dbpedia.org/sparql")
sparql.setQuery("""
    PREFIX dbo: <http://dbpedia.org/ontology/>
    
    SELECT ?city ?population
    WHERE {
        ?city a dbo:City ;
            dbo:populationTotal ?population .
    }
    LIMIT 10
""")
sparql.setReturnFormat(JSON)
results = sparql.query().convert()

# Process results
for result in results["results"]["bindings"]:
    print(f"{result['city']['value']}: {result['population']['value']}")
```

### Update Execution

```python
from SPARQLWrapper import SPARQLWrapper, POST, DIGEST

# Configure endpoint
sparql = SPARQLWrapper("http://localhost:3030/dataset/update")
sparql.setMethod(POST)
sparql.setHTTPAuth(DIGEST)
sparql.setCredentials("user", "password")

# Execute update
sparql.setQuery("""
    PREFIX ex: <http://example.com/>
    
    INSERT DATA {
        GRAPH <http://example.com/graph> {
            ex:entity1 ex:property "value" .
        }
    }
""")
sparql.query()
```

## Best Practices

### 1. Limit Result Sets

Always use LIMIT in queries to prevent memory issues:

```sparql
SELECT ?s ?p ?o
WHERE { ?s ?p ?o }
LIMIT 10000
```

### 2. Use Pagination

For large result sets, paginate:

```sparql
SELECT ?s ?p ?o
WHERE { ?s ?p ?o }
LIMIT 1000
OFFSET 0
```

```sparql
SELECT ?s ?p ?o
WHERE { ?s ?p ?o }
LIMIT 1000
OFFSET 1000
```

### 3. Optimize Queries

- Use specific predicates and types
- Filter early in the query
- Use OPTIONAL sparingly
- Avoid UNION when possible

### 4. Handle Errors

```python
from SPARQLWrapper import SPARQLWrapper
from SPARQLWrapper.SPARQLExceptions import QueryBadFormed, EndPointNotFound

try:
    sparql = SPARQLWrapper("http://example.com/sparql")
    sparql.setQuery("SELECT * WHERE { ?s ?p ?o } LIMIT 10")
    results = sparql.query()
    
except QueryBadFormed as e:
    print(f"Invalid SPARQL query: {e}")
    
except EndPointNotFound as e:
    print(f"Endpoint not found: {e}")
    
except Exception as e:
    print(f"SPARQL error: {e}")
```

### 5. Connection Pooling

Reuse connections for multiple queries:

```python
# Configure once, reuse many times
sparql = SPARQLWrapper("http://example.com/sparql")
sparql.setReturnFormat(JSON)

for query in queries:
    sparql.setQuery(query)
    results = sparql.query().convert()
    process_results(results)
```

### 6. Timeout Configuration

Set timeouts to prevent hanging:

```python
sparql = SPARQLWrapper("http://example.com/sparql")
sparql.setTimeout(30)  # 30 second timeout
```

## Common Use Cases

### 1. Enriching CSV with LOD

Load CSV, enrich with Linked Open Data:

```turtle
:csv_data a csvw:Table ;
    prov:wasGeneratedBy [ a setl:Extract ; prov:used <data.csv> ] .

:lod_enrichment a setl:Table ;
    prov:wasGeneratedBy [
        a setl:Extract ;
        setl:endpoint <http://dbpedia.org/sparql> ;
        setl:query '''SELECT ?person ?abstract WHERE { ... }'''
    ] .

# Combine in transform...
```

### 2. Migrating Between Triplestores

Extract from one triplestore, load to another:

```turtle
:source_data a setl:Table ;
    prov:wasGeneratedBy [
        a setl:Extract ;
        setl:endpoint <http://old-triplestore:3030/data/query> ;
        setl:query '''SELECT * WHERE { ?s ?p ?o }'''
    ] .

:output prov:wasAttributedTo [
    a setl:Load ;
    setl:endpoint <http://new-triplestore:3030/data/update> ;
    setl:graphName <http://example.com/migrated>
] .
```

### 3. Periodic Updates

Query external data and update local store:

```python
import schedule
from rdflib import Graph
import setlr

def update_from_sparql():
    setl_graph = Graph()
    setl_graph.parse('sparql-update.setl.ttl')
    setlr.run_setl(setl_graph)
    print("SPARQL update complete")

# Run every hour
schedule.every().hour.do(update_from_sparql)
```

## Troubleshooting

### Connection Issues

```python
import requests

# Test endpoint connectivity
try:
    response = requests.get("http://example.com/sparql", timeout=5)
    print(f"Endpoint status: {response.status_code}")
except requests.exceptions.RequestException as e:
    print(f"Cannot connect: {e}")
```

### Query Validation

Test queries independently before using in SETL:

```bash
# Use curl to test
curl -X POST http://example.com/sparql \
  -H "Accept: application/sparql-results+json" \
  --data-urlencode "query=SELECT * WHERE { ?s ?p ?o } LIMIT 10"
```

### Debug Logging

Enable debug logging:

```python
import logging

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger('SPARQLWrapper')
logger.setLevel(logging.DEBUG)
```

## Related Documentation

- [Advanced Features](advanced.md) - Multi-source transforms
- [Python API](python-api.md) - Programmatic usage
- [Examples](examples.md) - Complete examples

## Support

For SPARQL-related questions:
- Open a [discussion](https://github.com/tetherless-world/setlr/discussions)
- Report issues on [GitHub](https://github.com/tetherless-world/setlr/issues)
