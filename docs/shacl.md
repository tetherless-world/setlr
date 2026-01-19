# SHACL Validation

SETLr includes built-in support for validating RDF output using SHACL (Shapes Constraint Language), ensuring your generated data meets quality requirements.

## Overview

SHACL validation enables:
- Schema validation of generated RDF
- Data quality checks
- Constraint enforcement
- Automated validation in workflows
- Validation reports

## Basic SHACL Validation

Define shapes to validate your RDF output.

### Simple Shape Example

```turtle
@prefix setl: <http://purl.org/twc/vocab/setl/> .
@prefix prov: <http://www.w3.org/ns/prov#> .
@prefix sh: <http://www.w3.org/ns/shacl#> .
@prefix ex: <http://example.com/> .

# Data extraction and transformation
:input_table a csvw:Table ;
    prov:wasGeneratedBy [ a setl:Extract ; prov:used <people.csv> ] .

:output a void:Dataset ;
    prov:wasGeneratedBy [
        a setl:Transform, setl:JSLDT ;
        prov:used :input_table ;
        prov:value '''[{
            "@for": "row in input_table",
            "@do": {
                "@id": "http://example.com/person/{{row.ID}}",
                "@type": "http://xmlns.com/foaf/0.1/Person",
                "http://xmlns.com/foaf/0.1/name": "{{row.Name}}",
                "http://xmlns.com/foaf/0.1/mbox": "mailto:{{row.Email}}"
            }
        }]'''
    ] .

# SHACL validation shape
:PersonShape a sh:NodeShape ;
    sh:targetClass foaf:Person ;
    sh:property [
        sh:path foaf:name ;
        sh:minCount 1 ;
        sh:maxCount 1 ;
        sh:datatype xsd:string ;
        sh:minLength 1 ;
    ] ;
    sh:property [
        sh:path foaf:mbox ;
        sh:minCount 1 ;
        sh:pattern "^mailto:" ;
    ] .

# Apply validation
:output setl:hasShapesGraph :shapes_graph .

:shapes_graph prov:wasGeneratedBy [
    a setl:Extract ;
    prov:used <person-shapes.ttl>
] .
```

### Validation in SETL Scripts

```turtle
@prefix setl: <http://purl.org/twc/vocab/setl/> .
@prefix prov: <http://www.w3.org/ns/prov#> .

# Transform data
:output a void:Dataset ;
    prov:wasGeneratedBy [
        a setl:Transform, setl:JSLDT ;
        prov:used :input ;
        prov:value '''[...]'''
    ] ;
    # Enable SHACL validation
    setl:validateWithShapes :shapes .

# Load shapes from file
:shapes prov:wasGeneratedBy [
    a setl:Extract ;
    prov:used <shapes.ttl>
] .
```

## SHACL Constraints

### Required Properties

Ensure properties exist:

```turtle
:PersonShape a sh:NodeShape ;
    sh:targetClass ex:Person ;
    sh:property [
        sh:path ex:name ;
        sh:minCount 1 ;  # Required
        sh:message "Person must have a name"
    ] .
```

### Cardinality Constraints

Control how many values:

```turtle
sh:property [
    sh:path ex:email ;
    sh:minCount 1 ;    # At least one
    sh:maxCount 1 ;    # At most one
] .

sh:property [
    sh:path ex:phoneNumber ;
    sh:minCount 0 ;    # Optional
    sh:maxCount 5 ;    # Up to 5
] .
```

### Datatype Constraints

Validate datatypes:

```turtle
sh:property [
    sh:path ex:age ;
    sh:datatype xsd:integer ;
    sh:minInclusive 0 ;
    sh:maxInclusive 150 ;
] .

sh:property [
    sh:path ex:email ;
    sh:datatype xsd:string ;
    sh:pattern "^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\\.[a-zA-Z]{2,}$" ;
] .

sh:property [
    sh:path ex:website ;
    sh:nodeKind sh:IRI ;  # Must be a URI
] .
```

