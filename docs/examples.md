# Examples

Complete working examples demonstrating SETLr features.

## Example 1: Basic CSV to RDF

Transform a simple CSV file into FOAF RDF.

### Input: people.csv

```csv
ID,Name,Email,Age
1,Alice Smith,alice@example.com,30
2,Bob Jones,bob@example.com,25
3,Carol White,carol@example.com,35
```

### SETL Script: people.setl.ttl

```turtle
@prefix setl: <http://purl.org/twc/vocab/setl/> .
@prefix prov: <http://www.w3.org/ns/prov#> .
@prefix csvw: <http://www.w3.org/ns/csvw#> .
@prefix void: <http://rdfs.org/ns/void#> .
@prefix dcterms: <http://purl.org/dc/terms/> .
@prefix pv: <http://purl.org/net/provenance/ns#> .
@prefix : <http://example.com/> .

:table a csvw:Table, setl:Table ;
    csvw:delimiter "," ;
    prov:wasGeneratedBy [
        a setl:Extract ;
        prov:used <people.csv> ;
    ] .

:graph a void:Dataset ;
    prov:wasGeneratedBy [
        a setl:Transform, setl:JSLDT ;
        prov:used :table ;
        setl:hasContext '''{
            "foaf": "http://xmlns.com/foaf/0.1/"
        }''' ;
        prov:value '''[{
            "@id": "http://example.com/person/{{row.ID}}",
            "@type": "foaf:Person",
            "foaf:name": "{{row.Name}}",
            "foaf:mbox": "mailto:{{row.Email}}",
            "foaf:age": "{{row.Age}}"
        }]''' ;
    ] .

<people.ttl> a pv:File ;
    dcterms:format "text/turtle" ;
    prov:wasGeneratedBy [
        a setl:Load ;
        prov:used :graph ;
    ] .
```

### Run

```bash
setlr people.setl.ttl
```

### Output: people.ttl

```turtle
@prefix foaf: <http://xmlns.com/foaf/0.1/> .

<http://example.com/person/1> a foaf:Person ;
    foaf:age "30" ;
    foaf:mbox "mailto:alice@example.com" ;
    foaf:name "Alice Smith" .

<http://example.com/person/2> a foaf:Person ;
    foaf:age "25" ;
    foaf:mbox "mailto:bob@example.com" ;
    foaf:name "Bob Jones" .

<http://example.com/person/3> a foaf:Person ;
    foaf:age "35" ;
    foaf:mbox "mailto:carol@example.com" ;
    foaf:name "Carol White" .
```

## Example 2: Conditionals and Iteration

Handle optional fields and delimited values.

### Input: social.csv

```csv
ID,Name,MarriedTo,Friends
Alice,Alice Smith,Bob,Bob; Carol
Bob,Bob Smith,Alice,Alice; Carol; Dave
Carol,Carol White,,Alice; Bob
Dave,Dave Jones,,Bob
```

### SETL Script: social.setl.ttl

```turtle
@prefix setl: <http://purl.org/twc/vocab/setl/> .
@prefix prov: <http://www.w3.org/ns/prov#> .
@prefix csvw: <http://www.w3.org/ns/csvw#> .
@prefix void: <http://rdfs.org/ns/void#> .
@prefix dcterms: <http://purl.org/dc/terms/> .
@prefix pv: <http://purl.org/net/provenance/ns#> .
@prefix : <http://example.com/> .

:table a csvw:Table, setl:Table ;
    prov:wasGeneratedBy [
        a setl:Extract ;
        prov:used <social.csv> ;
    ] .

:graph a void:Dataset ;
    prov:wasGeneratedBy [
        a setl:Transform, setl:JSLDT ;
        prov:used :table ;
        setl:hasContext '''{
            "foaf": "http://xmlns.com/foaf/0.1/",
            "schema": "http://schema.org/"
        }''' ;
        prov:value '''[{
            "@id": "http://example.com/person/{{row.ID}}",
            "@type": "foaf:Person",
            "foaf:name": "{{row.Name}}",
            "schema:spouse": [{
                "@if": "not isempty(row.MarriedTo)",
                "@id": "http://example.com/person/{{row.MarriedTo}}"
            }],
            "foaf:knows": [{
                "@if": "not isempty(row.Friends)",
                "@for": "friend in row.Friends.split('; ')",
                "@do": { "@id": "http://example.com/person/{{friend}}" }
            }]
        }]''' ;
    ] .

<social.ttl> a pv:File ;
    dcterms:format "text/turtle" ;
    prov:wasGeneratedBy [
        a setl:Load ;
        prov:used :graph ;
    ] .
```

