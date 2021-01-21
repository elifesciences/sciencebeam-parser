#!/bin/bash

set -e # everything must succeed.

CONVERT_API_URL=http://localhost:8075/api/convert


docker_stats_json() {
    docker stats --no-stream --format \
        '{"container": "{{.Name}}", "cpu_percentage": "{{.CPUPerc}}", "memory_usage": "{{.MemUsage}}", "num_pids": {{.PIDs}}}' \
        | jq -c '. + {"memory_used": (.memory_usage | scan("^\\S+"))}'
}


docker_stats_json_run_to_file() {
    run_no="$1"
    output_file="$2"
    timestamp=$(date --iso-8601=seconds)
    if [ -z "${output_file}" ]; then
        echo "Usage: $0 <run no> <output file>"
        exit 1
    fi
    docker_stats_json \
        | jq -c '. + {"run_id": '${run_no}', "timestamp": "'${timestamp}'"}' \
        >> "${output_file}" 2>&1
}


source_file="${1:-./test-data/minimal-office-open.docx}"

if [ -z "${source_file}" ]; then
    echo "Usage: $0 <source file>"
    exit 1
fi

if [ ! -f "${source_file}" ]; then
    echo "Error: file does not exist: ${source_file}"
    exit 2
fi

output_file="./.temp/docker-stats-runs.jsonl"

echo "source_file: ${source_file}"
echo "api: ${CONVERT_API_URL}"

echo "saving docker stats to: ${output_file}"
docker_stats_json_run_to_file 0 "${output_file}"

for log_counter in {1..100000}; do
    sleep 10
    docker_stats_json_run_to_file $log_counter "${output_file}"
done &
bg_log_pid=$!
trap 'kill -9 $bg_log_pid' EXIT

num_max_procs=10
num_current_jobs="\j"  # The prompt escape for number of jobs currently running

for counter in {1..100000}; do
    echo "num_current_jobs: ${num_current_jobs@P}"
    while (( ${num_current_jobs@P} >= num_max_procs )); do
        wait -n
    done
    echo "run: ${counter}"

    curl --fail --show-error \
        -H "Accept: application/pdf" \
        --form "file=@${source_file};filename=${source_file}" \
        --silent $CONVERT_API_URL \
        > /dev/null \
        &
done