### Value Constraints

Restrict allowed values:

```turtle
sh:property [
    sh:path ex:status ;
    sh:in ( "active" "inactive" "pending" ) ;
] .

sh:property [
    sh:path ex:priority ;
    sh:minInclusive 1 ;
    sh:maxInclusive 10 ;
] .
```

### String Constraints

Validate string patterns:

```turtle
sh:property [
    sh:path ex:zipCode ;
    sh:pattern "^\\d{5}(-\\d{4})?$" ;
    sh:flags "i" ;  # Case insensitive
] .

sh:property [
    sh:path ex:name ;
    sh:minLength 2 ;
    sh:maxLength 100 ;
] .
```

### Class Constraints

Ensure correct types:

```turtle
sh:property [
    sh:path ex:creator ;
    sh:class ex:Person ;  # Must be a Person
] .

sh:property [
    sh:path ex:organization ;
    sh:or (
        [ sh:class ex:Company ]
        [ sh:class ex:Institution ]
    ) ;
] .
```

## Validation Reports

### Interpreting Reports

When validation fails, SETLr generates a detailed report:

```python
from rdflib import Graph
import setlr

# Run SETL with validation
setl_graph = Graph()
setl_graph.parse('transform.setl.ttl', format='turtle')

try:
    resources = setlr.run_setl(setl_graph)
    print("Validation passed!")
    
except setlr.ValidationError as e:
    print("Validation failed!")
    print(e.report)  # Access validation report
    
    # Report contains:
    # - sh:result - Individual violations
    # - sh:focusNode - Node that failed
    # - sh:resultPath - Property that failed
    # - sh:resultMessage - Error message
```

### Example Validation Report

```turtle
@prefix sh: <http://www.w3.org/ns/shacl#> .

[ a sh:ValidationReport ;
  sh:conforms false ;
  sh:result [
    a sh:ValidationResult ;
    sh:focusNode <http://example.com/person/123> ;
    sh:resultPath <http://xmlns.com/foaf/0.1/name> ;
    sh:resultSeverity sh:Violation ;
    sh:resultMessage "Person must have a name" ;
    sh:sourceConstraintComponent sh:MinCountConstraintComponent ;
    sh:sourceShape :PersonShape ;
  ]
] .
```

## Advanced SHACL Features

### Conditional Constraints

Use `sh:or`, `sh:and`, `sh:not`:

```turtle
:UserShape a sh:NodeShape ;
    sh:targetClass ex:User ;
    # Must have email OR phone
    sh:or (
        [ sh:property [ sh:path ex:email ; sh:minCount 1 ] ]
        [ sh:property [ sh:path ex:phone ; sh:minCount 1 ] ]
    ) .
```

### Qualified Cardinality

Count specific types:

```turtle
sh:property [
    sh:path ex:author ;
    sh:qualifiedValueShape [ sh:class ex:Person ] ;
    sh:qualifiedMinCount 1 ;  # At least one author that is a Person
] .
```

### Property Pair Constraints

Compare two properties:

```turtle
:DateRangeShape a sh:NodeShape ;
    sh:targetClass ex:Event ;
    sh:property [
        sh:path ex:startDate ;
        sh:lessThan ex:endDate ;  # Start before end
    ] .
```

### Closed Shapes

Restrict to only defined properties:

```turtle
:PersonShape a sh:NodeShape ;
    sh:targetClass ex:Person ;
    sh:closed true ;
    sh:ignoredProperties ( rdf:type ) ;
    sh:property [ sh:path ex:name ] ;
    sh:property [ sh:path ex:email ] ;
    # Any other property is invalid
.
```

### Custom Messages

Provide helpful error messages:

```turtle
sh:property [
    sh:path ex:age ;
    sh:datatype xsd:integer ;
    sh:minInclusive 0 ;
    sh:message "Age must be a non-negative integer"@en ;
] .
```

