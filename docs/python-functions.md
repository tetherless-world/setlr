# Python Functions in Transforms

SETLr allows you to execute custom Python code within SETL transforms using `setl:PythonScript`.

## Overview

Python scripts in SETLr can:
- Perform complex data processing
- Generate RDF triples programmatically
- Access pandas DataFrames directly
- Use any Python library

⚠️ **Security Warning**: Python scripts execute with full system access. Only run trusted SETL scripts.

## Basic Python Script

```turtle
@prefix setl: <http://purl.org/twc/vocab/setl/> .
@prefix prov: <http://www.w3.org/ns/prov#> .
@prefix void: <http://rdfs.org/ns/void#> .
@prefix : <http://example.com/> .

# First, extract your data
:dataTable a setl:Table ;
    prov:wasGeneratedBy [
        a setl:Extract ;
        prov:used <data.csv> ;
    ] .

# Python script transform
:processedGraph a void:Dataset ;
    prov:wasGeneratedBy [
        a setl:PythonScript ;
        prov:used :dataTable ;
        prov:value '''
# Access the table as pandas DataFrame
for index, row in table.iterrows():
    value = row['Value'] * 2
    print(f"Processing row {index}: {value}")
''' ;
    ] .
```

## Available Variables

Inside Python scripts, you have access to:

| Variable | Type | Description |
|----------|------|-------------|
| `table` | pandas.DataFrame | The input table (if `prov:used` references a table) |
| `result` | rdflib.Graph | Output graph - add triples here |
| `resources` | dict | All generated resources from the SETL script |
| `transform` | rdflib.Resource | The current transform resource |
| `setl_graph` | rdflib.Graph | The SETL script graph |
| `rdflib` | module | RDFLib library |
| `RDF`, `RDFS`, `OWL` | Namespace | Common RDF namespaces |

## Generating RDF Triples

```turtle
:peopleGraph a void:Dataset ;
    prov:wasGeneratedBy [
        a setl:PythonScript ;
        prov:used :peopleTable ;
        prov:value '''
from rdflib import Namespace, Literal
from rdflib.namespace import RDF

# Define namespace
ex = Namespace('http://example.com/')
foaf = Namespace('http://xmlns.com/foaf/0.1/')

# Generate triples for each row
for index, row in table.iterrows():
    person = ex[f"person/{row['ID']}"]
    result.add((person, RDF.type, foaf.Person))
    result.add((person, foaf.name, Literal(row['Name'])))
    result.add((person, foaf.age, Literal(row['Age'])))
''' ;
    ] .
```

## Complex Data Processing

### Example: Data Validation and Filtering

```turtle
:validatedGraph a void:Dataset ;
    prov:wasGeneratedBy [
        a setl:PythonScript ;
        prov:used :dataTable ;
        prov:value '''
from rdflib import Namespace, Literal
import re

ex = Namespace('http://example.com/')

# Validate email addresses
email_pattern = re.compile(r'^[\\w\\.-]+@[\\w\\.-]+\\.\\w+$')

for index, row in table.iterrows():
    # Skip rows with invalid emails
    if not email_pattern.match(row['Email']):
        print(f"Skipping row {index}: invalid email {row['Email']}")
        continue
    
    # Create RDF for valid rows
    person = ex[f"person/{row['ID']}"]
    result.add((person, RDF.type, ex.Person))
    result.add((person, ex.email, Literal(row['Email'])))
''' ;
    ] .
```

### Example: Aggregate Statistics

```turtle
:statsGraph a void:Dataset ;
    prov:wasGeneratedBy [
        a setl:PythonScript ;
        prov:used :salesTable ;
        prov:value '''
from rdflib import Namespace, Literal
from rdflib.namespace import RDF

ex = Namespace('http://example.com/')

# Calculate aggregates
total_sales = table['Amount'].sum()
avg_sales = table['Amount'].mean()
max_sales = table['Amount'].max()

# Add summary triples
summary = ex.SalesSummary
result.add((summary, RDF.type, ex.Summary))
result.add((summary, ex.totalSales, Literal(total_sales)))
result.add((summary, ex.averageSales, Literal(avg_sales)))
result.add((summary, ex.maxSales, Literal(max_sales)))

print(f"Processed {len(table)} sales records")
print(f"Total: ${total_sales:,.2f}")
''' ;
    ] .
```

## Using External Libraries

You can import and use any installed Python library:

```turtle
:enrichedGraph a void:Dataset ;
    prov:wasGeneratedBy [
        a setl:PythonScript ;
        prov:used :addressTable ;
        prov:value '''
from rdflib import Namespace, Literal
import requests  # Make HTTP requests
import json

ex = Namespace('http://example.com/')
geo = Namespace('http://www.w3.org/2003/01/geo/wgs84_pos#')

for index, row in table.iterrows():
    address = row['Address']
    
    # Geocode address (example - use real geocoding service)
    # response = requests.get(f"https://api.geocode.com?address={address}")
    # coords = response.json()
    
    # For demo, use placeholder coordinates
    coords = {"lat": 40.7128, "lng": -74.0060}
    
    location = ex[f"location/{row['ID']}"]
    result.add((location, RDF.type, ex.Location))
    result.add((location, geo.lat, Literal(coords['lat'])))
    result.add((location, geo.long, Literal(coords['lng'])))
''' ;
    ] .
```

