#!/usr/bin/env bash
# Download Apache Kafka 4.1.2, format KRaft storage, create the project topic.
# Usage: ./tools/setup_kafka.sh

set -euo pipefail

if [[ "${BASH_SOURCE[0]}" != "$0" ]]; then
  echo "Do not source this file. Run: ./tools/setup_kafka.sh" >&2
  return 1
fi

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
KAFKA_HOME="${ROOT_DIR}/tools/kafka"
KAFKA_DATA="${ROOT_DIR}/tools/kafka-data"
KAFKA_CONF_DIR="${ROOT_DIR}/tools/kafka-config"
CONF="${KAFKA_CONF_DIR}/server.properties"
TOPIC="smart-city-sensor-data"
KAFKA_VERSION="4.1.2"
KAFKA_TGZ="kafka_2.13-${KAFKA_VERSION}.tgz"
KAFKA_URL="https://downloads.apache.org/kafka/${KAFKA_VERSION}/${KAFKA_TGZ}"

if ! command -v java >/dev/null 2>&1; then
  echo "Java is required. Install with:" >&2
  echo "  sudo apt install -y openjdk-17-jre-headless" >&2
  exit 1
fi

mkdir -p "${KAFKA_CONF_DIR}" "${KAFKA_DATA}"

if [[ ! -x "${KAFKA_HOME}/bin/kafka-server-start.sh" ]]; then
  echo "Downloading ${KAFKA_TGZ}..."
  curl -L --fail -o "/tmp/${KAFKA_TGZ}" "${KAFKA_URL}"
  rm -rf "${KAFKA_HOME}"
  mkdir -p "${KAFKA_HOME}"
  tar -xzf "/tmp/${KAFKA_TGZ}" -C "${KAFKA_HOME}" --strip-components=1
  echo "Kafka extracted to ${KAFKA_HOME}"
else
  echo "Kafka already present in ${KAFKA_HOME}"
fi

if [[ ! -f "${CONF}" ]]; then
  cp "${KAFKA_HOME}/config/server.properties" "${CONF}"
fi

# Always point log.dirs at this project's data directory.
sed -i "s|^log.dirs=.*|log.dirs=${KAFKA_DATA}|" "${CONF}"

if [[ ! -f "${KAFKA_DATA}/meta.properties" ]]; then
  echo "Formatting KRaft storage..."
  CLUSTER_ID="$("${KAFKA_HOME}/bin/kafka-storage.sh" random-uuid)"
  echo "${CLUSTER_ID}" > "${KAFKA_CONF_DIR}/cluster.id"
  "${KAFKA_HOME}/bin/kafka-storage.sh" format \
    -t "${CLUSTER_ID}" \
    -c "${CONF}" \
    --standalone
else
  echo "KRaft storage already formatted."
fi

echo "Starting Kafka temporarily to create topic..."
"${ROOT_DIR}/tools/start_kafka.sh"
"${KAFKA_HOME}/bin/kafka-topics.sh" --bootstrap-server localhost:9092 \
  --create --if-not-exists \
  --topic "${TOPIC}" \
  --partitions 1 \
  --replication-factor 1
echo "Topic ready: ${TOPIC}"
echo "Setup complete. You can run: ./start_demo.sh"
