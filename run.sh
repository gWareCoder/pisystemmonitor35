#!/bin/bash
# Launcher script for 3.5" SPI-1 System Monitor
set -e

DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" >/dev/null 2>&1 && pwd)"
cd "$DIR"

# Ensure environment variables for Wayland / X11
export DISPLAY="${DISPLAY:-:0}"
if [ -n "$WAYLAND_DISPLAY" ]; then
    # Prefer xcb or wayland
    export QT_QPA_PLATFORM="${QT_QPA_PLATFORM:-xcb}"
fi

python3 "$DIR/main.py" "$@"
