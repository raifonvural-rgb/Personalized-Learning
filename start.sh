#!/usr/bin/env bash

set -euo pipefail

cd "$(dirname "$(readlink -f "$0")")"

CONFIG="$HOME/.config/autism_material_demo/openai.env"

if [[ ! -f "$CONFIG" ]]; then
    echo "ERROR: OpenAI configuration file not found."
    exit 1
fi

if [[ "$(stat -c '%a' "$CONFIG")" != "600" ]]; then
    echo "ERROR: Configuration file permissions must be 600."
    exit 1
fi

source "$CONFIG"

if [[ -z "${OPENAI_API_KEY:-}" ]]; then
    echo "ERROR: OpenAI API key is not configured."
    exit 1
fi

echo "Starting Autism Material Demo..."
echo "OpenAI configuration loaded."

exec .venv/bin/python app.py
