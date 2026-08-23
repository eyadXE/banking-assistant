#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"
case "${1:-help}" in
  bank)     python3 bank.py ;;
  classify) python3 classifier.py ;;
  chat)     python3 assistant.py ;;
  web)      uvicorn server:app --host 0.0.0.0 --port "${PORT:-8000}" ;;
  test)     python3 tests.py ;;
  *) echo "Usage: ./run.sh {bank|classify|chat|web|test}" ;;
esac
