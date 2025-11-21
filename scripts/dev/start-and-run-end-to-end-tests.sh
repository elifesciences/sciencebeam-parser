#!/bin/bash

set -e

echo 'Starting and running end-to-end tests...'

python -m sciencebeam_parser.service.server --port=8070 --host=0.0.0.0 &
SERVER_PID=$!
echo "Server PID: $SERVER_PID"

cleanup() {
  echo "Stopping server (PID $SERVER_PID)..."
  kill "$SERVER_PID" 2>/dev/null || true
  wait "$SERVER_PID" 2>/dev/null || true
}
trap cleanup EXIT

# wait until server responds (timeout ~30s)
echo "Waiting for server on http://127.0.0.1:8070/ ..."
for i in $(seq 1 30); do
  if curl -sSf --max-time 1 http://127.0.0.1:8070/ >/dev/null 2>&1; then
    echo "Server is up"
    break
  fi
  sleep 1
done

$(dirname $0)/end-to-end-tests.sh
TEST_EXIT_CODE=$?

echo "End-to-end tests exited with code: $TEST_EXIT_CODE"

exit $TEST_EXIT_CODE
