#!/bin/bash
set -e

pip install -r requirements.dev.txt

pytest sciencebeam

pylint sciencebeam
pylint setup.py
