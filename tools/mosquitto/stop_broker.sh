#!/usr/bin/env bash
# Stop the local Eclipse Mosquitto broker started by start_broker.sh.
# Run as:  ./tools/mosquitto/stop_broker.sh
# Do NOT use: source ./tools/mosquitto/stop_broker.sh

set -euo pipefail

if [[ "${BASH_SOURCE[0]}" != "$0" ]]; then
  echo "Do not source this file." >&2
  echo "Run: ./tools/mosquitto/stop_broker.sh" >&2
  return 1
fi

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PID_FILE="${ROOT_DIR}/mosquitto.pid"

if [[ ! -f "${PID_FILE}" ]]; then
  echo "No pid file found. Trying to stop by process name..."
  if pkill -f "${ROOT_DIR}/root/usr/sbin/mosquitto"; then
    echo "Stopped."
  else
    echo "Broker is not running."
  fi
  exit 0
fi

PID="$(cat "${PID_FILE}")"
if kill -0 "${PID}" 2>/dev/null; then
  kill "${PID}"
  rm -f "${PID_FILE}"
  echo "Mosquitto stopped (pid ${PID})"
else
  rm -f "${PID_FILE}"
  echo "Broker was not running."
fi
