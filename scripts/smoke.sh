#!/usr/bin/env bash
set -euo pipefail
BASE="${1:-http://127.0.0.1:8000}"
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
WAV="${ROOT}/fixtures/sample.wav"

echo "GET ${BASE}/health"
curl -fsS "${BASE}/health"
echo

echo "waiting for ${BASE}/ready"
for i in $(seq 1 120); do
  if curl -fsS "${BASE}/ready" >/dev/null 2>&1; then
    echo "ready"
    break
  fi
  if [ "$i" -eq 120 ]; then
    echo "timeout waiting for /ready" >&2
    curl -sS "${BASE}/ready" || true
    exit 1
  fi
  sleep 5
done
curl -fsS "${BASE}/ready"
echo

echo "POST ${BASE}/diarize"
curl -fsS -X POST "${BASE}/diarize" -F "file=@${WAV}"
echo
