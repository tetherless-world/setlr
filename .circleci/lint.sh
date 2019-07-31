#!/bin/bash

mkdir -p lint-results/py

flake8 . &>lint-results/py/flake8.txt
pycodestyle . &>lint-results/py/pycodestyle.txt

cd ..
pylint --rcfile setlr/.pylintrc setlr &>setlr/lint-results/py/pylint.txt
