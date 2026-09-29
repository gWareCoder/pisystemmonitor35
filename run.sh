#!/bin/bash
# Launcher script for 3.5" SPI-1 System Monitor
set -e

DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" >/dev/null 2>&1 && pwd)"
cd "$DIR"

# Ensure environment variables for Wayland / X11
export DISPLAY="${DISPLAY:-:0}"
if [ -n "$WAYLAND_DISPLAY" ]; then
    # Let Qt use native Wayland or xcb fallback
    export QT_QPA_PLATFORM="${QT_QPA_PLATFORM:-wayland;xcb}"
fi

# Run with process identity spi1-system-monitor so WM_CLASS and app_id match desktop file
exec -a spi1-system-monitor python3 "$DIR/main.py" "$@"
