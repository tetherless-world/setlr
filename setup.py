import os
from setuptools import setup, find_packages
from sys import argv
#from _version import __version__

__version__='1.0.1'

# Utility function to read the README file.
# Used for the long_description.  It's nice, because now 1) we have a top level
# README file and 2) it's easier to type in the README file than to put a raw
# string in below ...
def read(fname):
    return open(os.path.join(os.path.dirname(__file__), fname)).read()

if '--version' in argv:
    print(__version__)
else:
    setup(
        name = "setlr",
        version = __version__,
        author = "Jamie McCusker",
        author_email = "mccusj@cs.rpi.edu",
        description = ("setlr is a tool for Semantic Extraction, Transformation, and Loading."),
        license = "Apache License 2.0",
        keywords = "rdf semantic etl",
        url = "http://packages.python.org/setlr",
        packages=['setlr'],
        long_description='''SETLr is a tool for generating RDF graphs, including named graphs, from almost any kind of tabular data.''',
        include_package_data = True,
        install_requires = [
            'future',
            'pip>=9.0.0',
            'cython',
            'numpy',
            'rdflib>=6.0.0',
            'pandas>=0.23.0',
            'requests',
            'toposort',
            'beautifulsoup4',
            'jinja2',
            'lxml',
            'six',
            'xlrd',
            'ijson',
            'click',
            'tqdm',
            'requests-testadapter',
            'python-slugify',
            'pyshacl[js]'
        ],
        entry_points = {
            'console_scripts': ['setlr=setlr:main'],
        },
        classifiers=[
            "Development Status :: 5 - Production/Stable",
            "Topic :: Utilities",
            "License :: OSI Approved :: Apache Software License",
        ],
    )

