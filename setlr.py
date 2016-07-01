#!/usr/bin/env python

from rdflib import *
import rdflib
import csv
import json
import sys, collections
import requests
import pandas
from jinja2 import Template
from toposort import toposort_flatten
from StringIO import StringIO
from numpy import isnan

csvw = Namespace('http://www.w3.org/ns/csvw#')
ov = Namespace('http://open.vocab.org/terms/')
setl = Namespace('http://purl.org/twc/vocab/setl/')
prov = Namespace('http://www.w3.org/ns/prov#')
pv = Namespace('http://purl.org/net/provenance/ns#')
sp = Namespace('http://spinrdf.org/sp#')
sd = Namespace('http://www.w3.org/ns/sparql-service-description#')
dc = Namespace('http://purl.org/dc/terms/')

sys.setrecursionlimit(10000)

datatypeConverters = collections.defaultdict(lambda: str)
datatypeConverters.update({
    XSD.string: str,
    XSD.decimal: float,
    XSD.integer: int,
    XSD.float: float,
    XSD.double: float
})

run_samples = False

def read_csv(location, result):
    args = dict(
        sep = result.value(csvw.delimiter),
        header = range(result.value(csvw.headerRowCount)),
        skiprows = result.value(csvw.skipRows)
    )
    if result.value(csvw.header):
        args['header'] = [0]
    return pandaas.read_csv(location,**args)

extractors = {
    setl.XPORT : lambda location, result: pandas.read_sas(StringIO(requests.get(location).content), format='xport'),
    setl.SAS7BDAT : lambda location, result: pandas.read_sas(StringIO(requests.get(location).content), format='sas7bdat'),
    csvw.Table : read_csv
}

def load_csv(csv_resource):
    column_descriptions = {}
    for col in csv_resource[csvw.column]:
        label = col.value(RDFS.label).value
        column_descriptions[label] = col
    csv_graph = Graph(identifier=csv_resource)
    s = [x for x in csv.reader(open(str(csv_resource.value(csvw.url).identifier).replace("file://","")),
                   delimiter=str(csv_resource.value(csvw.delimiter,default=",").value),
                   quotechar=str(csv_resource.value(csvw.quoteChar,default='"').value))]
    header = None
    properties = []
    propertyMap = {}
    skip_value = csv_resource.value(csvw.null)
    if skip_value is not None:
        skip_value = skip_value.value
    for i, r in enumerate(s):
        if header is None:
            header = r
            for j, h in enumerate(header):
                col_desc = None
                if h in column_descriptions:
                    col_desc = column_descriptions[h]
                col = csv_graph.resource(URIRef("urn:col_"+str(h)))
                col.add(RDFS.label, Literal(h))
                col.add(ov.csvCol, Literal(j))
                if col_desc is not None:
                    col.add(RDFS.range, col_desc.value(RDFS.range, default=XSD.string))
                properties.append(col)
                propertyMap[h] = col
            continue
        res = csv_graph.resource(csv_resource.identifier+"_row_"+str(i))
        res.add(RDF.type, csvw.Row)
        res.add(csvw.rownum, Literal(i))
        for j, value in enumerate(r):
            if skip_value is not None and skip_value == value:
                continue
            #print i, j, value
            prop = properties[j]
            datatype = prop.value(RDFS['range'], default=XSD.string)
            lit =  Literal(value, datatype=datatype.identifier)
            #print i, prop.identifier, lit.n3()
            res.add(prop.identifier, lit)
    print "Table has", len(s), "rows,", len(header), "columns, and", len(csv_graph), "triples."
    return csv_graph

formats = {
    None:'xml',
    "application/rdf+xml":'xml',
    "text/rdf":'xml',
    'text/turtle':'turtle',
    'application/x-turtle':'turtle',
    'text/plain':'nt',
    'text/n3':'n3',
    'application/trig':'trig',
    'application/json':'json-ld'
}

def get_order(setl_graph):
    nodes = collections.defaultdict(set)

    for typ in [setl.Extract, setl.Transform, setl.Load]:
        for task in setl_graph.subjects(RDF.type, typ):
            task = setl_graph.resource(task)
            for used in task[prov.used]:
                nodes[task.identifier].add(used.identifier)
        
            for generated in task.subjects(prov.wasGeneratedBy):
                nodes[generated.identifier].add(task.identifier)
    
    return toposort_flatten(nodes)

def extract(e, resources):
    print 'Extracting',e.identifier
    used = e.value(prov.used)
    for result in e.subjects(prov.wasGeneratedBy):
        if used is None:
            used = result
        for t in result[RDF.type]:
            # Do we know how to generate this?
            if t.identifier in extractors:
                print "Extracted", result.identifier
                resources[result.identifier] = extractors[t.identifier](used.identifier, result)
                return
            
