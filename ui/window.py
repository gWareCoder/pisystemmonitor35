"""Main Application Window sized 480x320 and targeted to SPI-1 display."""
import os
import sys
import datetime
from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QFrame, QLabel, QHBoxLayout, QVBoxLayout,
    QApplication, QPushButton
)
from PyQt5.QtCore import Qt, QTimer, QPoint

from .styles import DARK_THEME
from .components import TickerRibbon
from .dashboard_view import DashboardView
from monitor.worker import MetricsWorker


from PyQt5.QtGui import QIcon

class MainWindow(QMainWindow):
    """3.5-inch (480x320) System Monitor Window."""
    def __init__(self, config: dict, parent=None):
        super().__init__(parent)
        self.config = config
        self.setObjectName("spi1-system-monitor")
        self.setWindowTitle("SPI-1 System Monitor")

        # Set Window Icon
        icon_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "resources", "icon.png")
        if os.path.exists(icon_path):
            self.setWindowIcon(QIcon(icon_path))

        # Styling
        self.setStyleSheet(DARK_THEME)

        display_cfg = config.get("display", {})
        self.target_screen_name = display_cfg.get("target_output", "SPI-1")
        self.is_borderless = display_cfg.get("borderless", True)
        self.is_fullscreen = display_cfg.get("fullscreen", False)
        self.win_w = display_cfg.get("width", 480)
        self.win_h = display_cfg.get("height", 320)
        self.win_x = display_cfg.get("x", 0)
        self.win_y = display_cfg.get("y", 0)

        # Set fixed size for 3.5" display
        self.setFixedSize(self.win_w, self.win_h)

        if self.is_borderless:
            self.setWindowFlags(Qt.FramelessWindowHint | Qt.Window)

        # Initialize layout
        self.init_ui()

        # Clock timer (updates every 1 second)
        self.clock_timer = QTimer(self)
        self.clock_timer.timeout.connect(self.update_clock)
        self.clock_timer.start(1000)
        self.update_clock()

        # Background metrics worker
        self.worker = MetricsWorker(config=self.config, parent=self)
        self.worker.system_updated.connect(self.on_system_updated)
        self.worker.bluetooth_updated.connect(self.dashboard_view.update_bluetooth)
        self.worker.market_updated.connect(self.ticker_ribbon.update_market)
        self.worker.tokens_updated.connect(self.ticker_ribbon.update_tokens)
        self.worker.start()

    def on_system_updated(self, data: dict):
        self.dashboard_view.update_system_data(data)
        storage = data.get("storage", {})
        net = storage.get("network", {})
        if net and "hostname" in net and "ip" in net:
            self.host_ip_label.setText(f"{net['hostname']} • {net['ip']}")

    def init_ui(self):
        container = QWidget(self)
        self.setCentralWidget(container)
        root_layout = QVBoxLayout(container)
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.setSpacing(0)

        # 1. Header Bar (Height: 24px)
        self.header_bar = QFrame()
        self.header_bar.setFixedHeight(24)
        self.header_bar.setProperty("class", "headerBar")
        header_layout = QHBoxLayout(self.header_bar)
        header_layout.setContentsMargins(8, 0, 6, 0)
        header_layout.setSpacing(6)

        # Time & Date display
        self.time_label = QLabel("00:00:00")
        self.time_label.setProperty("class", "timeLabel")
        self.time_label.setStyleSheet("color: #ffffff; font-weight: 700; font-size: 11px;")

        self.date_sep = QLabel("•")
        self.date_sep.setStyleSheet("color: #8b949e; font-size: 9px;")

        self.date_label = QLabel("Mon, Jan 1")
        self.date_label.setProperty("class", "dateLabel")
        self.date_label.setStyleSheet("color: #8b949e; font-weight: 500; font-size: 10px;")

        header_layout.addWidget(self.time_label)
        header_layout.addWidget(self.date_sep)
        header_layout.addWidget(self.date_label)
        header_layout.addStretch()

        # Hostname & IP Address in header
        from monitor.system_info import get_network_info
        init_net = get_network_info()
        self.host_ip_label = QLabel(f"{init_net['hostname']} • {init_net['ip']}")
        self.host_ip_label.setStyleSheet("color: #58a6ff; font-weight: 700; font-size: 9.5px; background: #21262d; border: 1px solid #30363d; border-radius: 3px; padding: 1px 5px;")
        header_layout.addWidget(self.host_ip_label)

        # Optional exit button for touchscreen
        exit_btn = QPushButton("✕")
        exit_btn.setFixedSize(16, 16)
        exit_btn.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                color: #6e7681;
                border: none;
                font-size: 10px;
                font-weight: 700;
            }
            QPushButton:hover {
                color: #f85149;
            }
        """)
        exit_btn.clicked.connect(self.close)
        header_layout.addWidget(exit_btn)

        root_layout.addWidget(self.header_bar)

        # 2. Ticker Ribbon (Height: 19px)
        self.ticker_ribbon = TickerRibbon()
        root_layout.addWidget(self.ticker_ribbon)

        # 3. Main Dashboard View
        self.dashboard_view = DashboardView()
        root_layout.addWidget(self.dashboard_view)

    def update_clock(self):
        """Update live time and date string."""
        now = datetime.datetime.now()
        self.time_label.setText(now.strftime("%H:%M:%S"))
        self.date_label.setText(now.strftime("%a, %b %d"))

    def place_on_target_screen(self):
        """Position window on SPI-1 display output at (0, 0)."""
        app = QApplication.instance()
        target_screen = None

        if app:
            screens = app.screens()
            # 1. Match by name (e.g. SPI-1)
            for s in screens:
                if self.target_screen_name.lower() in s.name().lower():
                    target_screen = s
                    break

            # 2. Match by position (0, 0)
            if not target_screen:
                for s in screens:
                    geo = s.geometry()
                    if geo.x() == self.win_x and geo.y() == self.win_y and geo.width() == self.win_w:
                        target_screen = s
                        break

            # Move to target screen geometry
            if target_screen:
                screen_geo = target_screen.geometry()
                self.move(screen_geo.x(), screen_geo.y())
                if hasattr(self, "windowHandle") and self.windowHandle():
                    self.windowHandle().setScreen(target_screen)
            else:
                # Default coordinate move
                self.move(self.win_x, self.win_y)

        if self.is_fullscreen:
            self.showFullScreen()
        else:
            self.show()

    def closeEvent(self, event):
        """Clean shutdown on exit."""
        if hasattr(self, "worker") and self.worker:
            self.worker.stop()
        event.accept()
