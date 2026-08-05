#!/bin/sh
set -eu

mkdir -p benchmark-results
docker run --rm williamyeh/hey \
  -z "${DURATION:-30s}" \
  -c "${CONCURRENCY:-100}" \
  "http://host.docker.internal:8000/api/v1/trends?limit=20" \
  | tee benchmark-results/top-n.txt
