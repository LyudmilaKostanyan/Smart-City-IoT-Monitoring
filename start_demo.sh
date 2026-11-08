#!/usr/bin/env bash
# Start the full Smart City demo and open the dashboard in a browser.
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

SUB_PID=""
PUB_PID=""
DASH_PID=""

cleanup() {
  echo
  echo "Stopping demo components..."
  [[ -n "${DASH_PID}" ]] && kill "${DASH_PID}" 2>/dev/null || true
  [[ -n "${PUB_PID}" ]] && kill "${PUB_PID}" 2>/dev/null || true
  [[ -n "${SUB_PID}" ]] && kill "${SUB_PID}" 2>/dev/null || true
  pkill -f "streamlit run ${ROOT_DIR}/dashboard/app.py" 2>/dev/null || true
  "${ROOT_DIR}/tools/mosquitto/stop_broker.sh" >/dev/null 2>&1 || true
  echo "Demo stopped."
}

trap cleanup EXIT INT TERM

if [[ ! -x "${VENV_PYTHON}" || ! -x "${VENV_STREAMLIT}" ]]; then
  echo "Virtual environment not found. Run:"
  echo "  python3 -m venv .venv && source .venv/bin/activate && pip install -r requirements.txt"
  exit 1
fi

cd "${ROOT_DIR}"

echo "1/4 Starting MQTT broker..."
./tools/mosquitto/start_broker.sh

echo "2/4 Starting MQTT subscriber..."
"${VENV_PYTHON}" subscriber/run_subscriber.py > /tmp/smartcity_subscriber.log 2>&1 &
SUB_PID=$!

echo "3/4 Starting MQTT publisher..."
"${VENV_PYTHON}" simulator/run_publisher.py --cycles 0 --interval 2 > /tmp/smartcity_publisher.log 2>&1 &
PUB_PID=$!

echo "4/4 Starting Streamlit dashboard..."
"${VENV_STREAMLIT}" run dashboard/app.py --server.headless true --server.port 8501 \
  > /tmp/smartcity_dashboard.log 2>&1 &
DASH_PID=$!

echo "Waiting for dashboard..."
for _ in $(seq 1 30); do
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
echo "Demo is running."
echo "Dashboard: ${DASHBOARD_URL}"
echo "Logs:"
echo "  /tmp/smartcity_subscriber.log"
echo "  /tmp/smartcity_publisher.log"
echo "  /tmp/smartcity_dashboard.log"
echo
echo "Press Ctrl+C to stop everything."

# Keep the script alive while child processes run.
while kill -0 "${DASH_PID}" 2>/dev/null; do
  sleep 1
done