### Severity Levels

Set constraint severity:

```turtle
sh:property [
    sh:path ex:email ;
    sh:minCount 1 ;
    sh:severity sh:Violation ;  # Hard failure
] .

sh:property [
    sh:path ex:phone ;
    sh:minCount 1 ;
    sh:severity sh:Warning ;  # Warning only
] .

sh:property [
    sh:path ex:fax ;
    sh:maxCount 1 ;
    sh:severity sh:Info ;  # Information
] .
```

## Validation in Python

### Manual Validation

```python
from rdflib import Graph
from pyshacl import validate

# Load data graph
data_graph = Graph()
data_graph.parse('data.ttl', format='turtle')

# Load shapes graph
shapes_graph = Graph()
shapes_graph.parse('shapes.ttl', format='turtle')

# Validate
conforms, report_graph, report_text = validate(
    data_graph,
    shacl_graph=shapes_graph,
    inference='rdfs',  # Enable RDFS inference
    abort_on_first=False,  # Find all violations
    meta_shacl=False,  # Don't validate shapes themselves
    debug=False
)

if conforms:
    print("✓ Validation passed")
else:
    print("✗ Validation failed")
    print(report_text)
```

### Validation with Inference

Enable reasoning during validation:

```python
from pyshacl import validate

conforms, report_graph, report_text = validate(
    data_graph,
    shacl_graph=shapes_graph,
    inference='rdfs',  # RDFS inference
    # inference='owlrl',  # OWL RL inference
    # inference='both',  # Both RDFS and OWL RL
)
```

### Advanced Validation Options

```python
from pyshacl import validate

conforms, report_graph, report_text = validate(
    data_graph,
    shacl_graph=shapes_graph,
    ont_graph=ontology_graph,  # Separate ontology
    inference='rdfs',
    abort_on_first=False,  # Continue after first violation
    allow_infos=True,  # Include info-level results
    allow_warnings=True,  # Include warnings
    meta_shacl=True,  # Validate the shapes themselves
    advanced=True,  # Enable SHACL-AF features
    js=True,  # Enable JavaScript constraints
    debug=True  # Verbose output
)
```

## Practical Examples

### Example 1: Person Validation

```turtle
@prefix sh: <http://www.w3.org/ns/shacl#> .
@prefix ex: <http://example.com/> .
@prefix foaf: <http://xmlns.com/foaf/0.1/> .

ex:PersonShape a sh:NodeShape ;
    sh:targetClass foaf:Person ;
    sh:property [
        sh:path foaf:name ;
        sh:minCount 1 ;
        sh:datatype xsd:string ;
        sh:minLength 1 ;
        sh:message "Every person must have a non-empty name"
    ] ;
    sh:property [
        sh:path foaf:mbox ;
        sh:maxCount 1 ;
        sh:pattern "^mailto:[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\\.[a-zA-Z]{2,}$" ;
        sh:message "Email must be valid mailto: URI"
    ] ;
    sh:property [
        sh:path foaf:age ;
        sh:maxCount 1 ;
        sh:datatype xsd:integer ;
        sh:minInclusive 0 ;
        sh:maxInclusive 150 ;
    ] .
```

### Example 2: Organizational Hierarchy

```turtle
ex:OrganizationShape a sh:NodeShape ;
    sh:targetClass ex:Organization ;
    sh:property [
        sh:path ex:hasEmployee ;
        sh:class ex:Person ;
    ] ;
    sh:property [
        sh:path ex:parentOrganization ;
        sh:maxCount 1 ;
        sh:class ex:Organization ;
    ] ;
    sh:property [
        sh:path ex:legalName ;
        sh:minCount 1 ;
        sh:maxCount 1 ;
        sh:datatype xsd:string ;
    ] .

ex:PersonShape a sh:NodeShape ;
    sh:targetClass ex:Person ;
    sh:property [
        sh:path ex:worksFor ;
        sh:maxCount 1 ;
        sh:class ex:Organization ;
    ] .
```

