from setuptools import setup
from sys import argv

__version__='1.0.2'

if '--version' in argv:
    print(__version__)
else:
    # Configuration is now in pyproject.toml
    setup()

