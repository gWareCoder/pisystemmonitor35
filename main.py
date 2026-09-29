#!/usr/bin/env python3
"""Main entry point for 3.5" SPI-1 System Monitor."""
import os
import sys
import json
import argparse
from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import Qt

# Ensure current directory is in python path
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

from ui.window import MainWindow


def load_config(config_path: str = None) -> dict:
    """Load configuration JSON or return defaults."""
    if not config_path:
        config_path = os.path.join(current_dir, "config.json")

    if os.path.exists(config_path):
        try:
            with open(config_path, "r") as f:
                return json.load(f)
        except Exception as e:
            print(f"Warning: Failed to load {config_path}: {e}")

    return {
        "display": {
            "target_output": "SPI-1",
            "borderless": True,
            "fullscreen": False,
            "width": 480,
            "height": 320,
            "x": 0,
            "y": 0,
        },
        "refresh_intervals": {
            "system_seconds": 1.5,
            "market_seconds": 60,
            "tokens_seconds": 10,
            "bluetooth_seconds": 5,
        },
        "antigravity": {
            "plan_name": "Google AI Pro",
            "plan_token_budget": 500000,
            "rolling_window_hours": 5,
        },
        "market": {
            "symbols": ["^IXIC", "^DJI"],
            "display_names": {"^IXIC": "NDX", "^DJI": "DOW"}
        }
    }


def main():
    parser = argparse.ArgumentParser(description="3.5\" SPI-1 Display System Monitor")
    parser.add_argument("--config", "-c", type=str, help="Path to config.json")
    parser.add_argument("--output", "-o", type=str, help="Target display output name (e.g. SPI-1, HDMI-A-1)")
    parser.add_argument("--windowed", "-w", action="store_true", help="Run with standard window borders and decorations")
    parser.add_argument("--fullscreen", "-f", action="store_true", help="Run in true fullscreen mode")
    parser.add_argument("--test", action="store_true", help="Run metric sanity checks and exit")

    args = parser.parse_args()

    config = load_config(args.config)

    # CLI Overrides
    if args.output:
        config["display"]["target_output"] = args.output
    if args.windowed:
        config["display"]["borderless"] = False
    if args.fullscreen:
        config["display"]["fullscreen"] = True

    if args.test:
        print("=== Running Monitor Sanity Test ===")
        from monitor.cpu import get_cpu_metrics
        from monitor.gpu import get_gpu_metrics
        from monitor.bluetooth import get_bluetooth_batteries
        from monitor.processes import get_top_processes
        from monitor.antigravity_tokens import get_token_metrics
        from monitor.market import get_market_quotes

        print("[CPU]:", get_cpu_metrics())
        print("[GPU]:", get_gpu_metrics())
        print("[BT Devices]:", get_bluetooth_batteries())
        print("[Top 2 Procs]:", get_top_processes(2))
        print("[Tokens]:", get_token_metrics())
        print("[Market]:", get_market_quotes(config.get("market", {}).get("display_names")))
        print("=== All modules verified successfully ===")
        sys.exit(0)

    # Enable High-DPI scaling if needed
    QApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)
    QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps, True)

    from PyQt5.QtGui import QIcon

    app = QApplication(sys.argv)
    app.setApplicationName("spi1-system-monitor")
    app.setDesktopFileName("spi1-system-monitor")

    icon_path = os.path.join(current_dir, "resources", "icon.png")
    if os.path.exists(icon_path):
        app_icon = QIcon(icon_path)
        app.setWindowIcon(app_icon)

    window = MainWindow(config)
    if os.path.exists(icon_path):
        window.setWindowIcon(QIcon(icon_path))
    window.place_on_target_screen()

    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
