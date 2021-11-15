#!/bin/sh

set -e

commit="$1"
repository="${2:-testpypi}"

if [ -z "$commit" ] || [ -z "$repository" ]; then
  echo "Usage: $0 <commit> [<repository>]"
  exit 1
fi

echo "commit=${commit}, repository=${repository}"

date_version=$(date '+%Y.%-m.%-d')
version_prefix="${date_version}.dev"
version=$($(dirname $0)/get-commit-version.sh "${version_prefix}" "${commit}")
echo 'test'
echo "version=${version}"

$(dirname $0)/set-version.sh "${version}"

cat sciencebeam_parser/__init__.py

python setup.py sdist

$(dirname $0)/push-pypi-version.sh "${version}" "${repository}"