**Key Features:**
- `@if` checks for empty MarriedTo field
- `@for` loops over semicolon-separated friends
- Only generates triples when data exists

## Example 3: XML to RDF with XPath

Extract book data from XML with XPath filtering.

### Input: books.xml

```xml
<?xml version="1.0"?>
<catalog>
  <book id="bk101">
    <author>Gambardella, Matthew</author>
    <title>XML Developer's Guide</title>
    <genre>Computer</genre>
    <price>44.95</price>
  </book>
  <book id="bk102">
    <author>Ralls, Kim</author>
    <title>Midnight Rain</title>
    <genre>Fantasy</genre>
    <price>5.95</price>
  </book>
</catalog>
```

### SETL Script: books.setl.ttl

```turtle
@prefix setl: <http://purl.org/twc/vocab/setl/> .
@prefix prov: <http://www.w3.org/ns/prov#> .
@prefix void: <http://rdfs.org/ns/void#> .
@prefix : <http://example.com/> .

:table a setl:Table ;
    setl:xpath "//book" ;
    prov:wasGeneratedBy [
        a setl:Extract ;
        prov:used <books.xml> ;
    ] .

:graph a void:Dataset ;
    prov:wasGeneratedBy [
        a setl:Transform, setl:JSLDT ;
        prov:used :table ;
        prov:value '''[{
            "@id": "http://example.com/book/{{row['@id']}}",
            "@type": "http://schema.org/Book",
            "http://schema.org/author": "{{row.author}}",
            "http://schema.org/name": "{{row.title}}",
            "http://schema.org/genre": "{{row.genre}}",
            "http://schema.org/price": "{{row.price}}"
        }]''' ;
    ] .
```

**Key Features:**
- `setl:xpath` filters to only `<book>` elements
- XML attributes accessed with `row['@id']`
- Efficient streaming parse for large XML files

## Example 4: Python Function Transform

Use custom Python code for complex processing.

### Input: sales.csv

```csv
Product,Quantity,Price
Widget,10,15.99
Gadget,5,29.99
Doohickey,3,9.99
```

### SETL Script: sales.setl.ttl

```turtle
@prefix setl: <http://purl.org/twc/vocab/setl/> .
@prefix prov: <http://www.w3.org/ns/prov#> .
@prefix void: <http://rdfs.org/ns/void#> .
@prefix : <http://example.com/> .

:table a setl:Table ;
    prov:wasGeneratedBy [
        a setl:Extract ;
        prov:used <sales.csv> ;
    ] .

:graph a void:Dataset ;
    prov:wasGeneratedBy [
        a setl:PythonScript ;
        prov:used :table ;
        prov:value '''
from rdflib import Namespace, Literal
from rdflib.namespace import RDF

ex = Namespace("http://example.com/")
schema = Namespace("http://schema.org/")

# Calculate totals
for index, row in table.iterrows():
    total = float(row['Quantity']) * float(row['Price'])
    
    # Create product
    product = ex[f"product/{index}"]
    result.add((product, RDF.type, schema.Product))
    result.add((product, schema.name, Literal(row['Product'])))
    result.add((product, ex.quantity, Literal(row['Quantity'])))
    result.add((product, ex.price, Literal(row['Price'])))
    result.add((product, ex.total, Literal(f"{total:.2f}")))

# Add summary
summary = ex.SalesSummary
result.add((summary, RDF.type, ex.Summary))
result.add((summary, ex.totalRevenue, Literal(f"{table['Quantity'] * table['Price'].astype(float).sum():.2f}")))
''' ;
    ] .
```

**Key Features:**
- Full Python code for complex calculations
- Access pandas DataFrame methods
- Direct RDF triple generation

## Example 5: Combining Multiple Tables

Join data from multiple sources.

### Input Files

employees.csv:
```csv
EmpID,Name,DeptID
1,Alice,10
2,Bob,20
3,Carol,10
```

departments.csv:
```csv
DeptID,DeptName
10,Engineering
20,Sales
```

### SETL Script: combined.setl.ttl

