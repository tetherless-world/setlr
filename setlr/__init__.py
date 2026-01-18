#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""setlr: Semantic Extract, Transform and Load-er

This package provides tools for generating RDF graphs from tabular data
using declarative SETL (Semantic Extract, Transform, Load) scripts.

Main functions:
    run_setl(setl_graph): Execute a SETL script (recommended)
    _setl(setl_graph): Deprecated, use run_setl() instead
    main(): Command-line interface entry point
"""

# Import the core functionality
from .core import (
    # Main API functions
    run_setl,
    _setl,  # Deprecated, but kept for backward compatibility
    main,
    
    # Utility functions that might be used by library users
    read_csv,
    read_excel,
    read_json,
    read_xml,
    read_graph,
    extract,
    json_transform,
    transform,
    load,
    isempty,
    hash,
    camelcase,
    get_content,
    
    # Logger for configuration
    logger,
    
    # Namespaces
    csvw,
    ov,
    setl,
    prov,
    pv,
    sp,
    sd,
    dc,
    void,
    shacl,
    api_vocab,
)

# Version
__version__ = '1.0.1'

# Define what gets imported with "from setlr import *"
__all__ = [
    'run_setl',
    '_setl',  # Deprecated but included for backward compatibility with wildcard imports
    'main',
    # Include commonly used utilities
    'logger',
    'read_csv',
    'read_excel', 
    'read_json',
    'read_xml',
    'read_graph',
    'extract',
    'json_transform',
    'transform',
    'load',
    'isempty',
    'hash',
    'camelcase',
    'get_content',
    # Namespaces
    'csvw',
    'ov',
    'setl',
    'prov',
    'pv',
    'sp',
    'sd',
    'dc',
    'void',
    'shacl',
    'api_vocab',
]
