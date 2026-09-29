"""Background polling worker threads using PyQt5 signals."""
import time
from PyQt5.QtCore import QThread, pyqtSignal

from .cpu import get_cpu_metrics
from .gpu import get_gpu_metrics
from .bluetooth import get_bluetooth_batteries
from .market import get_market_quotes
from .antigravity_tokens import get_token_metrics
from .processes import get_top_processes
from .system_info import get_system_storage_info


class MetricsWorker(QThread):
    """
    Background worker that samples system, process, bluetooth, market,
    and token metrics at designated intervals and emits PyQt signals.
    """
    system_updated = pyqtSignal(dict)      # CPU, GPU, Processes, Storage (RAM/Disk), Network
    bluetooth_updated = pyqtSignal(list)    # Bluetooth devices
    market_updated = pyqtSignal(dict)       # NASDAQ, DOW quotes
    tokens_updated = pyqtSignal(dict)       # Antigravity tokens & quota

    def __init__(self, config: dict, parent=None):
        super().__init__(parent)
        self.config = config
        self._running = True

        intervals = config.get("refresh_intervals", {})
        self.sys_interval = intervals.get("system_seconds", 1.5)
        self.market_interval = intervals.get("market_seconds", 60.0)
        self.tokens_interval = intervals.get("tokens_seconds", 10.0)
        self.bt_interval = intervals.get("bluetooth_seconds", 5.0)

        self.plan_budget = config.get("antigravity", {}).get("plan_token_budget", 500000)
        self.rolling_hours = config.get("antigravity", {}).get("rolling_window_hours", 5.0)
        self.market_symbols = config.get("market", {}).get("display_names", {"^IXIC": "NDX", "^DJI": "DOW"})

    def stop(self):
        """Stop background worker cleanly."""
        self._running = False
        self.wait(1000)

    def run(self):
        """Main monitoring loop."""
        last_sys = 0.0
        last_market = 0.0
        last_tokens = 0.0
        last_bt = 0.0

        while self._running:
            now = time.time()

            # 1. System Metrics (CPU, GPU, Top 2 Processes, RAM, Disk, Network)
            if now - last_sys >= self.sys_interval:
                try:
                    cpu_data = get_cpu_metrics()
                    gpu_data = get_gpu_metrics()
                    proc_data = get_top_processes(top_n=2)
                    storage_data = get_system_storage_info()
                    self.system_updated.emit({
                        "cpu": cpu_data,
                        "gpu": gpu_data,
                        "processes": proc_data,
                        "storage": storage_data,
                    })
                except Exception:
                    pass
                last_sys = now

            # 2. Bluetooth Batteries
            if now - last_bt >= self.bt_interval:
                try:
                    bt_data = get_bluetooth_batteries()
                    self.bluetooth_updated.emit(bt_data)
                except Exception:
                    pass
                last_bt = now

            # 3. Antigravity Tokens & Quota
            if now - last_tokens >= self.tokens_interval:
                try:
                    token_data = get_token_metrics(
                        plan_budget=self.plan_budget,
                        rolling_window_hours=self.rolling_hours,
                    )
                    self.tokens_updated.emit(token_data)
                except Exception:
                    pass
                last_tokens = now

            # 4. Market Tickers (NASDAQ & DOW)
            if now - last_market >= self.market_interval:
                try:
                    quotes = get_market_quotes(self.market_symbols)
                    self.market_updated.emit(quotes)
                except Exception:
                    pass
                last_market = now

            # Short sleep to prevent busy-waiting
            time.sleep(0.2)