```turtle
@prefix setl: <http://purl.org/twc/vocab/setl/> .
@prefix prov: <http://www.w3.org/ns/prov#> .
@prefix dcterms: <http://purl.org/dc/terms/> .
@prefix void: <http://rdfs.org/ns/void#> .
@prefix : <http://example.com/> .

:employees a setl:Table ;
    prov:wasGeneratedBy [
        a setl:Extract ;
        prov:used <employees.csv> ;
    ] .

:departments a setl:Table ;
    prov:wasGeneratedBy [
        a setl:Extract ;
        prov:used <departments.csv> ;
    ] .

:graph a void:Dataset ;
    prov:wasGeneratedBy [
        a setl:PythonScript ;
        prov:used :employees ;
        prov:qualifiedUsage [
            a prov:Usage ;
            prov:entity :departments ;
            prov:hadRole [ dcterms:identifier "depts" ] ;
        ] ;
        prov:value '''
from rdflib import Namespace, Literal
from rdflib.namespace import RDF
import pandas as pd

ex = Namespace("http://example.com/")

# Get departments table
depts = resources[str(URIRef("http://example.com/departments"))]

# Join tables
merged = pd.merge(table, depts, on='DeptID')

# Generate RDF
for index, row in merged.iterrows():
    emp = ex[f"employee/{row['EmpID']}"]
    result.add((emp, RDF.type, ex.Employee))
    result.add((emp, ex.name, Literal(row['Name'])))
    result.add((emp, ex.department, Literal(row['DeptName'])))
''' ;
    ] .
```

**Key Features:**
- Multiple extract activities
- `prov:qualifiedUsage` for secondary table
- pandas merge for joining data

## Example 6: Using from Python

Complete Python script for ETL.

```python
from rdflib import Graph, Namespace, Literal, URIRef
from rdflib.namespace import RDF, PROV
import setlr
import tempfile
import os

# Define namespaces
setl = Namespace('http://purl.org/twc/vocab/setl/')
void = Namespace('http://rdfs.org/ns/void#')
csvw = Namespace('http://www.w3.org/ns/csvw#')
ex = Namespace('http://example.com/')

# Create sample CSV
with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
    f.write('ID,Name,Value\\n')
    f.write('1,Item A,100\\n')
    f.write('2,Item B,200\\n')
    f.write('3,Item C,150\\n')
    csv_file = f.name

try:
    # Build SETL graph
    setl_graph = Graph()
    setl_graph.bind('setl', setl)
    setl_graph.bind('prov', PROV)
    setl_graph.bind('void', void)
    setl_graph.bind('csvw', csvw)
    setl_graph.bind('ex', ex)

    # Extract
    table = ex.table
    setl_graph.add((table, RDF.type, setl.Table))
    setl_graph.add((table, RDF.type, csvw.Table))
    
    extract = setl_graph.resource(setl_graph.skolemize())
    extract.add(RDF.type, setl.Extract)
    extract.add(PROV.used, URIRef('file://' + csv_file))
    setl_graph.add((table, PROV.wasGeneratedBy, extract.identifier))

    # Transform
    output = ex.output
    setl_graph.add((output, RDF.type, void.Dataset))
    
    transform = setl_graph.resource(setl_graph.skolemize())
    transform.add(RDF.type, setl.Transform)
    transform.add(RDF.type, setl.JSLDT)
    transform.add(PROV.used, table)
    
    template = '''[{
        "@id": "http://example.com/item/{{row.ID}}",
        "@type": "http://example.com/Item",
        "http://example.com/name": "{{row.Name}}",
        "http://example.com/value": "{{row.Value}}"
    }]'''
    transform.add(PROV.value, Literal(template))
    setl_graph.add((output, PROV.wasGeneratedBy, transform.identifier))

    # Execute
    print("Executing SETL script...")
    resources = setlr.run_setl(setl_graph)

    # Access results
    table_df = resources[table]
    print(f"\\nLoaded table with {len(table_df)} rows:")
    print(table_df)

    output_graph = resources[output]
    print(f"\\nGenerated {len(output_graph)} RDF triples")
    
    # Query the graph
    item_type = URIRef('http://example.com/Item')
    items = list(output_graph.subjects(RDF.type, item_type))
    print(f"\\nFound {len(items)} items:")
    for item in items:
        print(f"  - {item}")

    # Save to file
    output_graph.serialize('output.ttl', format='turtle')
    print("\\nSaved to output.ttl")

finally:
    os.unlink(csv_file)
```

## More Examples

Browse the [example/](../example/) directory for additional examples:

- `social.setl.ttl` - Social network with conditionals and loops
- `ontology.setl.ttl` - OWL ontology transformation

## See Also

- [Tutorial](tutorial.md) - Step-by-step learning
- [JSLDT Reference](jsldt.md) - Template language details
- [Python API](python-api.md) - Programmatic usage
- [Advanced Features](advanced.md) - More capabilities
