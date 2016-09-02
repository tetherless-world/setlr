#!/usr/bin/env python
# -*- coding: utf-8 -*-

from rdflib import *
from rdflib.util import guess_format
import rdflib
import csv
import json
import sys, collections
import requests
import pandas
import re
from jinja2 import Template
from toposort import toposort_flatten
from StringIO import StringIO
from numpy import isnan
import uuid

import hashlib

def hash(value):
    m = hashlib.sha256()
    m.update(value.encode('utf-8'))
    return m.hexdigest()

csvw = Namespace('http://www.w3.org/ns/csvw#')
ov = Namespace('http://open.vocab.org/terms/')
setl = Namespace('http://purl.org/twc/vocab/setl/')
prov = Namespace('http://www.w3.org/ns/prov#')
pv = Namespace('http://purl.org/net/provenance/ns#')
sp = Namespace('http://spinrdf.org/sp#')
sd = Namespace('http://www.w3.org/ns/sparql-service-description#')
dc = Namespace('http://purl.org/dc/terms/')
void = Namespace('http://rdfs.org/ns/void#')

sys.setrecursionlimit(10000)

from requests_testadapter import Resp

class LocalFileAdapter(requests.adapters.HTTPAdapter):
    def build_response_from_file(self, request):
        file_path = request.url[7:]
        with open(file_path, 'rb') as file:
            buff = bytearray(os.path.getsize(file_path))
            file.readinto(buff)
            resp = Resp(buff)
            r = self.build_response(request, resp)
            return r
    def send(self, request, stream=False, timeout=None,
             verify=True, cert=None, proxies=None):
        return self.build_response_from_file(request)

requests_session = requests.session()
requests_session.mount('file://', LocalFileAdapter())
requests_session.mount('file:///', LocalFileAdapter())
    
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
        sep = result.value(csvw.delimiter, default=Literal(",")).value,
        #header = result.value(csvw.headerRow, default=Literal(0)).value),
        skiprows = result.value(csvw.skipRows, default=Literal(0)).value
    )
    if result.value(csvw.header):
        args['header'] = [0]
    df = pandas.read_csv(location,encoding='utf-8', **args)
    return df

_rdf_formats_to_guess = [
    'xml',
    'json-ld',
    'trig',
    'nquads',
    'trix'
]
    
def read_graph(location, result, g = None):
    if g is None:
        g = Dataset(default_union=True)
    graph = g.graph(result.identifier)
    if len(graph) == 0:
        data = get_content(location).read()
        f = guess_format(location)
        for fmt in [f] + _rdf_formats_to_guess:
            try:
                graph.parse(data=data, format=fmt)
                break
            except Exception as e:
                #print e
                pass
        if len(graph) == 0:
            print "Could not parse graph: ", location
        for ontology in graph.subjects(RDF.type, OWL.Ontology):
            imports = [graph.resource(x) for x in graph.objects(ontology, OWL.imports)]
            for i in imports:
                read_graph(i.identifier, i, g = g)
    return g

def get_content(location):
    if location.startswith("file://"):
        return open(location[7:],'rb')
    else:
        return StringIO(requests.get(location).content)

extractors = {
    setl.XPORT : lambda location, result: pandas.read_sas(get_content(location), format='xport'),
    setl.SAS7BDAT : lambda location, result: pandas.read_sas(get_content(location), format='sas7bdat'),
    csvw.Table : read_csv,
    OWL.Ontology : read_graph,
    void.Dataset : read_graph
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
    'application/turtle':'turtle',
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

            for usage in task[prov.qualifiedUsage]:
                used = usage.value(prov.entity)
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

def isempty(value):
    try:
        return isnan(value)
    except:
        return value is None

def clone(value):
    __doc__ = '''This is only a JSON-level cloning of objects. Atomic objects are invariant, and don't need to be cloned.'''
    if isinstance(value, list):
        return [x for x in value]
    elif isinstance(value, dict):
        return dict(value)
    else:
        return value
    
def json_transform(transform, resources):
    print "Transforming", transform.identifier
    tables = [u for u in transform[prov.used] if u[RDF.type:setl.Table]]
    variables = {}
    for usage in transform[prov.qualifiedUsage]:
        used = usage.value(prov.entity)
        role = usage.value(prov.hadRole)
        roleID  = role.value(dc.identifier)
        variables[roleID.value] = resources[used.identifier]

    def process_row(row, template, rowname, table, resources):
        result = []
        e = {'row':row,
             'name': rowname,
             'table': table,
             'resources': resources,
             'template': template,
             "transform": transform,
             "setl_graph": transform.graph,
             "isempty":isempty,
             "hash":hash
        }
        e.update(variables)
        e.update(rdflib.__dict__)
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
                    try:
                        incl = eval(value['@if'], globals(), env)
                        if not incl:
                            continue
                    except Exception as e:
                        trace = sys.exc_info()[2]
                        print "Error in conditional", value['@if']
                        print "Locals:", env.keys()
                        raise e, None, trace
                if '@for' in value:
                    f = value['@for']
                    if isinstance(f, list):
                        f = ' '.join(f)
                    variable_list, expression = f.split(" in ", 1)
                    variable_list = re.split(',\s+', variable_list.strip())
                    val = value
                    if '@do' in value:
                        val = value['@do']
                    else:
                        del val['@for']
                    try:
                        values = eval(expression, globals(), env)
                        if values is not None:
                            for v in values:
                                if len(variable_list) == 1:
                                    v = [v]
                                new_env = dict(env)
                                for i, variable in enumerate(variable_list):
                                    new_env[variable] = v[i]
                                child = clone(val)
                                todo.append((child, parent, new_env))
                    except KeyError:
                        pass
                    except Exception as e:
                        trace = sys.exc_info()[2]
                        print "Error in for:", value['@for']
                        print "Locals:", env.keys()
                        raise e, None, trace
                    continue
                this = {}
                for child in value.items():
                    if child[0] == '@if':
                        continue
                    if child[0] == '@for':
                        continue
                    todo.append((child, this, env))
            elif isinstance(value, list):
                this = []
                for child in value:
                    todo.append((child, this, env))
            elif isinstance(value, unicode):
                try:
                    template = Template(unicode(value))
                    this = template.render(**env)
                except Exception as e:
                    trace = sys.exc_info()[2]
                    print "Error in template", value, type(value)
                    raise e, None, trace
            else:
                this = value

            if key is not None:
                parent[key] = this
            else:
                parent.append(this)
        return result
    
    generated = list(transform.subjects(prov.wasGeneratedBy))[0]
    print "Generating", generated.identifier

    result = resources[generated.identifier] if generated.identifier in resources else ConjunctiveGraph()
    s = transform.value(prov.value).value
    try:
        jslt = json.loads(s)
    except Exception as e:
        trace = sys.exc_info()[2]
        if 'line' in e.message:
            line = int(re.search("line ([0-9]+)", e.message).group(1))
            print "Error in parsing JSON Template at line %d:" % line
            print '\n'.join(["%d: %s"%(i+line-3, x) for i, x in enumerate(s.split("\n")[line-3:line+4])])
        raise e, None, trace
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
                    "@graph": process_row(row, jslt, rowname, table, resources)
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
        file_graph.namespace_manager = used_graph.namespace_manager
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
    content = open(setl_file).read()
    setl_graph.parse(data=content, format="turtle")

    graphs = _setl(setl_graph)
                
if __name__ == '__main__':
    main()
