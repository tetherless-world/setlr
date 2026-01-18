#!/usr/bin/env python
# -*- coding: utf-8 -*-

from rdflib.util import guess_format
import rdflib
import csv
import json
import sys
import collections
import requests
import pandas
import re
import os
import click

from jinja2 import Template
from toposort import toposort_flatten
from numpy import isnan
import tempfile
import ijson
from . import iterparse_filter
#import xml.etree.ElementTree as ET
import xml.etree.ElementTree

from itertools import chain

import zipfile
import gzip

import logging

from tqdm import tqdm

import hashlib
from slugify import slugify
from pyshacl import validate

from .trig_store import TrigStore

from requests_testadapter import Resp


def hash(value):
    m = hashlib.sha256()
    m.update(value.encode('utf-8'))
    return m.hexdigest()

csvw = rdflib.Namespace('http://www.w3.org/ns/csvw#')
ov = rdflib.Namespace('http://open.vocab.org/terms/')
setl = rdflib.Namespace('http://purl.org/twc/vocab/setl/')
prov = rdflib.Namespace('http://www.w3.org/ns/prov#')
pv = rdflib.Namespace('http://purl.org/net/provenance/ns#')
sp = rdflib.Namespace('http://spinrdf.org/sp#')
sd = rdflib.Namespace('http://www.w3.org/ns/sparql-service-description#')
dc = rdflib.Namespace('http://purl.org/dc/terms/')
void = rdflib.Namespace('http://rdfs.org/ns/void#')
shacl = rdflib.Namespace('http://www.w3.org/ns/shacl#')
api_vocab = rdflib.Namespace('http://purl.org/linked-data/api/vocab#')

sys.setrecursionlimit(10000)


# Regex pattern for extracting Jinja2 template variables (compiled once for performance)
TEMPLATE_VAR_PATTERN = re.compile(r'\{\{([^}]+)\}\}')

def camelcase(s):
    return slugify(s).title().replace("-","")

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
    rdflib.XSD.string: str,
    rdflib.XSD.decimal: float,
    rdflib.XSD.integer: int,
    rdflib.XSD.float: float,
    rdflib.XSD.double: float
})

run_samples = -1

_rdf_formats_to_guess = [
    'xml',
    'json-ld',
    'trig',
    'nquads',
    'trix'
]


def read_csv(location, result):
    args = dict(
        sep = result.value(csvw.delimiter, default=rdflib.Literal(",")).value,
        #header = result.value(csvw.headerRow, default=rdflib.Literal(0)).value),
        skiprows = result.value(csvw.skipRows, default=rdflib.Literal(0)).value,
        dtype=str,
        # dtype = object    # Does not seem to play well with future and python2/3 conversion
    )
    if result.value(csvw.header):
        args['header'] = [0]
    with get_content(location, result) as fo:
        df = pandas.read_csv(fo, encoding='utf-8', **args)
        #logger.debug("Loaded %s", location)
        return df

def read_graph(location, result, g = None):
    if g is None:
        g = rdflib.ConjunctiveGraph()
    graph = rdflib.ConjunctiveGraph(store=g.store, identifier=result.identifier)
    if len(graph) == 0:
        data = get_content(location, result).read()
        f = guess_format(location)
        for fmt in [f] + _rdf_formats_to_guess:
            try:
                graph.parse(data=data, format=fmt)
                break
            except Exception:
                pass
        if len(graph) == 0:
            logger.error("Could not parse graph: %s", location)
        if result[rdflib.RDF.type:rdflib.OWL.Ontology]:
            for ontology in graph.subjects(rdflib.RDF.type, rdflib.OWL.Ontology):
                imports = [graph.resource(x) for x in graph.objects(ontology, rdflib.OWL.imports)]
                for i in imports:
                    read_graph(i.identifier, i, g = g)
    return g

