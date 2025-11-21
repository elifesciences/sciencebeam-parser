#!/bin/sh

set -e

version_prefix="$1"
commit="$2"

log() {
  echo $@ >> /dev/stderr
}

if [ -z "$version_prefix" ] || [ -z "$commit" ]; then
  log "Usage: $0 <version_prefix> <commit>"
  exit 1
fi

log "version_prefix=${version_prefix}, commit=${commit}"

short_commit="$(echo $commit | tail -c 8)"
log "short_commit=${short_commit}"

int_commit="$(bash -c 'echo $((16#'$short_commit'))')"
log "int_commit=${int_commit}"

version="${version_prefix}${int_commit}"
log "version=${version}"

echo "${version}"
