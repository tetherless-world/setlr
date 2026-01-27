# Advanced Features

SETLr provides powerful advanced capabilities for complex data transformation workflows, large-scale processing, and production deployments.

## Overview

This guide covers advanced topics including:

- Multi-source transforms
- Conditional loading and filtering
- Performance optimization
- Error handling and debugging
- Integration patterns

For specific advanced features, see:
- [Streaming XML with XPath](streaming-xml.md) - Efficient large file processing
- [Python Functions in Transforms](python-functions.md) - Custom Python code
- [SPARQL Support](sparql.md) - Query and update endpoints
- [SHACL Validation](shacl.md) - Validate your RDF output

## Multi-Source Transforms

SETLr can combine data from multiple sources in a single transform.

### Combining Multiple Tables

```turtle
@prefix setl: <http://purl.org/twc/vocab/setl/> .
@prefix prov: <http://www.w3.org/ns/prov#> .
@prefix csvw: <http://www.w3.org/ns/csvw#> .

# Load first table
:users a csvw:Table, setl:Table ;
    prov:wasGeneratedBy [ 
        a setl:Extract ; 
        prov:used <users.csv> 
    ] .

# Load second table
:orders a csvw:Table, setl:Table ;
    prov:wasGeneratedBy [ 
        a setl:Extract ; 
        prov:used <orders.csv> 
    ] .

# Transform using both tables
:output prov:wasGeneratedBy [
    a setl:Transform, setl:JSLDT ;
    prov:used :users, :orders ;
    prov:value '''
    [{
        "@for": "user in users",
        "@do": {
            "@id": "http://example.com/user/{{user.ID}}",
            "@type": "Person",
            "name": "{{user.Name}}",
            "orders": [{
                "@for": "order in orders",
                "@if": "order.UserID == user.ID",
                "@do": {
                    "@id": "http://example.com/order/{{order.OrderID}}"
                }
            }]
        }
    }]
    '''
] .
```

### Loading from Different Formats

```turtle
# CSV data
:csv_table a csvw:Table, setl:Table ;
    prov:wasGeneratedBy [ 
        a setl:Extract ; 
        prov:used <data.csv> 
    ] .

# JSON data  
:json_data a setl:Table ;
    prov:wasGeneratedBy [ 
        a setl:Extract ;
        prov:used <data.json> ;
        setl:hasJSONSelector "$.items[*]"
    ] .

# XML data
:xml_data a setl:Table ;
    prov:wasGeneratedBy [ 
        a setl:Extract ;
        prov:used <data.xml> ;
        setl:hasXPathSelector "//item"
    ] .
```

## Conditional Loading

Use conditional logic to selectively process data based on runtime conditions.

### Filtering with @if

```json
[{
    "@for": "row in table",
    "@if": "row.Status == 'active' and row.Score > 50",
    "@do": {
        "@id": "http://example.com/entity/{{row.ID}}",
        "@type": "ActiveEntity",
        "score": "{{row.Score}}"
    }
}]
```

### Conditional Fields

```json
{
    "@id": "http://example.com/person/{{row.ID}}",
    "@type": "Person",
    "name": "{{row.Name}}",
    "email": {
        "@if": "row.Email",
        "@do": "mailto:{{row.Email}}"
    },
    "phone": {
        "@if": "row.Phone and row.PhoneVerified",
        "@do": "{{row.Phone}}"
    }
}
```

## Performance Optimization

### Multicore Processing

SETLr automatically uses multiple CPU cores for parallel row processing in JSON-LD transforms. This provides transparent performance improvements for large datasets without requiring code changes.

**Key Features:**
- **Automatic parallelization**: Row processing is distributed across all available CPU cores
- **Thread-safe**: Graph updates are synchronized to ensure data consistency
- **Configurable workers**: Control the number of parallel workers via environment variable

**Configuration:**

