#!/usr/bin/env bash
# Double-click launcher for macOS (the first time: right-click > Open).
# On Linux, run it with:  bash AutoCaption.command
set -e
cd "$(dirname "$0")"
trap 'echo; echo "Something went wrong - see the messages above."; read -rp "Press Enter to close..."' ERR

if [ ! -x ".venv/bin/python" ]; then
    echo "================================================"
    echo "  auto-caption - first-time setup"
    echo "  Installing... this takes a few minutes."
    echo "  Every launch after this one is instant."
    echo "================================================"
    echo
    if ! command -v python3 >/dev/null 2>&1; then
        echo "Python 3 was not found. Install it from https://www.python.org/downloads/"
        echo "(macOS with Homebrew:  brew install python)"
        read -rp "Press Enter to close..."
        exit 1
    fi
    python3 -m venv .venv
    .venv/bin/python -m pip install --quiet --upgrade pip
    echo "Downloading and installing components..."
    .venv/bin/python -m pip install -e .
    echo
    echo "Setup complete! Launching auto-caption..."
fi

exec .venv/bin/python -m autocaption.gui