def json_transform(transform, resources):
    print "Transforming", transform.identifier
    tables = [u for u in transform[prov.used] if u[RDF.type:setl.Table]]

    def process_row(row, template, rowname):
        result = []
        e = {'row':row, 'name': rowname, 'template': template}
        todo = [[x, result, e] for x in template]
        while len(todo) > 0:
            task, parent, env = todo.pop()
            key = None
            value = task
            this = None
            if isinstance(parent, dict):
                key, value = task
                kt = Template(key)
                key = kt.render(**env)
            if isinstance(value, dict):
                if '@if' in value:
                    incl = eval(value['@if'], globals(), env)
                    if not incl:
                        continue
                this = {}
                for child in value.items():
                    if child[0] == '@if':
                        continue
                    todo.append((child, this, env))
            elif isinstance(value, list):
                this = []
                for child in value:
                    todo.append((child, this, env))
            elif isinstance(value, unicode):
                template = Template(value)
                this = template.render(**env)
            else:
                this = value

            if key is not None:
                parent[key] = this
            else:
                parent.append(this)
        return result
    
    generated = list(transform.subjects(prov.wasGeneratedBy))[0]
    print "Generating", generated.identifier

    result = ConjunctiveGraph()
    s = transform.value(prov.value).value
    jslt = json.loads(s)
    context = transform.value(setl.hasContext)
    if context is not None:
        context = json.loads(context.value)
    for t in tables:
        print "Using", t.identifier
        table = resources[t.identifier]
        if run_samples:
            table = table.head()
        print "Transforming", len(table.index), "rows."
        for rowname, row in table.iterrows():
            try:
                root = {
                    "@id": generated.identifier,
                    "@graph": process_row(row, jslt, rowname)
                }
                if context is not None:
                    root['@context'] = context
                #graph = ConjunctiveGraph(identifier=generated.identifier)
                #graph.parse(data=json.dumps(root),format="json-ld")
                result.parse(data=json.dumps(root), format="json-ld")
            except Exception as e:
                trace = sys.exc_info()[2]
                print "Error on", rowname, row
                raise e, None, trace

    resources[generated.identifier] = result
    
    
            
def transform(transform_resource, resources):
    print 'Transforming',transform_resource.identifier

    transform_graph = ConjunctiveGraph()
    for result in transform_graph.subjects(prov.wasGeneratedBy):
        transform_graph = ConjunctiveGraph(identifier=result.identifier)

    used = set(transform_resource[prov.used])
    
    for csv in [u for u in used if u[RDF.type:csvw.Table]]:
        csv_graph = Graph(store=transform_graph.store, identifier=csv)
        csv_graph += graphs[csv.identifier]

    
    for script in [u for u in used if u[RDF.type:setl.PythonScript]]:
        print "Script:", script.identifier
        s = script.value(prov.value).value
        l = dict(graph = transform_graph, setl_graph = transform_resource.graph)
        gl = dict()
        exec(s, gl, l)

    for jsldt in [u for u in used if u[RDF.type:setl.PythonScript]]:
        print "Script:", script.identifier
        s = script.value(prov.value).value
        l = dict(graph = transform_graph, setl_graph = transform_resource.graph)
        gl = dict()
        exec(s, gl, l)

    for update in [u for u in used if u[RDF.type:sp.Update]]:
        print "Update:", update.identifier
        query = update.value(prov.value).value
        transform_graph.update(query)
        
    for construct in [u for u in used if u[RDF.type:sp.Construct]]:
        print "Construct:", construct.identifier
        query = construct.value(prov.value).value
        g = transform_graph.query(query)
        transform_graph += g
        
    for csv in [u for u in used if u[RDF.type:csvw.Table]]:
        g = Graph(identifier=csv.identifier,store=transform_graph.store)
        g.remove((None, None, None))
        transform_graph.store.remove_graph(csv.identifier)
            
    for result in transform_graph.subjects(prov.wasGeneratedBy):
        graphs[result.identifier] = transform_graph

def load(load_resource, resources):
    print 'Loading',load_resource.identifier
    file_graph = ConjunctiveGraph()
    for used in load_resource[prov.used]:
        print "Using",used.identifier
        used_graph = resources[used.identifier]
        #print used_graph.serialize(format="trig")
        file_graph.addN(used_graph.quads())

    for generated in load_resource.subjects(prov.wasGeneratedBy):
        # TODO: support LDP-based loading
        if generated[RDF.type:pv.File]:
            fmt = generated.value(dc['format'])
            if fmt is not None:
                fmt = fmt.value
            if fmt in formats:
                fmt = formats[fmt]
                print fmt
            with open(generated.identifier.replace("file://",''), 'wb') as o:
                o.write(file_graph.serialize(format=fmt))
                o.close()
        elif generated[RDF.type:sd.Service]:
            from rdflib.plugins.stores.sparqlstore import SPARQLUpdateStore
            endpoint = generated.value(sd.endpoint, default=generated).identifier
            store = SPARQLUpdateStore(endpoint, endpoint, autocommit=False)
            endpoint_graph = ConjunctiveGraph(store=store, identifier=generated.identifier)
            endpoint_graph += file_graph
            endpoint_graph.commit()
    
        
actions = {
    setl.Extract : extract,
    setl.Transform : json_transform,
    setl.Load : load,
}
            
def _setl(setl_graph):
    resources = {}

    tasks = [setl_graph.resource(t) for t in get_order(setl_graph)]

    for task in tasks:
        action = [actions[t.identifier] for t in task[RDF.type] if t.identifier in actions]
        if len(action) > 0:
            action[0](task, resources)
    
    return resources
    
def main():
    global run_samples
    setl_file = sys.argv[1]
    if 'sample' in sys.argv:
        run_samples = True
        print "Only processing a few sample rows."
    setl_graph = ConjunctiveGraph()
    setl_graph.parse(open(setl_file), format="turtle")

    graphs = _setl(setl_graph)
                
if __name__ == '__main__':
    main(sys.argv[1])
