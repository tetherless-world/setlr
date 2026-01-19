#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Unit tests for XML streaming capability using iterparse_filter.

Tests the XML parsing with XPath filtering for efficient processing
of large XML files.
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
ex = Namespace('http://example.com/')


class TestStreamingXML(unittest.TestCase):
    """Test XML streaming with XPath filtering"""

    def test_basic_xml_extraction(self):
        """Test basic XML file extraction"""
        # Create a test XML file
        xml_content = '''<?xml version="1.0"?>
<root>
  <person id="1">
    <name>Alice</name>
    <age>30</age>
  </person>
  <person id="2">
    <name>Bob</name>
    <age>25</age>
  </person>
</root>'''

        with tempfile.NamedTemporaryFile(mode='w', suffix='.xml', delete=False) as f:
            f.write(xml_content)
            xml_file = f.name

        try:
            # Create SETL script
            setl_graph = Graph()
            setl_graph.bind('setl', setl)
            setl_graph.bind('prov', PROV)
            setl_graph.bind('csvw', csvw)

            # Define XML table
            table = ex.xmlTable
            setl_graph.add((table, RDF.type, setl.Table))
            setl_graph.add((table, RDF.type, csvw.Table))
            
            extract = setl_graph.resource(setl_graph.skolemize())
            extract.add(RDF.type, setl.Extract)
            extract.add(PROV.used, URIRef('file://' + xml_file))
            setl_graph.add((table, PROV.wasGeneratedBy, extract.identifier))

            # Execute SETL
            resources = setlr.run_setl(setl_graph)

            # Verify table was created
            self.assertIn(str(table), resources)
            table_df = resources[str(table)]
            
            # Should have extracted some data
            self.assertIsNotNone(table_df)

        finally:
            os.unlink(xml_file)

    def test_xml_with_xpath(self):
        """Test XML extraction with XPath filtering"""
        # Create a test XML file with nested structure
        xml_content = '''<?xml version="1.0"?>
<catalog>
  <book id="bk101">
    <author>Gambardella, Matthew</author>
    <title>XML Developer's Guide</title>
    <price>44.95</price>
  </book>
  <book id="bk102">
    <author>Ralls, Kim</author>
    <title>Midnight Rain</title>
    <price>5.95</price>
  </book>
  <magazine id="mg001">
    <title>Tech Weekly</title>
    <price>9.99</price>
  </magazine>
</catalog>'''

        with tempfile.NamedTemporaryFile(mode='w', suffix='.xml', delete=False) as f:
            f.write(xml_content)
            xml_file = f.name

        try:
            # Create SETL script with XPath
            setl_graph = Graph()
            setl_graph.bind('setl', setl)
            setl_graph.bind('prov', PROV)

            # Define XML table with XPath to select only books
            table = ex.booksTable
            setl_graph.add((table, RDF.type, setl.Table))
            setl_graph.add((table, setl.xpath, Literal('//book')))
            
            extract = setl_graph.resource(setl_graph.skolemize())
            extract.add(RDF.type, setl.Extract)
            extract.add(PROV.used, URIRef('file://' + xml_file))
            setl_graph.add((table, PROV.wasGeneratedBy, extract.identifier))

            # Execute SETL
            resources = setlr.run_setl(setl_graph)

            # Verify table was created
            self.assertIn(str(table), resources)

        finally:
            os.unlink(xml_file)


if __name__ == '__main__':
    unittest.main()
