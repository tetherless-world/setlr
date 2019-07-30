import unittest
import rdflib
import json
import os

from setlr import read_json

# Checks the the file stays open through reading
class TestReadJson(unittest.TestCase):
    def test_read_json(self):
        expected_string = ''
        root_dir_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
        json_file = root_dir_path + "/tests/setlr_test/test_read_json.json"
        with open(json_file) as f:
            expected_string = f.read()
        expected_json = json.loads(expected_string)
        
        result = read_json(("file://{}".format(json_file)), rdflib.resource.Resource(rdflib.graph.Graph(), "test_read_json"))
        result = [r for r in result]      

        self.assertCountEqual(expected_json, result[0][1], "JSON objects not equal")

if __name__ == "__main__":
    unittest.main()