class FileLikeFromIter(object):
    _closed = False

    def __init__(self, content_iter):
        self.iter = content_iter
        self.data = b''

    def __iter__(self):
        return self.iter

    def readable(self):
        return True

    def writable(self):
        return False

    def seekable(self):
        return False

    def closed(self):
        if self._closed:
            return True
        if len(self.data) > 0:
            return False
        try:
            self.data = next(self.iter)
        except StopIteration:
            self.closed = True
            return True
        return False

    # Enter and Exit are needed to allow this to work with with
    def __enter__(self):
        return self

    # Could be improved for better error/exception handling
    def __exit__(self, err_type, value, tracebock):
        pass

    def read(self, n=None):
        if n is None:
            return self.data + b''.join(line for line in self.iter)
        else:
            while len(self.data) < n:
                try:
                    self.data = b''.join((self.data, next(self.iter)))
                except StopIteration:
                    break
            result, self.data = self.data[:n], self.data[n:]
            return result

def _open_local_file(location):
    if location.startswith("file://"):
        if os.name == 'nt': # skip the initial
            return open(location.replace('file:///','').replace('file://',''),'rb')
        else:
            return open(location.replace('file://',''),'rb')

content_handlers = [
    _open_local_file,
    lambda location: FileLikeFromIter(requests.get(location,stream=True).iter_content(1024*1024))
]

def get_content(location, result):
    response = None
    for handler in content_handlers:
        response = handler(location)
        if response is not None:
            break
    if result[rdflib.RDF.type:setl.Tempfile]:
        result = to_tempfile(response)

    for t in result[rdflib.RDF.type]:
        # Do we know how to unpack this?
        if t.identifier in unpackers:
            response = unpackers[t.identifier](response)
    return response

def to_tempfile(f):
    tf = tempfile.TemporaryFile()
    logger.debug("Writing %s to disk.", f)
    for chunk in f:
        if chunk: # filter out keep-alive new chunks
            tf.write(chunk)
    tf.seek(0)
    logger.debug("Finished writing %s to disk.", f)
    return tf

def unpack_zipfile(f):
    zf = zipfile.ZipFile(f, mode='r')
    files = zf.infolist()
    return zf.open(files[0])

unpackers = {
#    setl.Tempfile : lambda x: x,
    setl.ZipFile : lambda x: unpack_zipfile(to_tempfile(x)),
    setl.GZipFile : lambda f: gzip.GzipFile(fileobj=f,mode='r')
}

packers = {
#    setl.Tempfile : lambda x: x,
    setl.GZipFile : lambda f: gzip.GzipFile(fileobj=f,mode='wb')
}

def read_excel(location, result):
    args = dict(
        sheet_name = result.value(setl.sheetname, default=rdflib.Literal(0)).value,
        header = [int(x) for x in result.value(csvw.headerRow, default=rdflib.Literal('0')).value.split(',')],
        skiprows = result.value(csvw.skipRows, default=rdflib.Literal(0)).value
    )
    if result.value(csvw.header):
        args['header'] = [result.value(csvw.header).value]
    with get_content(location, result) as fo:
        df = pandas.read_excel(fo, encoding='utf-8', **args)
        return df

def read_xml(location, result):
    validate_dtd = False
    if result[rdflib.RDF.type:setl.DTDValidatedXML]:
        validate_dtd = True
    f = iterparse_filter.IterParseFilter(validate_dtd=validate_dtd)
    if result.value(setl.xpath) is None:
        logger.debug("no xpath to select on from %s", location)
        f.iter_end("/*")
    for xp in result[setl.xpath]:
        f.iter_end(xp.value)
    with get_content(location, result) as fo:
        for (i, (event, ele)) in enumerate(tqdm(f.iterparse(fo))):
            yield i, ele


def read_json(location, result):
    selector = result.value(api_vocab.selector)
    if selector is not None:
        selector = selector.value
    else:
        selector = ""
    with get_content(location, result) as fo:
        yield from enumerate(tqdm(ijson.items(fo, selector)))


extractors = {
    setl.XPORT : lambda location, result: pandas.read_sas(get_content(location, result), format='xport'),
    setl.SAS7BDAT : lambda location, result: pandas.read_sas(get_content(location, result), format='sas7bdat'),
    setl.Excel : read_excel,
    csvw.Table : read_csv,
    rdflib.OWL.Ontology : read_graph,
    void.Dataset : read_graph,
    setl.JSON : read_json,
    setl.XML : read_xml,
    rdflib.URIRef("https://www.iana.org/assignments/media-types/text/plain") : lambda location, result: get_content(location, result)
}


