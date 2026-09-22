#!/bin/bash
SCRIPT_PATH="$(readlink "$0" 2>/dev/null || echo "$0")"
cd "$(dirname "$SCRIPT_PATH")"
source venv/bin/activate
python3 main.py "$@"

