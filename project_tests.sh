#!/bin/bash
set -e

echo "running flake8"
flake8 sciencebeam setup.py

echo "running pylint"
pylint sciencebeam setup.py

echo "running pytest"
pytest -p no:cacheprovider

echo "done"
