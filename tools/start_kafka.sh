#!/usr/bin/env bash
# Start local single-node Apache Kafka (KRaft mode).
# Usage: ./tools/start_kafka.sh

set -euo pipefail

if [[ "${BASH_SOURCE[0]}" != "$0" ]]; then
  echo "Do not source this file. Run: ./tools/start_kafka.sh" >&2
  return 1
fi

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
KAFKA_HOME="${ROOT_DIR}/tools/kafka"
KAFKA_DATA="${ROOT_DIR}/tools/kafka-data"
CONF="${ROOT_DIR}/tools/kafka-config/server.properties"
PID_FILE="${ROOT_DIR}/tools/kafka-config/kafka.pid"
LOG_FILE="${ROOT_DIR}/tools/kafka-config/kafka.log"

if [[ ! -x "${KAFKA_HOME}/bin/kafka-server-start.sh" ]]; then
  echo "Kafka is not installed in ${KAFKA_HOME}" >&2
  echo "Run first: ./tools/setup_kafka.sh" >&2
  exit 1
fi

if [[ ! -f "${CONF}" ]]; then
  echo "Missing ${CONF}. Run: ./tools/setup_kafka.sh" >&2
  exit 1
fi

mkdir -p "${KAFKA_DATA}"
sed -i "s|^log.dirs=.*|log.dirs=${KAFKA_DATA}|" "${CONF}"

if [[ -f "${PID_FILE}" ]] && kill -0 "$(cat "${PID_FILE}")" 2>/dev/null; then
  echo "Kafka already running (pid $(cat "${PID_FILE}")) on localhost:9092"
  exit 0
fi

nohup "${KAFKA_HOME}/bin/kafka-server-start.sh" "${CONF}" > "${LOG_FILE}" 2>&1 &
echo $! > "${PID_FILE}"

echo "Starting Kafka (pid $(cat "${PID_FILE}"))..."
for _ in $(seq 1 40); do
  if "${KAFKA_HOME}/bin/kafka-topics.sh" \
      --bootstrap-server localhost:9092 \
      --list >/dev/null 2>&1; then
    echo "Kafka is ready on localhost:9092"
    exit 0
  fi
  sleep 0.5
done

echo "Kafka did not become ready in time. Check ${LOG_FILE}" >&2
exit 1
