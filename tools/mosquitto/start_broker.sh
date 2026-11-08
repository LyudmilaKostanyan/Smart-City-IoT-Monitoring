#!/usr/bin/env bash
# Start a local Eclipse Mosquitto broker without system install / sudo.
# Run as:  ./tools/mosquitto/start_broker.sh
# Do NOT use: source ./tools/mosquitto/start_broker.sh

set -euo pipefail

if [[ "${BASH_SOURCE[0]}" != "$0" ]]; then
  echo "Do not source this file." >&2
  echo "Run: ./tools/mosquitto/start_broker.sh" >&2
  return 1
fi

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BIN="${ROOT_DIR}/root/usr/sbin/mosquitto"
CONF="${ROOT_DIR}/mosquitto.conf"
PID_FILE="${ROOT_DIR}/mosquitto.pid"
LIB_DIR="${ROOT_DIR}/root/usr/lib/x86_64-linux-gnu"

export LD_LIBRARY_PATH="${LIB_DIR}:${LD_LIBRARY_PATH:-}"

if [[ ! -x "${BIN}" ]]; then
  echo "Mosquitto binary not found: ${BIN}" >&2
  exit 1
fi

if [[ -f "${PID_FILE}" ]] && kill -0 "$(cat "${PID_FILE}")" 2>/dev/null; then
  echo "Mosquitto already running on localhost:1883 (pid $(cat "${PID_FILE}"))"
  echo "Nothing to do — the broker is already running."
  exit 0
fi

rm -f "${PID_FILE}"
"${BIN}" -c "${CONF}" -d
sleep 0.4

if [[ -f "${PID_FILE}" ]] && kill -0 "$(cat "${PID_FILE}")" 2>/dev/null; then
  echo "Mosquitto started on localhost:1883 (pid $(cat "${PID_FILE}"))"
else
  echo "Failed to start Mosquitto. Check ${ROOT_DIR}/mosquitto.log" >&2
  exit 1
fi
