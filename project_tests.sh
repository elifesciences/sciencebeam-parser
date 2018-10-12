#!/bin/bash
set -e

pip install -r requirements.dev.txt

pytest sciencebeam

echo "running pylint"
pylint sciencebeam setup.py

echo "running flake8"
flake8 sciencebeam setup.py

echo "done"
