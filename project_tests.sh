#!/bin/bash
set -e

docker run --rm elife/sciencebeam /bin/bash -c 'venv/bin/pip install -r requirements.dev.txt && venv/bin/pytest sciencebeam'
