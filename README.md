# 3.5" SPI-1 Display System Monitor

<p align="center">
  <img src="docs/preview.png" alt="3.5\" SPI-1 System Monitor Preview" width="560">
</p>

A high-performance, hardware-accelerated, dark-themed system monitor tailored specifically for a **3.5-inch display** (480x320 resolution) on the **Raspberry Pi 5** running under the **`labwc` Wayland compositor** on output **`SPI-1`**.

---

## Table of Contents

- [Key Features](#key-features)
- [Visual Layout Overview](#visual-layout-overview)
- [Implementation Plan & Architecture](#implementation-plan--architecture)
  - [Design Goals](#design-goals)
  - [Hardware & Software Specifications](#hardware--software-specifications)
  - [Display Targeting & Window Management](#display-targeting--window-management)
  - [Threading & Metric Collection Pipeline](#threading--metric-collection-pipeline)
  - [UI Layout & Pixel Budgeting](#ui-layout--pixel-budgeting)
- [How to Run the Application](#how-to-run-the-application)
  - [Prerequisites](#prerequisites)
  - [1. Sanity Check / Terminal Test](#1-sanity-check--terminal-test)
  - [2. Launch via Script or Python](#2-launch-via-script-or-python)
  - [3. Launch via Desktop Shortcut](#3-launch-via-desktop-shortcut)
  - [4. Command-Line Options](#4-command-line-options)
  - [5. Lock Window to SPI-1 Desktop via labwc](#5-lock-window-to-spi-1-desktop-via-labwc)
  - [6. Enable Autostart on Boot / Login](#6-enable-autostart-on-boot--login)
- [Configuration (`config.json`)](#configuration-configjson)
- [Directory Structure](#directory-structure)
- [Troubleshooting](#troubleshooting)
- [License](#license)

---

## Key Features

- **Optimized for 3.5" (480x320)**: Pixel-perfect compact layout designed to eliminate scrollbars and make all system metrics readable at a glance from TFT viewing angles.
- **SPI-1 Display Auto-Placement**: Programmatically locates the `SPI-1` output at coordinates `(0, 0)` and includes automated `labwc` window rules so it always launches cleanly on your 3.5" screen without window titlebars wasting space.
- **User, Hostname & LAN IP Address**: Displays `user@hostname • ip` (e.g. `tomg@sandbox • 127.0.0.1` or `tomg@rpi5 • 192.168.1.142`) inside a clean styled badge in the top-right header bar.
- **Live Time & Date**: Digital clock with seconds (`HH:MM:SS`) and formatted date (`Day, Month Date`).
- **RAM & Root Disk Storage in GB**: Real-time display of system memory used, available, and total in GB (e.g. `1.6G / 15.8G (13.9G rem)`) plus root partition (`/`) disk space used and free in GB with dedicated progress meters.
- **Live CPU & SoC Temperature**: Overall CPU utilization %, per-core 4-core mini meter bars, dynamic green/amber/red color transitions, and SoC thermal temperature (°C).
- **Broadcom VideoCore VII (v3d) GPU Tracking**: Real-time DRM engine utilization %, dynamic GPU clock frequency (up to 960 MHz), and allocated buffer memory (`bo_stats`).
- **Connected Bluetooth Device Batteries**: Live battery percentage badges and status bars for connected peripherals (headphones, mice, keyboards, controllers) via BlueZ D-Bus and UPower.
- **Top 2 CPU & Top 2 Memory Processes**: High-legibility process cards showcasing the top two consumers of processing and memory with process name, PID, and percentage badges.
- **Market Tickers (NASDAQ & DOW)**: Live quotes for NASDAQ (`NDX`) and Dow Jones (`DOW`) with point change and percentage change color coding (+ green / - red), backed by an offline cache.
- **Antigravity Token & Quota Tracker**: Automatically analyzes Antigravity conversation transcripts to compute active session tokens, rolling 5-hour quota consumption, and remaining tokens for your Google AI plan.
- **Desktop & Taskbar Launcher**: Double-clickable shortcut placed right on your Desktop (`~/Desktop/spi1-system-monitor.desktop`), custom icon in your application menu, and taskbar integration.

---

## Visual Layout Overview

```
+-----------------------------------------------------------------------------------+
| 13:56:19 • Tue, Sep 29                     [ tomg@sandbox • 127.0.0.1 ]       [✕] |  <- Header (24px)
+-----------------------------------------------------------------------------------+
| NDX: 26,797.5 (-0.09%) • DOW: 51,349.9 (-0.26%) • AGY: 66.9k used • 433.1k rem(87%)| <- Ticker (19px)
+----------------------------------------+------------------------------------------+
| CPU UTILIZATION          60.0°C  40.0% | TOP 2 CPU PROCESSES                      |
| [====================--------]         | #1 python3 (17)                     0.0% |
| [-] [-] [-] [-] (4-core mini bars)     | [----------------------------------------|
+----------------------------------------+ #2 exe (1)                          0.0% |
| GPU (VC7 / v3d)       960 MHz   100.0% | [----------------------------------------|
| [==============================]        +------------------------------------------+
| Buffer Alloc: 378.8 MB                 | TOP 2 MEMORY PROCESSES                   |
+----------------------------------------+ #1 exe (1)               0.7% (112.7 MB) |
| RAM             2.0G / 15.8G (13.4G rem) [=---------------------------------------|
| [==----------------------------------] | #2 python3 (17)           0.4% (58.1 MB) |
| DISK (/)         0.0G / 7.9G (7.9G rem)| [----------------------------------------|
| [------------------------------------] +------------------------------------------+
+----------------------------------------+
| BLUETOOTH BATTERIES        0 connected |
|       No Bluetooth devices connected   |
+----------------------------------------+
```

---

## Implementation Plan & Architecture

### Design Goals
1. **Space Efficiency**: Standard desktop monitors are 1080p or 4K. A 3.5" display (480x320) only has 153,600 pixels. Window borders and titlebars consume 30–36 vertical pixels (~11% of the entire screen). The application must run **borderless** by default and fit every metric cleanly without vertical or horizontal scrollbars.
2. **Dedicated Output Targeting**: The user runs a dual-screen profile with `HDMI-A-1` (1920x1080 at `480,0`) and `SPI-1` (480x320 at `0,0`). The monitor must anchor itself specifically to `SPI-1` without user dragging.
3. **Decoupled I/O & Non-Blocking GUI**: All metric collectors (D-Bus, Yahoo Finance API, `/proc` file scanning, transcripts) must run asynchronously in background worker threads so the Qt UI renders at a smooth frame rate with zero input freezing.
4. **Legibility at TFT Viewing Angles**: Using high-contrast dark theme colors (`#0e1117` background, vibrant `#58a6ff` cyan, `#3fb950` green, and `#f85149` red) with crisp sans-serif typography (8.5pt–11pt).

### Hardware & Software Specifications
- **Host**: Raspberry Pi 5 (`BCM2712` aarch64, Linux kernel 6.12+).
- **GPU**: Broadcom VideoCore VII (`v3d` DRM driver).
- **Display Output**: DRM device `card1-SPI-1` at position `(0, 0)`, resolution `480x320`.
- **Compositor**: `labwc` (wlroots-based stacking Wayland compositor) with `kanshi` display profile daemon.
- **Framework**: Python 3, `PyQt5` (with hardware-accelerated OpenGL/DRM backend).

### Display Targeting & Window Management
To guarantee that the application always opens on the `SPI-1` display:
1. **Qt Screen Enumeration**: On startup, `MainWindow.place_on_target_screen()` inspects `QApplication.screens()`. It matches either the display name (`SPI-1`) or geometry `(0, 0, 480, 320)`, moving the window to the screen's exact coordinates.
2. **`labwc` Window Rule Injection**:
   The installer script ([`install_rules.py`](install_rules.py)) writes a native rule into `~/.config/labwc/rc.xml`:
   ```xml
   <windowRules>
     <windowRule identifier="spi1-system-monitor" serverDecoration="no">
       <action name="MoveToOutput" output="SPI-1" />
       <action name="SnapToRegion" region="output" />
     </windowRule>
   </windowRules>
   ```
   This strips server decorations and directs the window directly to `SPI-1`.

### Threading & Metric Collection Pipeline

```
                                  +-----------------------------------------------+
                                  |            PyQt5 480x320 GUI                  |
                                  |    (Header Bar, Ticker, Dashboard View)       |
                                  +-----------------------+-----------------------+
                                                          |
                                           Background MetricsWorker (QThread)
                                                          |
                 +----------------------+-----------------+------------------+-----------------------+
                 |                      |                                    |                       |
                 v                      v                                    v                       v
          [ CPU & Thermals ]     [ GPU (VC7 / v3d) ]                 [ RAM & Disk ]            [ Process Monitor ]
       - psutil.cpu_percent   - /proc/<pid>/fdinfo (drm-engine)    - psutil.virtual_memory   - psutil.process_iter
       - 4-core mini bars     - vcgencmd measure_clock v3d         - psutil.disk_usage('/')  - Top 2 by CPU%
       - SoC Temperature      - Buffer objects (bo_stats)          - Formatted in GB         - Top 2 by Mem%
                 |                      |                                    |                       |
                 +----------------------+-----------------+------------------+-----------------------+
                                                          |
                                       +------------------+------------------+
                                       |                                     |
                                       v                                     v
                            [ Bluetooth Batteries ]                 [ Market & Token Quota ]
                         - BlueZ via System D-Bus               - Yahoo Finance API (NDX & DOW)
                         - org.bluez.Battery1 Percentage        - Persistent JSON cache fallback
                         - UPower fallback                      - ~/.gemini/antigravity transcripts
                                                                - Google AI Pro 5h rolling quota
```

- **CPU & Thermals** ([`monitor/cpu.py`](monitor/cpu.py)): Samples overall CPU percentage and per-core loads via `psutil`. Reads temperature from `/sys/class/thermal/thermal_zone0/temp` and `vcgencmd measure_temp`.
- **GPU Metrics** ([`monitor/gpu.py`](monitor/gpu.py)): Scans `/proc/<pid>/fdinfo/<fd>` for processes utilizing `v3d` (`drm-engine-fragment`, `bin`, `compute`) and calculates delta active nanoseconds over elapsed time. Clock speed is gathered from `vcgencmd measure_clock v3d` (up to 960 MHz). Buffer memory allocation is read from `/sys/kernel/debug/dri/0/bo_stats`.
- **RAM & Disk Storage** ([`monitor/system_info.py`](monitor/system_info.py)): Converts system virtual memory and root partition disk usage to GB (used, free/remaining, total, and percentage).
- **User, Hostname & LAN IP** ([`monitor/system_info.py`](monitor/system_info.py)): Detects current active user (`os.environ['USER']` / `getpass.getuser()`), system hostname (`socket.gethostname()`), and traverses active network adapters (`wlan0`, `eth0`) for the primary IPv4 address.
- **Bluetooth Battery Reporting** ([`monitor/bluetooth.py`](monitor/bluetooth.py)): Connects to the system D-Bus and enumerates objects under `org.bluez.Device1` that have an active `org.bluez.Battery1` interface to read the `Percentage` property. Falls back to `org.freedesktop.UPower` for standard wireless mice/keyboards.
- **Top 2 CPU & Top 2 Memory Processes** ([`monitor/processes.py`](monitor/processes.py)): Samples running processes via `psutil.process_iter()`, filters and sorts the top two CPU consumers and top two memory consumers, displaying PID, process name, and RSS MB.
- **Market Tickers** ([`monitor/market.py`](monitor/market.py)): Queries NASDAQ (`^IXIC`) and Dow Jones (`^DJI`) market data in the background every 60 seconds with an offline disk cache (`~/.cache/spi1-sysmon/market_cache.json`).
- **Antigravity Token & Plan Quota** ([`monitor/antigravity_tokens.py`](monitor/antigravity_tokens.py)): Analyzes conversation transcripts in `~/.gemini/antigravity/brain/` and reads user subscription tier (`Google AI Pro`) from `state.vscdb`. Calculates tokens consumed in the active session and evaluates the 5-hour rolling quota budget (default: 500,000 tokens) to report remaining tokens.

### UI Layout & Pixel Budgeting
Total window size is **480x320 pixels**:
- **Header Bar (24px)**: Time (`HH:MM:SS`), date (`Day, Month Date`), and `user@hostname • ip` badge.
- **Ticker Ribbon (19px)**: Compact status line with live points and % change for NASDAQ and DOW, plus Antigravity quota tokens.
- **Left Column (~215px)**:
  - CPU Utilization Card (~64px)
  - GPU VideoCore VII Card (~54px)
  - RAM & Disk Storage Card (~66px)
  - Bluetooth Batteries Card (~64px)
- **Right Column (~255px)**:
  - Top 2 CPU Processes Card (~125px)
  - Top 2 Memory Processes Card (~125px)

---

## How to Run the Application

### Prerequisites
Make sure system packages for Python 3, PyQt5, and D-Bus are installed:
```bash
sudo apt update
sudo apt install -y python3 python3-pyqt5 python3-psutil python3-dbus libraspberrypi-bin
```

### 1. Sanity Check / Terminal Test
Before opening the graphical interface, you can verify that all metrics (CPU, GPU, Bluetooth, RAM, Disk, Network, Processes, Market, Tokens) are functional:
```bash
cd /home/tomg/.gemini/antigravity/scratch/spi1-system-monitor
python3 main.py --test
```
*Expected output: All metric dictionaries printed to terminal with exit code 0.*

### 2. Launch via Script or Python
Run the launcher script (automatically configures display environment variables):
```bash
./run.sh
```

Or launch directly with Python:
```bash
python3 main.py
```

### 3. Launch via Desktop Shortcut
A ready-to-use shortcut has been installed to your Desktop:
- Double-click **3.5" SPI-1 System Monitor** on your desktop.
- Right-click the shortcut and choose **"Open in Windowed Mode"** if you want standard window borders for testing on your main HDMI monitor.

### 4. Command-Line Options
You can pass custom arguments to `main.py` or `./run.sh`:

| Flag | Short | Description |
|------|-------|-------------|
| `--windowed` | `-w` | Run with standard window borders and decorations (useful when testing on an HDMI monitor). |
| `--fullscreen` | `-f` | Launch in true fullscreen mode. |
| `--output <NAME>` | `-o` | Target a different output screen (e.g. `--output HDMI-A-1`). |
| `--config <PATH>` | `-c` | Specify a custom path to `config.json`. |
| `--test` | `-t` | Run non-GUI metric tests in the terminal and exit. |

**Examples:**
```bash
# Test on your HDMI screen with regular window borders
python3 main.py --windowed --output HDMI-A-1

# Launch borderless on SPI-1
python3 main.py
```

### 5. Lock Window to SPI-1 Desktop via labwc
Run the automated installer to configure `labwc` compositor rules:
```bash
python3 install_rules.py
```
This performs the following actions safely:
1. Backs up `~/.config/labwc/rc.xml` to `rc.xml.bak`.
2. Adds a `<windowRule>` for `spi1-system-monitor` to remove window borders and snap to `SPI-1`.
3. Installs multi-resolution application icons (16, 24, 32, 48, 64, 128, 256) into `~/.local/share/icons/hicolor/` and `~/.local/share/pixmaps/` so the taskbar displays the app icon when running.
4. Creates the desktop shortcut at `~/Desktop/spi1-system-monitor.desktop`.
5. Sends `SIGHUP` to `labwc` to reload the new configuration.

### 6. Enable Autostart on Boot / Login
To automatically launch the system monitor whenever your Raspberry Pi desktop session starts:
```bash
python3 install_rules.py --autostart
```
To disable autostart:
```bash
python3 install_rules.py --no-autostart
```

---

## Configuration (`config.json`)

All refresh rates, display defaults, and token quota targets can be adjusted in [`config.json`](config.json):

```json
{
  "display": {
    "target_output": "SPI-1",
    "borderless": true,
    "fullscreen": false,
    "width": 480,
    "height": 320,
    "x": 0,
    "y": 0
  },
  "refresh_intervals": {
    "system_seconds": 1.5,
    "market_seconds": 60,
    "tokens_seconds": 10,
    "bluetooth_seconds": 5
  },
  "antigravity": {
    "plan_name": "Google AI Pro",
    "plan_token_budget": 500000,
    "rolling_window_hours": 5
  },
  "market": {
    "symbols": ["^IXIC", "^DJI"],
    "display_names": {
      "^IXIC": "NDX",
      "^DJI": "DOW"
    }
  }
}
```

---

## Directory Structure

```
spi1-system-monitor/
├── main.py                  # Main Python application entry point
├── run.sh                   # Environment launcher script
├── install_rules.py         # Configures labwc rc.xml window rules, desktop shortcut & autostart
├── config.json              # Customization options (intervals, display, plan budget)
├── README.md                # Documentation with architecture and usage guide
├── docs/
│   ├── preview.png          # Screenshot of the 480x320 UI
│   └── icon.png             # Application icon
├── resources/
│   ├── icon.png             # Master 128x128 high-resolution window and taskbar icon
│   └── icon_*.png           # Multi-resolution icons (16, 24, 32, 48, 64, 128, 256)
├── monitor/
│   ├── __init__.py
│   ├── cpu.py               # CPU utilization, cores, and SoC temperature
│   ├── gpu.py               # VideoCore VII (v3d) DRM engine & clock speed
│   ├── system_info.py       # RAM, Disk, Hostname, User, and LAN IP address
│   ├── bluetooth.py         # BlueZ D-Bus / UPower Bluetooth battery monitor
│   ├── market.py            # NASDAQ and Dow Jones market quotes with cache
│   ├── antigravity_tokens.py# Antigravity token usage and plan quota
│   ├── processes.py         # Top 2 CPU and Memory processes
│   └── worker.py            # Multi-interval background QThread worker
└── ui/
    ├── __init__.py
    ├── window.py            # 480x320 Main window with screen positioning
    ├── dashboard_view.py    # All-in-One dashboard layout
    ├── components.py        # Meters, process rows, battery rows, ticker ribbon
    └── styles.py            # High-contrast dark theme CSS
```

---

## Troubleshooting

- **Window opens on the HDMI monitor instead of SPI-1**:
  - Run `python3 install_rules.py` to ensure the `labwc` rule is registered.
  - Verify output names with `wlr-randr`. If your output is named differently, pass `--output <YOUR_OUTPUT>` or update `config.json`.
- **Bluetooth battery shows "N/A" or "No Bluetooth devices connected"**:
  - Ensure Bluetooth is enabled (`bluetoothctl power on`).
  - Some older Bluetooth peripherals do not implement the `org.bluez.Battery1` GATT battery service profile.
- **Market quotes show previous prices or zero change**:
  - Check your internet connectivity. The application caches the last successful quotes in `~/.cache/spi1-sysmon/market_cache.json` and updates automatically when online.

---

## License

MIT License.
