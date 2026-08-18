#!/usr/bin/env bash
# Record a py-spy flame graph of the running app container while hitting one
# of the AP1 demo endpoints concurrently.
#
# Usage: ./scripts/profile_pyspy.sh <bad|good|bridge> <output.svg>
set -euo pipefail

MODE="${1:-bad}"
OUT="${2:-flamegraph-$MODE.svg}"
CONCURRENCY="${3:-3}"

echo "Recording py-spy while firing $CONCURRENCY concurrent requests at /demo/ap1/$MODE ..."

(for i in $(seq 1 "$CONCURRENCY"); do
  curl -s -o /dev/null "http://localhost:8000/demo/ap1/$MODE" &
done
wait) &

docker compose exec app py-spy record -o "/tmp/$OUT" --pid 1 --duration 5 --rate 200
docker compose cp "app:/tmp/$OUT" "benchmarks/ap1-blocking/$OUT"

echo "Saved benchmarks/ap1-blocking/$OUT"
