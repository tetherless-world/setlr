import unittest
import warnings
from rdflib import ConjunctiveGraph

# Import setlr module
import setlr


class TestBackwardCompatibility(unittest.TestCase):
    """Test that backward compatibility with _setl() is maintained"""
    
    def test_setl_deprecated_warning(self):
        """Test that _setl() shows deprecation warning"""
        setl_graph = ConjunctiveGraph()
        
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            result = setlr._setl(setl_graph)
            
            # Find our specific deprecation warning
            our_warnings = [warning for warning in w if "_setl()" in str(warning.message)]
            self.assertTrue(len(our_warnings) > 0, "Expected deprecation warning for _setl()")
            self.assertIn("Use run_setl() instead", str(our_warnings[0].message))
            
    def test_setl_still_works(self):
        """Test that _setl() still functions correctly despite deprecation"""
        from rdflib import URIRef
        setl_graph = ConjunctiveGraph()
        
        with warnings.catch_warnings(record=True):
            warnings.simplefilter("always")
            result = setlr._setl(setl_graph)
            
            # Check that result is a dictionary
            self.assertIsInstance(result, dict)
            # Check that it contains the expected actions (keys are URIRef objects)
            self.assertIn(URIRef('http://purl.org/twc/vocab/setl/Extract'), result)
            self.assertIn(URIRef('http://purl.org/twc/vocab/setl/Transform'), result)


class TestNewAPI(unittest.TestCase):
    """Test the new run_setl() API"""
    
    def test_run_setl_exists(self):
        """Test that run_setl() is accessible"""
        self.assertTrue(hasattr(setlr, 'run_setl'))
        self.assertTrue(callable(setlr.run_setl))
    
    def test_run_setl_basic_functionality(self):
        """Test that run_setl() works correctly"""
        from rdflib import URIRef
        setl_graph = ConjunctiveGraph()
        result = setlr.run_setl(setl_graph)
        
        # Check that result is a dictionary
        self.assertIsInstance(result, dict)
        # Check that it contains the expected actions (keys are URIRef objects)
        self.assertIn(URIRef('http://purl.org/twc/vocab/setl/Extract'), result)
        self.assertIn(URIRef('http://purl.org/twc/vocab/setl/Transform'), result)
        self.assertIn(URIRef('http://purl.org/twc/vocab/setl/Load'), result)
    
    def test_run_setl_no_deprecation_warning(self):
        """Test that run_setl() does not produce deprecation warning"""
        setl_graph = ConjunctiveGraph()
        
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            result = setlr.run_setl(setl_graph)
            
            # Filter to only our deprecation warnings (not rdflib's)
            our_warnings = [warning for warning in w if "_setl()" in str(warning.message)]
            self.assertEqual(len(our_warnings), 0, "run_setl() should not produce deprecation warning")
    
    def test_run_setl_has_documentation(self):
        """Test that run_setl() has proper documentation"""
        self.assertIsNotNone(setlr.run_setl.__doc__)
        self.assertIn("Execute a SETL", setlr.run_setl.__doc__)
        self.assertIn("Args:", setlr.run_setl.__doc__)
        self.assertIn("Returns:", setlr.run_setl.__doc__)
        self.assertIn("Example:", setlr.run_setl.__doc__)
    
    def test_setl_and_run_setl_equivalent(self):
        """Test that _setl() and run_setl() produce the same results"""
        setl_graph1 = ConjunctiveGraph()
        setl_graph2 = ConjunctiveGraph()
        
        with warnings.catch_warnings(record=True):
            warnings.simplefilter("always")
            result1 = setlr._setl(setl_graph1)
        
        result2 = setlr.run_setl(setl_graph2)
        
        # Both should return dictionaries with the same keys
        self.assertEqual(set(result1.keys()), set(result2.keys()))


if __name__ == "__main__":
    unittest.main()
