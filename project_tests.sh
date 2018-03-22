#!/bin/bash
set -e

docker run --rm elifesciences/sciencebeam /bin/bash -c 'pip install -r requirements.dev.txt && pytest sciencebeam'
