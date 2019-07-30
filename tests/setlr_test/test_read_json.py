import unittest
import rdflib
import json

from setlr import read_json

# Checks the the file stays open through reading
class TestReadJson(unittest.TestCase):
    def test_read_json(self):
        expected_string = '''
        [
            {
              "ID": "Alice",
              "Name": "Alice Smith",
              "MarriedTo": "Bob",
              "Knows": "Bob; Charles",
              "DOB": "1/12/1983"
            },
            {
              "ID": "Bob",
              "Name": "Bob Smith",
              "MarriedTo": "Alice",
              "Knows": "Alice; Charles",
              "DOB": "3/23/1985"
            },
            {
              "ID": "Charles",
              "Name": "Charles Brown",
              "MarriedTo": "",
              "Knows": "Alice; Bob",
              "DOB": "12/15/1955"
            },
            {
              "ID": "Dave",
              "Name": "Dave Jones",
              "MarriedTo": "",
              "Knows": "",
              "DOB": "4/25/1967"
            }
        ]
        '''
        expected_json = json.loads(expected_string)
        
        result = read_json(("file:///apps/setlr/tests/setlr_test/test_read_json.json"), rdflib.resource.Resource(rdflib.graph.Graph(), "test_read_json"))
        result = [r for r in result]      

        self.assertCountEqual(expected_json, result[0][1], "JSON objects not equal")

if __name__ == "__main__":
    unittest.main()