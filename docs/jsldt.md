# JSLDT Template Language Reference

Complete reference for the JSON-LD Template (JSLDT) language used in SETLr transforms.

## Overview

JSLDT is a template language for generating RDF from tabular data. It combines:
- **JSON-LD** for RDF structure
- **Jinja2** for dynamic values
- **Control structures** (`@if`, `@for`, `@with`) for logic

## Basic Template

```turtle
<http://example.com/output> a void:Dataset ;
    prov:wasGeneratedBy [
        a setl:Transform, setl:JSLDT ;
        prov:used :myTable ;
        prov:value '''[{
            "@id": "http://example.com/item/{{row.ID}}",
            "@type": "http://example.com/Item",
            "http://example.com/name": "{{row.Name}}"
        }]''' ;
    ] .
```

The template is applied to each row in the table, generating separate JSON-LD documents that are merged into one RDF graph.

## Available Variables

Inside JSLDT templates:

| Variable | Type | Description |
|----------|------|-------------|
| `row` | pandas.Series | Current row being processed |
| `table` | pandas.DataFrame | Full source table |
| `name` | int/str | Row index |
| `template` | str | Full JSON template |
| `transform` | rdflib.Resource | Current transform resource |
| `setl_graph` | rdflib.Graph | SETL script graph |
| `resources` | dict | All generated SETL resources |
| `re` | module | Python regex module |

### Built-in Functions

| Function | Description | Example |
|----------|-------------|---------|
| `isempty(value)` | Check if value is NaN/None | `not isempty(row.Email)` |
| `hash(value)` | SHA-256 hash | `hash(row.ID)` |

## Context

Define JSON-LD context with `setl:hasContext`:

```turtle
setl:hasContext '''{
    "foaf": "http://xmlns.com/foaf/0.1/",
    "schema": "http://schema.org/",
    "@vocab": "http://example.com/vocab/"
}''' ;
```

Or inline in the template:

```json
[{
    "@context": {
        "foaf": "http://xmlns.com/foaf/0.1/"
    },
    "@id": "...",
    ...
}]
```

## Jinja2 Templating

All strings (keys and values) are processed as Jinja2 templates.

### Basic Substitution

```json
{
    "@id": "http://example.com/person/{{row.ID}}",
    "http://example.com/name": "{{row.Name}}",
    "http://example.com/email": "{{row.Email}}"
}
```

### Expressions

```json
{
    "@id": "http://example.com/person/{{row.FirstName}}-{{row.LastName}}",
    "http://example.com/fullName": "{{row.FirstName}} {{row.LastName}}",
    "http://example.com/ageInMonths": "{{row.Age * 12}}"
}
```

### Filters

Jinja2 filters are available:

```json
{
    "http://example.com/name": "{{row.Name | upper}}",
    "http://example.com/email": "{{row.Email | lower}}",
    "http://example.com/title": "{{row.Title | title}}"
}
```

### Python Methods

Access pandas Series/DataFrame methods:

```json
{
    "@id": "http://example.com/{{row.Name.replace(' ', '_')}}",
    "http://example.com/items": "{{row.Items.split(';')[0]}}"
}
```

## Control Structures

### @if - Conditional Elements

Include elements only when condition is true:

```json
[{
    "@id": "http://example.com/person/{{row.ID}}",
    "@type": "foaf:Person",
    "foaf:name": "{{row.Name}}",
    "foaf:mbox": [{
        "@if": "not isempty(row.Email)",
        "@id": "mailto:{{row.Email}}"
    }]
}]
```

**Key Points:**
- Wrap in array `[{...}]` to ensure valid JSON-LD
- Condition is Python expression
- Element is omitted if condition is false
- Empty arrays are valid JSON-LD

**Common Patterns:**

```json
// Check for non-empty value
"@if": "not isempty(row.Field)"

// Check string value
"@if": "row.Status == 'active'"

// Check numeric value
"@if": "row.Age >= 18"

// Complex condition
"@if": "not isempty(row.Email) and row.Email.endswith('@example.com')"
```

