#!/usr/bin/env bash
# Start the full Smart City Kafka demo and open the dashboard in a browser.
# Usage: ./start_demo.sh
# Stop:  Ctrl+C

set -euo pipefail

if [[ "${BASH_SOURCE[0]}" != "$0" ]]; then
  echo "Do not source this file." >&2
  echo "Run: ./start_demo.sh" >&2
  return 1
fi

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV_PYTHON="${ROOT_DIR}/.venv/bin/python"
VENV_STREAMLIT="${ROOT_DIR}/.venv/bin/streamlit"
DASHBOARD_URL="http://localhost:8501"

CONS_PID=""
PUB_PID=""
DASH_PID=""

cleanup() {
  echo
  echo "Stopping demo components..."
  [[ -n "${DASH_PID}" ]] && kill "${DASH_PID}" 2>/dev/null || true
  [[ -n "${PUB_PID}" ]] && kill "${PUB_PID}" 2>/dev/null || true
  [[ -n "${CONS_PID}" ]] && kill "${CONS_PID}" 2>/dev/null || true
  pkill -f "streamlit run ${ROOT_DIR}/dashboard/app.py" 2>/dev/null || true
  "${ROOT_DIR}/tools/stop_kafka.sh" >/dev/null 2>&1 || true
  echo "Demo stopped."
}

trap cleanup EXIT INT TERM

if [[ ! -x "${VENV_PYTHON}" || ! -x "${VENV_STREAMLIT}" ]]; then
  echo "Virtual environment not found. Run:"
  echo "  python3 -m venv .venv && source .venv/bin/activate && pip install -r requirements.txt"
  exit 1
fi

cd "${ROOT_DIR}"

echo "1/4 Starting Kafka broker..."
./tools/start_kafka.sh

echo "2/4 Starting Kafka consumer (process + SQLite)..."
"${VENV_PYTHON}" subscriber/run_kafka_consumer.py > /tmp/smartcity_kafka_consumer.log 2>&1 &
CONS_PID=$!

echo "3/4 Starting Kafka publisher..."
"${VENV_PYTHON}" simulator/run_kafka_publisher.py --cycles 0 --interval 2 \
  > /tmp/smartcity_kafka_publisher.log 2>&1 &
PUB_PID=$!

echo "4/4 Starting Streamlit dashboard..."
"${VENV_STREAMLIT}" run dashboard/app.py --server.headless true --server.port 8501 \
  > /tmp/smartcity_dashboard.log 2>&1 &
DASH_PID=$!

echo "Waiting for dashboard..."
for _ in $(seq 1 40); do
  if curl -s -o /dev/null "http://127.0.0.1:8501/"; then
    break
  fi
  sleep 0.5
done

if command -v xdg-open >/dev/null 2>&1; then
  xdg-open "${DASHBOARD_URL}" >/dev/null 2>&1 || true
elif command -v sensible-browser >/dev/null 2>&1; then
  sensible-browser "${DASHBOARD_URL}" >/dev/null 2>&1 || true
else
  echo "Open this URL manually: ${DASHBOARD_URL}"
fi

echo
echo "Kafka demo is running."
echo "Dashboard: ${DASHBOARD_URL}"
echo "Logs:"
echo "  /tmp/smartcity_kafka_consumer.log"
echo "  /tmp/smartcity_kafka_publisher.log"
echo "  /tmp/smartcity_dashboard.log"
echo
echo "Press Ctrl+C to stop everything."

while kill -0 "${DASH_PID}" 2>/dev/null; do
  sleep 1
done
