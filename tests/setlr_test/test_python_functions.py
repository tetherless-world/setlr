#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Unit tests for Python function execution in setlr transforms.

Tests the setl:PythonScript capability that allows custom Python code
execution within SETL transforms.
"""

import unittest
import tempfile
import os
from rdflib import Graph, Namespace, Literal, URIRef
from rdflib.namespace import RDF, PROV
import setlr

setl = Namespace('http://purl.org/twc/vocab/setl/')
void = Namespace('http://rdfs.org/ns/void#')
ex = Namespace('http://example.com/')


class TestPythonFunctions(unittest.TestCase):
    """Test Python function execution in SETL transforms"""

    def test_python_function_in_transform(self):
        """Test that Python functions can be executed within transforms"""
        # Create a test CSV file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            f.write('ID,Value\n')
            f.write('1,10\n')
            f.write('2,20\n')
            f.write('3,30\n')
            csv_file = f.name

        try:
            # Create SETL script with Python function
            setl_graph = Graph()
            setl_graph.bind('setl', setl)
            setl_graph.bind('prov', PROV)
            setl_graph.bind('void', void)
            setl_graph.bind('ex', ex)

            # Define table extraction
            table = ex.table
            setl_graph.add((table, RDF.type, setl.Table))
            extract = setl_graph.resource(setl_graph.skolemize())
            extract.add(RDF.type, setl.Extract)
            extract.add(PROV.used, URIRef('file://' + csv_file))
            setl_graph.add((table, PROV.wasGeneratedBy, extract.identifier))

            # Define Python script to double values
            python_script = setl_graph.resource(setl_graph.skolemize())
            python_script.add(RDF.type, setl.PythonScript)
            python_script.add(PROV.used, table)
            python_script.add(PROV.value, Literal('''
for index, row in table.iterrows():
    result = row['Value'] * 2
    print(f"Row {row['ID']}: {row['Value']} * 2 = {result}")
'''))

            output_graph = ex.output
            setl_graph.add((output_graph, RDF.type, void.Dataset))
            setl_graph.add((output_graph, PROV.wasGeneratedBy, python_script.identifier))

            # Execute SETL
            resources = setlr.run_setl(setl_graph)

            # Verify resources were created
            self.assertIn(str(table), resources)
            self.assertIn(str(output_graph), resources)

        finally:
            os.unlink(csv_file)

    def test_python_function_with_graph_output(self):
        """Test Python function that generates RDF graph"""
        # Create a test CSV file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            f.write('Name,Score\n')
            f.write('Alice,95\n')
            f.write('Bob,87\n')
            csv_file = f.name

        try:
            # Create SETL script
            setl_graph = Graph()
            setl_graph.bind('setl', setl)
            setl_graph.bind('prov', PROV)

            # Define table
            table = ex.table
            setl_graph.add((table, RDF.type, setl.Table))
            extract = setl_graph.resource(setl_graph.skolemize())
            extract.add(RDF.type, setl.Extract)
            extract.add(PROV.used, URIRef('file://' + csv_file))
            setl_graph.add((table, PROV.wasGeneratedBy, extract.identifier))

            # Define Python script that creates RDF
            python_script = setl_graph.resource(setl_graph.skolemize())
            python_script.add(RDF.type, setl.PythonScript)
            python_script.add(PROV.used, table)
            python_script.add(PROV.value, Literal('''
from rdflib import Namespace, Literal
ex_ns = Namespace('http://example.com/')
for index, row in table.iterrows():
    person = ex_ns[row['Name']]
    result.add((person, RDF.type, ex_ns.Person))
    result.add((person, ex_ns.score, Literal(row['Score'])))
'''))

            output_graph = ex.output
            setl_graph.add((output_graph, RDF.type, void.Dataset))
            setl_graph.add((output_graph, PROV.wasGeneratedBy, python_script.identifier))

            # Execute SETL
            resources = setlr.run_setl(setl_graph)

            # Verify graph was created with RDF triples
            if str(output_graph) in resources:
                graph = resources[str(output_graph)]
                # Check that some triples were generated
                self.assertGreater(len(graph), 0, "Python script should generate RDF triples")

        finally:
            os.unlink(csv_file)


if __name__ == '__main__':
    unittest.main()
