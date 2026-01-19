# Streaming XML with XPath

SETLr supports efficient streaming parsing of large XML files using XPath filtering.

## Overview

For large XML files, loading the entire document into memory can be problematic. SETLr's streaming XML parser uses `iterparse` to process XML elements incrementally, combined with XPath expressions to filter only the elements you need.

## Basic XML Extraction

```turtle
@prefix setl: <http://purl.org/twc/vocab/setl/> .
@prefix prov: <http://www.w3.org/ns/prov#> .
@prefix : <http://example.com/> .

:xmlTable a setl:Table ;
    prov:wasGeneratedBy [
        a setl:Extract ;
        prov:used <data.xml> ;
    ] .
```

This extracts all elements from the XML file into a pandas DataFrame.

## XPath Filtering

Use `setl:xpath` to select specific elements:

```turtle
:bookTable a setl:Table ;
    setl:xpath "//book" ;  # Select only <book> elements
    prov:wasGeneratedBy [
        a setl:Extract ;
        prov:used <catalog.xml> ;
    ] .
```

### Example XML File

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
  <magazine id="mg001">
    <title>Tech Weekly</title>
    <price>9.99</price>
  </magazine>
</catalog>
```

With `setl:xpath "//book"`, only the `<book>` elements are extracted, not the `<magazine>`.

## Advanced XPath Patterns

### Select by Attribute

```turtle
:expensiveBooks a setl:Table ;
    setl:xpath "//book[price > 10]" ;
    prov:wasGeneratedBy [
        a setl:Extract ;
        prov:used <catalog.xml> ;
    ] .
```

### Select Nested Elements

```turtle
:chapters a setl:Table ;
    setl:xpath "//book/chapter" ;
    prov:wasGeneratedBy [
        a setl:Extract ;
        prov:used <book.xml> ;
    ] .
```

### Combine Conditions

```turtle
:computerBooks a setl:Table ;
    setl:xpath "//book[genre='Computer']" ;
    prov:wasGeneratedBy [
        a setl:Extract ;
        prov:used <catalog.xml> ;
    ] .
```

## DTD Validation

For XML files with DTD declarations, you can enable validation:

```turtle
:validatedTable a setl:Table, setl:DTDValidatedXML ;
    setl:xpath "//record" ;
    prov:wasGeneratedBy [
        a setl:Extract ;
        prov:used <data.xml> ;
    ] .
```

## Performance Considerations

### Memory Efficiency

Streaming XML parsing is particularly useful for:
- **Large files** (> 100 MB)
- **Many elements** (thousands of records)
- **Limited memory** environments

The parser only keeps the current element in memory, not the entire document.

### Progress Tracking

SETLr shows a progress bar when parsing XML:

```
Processing XML: 45%|████▌     | 1234/2750 [00:12<00:15, 98.2 elements/s]
```

## Complete Example

### SETL Script (`books.setl.ttl`)

```turtle
@prefix setl: <http://purl.org/twc/vocab/setl/> .
@prefix prov: <http://www.w3.org/ns/prov#> .
@prefix csvw: <http://www.w3.org/ns/csvw#> .
@prefix void: <http://rdfs.org/ns/void#> .
@prefix : <http://example.com/> .

# Extract: Parse XML with XPath
:booksTable a setl:Table, csvw:Table ;
    setl:xpath "//book" ;
    prov:wasGeneratedBy [
        a setl:Extract ;
        prov:used <catalog.xml> ;
    ] .

# Transform: Convert to RDF
:booksGraph a void:Dataset ;
    prov:wasGeneratedBy [
        a setl:Transform, setl:JSLDT ;
        prov:used :booksTable ;
        prov:value '''[{
            "@id": "http://example.com/book/{{row['@id']}}",
            "@type": "http://schema.org/Book",
            "http://schema.org/author": "{{row.author}}",
            "http://schema.org/name": "{{row.title}}",
            "http://schema.org/genre": "{{row.genre}}"
        }]''' ;
    ] .
```

### Run from Python

```python
from rdflib import Graph, URIRef
import setlr

# Load SETL script
setl_graph = Graph()
setl_graph.parse("books.setl.ttl", format="turtle")

# Execute (streaming XML parse happens here)
resources = setlr.run_setl(setl_graph)

# Access parsed data
books_df = resources[URIRef('http://example.com/booksTable')]
print(f"Extracted {len(books_df)} books")
print(books_df.head())

# Access generated RDF
books_graph = resources[URIRef('http://example.com/booksGraph')]
print(f"Generated {len(books_graph)} triples")
```

## XML Attributes

XML attributes are accessible in the DataFrame with `@` prefix:

```xml
<book id="bk101" isbn="1234567890">
  <title>My Book</title>
</book>
```

Access in template:
```
"{{row['@id']}}"     # → "bk101"
"{{row['@isbn']}}"   # → "1234567890"
"{{row.title}}"      # → "My Book"
```

## Nested Elements

For nested XML structures:

```xml
<book>
  <metadata>
    <author>John Doe</author>
    <year>2024</year>
  </metadata>
  <title>Example</title>
</book>
```

Use nested XPath:
```turtle
:metadata a setl:Table ;
    setl:xpath "//book/metadata" ;
    prov:wasGeneratedBy [
        a setl:Extract ;
        prov:used <books.xml> ;
    ] .
```

## Limitations

- XPath 1.0 syntax only (not full XPath 2.0)
- Element text content and attributes only (no CDATA sections)
- Cannot access parent or sibling elements after extraction

## See Also

- [JSLDT Template Language](jsldt.md) - For transforming extracted data
- [Python API](python-api.md) - Using XML extraction from Python
- [Examples](examples.md) - More XML examples
