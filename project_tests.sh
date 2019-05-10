#!/bin/bash
set -e

pytest sciencebeam -p no:cacheprovider

echo "running pylint"
pylint sciencebeam setup.py

echo "running flake8"
flake8 sciencebeam setup.py

echo "done"
