#!/usr/bin/env bash
# Runs the bot and restarts it after a crash. Stop with Ctrl+C.
cd "$(dirname "$0")" || exit 1
trap 'exit 0' INT TERM

while true; do
    uv run main.py
    echo "Bot exited with code $?, restarting in 10 seconds..."
    sleep 10
done