### @for - Iteration

Repeat elements for each item in an iterable:

```json
[{
    "@id": "http://example.com/person/{{row.ID}}",
    "foaf:knows": [{
        "@if": "not isempty(row.Friends)",
        "@for": "friend in row.Friends.split('; ')",
        "@do": {
            "@id": "http://example.com/person/{{friend}}"
        }
    }]
}]
```

**Key Points:**
- `@for` defines loop variable and iterable
- `@do` specifies what to repeat
- Loop variable is scoped to `@do` block
- Can combine with `@if` for filtering

**Common Patterns:**

```json
// Split delimited string
"@for": "item in row.Items.split('; ')"

// Iterate list
"@for": "tag in row.Tags"

// Enumerate with index
"@for": "i, item in enumerate(row.Items.split(','))"

// Multiple variables (from dict/tuple)
"@for": "key, value in row.iteritems()"
```

### @for with Multiple Variables

```json
[{
    "@for": "p, o in row.iteritems()",
    "@do": {
        "@if": "not isempty(o)",
        "@id": "http://example.com/{{name}}",
        "http://example.com/{{p}}": "{{o}}"
    }
}]
```

This iterates over all columns in the row.

### @with - Variable Binding

Assign values to variables:

```json
[{
    "@id": "http://example.com/person/{{row.ID}}",
    "@with": {
        "fullName": "{{row.FirstName}} {{row.LastName}}",
        "year": "{{row.BirthDate.split('-')[0]}}"
    },
    "@do": {
        "foaf:name": "{{fullName}}",
        "schema:birthYear": "{{year}}"
    }
}]
```

**Benefits:**
- Avoid repeating complex expressions
- Make templates more readable
- Pre-process values

## Advanced Patterns

### Nested Structures

```json
[{
    "@id": "http://example.com/person/{{row.ID}}",
    "@type": "foaf:Person",
    "foaf:name": "{{row.Name}}",
    "schema:address": {
        "@type": "schema:PostalAddress",
        "schema:streetAddress": "{{row.Street}}",
        "schema:addressLocality": "{{row.City}}",
        "schema:addressRegion": "{{row.State}}",
        "schema:postalCode": "{{row.Zip}}"
    }
}]
```

### Arrays of Values

```json
[{
    "@id": "http://example.com/person/{{row.ID}}",
    "foaf:name": "{{row.Name}}",
    "foaf:knows": [
        { "@id": "http://example.com/person/Alice" },
        { "@id": "http://example.com/person/Bob" }
    ]
}]
```

### Typed Literals

```json
[{
    "@id": "http://example.com/person/{{row.ID}}",
    "foaf:age": {
        "@value": "{{row.Age}}",
        "@type": "http://www.w3.org/2001/XMLSchema#integer"
    },
    "schema:birthDate": {
        "@value": "{{row.BirthDate}}",
        "@type": "http://www.w3.org/2001/XMLSchema#date"
    }
}]
```

### Language Tags

```json
[{
    "@id": "http://example.com/book/{{row.ID}}",
    "dcterms:title": [
        {
            "@value": "{{row.TitleEN}}",
            "@language": "en"
        },
        {
            "@value": "{{row.TitleFR}}",
            "@language": "fr"
        }
    ]
}]
```

### Named Graphs

Generate quads (triples with graph context):

```json
[{
    "@id": "http://example.com/graph/{{row.ID}}",
    "@graph": [{
        "@id": "http://example.com/person/{{row.ID}}",
        "@type": "foaf:Person",
        "foaf:name": "{{row.Name}}"
    }]
}]
```

## Secondary Resources

Use additional tables or graphs in transforms via `prov:qualifiedUsage`:

