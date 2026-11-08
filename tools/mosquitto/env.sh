#!/usr/bin/env bash
# Source this file to use local mosquitto_pub / mosquitto_sub without sudo install.
# Usage: source tools/mosquitto/env.sh

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
export PATH="${ROOT_DIR}/root/usr/bin:${PATH}"
export LD_LIBRARY_PATH="${ROOT_DIR}/root/usr/lib/x86_64-linux-gnu:${LD_LIBRARY_PATH:-}"
