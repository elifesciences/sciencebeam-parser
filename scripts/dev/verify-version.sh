#!/bin/bash

set -e

SCRIPT_HOME=$(dirname "$0")

version="$1"

actual_version="$("${SCRIPT_HOME}/print-version.sh")"

if [ "${actual_version}" != "${version}" ]; then
  echo "Version mismatches: ${actual_version} != ${version}"
  exit 2
else
  echo "Version maches (${actual_version})"
fi