## Accessing Multiple Tables

Use `prov:qualifiedUsage` to reference multiple input tables:

```turtle
@prefix prov: <http://www.w3.org/ns/prov#> .
@prefix dcterms: <http://purl.org/dc/terms/> .

:joinedGraph a void:Dataset ;
    prov:wasGeneratedBy [
        a setl:PythonScript ;
        prov:used :employeesTable ;
        prov:qualifiedUsage [
            a prov:Usage ;
            prov:entity :departmentsTable ;
            prov:hadRole [ dcterms:identifier "departments" ] ;
        ] ;
        prov:value '''
from rdflib import Namespace, Literal
import pandas as pd

ex = Namespace('http://example.com/')

# 'table' is employeesTable
# Access departments via resources
departments = resources['http://example.com/departmentsTable']

# Join tables
merged = pd.merge(table, departments, on='DeptID', how='left')

# Generate RDF from joined data
for index, row in merged.iterrows():
    emp = ex[f"employee/{row['EmpID']}"]
    result.add((emp, RDF.type, ex.Employee))
    result.add((emp, ex.name, Literal(row['Name'])))
    result.add((emp, ex.department, Literal(row['DeptName'])))
''' ;
    ] .
```

## Error Handling

Add error handling in your Python scripts:

```turtle
:robustGraph a void:Dataset ;
    prov:wasGeneratedBy [
        a setl:PythonScript ;
        prov:used :dataTable ;
        prov:value '''
from rdflib import Namespace, Literal
import traceback

ex = Namespace('http://example.com/')
errors = []

for index, row in table.iterrows():
    try:
        # Process row
        value = float(row['Value'])
        item = ex[f"item/{row['ID']}"]
        result.add((item, ex.value, Literal(value)))
    except ValueError as e:
        errors.append(f"Row {index}: {e}")
    except Exception as e:
        errors.append(f"Row {index}: Unexpected error: {e}")

if errors:
    print(f"Encountered {len(errors)} errors:")
    for error in errors[:10]:  # Show first 10
        print(f"  - {error}")
''' ;
    ] .
```

## Best Practices

### 1. Keep Scripts Focused

```python
# Good: Single responsibility
for index, row in table.iterrows():
    person = ex[f"person/{row['ID']}"]
    result.add((person, RDF.type, foaf.Person))
    result.add((person, foaf.name, Literal(row['Name'])))

# Avoid: Complex business logic mixed with RDF generation
# (Consider breaking into multiple transforms)
```

### 2. Use Logging

```python
import logging

logger = logging.getLogger('setlr')
logger.info(f"Processing {len(table)} rows")

for index, row in table.iterrows():
    logger.debug(f"Row {index}: {row['Name']}")
    # ... process row ...
```

### 3. Validate Input Data

```python
# Check for required columns
required_cols = ['ID', 'Name', 'Email']
missing = [col for col in required_cols if col not in table.columns]
if missing:
    raise ValueError(f"Missing required columns: {missing}")

# Check for empty table
if len(table) == 0:
    logger.warning("Empty table - no RDF generated")
```

### 4. Comment Your Code

```python
# Calculate person's age from birth year
current_year = 2024
for index, row in table.iterrows():
    birth_year = int(row['BirthYear'])
    age = current_year - birth_year
    
    # Only include adults (18+)
    if age >= 18:
        person = ex[f"person/{row['ID']}"]
        result.add((person, foaf.age, Literal(age)))
```

## Performance Tips

- **Use pandas operations**: Vectorized operations are faster than row-by-row iteration
- **Batch RDF additions**: Group `result.add()` calls when possible
- **Filter early**: Remove unwanted rows before processing
- **Profile your code**: Use `cProfile` for slow scripts

```python
# Faster: Use pandas filtering
adult_mask = table['Age'] >= 18
adults = table[adult_mask]

for index, row in adults.iterrows():
    # Process only adults
    pass

# Slower: Check condition in loop
for index, row in table.iterrows():
    if row['Age'] >= 18:
        # Process
        pass
```

## Debugging

Enable debug logging to see script execution:

```python
import logging
import setlr

setlr.logger.setLevel(logging.DEBUG)
```

Add print statements in your script:

```python
print(f"Table shape: {table.shape}")
print(f"Columns: {list(table.columns)}")
print(f"First row: {table.iloc[0].to_dict()}")
```

## See Also

- [Python API](python-api.md) - Using setlr from Python
- [JSLDT Template Language](jsldt.md) - Alternative transformation approach
- [Examples](examples.md) - More Python script examples
