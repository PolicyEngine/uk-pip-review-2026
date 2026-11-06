#!/usr/bin/env bash
# Serve the production build and check the page a reader would get: robots
# noindex and the status banner (MOCK on a drill branch). Cut down from the
# AB2026 dashboard's smoke-built-site.sh. Run after `bun run build`.
#
#   scripts/smoke-built-site.sh [expected-status]
#
# expected-status defaults to the status in public/data/results.json.
set -euo pipefail
cd "$(dirname "$0")/.."
PORT="${PORT:-3107}"
BASE_PATH="$(node -e 'process.stdout.write(require("./src/lib/basePath.json").basePath)')"
EXPECTED="${1:-$(node -e 'process.stdout.write(require("./public/data/results.json").status)')}"

npx next start -p "$PORT" >/tmp/pip-review-smoke.log 2>&1 &
SERVER=$!
trap 'kill $SERVER 2>/dev/null || true' EXIT
for _ in $(seq 1 60); do
  curl -sf "http://localhost:$PORT$BASE_PATH/" -o /tmp/pip-review-smoke.html && break
  sleep 1
done
HTML=/tmp/pip-review-smoke.html
test -s "$HTML" || { echo "page did not start"; exit 1; }
grep -q 'name="robots" content="noindex' "$HTML" || { echo "robots noindex missing"; exit 1; }
if [ "$EXPECTED" = "final" ]; then
  if grep -q 'data-testid="status-banner"' "$HTML"; then echo "final page carries a banner"; exit 1; fi
else
  grep -q "data-testid=\"status-banner\" data-status=\"$EXPECTED\"" "$HTML" || { echo "status banner for $EXPECTED missing"; exit 1; }
fi
if [ "$EXPECTED" = "mock" ]; then
  grep -q 'MOCK' "$HTML" || { echo "MOCK text missing"; exit 1; }
fi
echo "Served build ok at $BASE_PATH/: noindex, status $EXPECTED"
