#!/usr/bin/env bash

SUB_COMMAND="${1}"

if [[ ${SUB_COMMAND} == "bash" ]]; then
   shift
   exec "/bin/bash" "${@}"
elif [[ ${SUB_COMMAND} == "python" ]]; then
   shift
   exec "python" "${@}"
fi

exec python -m sciencebeam_parser.service.server "${@}"
