#!/bin/bash

set -e

echo 'Running end-to-end tests...'

PDFALTO_CONVERT_API_URL=http://localhost:8070/api/pdfalto
DOCKER_CONVERT_API_URL=http://localhost:8070/api/convert

EXAMPLE_PDF_DOCUMENT=test-data/minimal-example.pdf
EXAMPLE_DOCX_DOCUMENT=test-data/minimal-office-open.docx

echo 'Running: PDF to ALTO conversion end-to-end test...'
time curl --fail --show-error \
    --form "file=@$EXAMPLE_PDF_DOCUMENT;filename=$EXAMPLE_PDF_DOCUMENT" \
    --output /dev/null \
    "$PDFALTO_CONVERT_API_URL" \

echo 'Running: DOCX to TEI conversion end-to-end test...'
time curl --fail --show-error \
    --form "file=@$EXAMPLE_DOCX_DOCUMENT;filename=$EXAMPLE_DOCX_DOCUMENT" \
    --output /dev/null \
    "$DOCKER_CONVERT_API_URL"

echo 'Done: Running end-to-end tests'
