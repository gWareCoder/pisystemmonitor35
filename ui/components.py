"""Compact visual components optimized for 3.5" (480x320) display."""
from PyQt5.QtWidgets import (
    QWidget, QFrame, QLabel, QHBoxLayout, QVBoxLayout, QProgressBar
)
from PyQt5.QtCore import Qt
from .styles import get_meter_color, get_battery_color


class CompactMeter(QProgressBar):
    """Mini progress bar with dynamic color transitions."""
    def __init__(self, parent=None, height: int = 6):
        super().__init__(parent)
        self.setFixedHeight(height)
        self.setTextVisible(False)
        self.setRange(0, 100)
        self.setValue(0)
        self.update_style(0)

    def set_percent(self, value: float):
        int_val = int(round(value))
        self.setValue(min(100, max(0, int_val)))
        self.update_style(value)

    def update_style(self, value: float):
        color = get_meter_color(value)
        self.setStyleSheet(f"""
            QProgressBar {{
                background-color: #21262d;
                border: 1px solid #30363d;
                border-radius: 2px;
            }}
            QProgressBar::chunk {{
                background-color: {color};
                border-radius: 2px;
            }}
        """)


class ProcessRow(QWidget):
    """Single compact row for a process in Top 2 list."""
    def __init__(self, rank: int, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(2, 2, 2, 2)
        layout.setSpacing(2)

        # Top row: Rank badge + Name + Usage%
        top_row = QHBoxLayout()
        top_row.setContentsMargins(0, 0, 0, 0)
        top_row.setSpacing(5)

        self.rank_label = QLabel(f"#{rank}")
        self.rank_label.setStyleSheet("color: #58a6ff; font-weight: 700; font-size: 10px;")

        self.name_label = QLabel("---")
        self.name_label.setStyleSheet("color: #f0f6fc; font-weight: 600; font-size: 10px;")

        self.pid_label = QLabel("(---)")
        self.pid_label.setStyleSheet("color: #6e7681; font-size: 8.5px;")

        self.val_label = QLabel("0.0%")
        self.val_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        self.val_label.setStyleSheet("color: #3fb950; font-weight: 700; font-size: 10px;")

        top_row.addWidget(self.rank_label)
        top_row.addWidget(self.name_label)
        top_row.addWidget(self.pid_label)
        top_row.addStretch()
        top_row.addWidget(self.val_label)

        # Bottom row: Mini meter
        self.meter = CompactMeter(height=5)

        layout.addLayout(top_row)
        layout.addWidget(self.meter)

    def update_proc(self, name: str, pid: int, usage_percent: float, extra_text: str = ""):
        clean_name = name[:18] + "…" if len(name) > 19 else name
        self.name_label.setText(clean_name)
        self.pid_label.setText(f"({pid})")
        if extra_text:
            self.val_label.setText(f"{usage_percent:.1f}% ({extra_text})")
        else:
            self.val_label.setText(f"{usage_percent:.1f}%")
        self.meter.set_percent(usage_percent)


class BluetoothDeviceRow(QWidget):
    """Single row showing connected Bluetooth peripheral battery."""
    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 1, 0, 1)
        layout.setSpacing(5)

        self.icon_label = QLabel("⚡")
        self.icon_label.setStyleSheet("color: #58a6ff; font-size: 9px;")

        self.name_label = QLabel("---")
        self.name_label.setStyleSheet("color: #f0f6fc; font-weight: 500; font-size: 9px;")
        self.name_label.setMaximumWidth(110)

        self.battery_label = QLabel("--%")
        self.battery_label.setStyleSheet("color: #3fb950; font-weight: 700; font-size: 9px;")

        self.meter = QProgressBar()
        self.meter.setFixedSize(36, 6)
        self.meter.setTextVisible(False)
        self.meter.setRange(0, 100)
        self.meter.setValue(0)

        layout.addWidget(self.icon_label)
        layout.addWidget(self.name_label)
        layout.addStretch()
        layout.addWidget(self.battery_label)
        layout.addWidget(self.meter)

    def set_device(self, name: str, battery: int, icon_type: str = "bluetooth"):
        clean_name = name[:13] + "…" if len(name) > 14 else name
        self.name_label.setText(clean_name)

        if battery is not None and battery >= 0:
            self.battery_label.setText(f"{battery}%")
            self.meter.setValue(battery)
            color = get_battery_color(battery)
            self.battery_label.setStyleSheet(f"color: {color}; font-weight: 700; font-size: 9px;")
            self.meter.setStyleSheet(f"""
                QProgressBar {{
                    background-color: #21262d;
                    border: 1px solid #30363d;
                    border-radius: 2px;
                }}
                QProgressBar::chunk {{
                    background-color: {color};
                    border-radius: 1px;
                }}
            """)
            self.meter.show()
        else:
            self.battery_label.setText("N/A")
            self.battery_label.setStyleSheet("color: #6e7681; font-size: 9px;")
            self.meter.hide()


