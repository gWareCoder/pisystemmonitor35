"""Dashboard view layout optimized for 3.5" (480x320) display."""
from PyQt5.QtWidgets import (
    QWidget, QFrame, QLabel, QHBoxLayout, QVBoxLayout, QGridLayout
)
from PyQt5.QtCore import Qt
from .components import CompactMeter, ProcessRow, BluetoothDeviceRow


class DashboardView(QWidget):
    """Compact All-in-One Dashboard view."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.init_ui()

    def init_ui(self):
        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(4, 4, 4, 4)
        main_layout.setSpacing(5)

        # ==========================================
        # LEFT COLUMN (Width ~215px): CPU, GPU, Bluetooth
        # ==========================================
        left_col = QVBoxLayout()
        left_col.setContentsMargins(0, 0, 0, 0)
        left_col.setSpacing(4)

        # 1. CPU Card
        self.cpu_card = QFrame()
        self.cpu_card.setProperty("class", "metricCard")
        cpu_layout = QVBoxLayout(self.cpu_card)
        cpu_layout.setContentsMargins(5, 4, 5, 4)
        cpu_layout.setSpacing(2)

        # CPU Header
        cpu_head = QHBoxLayout()
        cpu_head.setContentsMargins(0, 0, 0, 0)
        cpu_title = QLabel("CPU")
        cpu_title.setStyleSheet("color: #8b949e; font-size: 8.5px; font-weight: 700; background: transparent;")
        self.cpu_val = QLabel("0.0%")
        self.cpu_val.setStyleSheet("color: #58a6ff; font-size: 10px; font-weight: 700; background: transparent;")
        self.cpu_temp = QLabel("--°C")
        self.cpu_temp.setStyleSheet("color: #d29922; font-size: 9px; font-weight: 600; background: transparent;")
        cpu_head.addWidget(cpu_title)
        cpu_head.addStretch()
        cpu_head.addWidget(self.cpu_temp)
        cpu_head.addSpacing(6)
        cpu_head.addWidget(self.cpu_val)

        # CPU Main Meter
        self.cpu_meter = CompactMeter(height=6)

        # 4-Core Mini Meters
        cores_layout = QHBoxLayout()
        cores_layout.setContentsMargins(0, 1, 0, 0)
        cores_layout.setSpacing(2)
        self.core_meters = []
        for i in range(4):
            cm = CompactMeter(height=3)
            self.core_meters.append(cm)
            cores_layout.addWidget(cm)

        cpu_layout.addLayout(cpu_head)
        cpu_layout.addWidget(self.cpu_meter)
        cpu_layout.addLayout(cores_layout)
        left_col.addWidget(self.cpu_card)

        # 2. GPU Card
        self.gpu_card = QFrame()
        self.gpu_card.setProperty("class", "metricCard")
        gpu_layout = QVBoxLayout(self.gpu_card)
        gpu_layout.setContentsMargins(5, 3, 5, 3)
        gpu_layout.setSpacing(2)

        # GPU Header
        gpu_head = QHBoxLayout()
        gpu_head.setContentsMargins(0, 0, 0, 0)
        gpu_title = QLabel("GPU (VC7 / v3d)")
        gpu_title.setStyleSheet("color: #8b949e; font-size: 8.5px; font-weight: 700; background: transparent;")
        self.gpu_val = QLabel("0.0%")
        self.gpu_val.setStyleSheet("color: #58a6ff; font-size: 10px; font-weight: 700; background: transparent;")
        self.gpu_clk = QLabel("--- MHz")
        self.gpu_clk.setStyleSheet("color: #bc8cff; font-size: 9px; font-weight: 600; background: transparent;")
        gpu_head.addWidget(gpu_title)
        gpu_head.addStretch()
        gpu_head.addWidget(self.gpu_clk)
        gpu_head.addSpacing(6)
        gpu_head.addWidget(self.gpu_val)

        # GPU Meter
        self.gpu_meter = CompactMeter(height=5)

        # Active process causing GPU utilization
        self.gpu_proc = QLabel("Active: Idle")
        self.gpu_proc.setStyleSheet("color: #8b949e; font-size: 8px; font-weight: 600; background: transparent;")

        # GPU Subtext (Buffer memory)
        self.gpu_sub = QLabel("Buffer Alloc: 0.0 MB")
        self.gpu_sub.setStyleSheet("color: #6e7681; font-size: 8px; background: transparent;")

        gpu_layout.addLayout(gpu_head)
        gpu_layout.addWidget(self.gpu_meter)
        gpu_layout.addWidget(self.gpu_proc)
        gpu_layout.addWidget(self.gpu_sub)
        left_col.addWidget(self.gpu_card)

        # 3. RAM & Disk Storage Card (Used / Remaining in GB)
        self.storage_card = QFrame()
        self.storage_card.setProperty("class", "metricCard")
        storage_layout = QVBoxLayout(self.storage_card)
        storage_layout.setContentsMargins(5, 3, 5, 3)
        storage_layout.setSpacing(2)

        # RAM Row
        ram_head = QHBoxLayout()
        ram_head.setContentsMargins(0, 0, 0, 0)
        ram_title = QLabel("RAM")
        ram_title.setStyleSheet("color: #8b949e; font-size: 8.5px; font-weight: 700; background: transparent;")
        self.ram_val = QLabel("0.0G / 0.0G (0.0G rem)")
        self.ram_val.setStyleSheet("color: #3fb950; font-size: 8.5px; font-weight: 600; background: transparent;")
        ram_head.addWidget(ram_title)
        ram_head.addStretch()
        ram_head.addWidget(self.ram_val)

        self.ram_meter = CompactMeter(height=4)

        # Disk Row
        disk_head = QHBoxLayout()
        disk_head.setContentsMargins(0, 1, 0, 0)
        disk_title = QLabel("DISK (/)")
        disk_title.setStyleSheet("color: #8b949e; font-size: 8.5px; font-weight: 700; background: transparent;")
        self.disk_val = QLabel("0.0G / 0.0G (0.0G rem)")
        self.disk_val.setStyleSheet("color: #58a6ff; font-size: 8.5px; font-weight: 600; background: transparent;")
        disk_head.addWidget(disk_title)
        disk_head.addStretch()
        disk_head.addWidget(self.disk_val)

        self.disk_meter = CompactMeter(height=4)

        storage_layout.addLayout(ram_head)
        storage_layout.addWidget(self.ram_meter)
        storage_layout.addLayout(disk_head)
        storage_layout.addWidget(self.disk_meter)
        left_col.addWidget(self.storage_card)

        # 4. Bluetooth Battery Card
        self.bt_card = QFrame()
        self.bt_card.setProperty("class", "metricCard")
        bt_layout = QVBoxLayout(self.bt_card)
        bt_layout.setContentsMargins(5, 3, 5, 3)
        bt_layout.setSpacing(2)

        bt_head = QHBoxLayout()
        bt_head.setContentsMargins(0, 0, 0, 0)
        bt_title = QLabel("BLUETOOTH BATTERIES")
        bt_title.setStyleSheet("color: #8b949e; font-size: 8.5px; font-weight: 700; background: transparent;")
        self.bt_count = QLabel("0 connected")
        self.bt_count.setStyleSheet("color: #6e7681; font-size: 8px; background: transparent;")
        bt_head.addWidget(bt_title)
        bt_head.addStretch()
        bt_head.addWidget(self.bt_count)

        self.bt_empty_label = QLabel("No Bluetooth devices connected")
        self.bt_empty_label.setAlignment(Qt.AlignCenter)
        self.bt_empty_label.setStyleSheet("color: #6e7681; font-size: 8px; padding: 2px 0px; background: transparent;")

        # Pre-allocate 2 device rows
        self.bt_rows = [BluetoothDeviceRow(), BluetoothDeviceRow()]
        for r in self.bt_rows:
            r.hide()

        bt_layout.addLayout(bt_head)
        bt_layout.addWidget(self.bt_empty_label)
        for r in self.bt_rows:
            bt_layout.addWidget(r)
        left_col.addWidget(self.bt_card)

        main_layout.addLayout(left_col, stretch=48)

        # ==========================================
        # RIGHT COLUMN (Width ~255px): Top 2 CPU & Top 2 Memory Processes
        # ==========================================
        right_col = QVBoxLayout()
        right_col.setContentsMargins(0, 0, 0, 0)
        right_col.setSpacing(4)

        # 1. Top 2 CPU Processes Card
        self.proc_cpu_card = QFrame()
        self.proc_cpu_card.setProperty("class", "metricCard")
        proc_cpu_layout = QVBoxLayout(self.proc_cpu_card)
        proc_cpu_layout.setContentsMargins(6, 6, 6, 6)
        proc_cpu_layout.setSpacing(4)

        proc_cpu_head = QHBoxLayout()
        proc_cpu_head.setContentsMargins(0, 0, 0, 0)
        proc_cpu_title = QLabel("TOP 2 CPU PROCESSES")
        proc_cpu_title.setStyleSheet("color: #8b949e; font-size: 8.5px; font-weight: 700; background: transparent;")
        proc_cpu_head.addWidget(proc_cpu_title)
        proc_cpu_head.addStretch()

        self.cpu_row1 = ProcessRow(rank=1)
        self.cpu_row2 = ProcessRow(rank=2)

        proc_cpu_layout.addLayout(proc_cpu_head)
        proc_cpu_layout.addWidget(self.cpu_row1)
        proc_cpu_layout.addWidget(self.cpu_row2)
        right_col.addWidget(self.proc_cpu_card)

        # 2. Top 2 Memory Processes Card
        self.proc_mem_card = QFrame()
        self.proc_mem_card.setProperty("class", "metricCard")
        proc_mem_layout = QVBoxLayout(self.proc_mem_card)
        proc_mem_layout.setContentsMargins(6, 6, 6, 6)
        proc_mem_layout.setSpacing(4)

        proc_mem_head = QHBoxLayout()
        proc_mem_head.setContentsMargins(0, 0, 0, 0)
        proc_mem_title = QLabel("TOP 2 MEMORY PROCESSES")
        proc_mem_title.setStyleSheet("color: #8b949e; font-size: 8.5px; font-weight: 700; background: transparent;")
        proc_mem_head.addWidget(proc_mem_title)
        proc_mem_head.addStretch()

        self.mem_row1 = ProcessRow(rank=1)
        self.mem_row2 = ProcessRow(rank=2)

        proc_mem_layout.addLayout(proc_mem_head)
        proc_mem_layout.addWidget(self.mem_row1)
        proc_mem_layout.addWidget(self.mem_row2)
        right_col.addWidget(self.proc_mem_card)

        main_layout.addLayout(right_col, stretch=52)

    def update_system_data(self, data: dict):
        """Update CPU, GPU, and Top 2 Processes."""
        cpu = data.get("cpu", {})
        overall_cpu = cpu.get("overall", 0.0)
        self.cpu_val.setText(f"{overall_cpu:.1f}%")
        self.cpu_meter.set_percent(overall_cpu)

        temp = cpu.get("temperature", 0.0)
        if temp > 0:
            self.cpu_temp.setText(f"{temp:.1f}°C")
            color = "#f85149" if temp >= 75.0 else ("#d29922" if temp >= 65.0 else "#3fb950")
            self.cpu_temp.setStyleSheet(f"color: {color}; font-size: 9px; font-weight: 600; background: transparent;")

        per_core = cpu.get("per_core", [])
        for i, val in enumerate(per_core[:4]):
            if i < len(self.core_meters):
                self.core_meters[i].set_percent(val)

        # GPU
        gpu = data.get("gpu", {})
        gpu_pct = gpu.get("utilization_percent", 0.0)
        self.gpu_val.setText(f"{gpu_pct:.1f}%")
        self.gpu_meter.set_percent(gpu_pct)

        clk = gpu.get("clock_mhz", 0)
        if clk > 0:
            self.gpu_clk.setText(f"{clk} MHz")

        mem = gpu.get("memory_mb", 0.0)
        self.gpu_sub.setText(f"Buffer Alloc: {mem:.1f} MB")

        active_proc = gpu.get("active_process", "Idle")
        active_pct = gpu.get("active_proc_percent", 0.0)
        if active_proc and active_proc.lower() != "idle" and (active_pct > 0 or gpu_pct >= 1.0):
            disp_name = active_proc[:17] + "…" if len(active_proc) > 18 else active_proc
            if active_pct > 0:
                self.gpu_proc.setText(f"Active: {disp_name} ({active_pct:.1f}%)")
            else:
                self.gpu_proc.setText(f"Active: {disp_name}")
            self.gpu_proc.setStyleSheet("color: #7ee787; font-size: 8px; font-weight: 600; background: transparent;")
        else:
            self.gpu_proc.setText("Active: Idle")
            self.gpu_proc.setStyleSheet("color: #8b949e; font-size: 8px; font-weight: 600; background: transparent;")

        # RAM & Disk Storage
        storage = data.get("storage", {})
        ram = storage.get("ram", {})
        if ram:
            used_g = ram.get("used_gb", 0.0)
            tot_g = ram.get("total_gb", 0.0)
            free_g = ram.get("free_gb", 0.0)
            pct = ram.get("percent", 0.0)
            self.ram_val.setText(f"{used_g:.1f}G / {tot_g:.1f}G ({free_g:.1f}G rem)")
            self.ram_meter.set_percent(pct)

        disk = storage.get("disk", {})
        if disk:
            used_d = disk.get("used_gb", 0.0)
            tot_d = disk.get("total_gb", 0.0)
            free_d = disk.get("free_gb", 0.0)
            pct_d = disk.get("percent", 0.0)
            self.disk_val.setText(f"{used_d:.1f}G / {tot_d:.1f}G ({free_d:.1f}G rem)")
            self.disk_meter.set_percent(pct_d)

        # Processes
        procs = data.get("processes", {})
        top_cpu = procs.get("cpu", [])
        if len(top_cpu) > 0:
            p = top_cpu[0]
            self.cpu_row1.update_proc(p["name"], p["pid"], p["cpu_percent"])
        if len(top_cpu) > 1:
            p = top_cpu[1]
            self.cpu_row2.update_proc(p["name"], p["pid"], p["cpu_percent"])

        top_mem = procs.get("memory", [])
        if len(top_mem) > 0:
            p = top_mem[0]
            rss_str = f"{p['rss_mb']}MB" if p.get("rss_mb") else ""
            self.mem_row1.update_proc(p["name"], p["pid"], p["memory_percent"], extra_text=rss_str)
        if len(top_mem) > 1:
            p = top_mem[1]
            rss_str = f"{p['rss_mb']}MB" if p.get("rss_mb") else ""
            self.mem_row2.update_proc(p["name"], p["pid"], p["memory_percent"], extra_text=rss_str)

    def update_bluetooth(self, devices: list):
        """Update connected Bluetooth devices and battery levels."""
        if not devices:
            self.bt_empty_label.show()
            self.bt_count.setText("0 connected")
            for r in self.bt_rows:
                r.hide()
            return

        self.bt_empty_label.hide()
        self.bt_count.setText(f"{len(devices)} connected")

        for i, r in enumerate(self.bt_rows):
            if i < len(devices):
                dev = devices[i]
                r.set_device(dev["name"], dev.get("battery"), dev.get("icon", "bluetooth"))
                r.show()
            else:
                r.hide()