try:
    from bs4 import BeautifulSoup
    extractors[setl.HTML] = lambda location, result: BeautifulSoup(get_content(location, result).read(), 'html.parser')
except Exception:
    pass


def load_csv(csv_resource):
    column_descriptions = {}
    for col in csv_resource[csvw.column]:
        label = col.value(rdflib.RDFS.label).value
        column_descriptions[label] = col
    csv_graph = rdflib.Graph(identifier=csv_resource)
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
                col = csv_graph.resource(rdflib.URIRef("urn:col_"+str(h)))
                col.add(rdflib.RDFS.label, rdflib.Literal(h))
                col.add(ov.csvCol, rdflib.Literal(j))
                if col_desc is not None:
                    col.add(rdflib.RDFS.range, col_desc.value(rdflib.RDFS.range, default=rdflib.XSD.string))
                properties.append(col)
                propertyMap[h] = col
            continue
        res = csv_graph.resource(csv_resource.identifier+"_row_"+str(i))
        res.add(rdflib.RDF.type, csvw.Row)
        res.add(csvw.rownum, rdflib.Literal(i))
        for j, value in enumerate(r):
            if skip_value is not None and skip_value == value:
                continue
            #print i, j, value
            prop = properties[j]
            datatype = prop.value(rdflib.RDFS['range'], default=rdflib.XSD.string)
            lit = rdflib.Literal(value, datatype=datatype.identifier)
            #print i, prop.identifier, lit.n3()
            res.add(prop.identifier, lit)
    logger.debug("Table has %s rows, %s columns, and %s triples", len(s), len(header), len(csv_graph))
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

def create_python_function(f, resources):
    global_vars = {'this' : f, 'resources': resources}
    local_vars = {}
    script = f.value(prov.value)
    for qd in f[prov.qualifiedDerivation]:
        entity = resources[qd.value(prov.entity).identifier]
        name = qd.value(prov.hadRole).value(dc.identifier)
        local_vars[name.value] = entity
    exec(script.value, local_vars, global_vars)
    resources[f.identifier] = global_vars['result']

def get_order(setl_graph):
    nodes = collections.defaultdict(set)

    for typ in actions:
        for task in setl_graph.subjects(rdflib.RDF.type, typ):
            task = setl_graph.resource(task)
            for used in task[prov.used]:
                nodes[task.identifier].add(used.identifier)

            for usage in task[prov.qualifiedUsage]:
                used = usage.value(prov.entity)
                nodes[task.identifier].add(used.identifier)
            for generated in task.subjects(prov.wasGeneratedBy):
                nodes[generated.identifier].add(task.identifier)
            for derivation in task[prov.qualifiedDerivation]:
                derived = derivation.value(prov.entity)
                nodes[task.identifier].add(derived.identifier)

    return toposort_flatten(nodes)

def extract(e, resources):
    logger.info('Extract %s',e.identifier)
    used = e.value(prov.used)
    for result in e.subjects(prov.wasGeneratedBy):
        if used is None:
            used = result
        for t in result[rdflib.RDF.type]:
            # Do we know how to generate this?
            if t.identifier in extractors:
                logger.info("Using %s", used.identifier)
                resources[result.identifier] = extractors[t.identifier](used.identifier, result)
                return resources[result.identifier]

def isempty(value):
    try:
        return isnan(value)
    except (TypeError, ValueError):
        return value is None

def clone(value):
    '''This is only a JSON-level cloning of objects. Atomic objects are invariant, and don't need to be cloned.'''
    if isinstance(value, list):
        return [x for x in value]
    elif isinstance(value, dict):
        return dict(value)
    else:
        return value

functions = {}
def get_function(expr, local_keys):
    used_local_keys = [k for k in local_keys if k in expr]
    key = tuple([expr]+sorted(used_local_keys))
    if key not in functions:
        script = '''lambda %s,**kwargs: %s'''% (', '.join(sorted(used_local_keys)), expr)
        #print(script)
        fn = eval(script)
        fn.__name__ = expr.encode("ascii", "ignore").decode('utf8')
        functions[key] = fn
    return functions[key]

templates = {}
def get_template(templ):
    if templ not in templates:
        t = Template(templ)
        templates[templ] = t
    return templates[templ]