class TickerRibbon(QFrame):
    """Sub-header ribbon displaying NASDAQ, DOW, and Antigravity tokens."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("tickerBar")
        self.setProperty("class", "tickerBar")
        self.setFixedHeight(19)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(6, 0, 6, 0)
        layout.setSpacing(8)

        # NASDAQ
        self.ndx_label = QLabel("NDX: 18,200.0 (---)")
        self.ndx_label.setStyleSheet("font-size: 8.5px; font-weight: 600; color: #8b949e;")

        # Divider 1
        dot1 = QLabel("•")
        dot1.setStyleSheet("color: #30363d; font-size: 8px;")

        # DOW
        self.dow_label = QLabel("DOW: 42,100.0 (---)")
        self.dow_label.setStyleSheet("font-size: 8.5px; font-weight: 600; color: #8b949e;")

        # Divider 2
        dot2 = QLabel("•")
        dot2.setStyleSheet("color: #30363d; font-size: 8px;")

        # Antigravity Tokens
        self.agy_label = QLabel("AGY: ---")
        self.agy_label.setStyleSheet("font-size: 8.5px; font-weight: 700; color: #bc8cff;")

        layout.addWidget(self.ndx_label)
        layout.addWidget(dot1)
        layout.addWidget(self.dow_label)
        layout.addWidget(dot2)
        layout.addStretch()
        layout.addWidget(self.agy_label)

    def update_market(self, quotes: dict):
        # NDX
        ndx = quotes.get("^IXIC")
        if ndx:
            price = ndx.get("price", 0.0)
            pct = ndx.get("percent_change", 0.0)
            sign = "+" if pct >= 0 else ""
            color = "#3fb950" if pct >= 0 else "#f85149"
            self.ndx_label.setText(f"NDX: {price:,.1f} ({sign}{pct:.2f}%)")
            self.ndx_label.setStyleSheet(f"font-size: 8.5px; font-weight: 600; color: {color};")

        # DOW
        dow = quotes.get("^DJI")
        if dow:
            price = dow.get("price", 0.0)
            pct = dow.get("percent_change", 0.0)
            sign = "+" if pct >= 0 else ""
            color = "#3fb950" if pct >= 0 else "#f85149"
            self.dow_label.setText(f"DOW: {price:,.1f} ({sign}{pct:.2f}%)")
            self.dow_label.setStyleSheet(f"font-size: 8.5px; font-weight: 600; color: {color};")

    def update_tokens(self, token_data: dict):
        session = token_data.get("session_tokens", 0)
        remaining = token_data.get("remaining_tokens", 0)
        pct_rem = token_data.get("percent_remaining", 0.0)

        # Format friendly K numbers
        sess_str = f"{session / 1000:.1f}k" if session >= 1000 else str(session)
        rem_str = f"{remaining / 1000:.1f}k" if remaining >= 1000 else str(remaining)

        self.agy_label.setText(f"AGY: {sess_str} used • {rem_str} rem ({pct_rem:.0f}%)")
