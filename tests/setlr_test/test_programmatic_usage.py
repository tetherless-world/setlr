#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Unit tests for using setlr programmatically from Python.

Tests the main API entry points (run_setl) for executing SETL scripts
from Python code.
"""

import unittest
import tempfile
import os
from rdflib import Graph, Namespace, Literal, URIRef
from rdflib.namespace import RDF, PROV
import setlr

setl = Namespace('http://purl.org/twc/vocab/setl/')
void = Namespace('http://rdfs.org/ns/void#')
csvw = Namespace('http://www.w3.org/ns/csvw#')
dcterms = Namespace('http://purl.org/dc/terms/')
ex = Namespace('http://example.com/')


class TestProgrammaticUsage(unittest.TestCase):
    """Test using setlr programmatically from Python"""

    def test_simple_csv_to_rdf(self):
        """Test complete ETL: CSV -> RDF using run_setl()"""
        # Create test CSV
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            f.write('ID,Name,Email\n')
            f.write('1,Alice,alice@example.com\n')
            f.write('2,Bob,bob@example.com\n')
            csv_file = f.name

        try:
            # Build SETL graph programmatically
            setl_graph = Graph()
            setl_graph.bind('setl', setl)
            setl_graph.bind('prov', PROV)
            setl_graph.bind('void', void)
            setl_graph.bind('csvw', csvw)
            setl_graph.bind('dcterms', dcterms)
            setl_graph.bind('ex', ex)

            # Extract: Load CSV
            table = ex.myTable
            setl_graph.add((table, RDF.type, setl.Table))
            setl_graph.add((table, RDF.type, csvw.Table))
            setl_graph.add((table, csvw.delimiter, Literal(',')))

            extract = setl_graph.resource(setl_graph.skolemize())
            extract.add(RDF.type, setl.Extract)
            extract.add(PROV.used, URIRef('file://' + csv_file))
            setl_graph.add((table, PROV.wasGeneratedBy, extract.identifier))

            # Transform: CSV -> RDF using JSLDT
            output = ex.output
            setl_graph.add((output, RDF.type, void.Dataset))

            transform = setl_graph.resource(setl_graph.skolemize())
            transform.add(RDF.type, setl.Transform)
            transform.add(RDF.type, setl.JSLDT)
            transform.add(PROV.used, table)

            # JSON-LD template
            template = '''[{
  "@id": "http://example.com/person/{{row.ID}}",
  "@type": "http://xmlns.com/foaf/0.1/Person",
  "http://xmlns.com/foaf/0.1/name": "{{row.Name}}",
  "http://xmlns.com/foaf/0.1/mbox": "mailto:{{row.Email}}"
}]'''
            transform.add(PROV.value, Literal(template))

            context = '''{"foaf": "http://xmlns.com/foaf/0.1/"}'''
            transform.add(setl.hasContext, Literal(context))

            setl_graph.add((output, PROV.wasGeneratedBy, transform.identifier))

            # Execute SETL script
            resources = setlr.run_setl(setl_graph)

            # Verify results - resources dict uses URIRef as keys
            self.assertIn(table, resources, "Table should be in resources")
            self.assertIn(output, resources, "Output graph should be in resources")

            # Check output graph has triples
            output_graph = resources[output]
            self.assertIsInstance(output_graph, Graph)
            self.assertGreater(len(output_graph), 0, "Output graph should have triples")

            # Verify specific triples exist
            foaf_name = URIRef('http://xmlns.com/foaf/0.1/name')
            names = list(output_graph.objects(predicate=foaf_name))
            self.assertGreater(len(names), 0, "Should have foaf:name triples")

        finally:
            os.unlink(csv_file)

    def test_access_generated_resources(self):
        """Test that run_setl returns a dictionary of all generated resources"""
        # Create minimal SETL script
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            f.write('ID\n1\n2\n')
            csv_file = f.name

        try:
            setl_graph = Graph()
            setl_graph.bind('setl', setl)
            setl_graph.bind('prov', PROV)
            setl_graph.bind('csvw', csvw)

            # Just extract
            table = ex.testTable
            setl_graph.add((table, RDF.type, setl.Table))
            setl_graph.add((table, RDF.type, csvw.Table))  # Need csvw.Table for CSV extraction
            
            extract = setl_graph.resource(setl_graph.skolemize())
            extract.add(RDF.type, setl.Extract)
            extract.add(PROV.used, URIRef('file://' + csv_file))
            setl_graph.add((table, PROV.wasGeneratedBy, extract.identifier))

            # Execute
            resources = setlr.run_setl(setl_graph)

            # Check return type
            self.assertIsInstance(resources, dict)
            self.assertIn(table, resources)

            # Verify we can access the table
            table_data = resources[table]
            self.assertIsNotNone(table_data)

        finally:
            os.unlink(csv_file)

    def test_multiple_transforms(self):
        """Test executing multiple transforms in a single SETL script"""
        # Create test CSV
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            f.write('Name,Value\n')
            f.write('A,10\n')
            f.write('B,20\n')
            csv_file = f.name

        try:
            setl_graph = Graph()
            setl_graph.bind('setl', setl)
            setl_graph.bind('prov', PROV)
            setl_graph.bind('void', void)
            setl_graph.bind('csvw', csvw)

            # Extract
            table = ex.data
            setl_graph.add((table, RDF.type, setl.Table))
            setl_graph.add((table, RDF.type, csvw.Table))  # Need csvw.Table for CSV extraction
            
            extract = setl_graph.resource(setl_graph.skolemize())
            extract.add(RDF.type, setl.Extract)
            extract.add(PROV.used, URIRef('file://' + csv_file))
            setl_graph.add((table, PROV.wasGeneratedBy, extract.identifier))

            # Transform 1
            output1 = ex.output1
            setl_graph.add((output1, RDF.type, void.Dataset))
            
            transform1 = setl_graph.resource(setl_graph.skolemize())
            transform1.add(RDF.type, setl.Transform)
            transform1.add(RDF.type, setl.JSLDT)
            transform1.add(PROV.used, table)
            transform1.add(PROV.value, Literal('[{"@id": "http://example.com/{{row.Name}}", "http://example.com/value": "{{row.Value}}"}]'))
            setl_graph.add((output1, PROV.wasGeneratedBy, transform1.identifier))

            # Transform 2 (uses same table)
            output2 = ex.output2
            setl_graph.add((output2, RDF.type, void.Dataset))
            
            transform2 = setl_graph.resource(setl_graph.skolemize())
            transform2.add(RDF.type, setl.Transform)
            transform2.add(RDF.type, setl.JSLDT)
            transform2.add(PROV.used, table)
            transform2.add(PROV.value, Literal('[{"@id": "http://example.com/item/{{row.Name}}", "http://example.com/hasValue": "{{row.Value}}"}]'))
            setl_graph.add((output2, PROV.wasGeneratedBy, transform2.identifier))

            # Execute
            resources = setlr.run_setl(setl_graph)

            # Verify both outputs were created
            self.assertIn(output1, resources)
            self.assertIn(output2, resources)
            
            # Both should be graphs
            self.assertIsInstance(resources[output1], Graph)
            self.assertIsInstance(resources[output2], Graph)

        finally:
            os.unlink(csv_file)


if __name__ == '__main__':
    unittest.main()
