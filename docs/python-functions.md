# Python Scripts in Transforms

SETLr allows you to execute custom Python code within transforms using `setl:PythonScript`.

## Overview

Python scripts in SETLr can:
- Perform complex data processing within transforms
- Manipulate RDF graphs
- Access the transform context
- Execute custom logic

⚠️ **Note**: This is an advanced feature. For most use cases, [JSLDT templates](jsldt.md) are recommended.

⚠️ **Security Warning**: Python scripts execute with full system access. Only run trusted SETL scripts.

## Using Python Scripts

Python scripts are used **within** JSLDT transforms to manipulate graphs:

```turtle
@prefix setl: <http://purl.org/twc/vocab/setl/> .
@prefix prov: <http://www.w3.org/ns/prov#> .
@prefix void: <http://rdfs.org/ns/void#> .
@prefix csvw: <http://www.w3.org/ns/csvw#> .
@prefix : <http://example.com/> .

# Extract data
:dataTable a csvw:Table, setl:Table ;
    prov:wasGeneratedBy [
        a setl:Extract ;
        prov:used <data.csv> ;
    ] .

# Transform with JSLDT that uses a Python script
:processedGraph a void:Dataset ;
    prov:wasGeneratedBy [
        a setl:Transform, setl:JSLDT ;
        prov:used :dataTable ;
        prov:used [
            a setl:PythonScript ;
            prov:value '''
# Variables available: graph, setl_graph
print(f"Processing transform with {len(graph)} triples")
''' 
        ] ;
        prov:value '''[{
            "@id": "http://example.com/{{row.ID}}",
            "@type": "http://example.com/Item",
            "http://example.com/name": "{{row.Name}}"
        }]''' ;
    ] .
```

## Available Variables

Inside Python scripts within transforms:

| Variable | Type | Description |
|----------|------|-------------|
| `graph` | rdflib.Graph | The transform output graph |
| `setl_graph` | rdflib.Graph | The SETL script description graph |

## Example: Count Triples by Type

```turtle
:validatedGraph a void:Dataset ;
    prov:wasGeneratedBy [
        a setl:Transform, setl:JSLDT ;
        prov:used :dataTable ;
        prov:used [
            a setl:PythonScript ;
            prov:value '''
from rdflib.namespace import RDF

# Count triples by type
types = {}
for s, p, o in graph.triples((None, RDF.type, None)):
    t = str(o)
    types[t] = types.get(t, 0) + 1

print("Triple counts by type:")
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

## Example: Add Computed Triples

```turtle
:enrichedGraph a void:Dataset ;
    prov:wasGeneratedBy [
        a setl:Transform, setl:JSLDT ;
        prov:used :salesTable ;
        prov:used [
            a setl:PythonScript ;
            prov:value '''
from rdflib import Namespace, Literal
from rdflib.namespace import RDF

ex = Namespace("http://example.com/")

# Add summary statistics
total_value = 0
count = 0

for s, p, o in graph.triples((None, ex.value, None)):
    try:
        total_value += float(o)
        count += 1
    except:
        pass

if count > 0:
    summary = ex.Summary
    graph.add((summary, RDF.type, ex.Statistics))
    graph.add((summary, ex.total, Literal(total_value)))
    graph.add((summary, ex.average, Literal(total_value / count)))
    graph.add((summary, ex.count, Literal(count)))
'''
        ] ;
        prov:value '''[{
            "@id": "http://example.com/sale/{{row.ID}}",
            "@type": "http://example.com/Sale",
            "http://example.com/value": "{{row.Value}}"
        }]''' ;
    ] .
```

## Best Practices

### 1. Prefer JSLDT Templates

For most transformations, use JSLDT templates instead of Python:

```turtle
# Good: Simple and declarative
prov:value '''[{
    "@id": "http://example.com/{{row.ID}}",
    "@type": "foaf:Person",
    "foaf:name": "{{row.Name}}"
}]'''
```

### 2. Use Python for Post-Processing

Use Python scripts for:
- Computing aggregates after template processing
- Adding summary statistics
- Validating generated RDF
- Logging and debugging

### 3. Keep Scripts Focused

```python
# Good: Single purpose
for s, p, o in graph.triples((None, RDF.type, ex.Item)):
    count += 1
print(f"Generated {count} items")

# Avoid: Complex multi-purpose scripts
# (use multiple transforms instead)
```

### 4. Handle Errors Gracefully

```python
# Good: Error handling
try:
    value = float(row['Value'])
    # Process value
except (ValueError, KeyError) as e:
    print(f"Warning: {e}")

# Avoid: Unhandled exceptions that crash the transform
```

## Common Patterns

### Validate Generated RDF

```python
# Check for required properties
from rdflib.namespace import RDF
ex = Namespace("http://example.com/")

for item in graph.subjects(RDF.type, ex.Item):
    has_name = (item, ex.name, None) in graph
    if not has_name:
        print(f"Warning: {item} missing name property")
```

### Add Cross-References

```python
# Link related entities
ex = Namespace("http://example.com/")

items = list(graph.subjects(RDF.type, ex.Item))
for i, item1 in enumerate(items):
    for item2 in items[i+1:]:
        # Add relationship based on some logic
        graph.add((item1, ex.related, item2))
```

### Compute Derived Properties

```python
# Calculate totals, averages, etc.
from rdflib import Literal

ex = Namespace("http://example.com/")
total = sum(float(o) for s, p, o in graph.triples((None, ex.price, None)))

summary = ex.PriceSummary
graph.add((summary, ex.totalPrice, Literal(total)))
```

## Debugging

Enable debug logging:

```python
import logging
import setlr

setlr.logger.setLevel(logging.DEBUG)
```

Add print statements in your script:

```python
print(f"Graph has {len(graph)} triples")
print(f"Types: {set(o for s, p, o in graph.triples((None, RDF.type, None)))}")
```

## Limitations

- Python scripts run **after** JSLDT template processing
- Cannot modify the input table
- Cannot access row data directly (use JSLDT templates for that)
- Scripts execute in the transform context

## See Also

- [JSLDT Template Language](jsldt.md) - Recommended transformation approach
- [Python API](python-api.md) - Using setlr from Python
- [Tutorial](tutorial.md) - Step-by-step guide
- [Examples](examples.md) - Complete examples
