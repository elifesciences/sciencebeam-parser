#!/bin/sh

set -e

commit="$1"

if [ -z "$commit" ]; then
  echo "Usage: $0 <commit>"
  exit 1
fi

date_version=$(date '+%Y.%-m.%-d.%-H.%-M.%-S')
version_prefix="${date_version}.dev"
version=$($(dirname $0)/get-commit-version.sh "${version_prefix}" "${commit}")

echo "${version}"