def flatten_lists(o):
    if isinstance(o, list):
        result = []
        for x in o:
            flattened = flatten_lists(x)
            if isinstance(flattened, list):
                result.extend(flattened)
            else:
                result.append(flattened)
        return result
    elif isinstance(o, dict):
        for key in o.keys():
            o[key] = flatten_lists(o[key])
        return o
    else:
        return o

def process_row(row, template, rowname, table, resources, transform, variables):
    result = []
    e = {
        'row':row,
        'name': rowname,
        'table': table,
        'resources': resources,
        'template': template,
        "transform": transform,
        "setl_graph": transform.graph,
        "isempty":isempty,
        "slugify" : slugify,
        "camelcase" : camelcase,
        "hash":hash,
        "isinstance":isinstance,
        "str":str,
        "float":float,
        "int":int,
        "chain": lambda x: chain(*x),
        "list":list
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
            if len(task) != 2:
                logger.debug(task)
            key, value = task
            kt = get_template(key)
            key = kt.render(**env)
        if isinstance(value, dict):
            if '@if' in value:
                try:
                    fn = get_function(value['@if'], list(env.keys()))
                    incl = fn(**env)
                    if incl is None or not incl:
                        continue
                except KeyError:
                    continue
                except AttributeError:
                    continue
                except TypeError:
                    continue
                except Exception as e:
                    logger.error("=" * 80)
                    logger.error("Error evaluating @if conditional: %s", value['@if'])
                    transform_obj = env.get('transform', {})
                    transform_id = transform_obj.identifier if hasattr(transform_obj, 'identifier') else 'unknown'
                    logger.error("Transform: %s, Row: %s", transform_id, env.get('name', 'unknown'))
                    logger.error("Error type: %s", type(e).__name__)
                    logger.error("Error message: %s", str(e))
                    logger.error("Row-specific variables:")
                    for key in ['row', 'name']:
                        if key in env:
                            v = env[key]
                            try:
                                logger.error("  %s: %s", key, str(v)[:200])
                            except Exception:
                                logger.error("  %s: <%s>", key, type(v).__name__)
                    logger.error("=" * 80)
                    raise RuntimeError(f"Error in @if conditional '{value['@if']}': {type(e).__name__}: {str(e)}") from e
            if '@for' in value:
                f = value['@for']
                if isinstance(f, list):
                    f = ' '.join(f)
                variable_list, expression = f.split(" in ", 1)
                variable_list = re.split(r',\s+', variable_list.strip())
                val = value
                if '@do' in value:
                    val = value['@do']
                else:
                    del val['@for']
                try:
                    fn = get_function(expression, list(env.keys()))
                    values = fn(**env)
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
                    logger.error("=" * 80)
                    logger.error("Error in @for loop: %s", value['@for'])
                    transform_obj = env.get('transform', {})
                    transform_id = transform_obj.identifier if hasattr(transform_obj, 'identifier') else 'unknown'
                    logger.error("Transform: %s, Row: %s", transform_id, env.get('name', 'unknown'))
                    logger.error("Error type: %s", type(e).__name__)
                    logger.error("Error message: %s", str(e))
                    logger.error("Expression: %s", expression)
                    logger.error("Variables to assign: %s", variable_list)
                    logger.error("Available variables: %s", sorted([k for k in env.keys() if not k.startswith('_')]))
                    logger.error("=" * 80)
                    raise RuntimeError(f"Error in @for loop '{value['@for']}': {type(e).__name__}: {str(e)}") from e
                continue
            if '@with' in value:
                f = value['@with']
                if isinstance(f, list):
                    f = ' '.join(f)
                expression, variable_list = f.split(" as ", 1)
                variable_list = re.split(r',\s+', variable_list.strip())
                val = value
                if '@do' in value:
                    val = value['@do']
                else:
                    del val['@with']
                try:
                    fn = get_function(expression, list(env.keys()))
                    v = fn(**env)
                    if v is not None:
                        if (len(variable_list) == 1 and not (isinstance(v, collections.Iterable) and not isinstance(v, str))):
                            v = [v]
                        new_env = dict(env)
                        for i, variable in enumerate(variable_list):
                            new_env[variable] = v[i]
                        child = clone(val)
                        todo.append((child, parent, new_env))
                except KeyError:
                    pass
                except Exception as e:
                    logger.error("=" * 80)
                    logger.error("Error in @with expression: %s", value['@with'])
                    transform_obj = env.get('transform', {})
                    transform_id = transform_obj.identifier if hasattr(transform_obj, 'identifier') else 'unknown'
                    logger.error("Transform: %s, Row: %s", transform_id, env.get('name', 'unknown'))
                    logger.error("Error type: %s", type(e).__name__)
                    logger.error("Error message: %s", str(e))
                    logger.error("Expression: %s", expression)
                    logger.error("Variables to assign: %s", variable_list)
                    logger.error("Available variables: %s", sorted([k for k in env.keys() if not k.startswith('_')]))
                    logger.error("=" * 80)
                    raise RuntimeError(f"Error in @with expression '{value['@with']}': {type(e).__name__}: {str(e)}") from e
                continue
            this = {}
            for child in list(value.items()):
                if child[0] == '@if':
                    continue
                if child[0] == '@for':
                    continue
                todo.append((child, this, env))
        elif isinstance(value, list):
            this = []
            for child in value:
                todo.append((child, this, env))
        elif isinstance(value, str):
            try:
                template = get_template(str(value))
                this = template.render(**env)
            except Exception as e:
                logger.error("=" * 80)
                logger.error("Error rendering Jinja2 template: %s", value[:200] if len(value) > 200 else value)
                transform_obj = env.get('transform', {})
                transform_id = transform_obj.identifier if hasattr(transform_obj, 'identifier') else 'unknown'
                logger.error("Transform: %s, Row: %s", transform_id, env.get('name', 'unknown'))
                logger.error("Error type: %s", type(e).__name__)
                logger.error("Error message: %s", str(e))
                logger.error("Template variables referenced in template:")
                # Try to extract variable references from the template
                matches = TEMPLATE_VAR_PATTERN.findall(value)
                if matches:
                    for match in matches:
                        var_name = match.strip().split('.')[0].split('[')[0].strip()
                        if var_name in env:
                            val = env[var_name]
                            if type(val).__name__ == 'Element':
                                # XML Element
                                try:
                                    val = xml.etree.ElementTree.tostring(val).decode('utf-8', errors='replace')[:200]
                                except Exception:
                                    val = "<XML Element>"
                            else:
                                try:
                                    val = str(val)[:200]
                                except Exception:
                                    val = f"<{type(val).__name__}>"
                            logger.error("  %s = %s", var_name, val)
                        else:
                            logger.error("  %s = <NOT FOUND>", var_name)
                logger.error("=" * 80)
                raise RuntimeError(f"Error rendering template: {type(e).__name__}: {str(e)}") from e
        else:
            this = value

        if key is not None:
            parent[key] = this
        else:
            parent.append(this)

    return flatten_lists(result)

def json_transform(transform, resources):
    logger.info("Transform %s", transform.identifier)
    tables = [u for u in transform[prov.used]]
    variables = {}
    for usage in transform[prov.qualifiedUsage]:
        used = usage.value(prov.entity)
        role = usage.value(prov.hadRole)
        roleID = role.value(dc.identifier)
        variables[roleID.value] = resources[used.identifier]
        #print "Using", used.identifier, "as", roleID.value

    generated = list(transform.subjects(prov.wasGeneratedBy))[0]
    logger.info("Generating %s", generated.identifier)

    connected_downstream_graph = '''
construct {
   ?target ?p ?o
} where {
   ?source (<>|!<>)* ?target.
   ?target ?p ?o.
}
'''
    shape_graph = rdflib.Graph()
    for shape in transform.objects(dc.conformsTo):
        if shape[rdflib.RDF.type:shacl.NodeShape] or shape[rdflib.RDF.type:shacl.PropertyShape]:
            logger.info("Validating against SHACL shape %s", shape.identifier)
            shape_graph += transform.graph.query(connected_downstream_graph,
                                                 initBindings={"source":shape.identifier})
    if generated.identifier in resources:
        result = resources[generated.identifier]
    else:
        result = rdflib.ConjunctiveGraph()
        if generated[rdflib.RDF.type : setl.Persisted]:
            store = TrigStore()
            result = rdflib.ConjunctiveGraph(store=store)
        if generated[rdflib.RDF.type : setl.Persisted]:
            tempdir = tempfile.mktemp()
            logger.info("Persisting %s to %s", generated.identifier, tempdir)
            result.store.open(tempdir, True)
    s = transform.value(prov.value).value
    try:
        jslt = json.loads(s)
    except json.JSONDecodeError as e:
        logger.error("Error parsing JSON-LD template for transform %s", transform.identifier)
        lineno = getattr(e, 'lineno', 0)
        colno = getattr(e, 'colno', 0)
        msg = getattr(e, 'msg', str(e))
        logger.error("JSON parsing error at line %d, column %d: %s", lineno, colno, msg)
        # Show context around the error (8 lines before, 3 after for better bracket matching)
        lines = s.split("\n")
        start_line = max(0, lineno - 8)
        end_line = min(len(lines), lineno + 3)
        logger.error("Template context:")
        for i in range(start_line, end_line):
            prefix = ">>> " if i == lineno - 1 else "    "
            logger.error("%s%d: %s", prefix, i + 1, lines[i])
        raise ValueError(f"Invalid JSON-LD template in transform {transform.identifier}: {msg} at line {lineno}, column {colno}") from e
    except Exception as e:
        logger.error("Error parsing JSON-LD template for transform %s: %s", transform.identifier, str(e))
        logger.error("Template content:\n%s", s[:500])  # Show first 500 chars
        raise ValueError(f"Invalid JSON-LD template in transform {transform.identifier}: {str(e)}") from e
    context = transform.value(setl.hasContext)
    if context is not None:
        context = json.loads(context.value)
    for t in tables:
        logger.info("Using %s", t.identifier)
        table = resources[t.identifier]
        it = table
        if isinstance(table, pandas.DataFrame):
            #if run_samples:
            #    table = table.head()
            it = tqdm(table.iterrows(), total=table.shape[0])
            #logger.info("Transforming %s rows.", len(table.index))
        else:
            logger.info("Transform %s", t.identifier)
        for rowname, row in it:
            if run_samples > 0 and rowname >= run_samples:
                break
            try:
                root = None
                data = None
                root = {
                    "@id": generated.identifier,
                    "@graph": process_row(row, jslt, rowname, table, resources, transform, variables)
                }
                if context is not None:
                    root['@context'] = context

                #logger.debug(json.dumps(root, indent=4))
                #before = len(result)
                #graph = rdflib.ConjunctiveGraph(identifier=generated.identifier)
                #graph.parse(data=json.dumps(root),format="json-ld")
                data = json.dumps(root)
                #del root
                
                if len(shape_graph) > 0:
                    d = rdflib.ConjunctiveGraph()
                    d.parse(data=data,format='json-ld')
                    conforms, report, message = validate(d,
                                                         shacl_graph=shape_graph,
                                                         advanced=True,
                                                         debug=False)
                    if not conforms:
                        print(message)
                result.parse(data=data, format="json-ld")
                #del data
                #after = len(result)
                #logger.debug("Row "+str(rowname))#+" added "+str(after-before)+" triples.")
                #sys.stdout.flush()
            except Exception as e:
                logger.error("=" * 80)
                logger.error("Error in transform %s while processing row %s", transform.identifier, rowname)
                if isinstance(table, pandas.DataFrame):
                    # Format row data with better NaN handling
                    row_dict = {}
                    for key, value in dict(row).items():
                        if pandas.isna(value):
                            row_dict[key] = "<empty/missing>"
                        else:
                            row_dict[key] = value
                    logger.error("Row data: %s", row_dict)
                else:
                    logger.error("Row identifier: %s", rowname)
                
                # Try to provide more specific error information
                error_type = type(e).__name__
                if "JSON-LD" in str(e) or "json" in str(e).lower():
                    logger.error("JSON-LD processing error: %s", str(e))
                    if data is not None:
                        logger.error("Generated JSON-LD (first 1000 chars):\n%s", data[:1000])
                elif hasattr(e, 'lineno'):
                    logger.error("%s at line %d: %s", error_type, e.lineno, str(e))
                else:
                    logger.error("%s: %s", error_type, str(e))
                
                logger.error("=" * 80)
                raise RuntimeError(f"Failed to transform row {rowname} in transform {transform.identifier}: {error_type}: {str(e)}") from e

    resources[generated.identifier] = result

def transform(transform_resource, resources):
    logger.info('Transforming %s',transform_resource.identifier)

    transform_graph = rdflib.ConjunctiveGraph()
    for result in transform_graph.subjects(prov.wasGeneratedBy):
        transform_graph = rdflib.ConjunctiveGraph(identifier=result.identifier)

    used = set(transform_resource[prov.used])

    for csv_file in [u for u in used if u[rdflib.RDF.type:csvw.Table]]:
        csv_graph = rdflib.Graph(store=transform_graph.store,
                                 identifier=csv_file)
        csv_graph += resources[csv_file.identifier]


    for script in [u for u in used if u[rdflib.RDF.type:setl.PythonScript]]:
        logger.info("Script: %s", script.identifier)
        s = script.value(prov.value).value
        local_vars = dict(graph = transform_graph, setl_graph = transform_resource.graph)
        global_vars = dict()
        exec(s, global_vars, local_vars)

    for jsldt in [u for u in used if u[rdflib.RDF.type:setl.PythonScript]]:
        logger.info("Script: %s", script.identifier)
        s = script.value(prov.value).value
        local_vars = dict(graph = transform_graph, setl_graph = transform_resource.graph)
        global_vars = dict()
        exec(s, global_vars, local_vars)

    for update in [u for u in used if u[rdflib.RDF.type:sp.Update]]:
        logger.info("Update: %s", update.identifier)
        query = update.value(prov.value).value
        transform_graph.update(query)

    for construct in [u for u in used if u[rdflib.RDF.type:sp.Construct]]:
        logger.info("Construct: %s", construct.identifier)
        query = construct.value(prov.value).value
        g = transform_graph.query(query)
        transform_graph += g

    for csv_file in [u for u in used if u[rdflib.RDF.type:csvw.Table]]:
        g = rdflib.Graph(identifier=csv_file.identifier,store=transform_graph.store)
        g.remove((None, None, None))
        transform_graph.store.remove_graph(csv_file.identifier)

    for result in transform_graph.subjects(prov.wasGeneratedBy):
        resources[result.identifier] = transform_graph

def _load_open(generated):
    if generated.identifier.startswith("file://"):
        if os.name == 'nt': # skip the initial
            filename = generated.identifier.replace('file:///','').replace('file://','')
        else:
            filename = generated.identifier.replace('file://','')

    fh = open(filename, 'wb')
    for type, pack in packers.items():
        if generated[rdflib.RDF.type : type]:
            return pack(fh)
    return fh

def load(load_resource, resources):
    logger.info('Load %s',load_resource.identifier)
    file_graph = rdflib.Dataset(default_union=True)
    for used in load_resource[prov.used]:
        if used[rdflib.RDF.type : setl.Persisted]:
            file_graph = rdflib.Dataset(store='Sleepycat', default_union=True)
            tempdir = tempfile.mkdtemp()
            logger.debug("Gathering %s into %s", load_resource.identifier, tempdir)
            file_graph.store.open(tempdir, True)
            break
    if len(list(load_resource[prov.used])) == 1:
        logger.info("Using %s",load_resource.value(prov.used).identifier)
        file_graph = resources[load_resource.value(prov.used).identifier]
    else:
        for used in load_resource[prov.used]:
            logger.info("Using %s",used.identifier)
            used_graph = resources[used.identifier]
            file_graph.namespace_manager = used_graph.namespace_manager
            #print used_graph.serialize(format="trig")
            file_graph.addN(used_graph.quads())

    for generated in load_resource.subjects(prov.wasGeneratedBy):
        # TODO: support LDP-based loading
        if generated[rdflib.RDF.type:pv.File]:
            fmt = generated.value(dc['format'])
            if fmt is not None:
                fmt = fmt.value
            if fmt in formats:
                fmt = formats[fmt]
                #print fmt
            with _load_open(generated) as o:
                file_graph.serialize(o, format=fmt)

        elif generated[rdflib.RDF.type:sd.Service]:
            from rdflib.plugins.stores.sparqlstore import SPARQLUpdateStore
            endpoint = generated.value(sd.endpoint, default=generated).identifier
            store = SPARQLUpdateStore(endpoint, endpoint, autocommit=False)
            endpoint_graph = rdflib.Dataset(store=store, identifier=generated.identifier, default_union=True)
            endpoint_graph.addN(file_graph.quads())
            endpoint_graph.commit()


actions = {
    setl.Extract : extract,
    setl.Transform : json_transform,
    setl.Load : load,
    setl.PythonScript : create_python_function,
    setl.IsEmpty : isempty
}

def _setl(setl_graph):
    """Internal implementation function. Use run_setl() instead.
    
    This function is deprecated and maintained for backward compatibility.
    
    Args:
        setl_graph: A ConjunctiveGraph containing the SETL script.
        
    Returns:
        dict: A dictionary of resources created during the SETL process.
    """
    import warnings
    warnings.warn(
        "_setl() is deprecated and will be removed in a future version. "
        "Use run_setl() instead, which provides the same functionality with better documentation.",
        DeprecationWarning,
        stacklevel=2
    )
    return run_setl(setl_graph)


def run_setl(setl_graph):
    """Execute a SETL (Semantic Extract, Transform, Load) script.
    
    This is the main entry point for programmatically running SETL scripts.
    It processes a SETL graph containing extraction, transformation, and loading
    instructions for working with RDF data.
    
    Args:
        setl_graph (ConjunctiveGraph): A ConjunctiveGraph containing the SETL script
            in RDF format. The graph should define resources with types from the
            SETL vocabulary (http://purl.org/twc/vocab/setl/) including:
            - setl:Extract: Extract data from sources
            - setl:Transform: Transform data using JSON-LD templates
            - setl:Load: Load data to destinations
    
    Returns:
        dict: A dictionary mapping resource URIs to their generated content.
            The dictionary contains:
            - Extracted data (DataFrames, RDF graphs, etc.)
            - Transformed RDF graphs
            - References to action functions
            
    Example:
        >>> from rdflib import ConjunctiveGraph
        >>> from setlr import run_setl
        >>> 
        >>> # Load a SETL script
        >>> setl_graph = ConjunctiveGraph()
        >>> setl_graph.parse("my_script.setl.ttl", format="turtle")
        >>> 
        >>> # Execute the script
        >>> resources = run_setl(setl_graph)
        >>> 
        >>> # Access generated resources
        >>> output_graph = resources['http://example.com/output']
    
    Raises:
        RuntimeError: If there are errors during extraction, transformation, or loading.
        ValueError: If the SETL script contains invalid JSON-LD templates or configuration.
    
    Note:
        This function initializes the module logger if not already set and processes
        all SETL tasks in topological order based on their dependencies.
    """
    global logger
    if logger is None:
        logger = logging.getLogger(__name__)
    resources = {}
    resources.update(actions)

    tasks = [setl_graph.resource(t) for t in get_order(setl_graph)]

    for task in tasks:
        action = [actions[t.identifier] for t in task[rdflib.RDF.type] if t.identifier in actions]
        if len(action) > 0:
            action[0](task, resources)
    return resources


logger = None

@click.command()
@click.option('--quiet', '-q', is_flag=True, default=False, help="Minimize logging.")
@click.option('-n', default=-1, help="Only process the first N rows.", type=int)
#@click.option('--rdf-validation', default=None, help="Save the RDF validation report to this file.")
#@click.option('--text-validation', default=None, help="Save the text validation report to this file.")
@click.argument('script', type=click.Path(exists=True))
def main(script, rdf_validation=None, text_validation=None, quiet=False, n=-1):
    """Command-line interface for running SETL scripts.
    
    Args:
        script: Path to the SETL script file (Turtle format).
        quiet: If True, minimize logging output.
        n: Only process the first N rows (-1 for all rows).
    """
    logging_level = logging.DEBUG
    if quiet:
        logging_level = logging.WARNING
    logging.basicConfig(level=logging_level)

    global logger
    logger = logging.getLogger(__name__)

    global run_samples
    run_samples = n
    setl_graph = rdflib.ConjunctiveGraph()
    content = open(script).read()
    setl_graph.parse(data=content, format="turtle")

    run_setl(setl_graph)
