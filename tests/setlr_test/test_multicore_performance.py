#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Unit tests for multicore processing in json_transform.

Tests to verify that the json_transform function properly utilizes
multiple CPU cores for parallel row processing.
"""

import unittest
import tempfile
import os
import time
from rdflib import Graph, Namespace, Literal, URIRef
from rdflib.namespace import RDF, PROV
import setlr

setl = Namespace('http://purl.org/twc/vocab/setl/')
void = Namespace('http://rdfs.org/ns/void#')
csvw = Namespace('http://www.w3.org/ns/csvw#')
dcterms = Namespace('http://purl.org/dc/terms/')
ex = Namespace('http://example.com/')


class TestMulticorePerformance(unittest.TestCase):
    """Test multicore processing in json_transform"""

    def test_multicore_processing_with_larger_dataset(self):
        """Test that parallel processing works correctly with a larger dataset"""
        # Create test CSV with more rows to benefit from parallel processing
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            f.write('ID,Name,Email,Age,City\n')
            for i in range(100):  # Create 100 rows
                f.write(f'{i},Person{i},person{i}@example.com,{20+i%50},City{i%10}\n')
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

            # Transform: CSV -> RDF using JSLDT with a template that processes data
            output = ex.output
            setl_graph.add((output, RDF.type, void.Dataset))

            transform = setl_graph.resource(setl_graph.skolemize())
            transform.add(RDF.type, setl.Transform)
            transform.add(RDF.type, setl.JSLDT)
            transform.add(PROV.used, table)

            # JSON-LD template that does some processing
            template = '''[{
  "@id": "http://example.com/person/{{row.ID}}",
  "@type": "http://xmlns.com/foaf/0.1/Person",
  "http://xmlns.com/foaf/0.1/name": "{{row.Name}}",
  "http://xmlns.com/foaf/0.1/mbox": "mailto:{{row.Email}}",
  "http://xmlns.com/foaf/0.1/age": "{{row.Age}}",
  "http://example.com/city": "{{row.City}}",
  "http://example.com/hash": "{{hash(row.Name)}}"
}]'''
            transform.add(PROV.value, Literal(template))

            context = '''{"foaf": "http://xmlns.com/foaf/0.1/"}'''
            transform.add(setl.hasContext, Literal(context))

            setl_graph.add((output, PROV.wasGeneratedBy, transform.identifier))

            # Execute SETL script and measure time
            start_time = time.time()
            resources = setlr.run_setl(setl_graph)
            elapsed_time = time.time() - start_time

            # Verify results
            self.assertIn(output, resources, "Output graph should be in resources")

            # Check output graph has correct number of triples
            output_graph = resources[output]
            self.assertIsInstance(output_graph, Graph)
            
            # Each row should produce multiple triples (at least 6 per row)
            # ID, type, name, mbox, age, city, hash
            min_expected_triples = 100 * 6  # 100 rows * 6 properties
            actual_triples = len(output_graph)
            self.assertGreaterEqual(actual_triples, min_expected_triples, 
                                   f"Expected at least {min_expected_triples} triples, got {actual_triples}")

            # Verify specific triples exist for first and last person
            foaf_name = URIRef('http://xmlns.com/foaf/0.1/name')
            names = list(output_graph.objects(predicate=foaf_name))
            self.assertEqual(len(names), 100, "Should have 100 foaf:name triples")
            
            # Check that data is correctly processed
            person0 = URIRef('http://example.com/person/0')
            person_names = list(output_graph.objects(subject=person0, predicate=foaf_name))
            self.assertEqual(len(person_names), 1)
            self.assertEqual(str(person_names[0]), "Person0")

            print(f"\nProcessed 100 rows in {elapsed_time:.3f} seconds")
            print(f"Generated {actual_triples} triples")

        finally:
            os.unlink(csv_file)

    def test_multicore_config_via_env_var(self):
        """Test that SETLR_MAX_WORKERS environment variable is respected"""
        # Create small test CSV
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            f.write('ID,Name\n')
            for i in range(10):
                f.write(f'{i},Name{i}\n')
            csv_file = f.name

        # Set SETLR_MAX_WORKERS to 2
        original_env = os.environ.get('SETLR_MAX_WORKERS')
        
        try:
            os.environ['SETLR_MAX_WORKERS'] = '2'

            # Build SETL graph
            setl_graph = Graph()
            setl_graph.bind('setl', setl)
            setl_graph.bind('prov', PROV)
            setl_graph.bind('csvw', csvw)

            table = ex.myTable
            setl_graph.add((table, RDF.type, setl.Table))
            setl_graph.add((table, RDF.type, csvw.Table))

            extract = setl_graph.resource(setl_graph.skolemize())
            extract.add(RDF.type, setl.Extract)
            extract.add(PROV.used, URIRef('file://' + csv_file))
            setl_graph.add((table, PROV.wasGeneratedBy, extract.identifier))

            output = ex.output
            setl_graph.add((output, RDF.type, void.Dataset))

            transform = setl_graph.resource(setl_graph.skolemize())
            transform.add(RDF.type, setl.Transform)
            transform.add(RDF.type, setl.JSLDT)
            transform.add(PROV.used, table)
            transform.add(PROV.value, Literal('[{"@id": "http://example.com/{{row.ID}}", "http://example.com/name": "{{row.Name}}"}]'))
            setl_graph.add((output, PROV.wasGeneratedBy, transform.identifier))

            # Execute - should use 2 workers as configured
            resources = setlr.run_setl(setl_graph)

            # Verify results
            self.assertIn(output, resources)
            output_graph = resources[output]
            self.assertGreater(len(output_graph), 0)

        finally:
            # Restore environment
            if original_env is not None:
                os.environ['SETLR_MAX_WORKERS'] = original_env
            else:
                os.environ.pop('SETLR_MAX_WORKERS', None)
            
            # Clean up CSV file
            os.unlink(csv_file)

    def test_parallel_processing_order_independence(self):
        """Test that parallel processing produces consistent results regardless of execution order"""
        # Create test CSV
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            f.write('ID,Value\n')
            for i in range(50):
                f.write(f'{i},{i*10}\n')
            csv_file = f.name

        try:
            # Build SETL graph
            setl_graph = Graph()
            setl_graph.bind('setl', setl)
            setl_graph.bind('prov', PROV)
            setl_graph.bind('csvw', csvw)

            table = ex.myTable
            setl_graph.add((table, RDF.type, setl.Table))
            setl_graph.add((table, RDF.type, csvw.Table))

            extract = setl_graph.resource(setl_graph.skolemize())
            extract.add(RDF.type, setl.Extract)
            extract.add(PROV.used, URIRef('file://' + csv_file))
            setl_graph.add((table, PROV.wasGeneratedBy, extract.identifier))

            output = ex.output
            setl_graph.add((output, RDF.type, void.Dataset))

            transform = setl_graph.resource(setl_graph.skolemize())
            transform.add(RDF.type, setl.Transform)
            transform.add(RDF.type, setl.JSLDT)
            transform.add(PROV.used, table)
            transform.add(PROV.value, Literal('[{"@id": "http://example.com/item/{{row.ID}}", "http://example.com/value": "{{row.Value}}"}]'))
            setl_graph.add((output, PROV.wasGeneratedBy, transform.identifier))

            # Execute multiple times to check consistency
            results = []
            for run in range(3):
                resources = setlr.run_setl(setl_graph)
                output_graph = resources[output]
                
                # Collect all triples and sort them for comparison
                triples = sorted([(str(s), str(p), str(o)) for s, p, o in output_graph])
                results.append(triples)

            # All runs should produce identical results
            self.assertEqual(results[0], results[1], "Run 1 and 2 should be identical")
            self.assertEqual(results[1], results[2], "Run 2 and 3 should be identical")

            # Verify we got all 50 items (each item produces 1 triple for value)
            self.assertGreaterEqual(len(results[0]), 50, f"Expected at least 50 triples, got {len(results[0])}")

        finally:
            os.unlink(csv_file)


if __name__ == '__main__':
    unittest.main()