### Example 3: Temporal Data

```turtle
ex:EventShape a sh:NodeShape ;
    sh:targetClass ex:Event ;
    sh:property [
        sh:path ex:startDate ;
        sh:minCount 1 ;
        sh:maxCount 1 ;
        sh:datatype xsd:dateTime ;
    ] ;
    sh:property [
        sh:path ex:endDate ;
        sh:maxCount 1 ;
        sh:datatype xsd:dateTime ;
    ] ;
    # End date must be after start date
    sh:sparql [
        sh:message "End date must be after start date" ;
        sh:prefixes ex: ;
        sh:select """
            SELECT $this
            WHERE {
                $this ex:startDate ?start ;
                      ex:endDate ?end .
                FILTER (?end <= ?start)
            }
        """
    ] .
```

## Best Practices

### 1. Design Shapes Early

Define validation requirements before generating data:
- Document expected schema
- Create shapes alongside SETL scripts
- Test with sample data

### 2. Use Meaningful Messages

```turtle
sh:message "Email is required and must be valid"@en ;
```

### 3. Layer Validations

```turtle
# Core validation (hard requirements)
:CorePersonShape sh:severity sh:Violation .

# Quality checks (warnings)
:QualityPersonShape sh:severity sh:Warning .

# Recommendations (info)
:OptimalPersonShape sh:severity sh:Info .
```

### 4. Test Shapes Independently

```python
# Test shapes separately from SETL
shapes_graph = Graph()
shapes_graph.parse('shapes.ttl')

test_data = Graph()
test_data.parse('test-data.ttl')

conforms, _, report = validate(test_data, shacl_graph=shapes_graph)
assert conforms, f"Validation failed: {report}"
```

### 5. Version Control Shapes

- Store shapes with your SETL scripts
- Version them together
- Document changes

## Integration Patterns

### CI/CD Validation

```yaml
# GitHub Actions
- name: Validate RDF Output
  run: |
    python -c "
    from rdflib import Graph
    from pyshacl import validate
    
    data = Graph()
    data.parse('output.ttl')
    
    shapes = Graph()
    shapes.parse('shapes.ttl')
    
    conforms, _, report = validate(data, shacl_graph=shapes)
    
    if not conforms:
        print(report)
        exit(1)
    "
```

### Pre-Production Checks

```python
def validate_before_load(data_graph, shapes_graph, endpoint):
    """Validate data before loading to production"""
    conforms, _, report = validate(data_graph, shacl_graph=shapes_graph)
    
    if not conforms:
        raise ValueError(f"Validation failed:\n{report}")
    
    # Load to production endpoint
    load_to_sparql(data_graph, endpoint)
```

## Troubleshooting

### Common Issues

**Issue**: Shapes not found
```python
# Ensure shapes are loaded correctly
shapes_graph = Graph()
print(f"Loaded {len(shapes_graph)} triples from shapes file")
```

**Issue**: Validation too strict
```turtle
# Use warnings for optional checks
sh:severity sh:Warning ;
```

**Issue**: Performance problems
```python
# Validate in batches for large datasets
batch_size = 10000
for batch in batches(data_graph, batch_size):
    validate(batch, shacl_graph=shapes_graph)
```

## Related Documentation

- [Advanced Features](advanced.md) - Integration patterns
- [Python API](python-api.md) - Programmatic usage
- [Examples](examples.md) - Complete examples

## External Resources

- [SHACL Specification](https://www.w3.org/TR/shacl/)
- [pyshacl Documentation](https://github.com/RDFLib/pySHACL)
- [SHACL Playground](https://shacl.org/playground/)

## Support

For SHACL-related questions:
- Open a [discussion](https://github.com/tetherless-world/setlr/discussions)
- Report issues on [GitHub](https://github.com/tetherless-world/setlr/issues)
