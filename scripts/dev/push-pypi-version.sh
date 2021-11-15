#!/bin/sh

set -e

version="$1"
repository="${2:-pypi}"

if [ -z "$version" ] || [ -z "$repository" ]; then
  echo "Usage: $0 <version> [<repository>]"
  exit 1
fi

echo "version=${version}, repository=${repository}"

$(dirname $0)/set-version.sh "${version}"

cat sciencebeam_parser/__init__.py

python setup.py sdist

ls -l $HOME/.pypirc

ls -l dist/

twine upload --repository "${repository}" --verbose "dist/sciencebeam_parser-${version}"*
