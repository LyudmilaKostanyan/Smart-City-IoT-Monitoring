#!/usr/bin/env bash
# Stop local Apache Kafka started by tools/start_kafka.sh.
# Usage: ./tools/stop_kafka.sh

set -euo pipefail

if [[ "${BASH_SOURCE[0]}" != "$0" ]]; then
  echo "Do not source this file. Run: ./tools/stop_kafka.sh" >&2
  return 1
fi

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
KAFKA_HOME="${ROOT_DIR}/tools/kafka"
CONF="${ROOT_DIR}/tools/kafka-config/server.properties"
PID_FILE="${ROOT_DIR}/tools/kafka-config/kafka.pid"

if [[ -x "${KAFKA_HOME}/bin/kafka-server-stop.sh" ]]; then
  "${KAFKA_HOME}/bin/kafka-server-stop.sh" >/dev/null 2>&1 || true
fi

if [[ -f "${PID_FILE}" ]]; then
  PID="$(cat "${PID_FILE}")"
  if kill -0 "${PID}" 2>/dev/null; then
    kill "${PID}" 2>/dev/null || true
    sleep 1
    kill -9 "${PID}" 2>/dev/null || true
  fi
  rm -f "${PID_FILE}"
fi

# Fallback if pid file is stale.
pkill -f "kafka.Kafka ${CONF}" 2>/dev/null || true
echo "Kafka stopped."