```bash
# Use all CPU cores (default)
setlr transform.setl.ttl

# Use specific number of workers
export SETLR_MAX_WORKERS=4
setlr transform.setl.ttl

# Use single-threaded mode (for debugging)
export SETLR_MAX_WORKERS=1
setlr transform.setl.ttl
```

**Python API:**

```python
import os
import setlr
from rdflib import Graph

# Configure before running
os.environ['SETLR_MAX_WORKERS'] = '8'  # Use 8 workers

setl_graph = Graph()
setl_graph.parse('transform.setl.ttl', format='turtle')
resources = setlr.run_setl(setl_graph)
```

**Performance Considerations:**
- **Best for**: CPU-bound transforms with complex templates, function evaluations, or large row counts (>100 rows)
- **Automatic**: No code changes needed; existing scripts benefit automatically
- **Thread-safe**: RDF graph updates are serialized to prevent data corruption
- **Memory**: Each worker needs memory for row processing; monitor usage with very large datasets

**Example Performance:**

For a dataset with 10,000 rows and complex template processing:
- 1 core: ~45 seconds
- 4 cores: ~15 seconds  
- 8 cores: ~8 seconds

Actual performance depends on:
- Template complexity
- Function evaluations (@if, @for, custom functions)
- SHACL validation overhead
- I/O for RDF serialization

### Streaming Processing

See [Streaming XML documentation](streaming-xml.md) for details.

### Batch Processing

Process data in batches to control memory usage:

```python
from rdflib import Graph, Namespace, URIRef
import setlr

# For very large datasets, process in chunks
chunk_size = 10000
offset = 0

output_graph = Graph()

while True:
    # Create SETL script for this batch
    setl_graph = create_batch_setl(offset, chunk_size)
    
    # Process batch
    resources = setlr.run_setl(setl_graph)
    
    # Accumulate results
    batch_output = resources[URIRef('http://example.com/output')]
    output_graph += batch_output
    
    # Check if done
    if len(batch_output) < chunk_size:
        break
    
    offset += chunk_size

# Save final results
output_graph.serialize('output.ttl', format='turtle')
```

### Pandas Optimization

For CSV/Excel files, pandas is used automatically. Optimize with:

```python
# Use appropriate dtypes to reduce memory
# Specify in your data loading if possible

# For very wide tables, select only needed columns
# by processing the source data first
```

## Error Handling and Debugging

### Verbose Logging

Enable detailed logging to diagnose issues:

```python
import logging
import setlr

# Enable debug logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger('setlr')
logger.setLevel(logging.DEBUG)

# Now run SETL
resources = setlr.run_setl(setl_graph)
```

### Progress Tracking

Use tqdm for progress tracking on large datasets:

```python
from tqdm import tqdm
import setlr

# Progress bars are automatically shown for:
# - Large file processing
# - Batch operations
# - Network transfers

resources = setlr.run_setl(setl_graph)
```

### Validation During Development

Validate intermediate results to catch issues early:

```python
from rdflib import Graph
import setlr

# Process data
resources = setlr.run_setl(setl_graph)
output = resources[URIRef('http://example.com/output')]

# Validate results
print(f"Generated {len(output)} triples")
print(f"Subjects: {len(set(output.subjects()))}")
print(f"Predicates: {len(set(output.predicates()))}")
print(f"Objects: {len(set(output.objects()))}")

# Check for specific patterns
for s, p, o in output.triples((None, RDF.type, None)):
    print(f"Type: {o}")
```

### Error Recovery

Handle errors gracefully in production:

```python
import setlr
from rdflib import Graph

try:
    setl_graph = Graph()
    setl_graph.parse('transform.setl.ttl', format='turtle')
    resources = setlr.run_setl(setl_graph)
    
except setlr.SetlrError as e:
    print(f"SETL processing error: {e}")
    # Handle gracefully
    
except Exception as e:
    print(f"Unexpected error: {e}")
    # Log and notify
```

## Integration Patterns

### CI/CD Integration

