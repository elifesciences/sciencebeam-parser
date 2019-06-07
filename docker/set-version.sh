#!/bin/sh

set -e

version="$1"
commit="$2"

if [ -z "$version" ] && [ ! -z "$commit" ]; then
  version=$($(dirname $0)/get-commit-version.sh "${commit}")
fi

sed -i -e "s/^__version__ = .*/__version__ = \"${version}\"/g" sciencebeam/__init__.py