```turtle
<http://example.com/output> a void:Dataset ;
    prov:wasGeneratedBy [
        a setl:Transform, setl:JSLDT ;
        prov:used :mainTable ;
        prov:qualifiedUsage [
            a prov:Usage ;
            prov:entity :lookupTable ;
            prov:hadRole [ dcterms:identifier "lookup" ] ;
        ] ;
        prov:value '''...''' ;
    ] .
```

Access in template via `resources`:

```json
[{
    "@for": "lrow in resources['http://example.com/lookupTable'].itertuples()",
    "@do": {
        "@id": "http://example.com/{{lrow.ID}}",
        "http://example.com/value": "{{lrow.Value}}"
    }
}]
```

## Optimization

### Persisted Datasets

For large outputs, persist to disk instead of memory:

```turtle
<http://example.com/output> a void:Dataset, setl:Persisted ;
    prov:wasGeneratedBy [
        a setl:Transform, setl:JSLDT ;
        prov:used :largeTable ;
        prov:value '''...''' ;
    ] .
```

This uses a TrigStore backend that writes triples to disk as they're generated.

## Debugging

### Test with Sample Rows

Process only first N rows:

```python
import setlr
setlr.core.run_samples = 10  # Process 10 rows only
```

### Print Variables

Add debug output:

```json
[{
    "@id": "http://example.com/{{row.ID}}",
    "@type": "{{row.Type if 'Type' in row.index else 'Unknown'}}"
}]
```

Or use Python's logging in template:

```python
# In transform
prov:value '''
<% import logging %>
<% logging.info("Processing row: " + str(row.to_dict())) %>
[{...}]
''' ;
```

### Check Row Data

Examine what's in each row:

```python
# View sample data
print(table.head())
print(table.columns)
print(table.dtypes)
```

## Error Messages

SETLr provides detailed error context when templates fail:

```
ERROR:setlr:Error rendering template: 'NoneType' object has no attribute 'split'
ERROR:setlr:Row data: {'ID': '3', 'Name': 'Alice', 'Friends': '<empty/missing>'}
ERROR:setlr:Template context:
ERROR:setlr:    3:   "@id": "http://example.com/{{row.ID}}",
ERROR:setlr:    4:   "foaf:knows": [{
ERROR:setlr:>>> 5:     "@for": "f in row.Friends.split(';')",
ERROR:setlr:    6:     "@do": { "@id": "http://example.com/{{f}}" }
ERROR:setlr:    7:   }]
```

## Best Practices

### 1. Always Check for Empty Values

```json
// Good
"foaf:mbox": [{
    "@if": "not isempty(row.Email)",
    "@id": "mailto:{{row.Email}}"
}]

// Bad - will fail on empty cells
"foaf:mbox": "mailto:{{row.Email}}"
```

### 2. Use Meaningful Variable Names

```json
// Good
"@for": "category in row.Categories.split(';')",
"@do": { "@id": "http://example.com/category/{{category}}" }

// Less clear
"@for": "c in row.Categories.split(';')",
"@do": { "@id": "http://example.com/category/{{c}}" }
```

### 3. Keep Templates Readable

```json
// Good - split complex logic
"@with": {
    "fullName": "{{row.First}} {{row.Last}}",
    "email": "{{row.Email.lower() if not isempty(row.Email) else ''}}"
},
"@do": {
    "foaf:name": "{{fullName}}",
    "foaf:mbox": "mailto:{{email}}"
}

// Harder to read
"foaf:name": "{{row.First}} {{row.Last}}",
"foaf:mbox": "mailto:{{row.Email.lower() if not isempty(row.Email) else ''}}"
```

### 4. Use Consistent Prefixes

Define all prefixes in context:

```json
{
    "foaf": "http://xmlns.com/foaf/0.1/",
    "schema": "http://schema.org/",
    "dc": "http://purl.org/dc/terms/"
}
```

## Examples

See [examples documentation](examples.md) for complete working examples.

## See Also

- [Tutorial](tutorial.md) - Step-by-step JSLDT guide
- [Python API](python-api.md) - Building JSLDT from Python
- [Advanced Features](advanced.md) - More transform options