Integrate SETLr into your CI/CD pipeline:

```yaml
# GitHub Actions example
name: Generate RDF

on: [push]

jobs:
  generate:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      
      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'
      
      - name: Install SETLr
        run: pip install setlr
      
      - name: Generate RDF
        run: setlr transform.setl.ttl -o output.ttl
      
      - name: Upload artifact
        uses: actions/upload-artifact@v4
        with:
          name: rdf-output
          path: output.ttl
```

### Docker Integration

Use SETLr in containerized environments:

```dockerfile
FROM python:3.11-slim

# Install SETLr
RUN pip install setlr

# Copy your SETL scripts and data
COPY transform.setl.ttl /app/
COPY data/ /app/data/

WORKDIR /app

# Run transformation
CMD ["setlr", "transform.setl.ttl", "-o", "/output/result.ttl"]
```

```bash
# Build and run
docker build -t my-setl-transform .
docker run -v $(pwd)/output:/output my-setl-transform
```

### Scheduled Processing

Run SETLr transformations on a schedule:

```python
# scheduled_transform.py
import schedule
import time
from rdflib import Graph
import setlr

def run_transform():
    """Run the SETL transformation"""
    print("Starting transformation...")
    
    setl_graph = Graph()
    setl_graph.parse('transform.setl.ttl', format='turtle')
    
    resources = setlr.run_setl(setl_graph)
    
    # Save output with timestamp
    timestamp = time.strftime('%Y%m%d_%H%M%S')
    output_file = f'output_{timestamp}.ttl'
    
    output = resources[URIRef('http://example.com/output')]
    output.serialize(output_file, format='turtle')
    
    print(f"Transformation complete: {output_file}")

# Schedule to run every day at 2 AM
schedule.every().day.at("02:00").do(run_transform)

while True:
    schedule.run_pending()
    time.sleep(60)
```

### REST API Wrapper

Expose SETLr as a REST API:

```python
from flask import Flask, request, jsonify
from rdflib import Graph
import setlr
import tempfile

app = Flask(__name__)

@app.route('/transform', methods=['POST'])
def transform():
    """Accept CSV data and SETL script, return RDF"""
    
    # Get input
    csv_data = request.files['data']
    setl_script = request.form['setl']
    
    # Save to temp files
    with tempfile.NamedTemporaryFile(mode='w', suffix='.csv') as csv_file:
        csv_data.save(csv_file.name)
        
        # Update SETL script with temp file path
        setl_graph = Graph()
        setl_graph.parse(data=setl_script, format='turtle')
        
        # Run transformation
        resources = setlr.run_setl(setl_graph)
        
        # Return RDF
        output = resources[URIRef('http://example.com/output')]
        return output.serialize(format='turtle'), 200, {
            'Content-Type': 'text/turtle'
        }

if __name__ == '__main__':
    app.run(debug=True)
```

## Best Practices

### 2. Version Control

- Store SETL scripts in version control
- Track changes to transforms with your data processing pipeline
- Use branches for experimental transforms

### 3. Testing

- Test SETL scripts with sample data before production use
- Validate output with SHACL shapes
- Compare output to expected results

### 4. Documentation

- Document complex transforms with comments (use rdfs:comment)
- Maintain README files for transform collections
- Include example data with your scripts

### 5. Monitoring

- Log transformation results (record counts, errors)
- Monitor resource usage for large datasets
- Set up alerts for transformation failures

## Next Steps

- Explore [Streaming XML](streaming-xml.md) for large file processing
- Learn about [Python Functions](python-functions.md) for custom logic
- Set up [SPARQL endpoints](sparql.md) for data loading
- Implement [SHACL validation](shacl.md) for quality control

## Support

For questions about advanced features:
- Check the [documentation](README.md)
- Open a [discussion](https://github.com/tetherless-world/setlr/discussions)
- Report issues on [GitHub](https://github.com/tetherless-world/setlr/issues)
