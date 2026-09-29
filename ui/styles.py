"""Stylesheet and color definitions optimized for 3.5" (480x320) display."""

DARK_THEME = """
QWidget {
    background-color: #0e1117;
    color: #f0f6fc;
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", "PibotoLt", "DejaVu Sans", Ubuntu, sans-serif;
    font-size: 10px;
}

QFrame.metricCard {
    background-color: #161b22;
    border: 1px solid #30363d;
    border-radius: 6px;
    padding: 3px;
}

QFrame.headerBar {
    background-color: #161b22;
    border-bottom: 1px solid #30363d;
    padding: 1px 6px;
}

QFrame.tickerBar {
    background-color: #0b0e14;
    border-bottom: 1px solid #21262d;
    padding: 0px 6px;
}

QLabel.titleLabel {
    color: #8b949e;
    font-weight: 700;
    font-size: 9px;
    letter-spacing: 0.5px;
}

QLabel.timeLabel {
    color: #ffffff;
    font-weight: 700;
    font-size: 11px;
}

QLabel.dateLabel {
    color: #8b949e;
    font-weight: 500;
    font-size: 10px;
}

QLabel.valueBig {
    color: #58a6ff;
    font-weight: 700;
    font-size: 13px;
}

QLabel.valueSmall {
    color: #c9d1d9;
    font-weight: 600;
    font-size: 9px;
}

QLabel.dimText {
    color: #6e7681;
    font-size: 8px;
}

QProgressBar {
    border: 1px solid #30363d;
    border-radius: 3px;
    text-align: center;
    background-color: #21262d;
    height: 7px;
    font-size: 7px;
    color: transparent;
}

QProgressBar::chunk {
    background-color: #3fb950;
    border-radius: 2px;
}

QProgressBar.warning::chunk {
    background-color: #d29922;
}

QProgressBar.danger::chunk {
    background-color: #f85149;
}

QPushButton.tabButton {
    background-color: #21262d;
    color: #8b949e;
    border: 1px solid #30363d;
    border-radius: 4px;
    padding: 2px 7px;
    font-size: 9px;
    font-weight: 600;
}

QPushButton.tabButton:hover {
    background-color: #30363d;
    color: #f0f6fc;
}

QPushButton.tabButton:checked {
    background-color: #1f6feb;
    color: #ffffff;
    border: 1px solid #388bfd;
}
"""


def get_meter_color(percentage: float) -> str:
    """Return color hex string according to utilization."""
    if percentage >= 85.0:
        return "#f85149"  # Danger red
    elif percentage >= 60.0:
        return "#d29922"  # Warning amber
    else:
        return "#3fb950"  # Good green


def get_battery_color(percentage: int) -> str:
    """Return color hex string according to battery remaining."""
    if percentage <= 15:
        return "#f85149"  # Critical red
    elif percentage <= 30:
        return "#d29922"  # Low amber
    else:
        return "#3fb950"  # Good green
