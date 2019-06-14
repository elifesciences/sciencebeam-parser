#!/bin/sh

set -e

commit="$1"
version_prefix="$2"

log() {
  echo $@ >> /dev/stderr
}

if [ -z "$commit" ]; then
  log "Usage: $0 <commit> [<version_prefix>]"
  exit 1
fi

if [ -z "$version_prefix" ]; then
  date_version=$(date '+%Y.%-m.%-d')
  version_prefix="${date_version}.dev"
fi

if [ "$commit" = "develop" ]; then
  commit=1
fi

log "version_prefix=${version_prefix}, commit=${commit}"

short_commit="$(echo $commit | tail -c 8)"
log "short_commit=${short_commit}"

int_commit="$(bash -c 'echo $((16#'$short_commit'))')"
log "int_commit=${int_commit}"

version="${version_prefix}${int_commit}"
log "version=${version}"

echo "${version}"
