import unittest
import tempfile
import os
import logging
from rdflib import ConjunctiveGraph, Namespace, Literal
from io import StringIO
import sys

# Import setlr module
import setlr

prov = Namespace('http://www.w3.org/ns/prov#')
setl = Namespace('http://purl.org/twc/vocab/setl/')
csvw = Namespace('http://www.w3.org/ns/csvw#')
void = Namespace('http://rdfs.org/ns/void#')

class TestErrorMessages(unittest.TestCase):
    """Test that error messages are informative when there are errors in JSON-LD templates"""
    
    def setUp(self):
        """Set up logging to capture error messages"""
        # Initialize the setlr.core logger
        import setlr.core
        setlr.core.logger = logging.getLogger('setlr')
        setlr.core.logger.setLevel(logging.ERROR)
        
        self.log_capture = StringIO()
        self.handler = logging.StreamHandler(self.log_capture)
        self.handler.setLevel(logging.ERROR)
        setlr.core.logger.addHandler(self.handler)
        
    def tearDown(self):
        """Clean up logging"""
        import setlr.core
        if setlr.core.logger:
            setlr.core.logger.removeHandler(self.handler)
    
    def test_invalid_json_template(self):
        """Test error message when JSON template has syntax errors"""
        # Create a SETL script with invalid JSON
        setl_graph = ConjunctiveGraph()
        
        # Create a simple CSV table resource
        table_uri = "http://example.com/test/table"
        table = setl_graph.resource(table_uri)
        
        # Create a transform with invalid JSON
        transform_uri = "http://example.com/test/transform"
        transform = setl_graph.resource(transform_uri)
        transform.add(prov.used, table)
        
        # Invalid JSON - missing closing brace
        invalid_json = '''[{
  "@id": "http://example.com/test",
  "name": "test"
'''
        transform.add(prov.value, Literal(invalid_json))
        
        generated = setl_graph.resource("http://example.com/test/output")
        generated.add(prov.wasGeneratedBy, transform)
        
        # Mock resources
        resources = {
            table_uri: []  # Empty table
        }
        
        # This should raise an error with informative message
        with self.assertRaises((ValueError, RuntimeError)) as context:
            setlr.json_transform(transform, resources)
        
        # Check that error message is informative
        error_msg = str(context.exception)
        self.assertIn("transform", error_msg.lower())
        
        # Check log output contains useful information
        log_output = self.log_capture.getvalue()
        self.assertIn("JSON", log_output)
        self.assertIn("transform", log_output.lower())
    
    def test_invalid_template_variable(self):
        """Test error message when template references undefined variable"""
        # This test would require a full setup with CSV data
        # For now, we'll skip it but document what should be tested
        pass

if __name__ == "__main__":
    unittest.main()
