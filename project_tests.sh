#!/bin/bash
set -e

pip install -r requirements.dev.txt

pytest sciencebeam

pylint sciencebeam setup.py

flake8 sciencebeam setup.py
