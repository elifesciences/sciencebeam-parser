#!/bin/sh

set -e

version="$1"

sed -i -e "s/^__version__ = .*/__version__ = \"${version}\"/g" sciencebeam_parser/__init__.py
