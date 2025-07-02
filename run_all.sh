#!/usr/bin/env bash

# Exit immediately if a command exits with a non-zero status
set -e

# run source venv/bin/activate

source venv/bin/activate

pip install -r requirements.txt

python3 src/main.py &
MAIN_PID=$!

python3 web_server/login-server.py &
WEB_PID=$!

# Ensure both processes are terminated when the script exits (Ctrl+C, script end, etc.)
trap 'kill $MAIN_PID $WEB_PID 2>/dev/null' EXIT INT TERM

# Wait for both background processes to finish before exiting the script
wait $MAIN_PID $WEB_PID
