#!/bin/bash
set -e

source .env

docker build -t elifesciences/sciencebeam --build-arg sciencebeam_gym_commit=${SCIENCEBEAM_GYM_COMMIT} .
