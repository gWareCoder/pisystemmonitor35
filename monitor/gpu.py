"""GPU metrics collector for Raspberry Pi 5 (VideoCore VII / v3d)."""
import os
import time
import subprocess
import re

_last_sample_time = 0.0
_last_engine_ns = 0
_last_pid_ns = {}


def get_v3d_clock_mhz() -> int:
    """Read VideoCore VII (v3d) clock frequency in MHz."""
    # Method 1: vcgencmd measure_clock v3d
    try:
        out = subprocess.check_output(["vcgencmd", "measure_clock", "v3d"], text=True)
        # frequency(0)=960006208
        match = re.search(r"=(\d+)", out)
        if match:
            return int(int(match.group(1)) / 1_000_000)
    except Exception:
        pass

    # Method 2: debugfs measure_clock
    try:
        dbg_path = "/sys/kernel/debug/dri/0/measure_clock"
        if os.path.exists(dbg_path):
            with open(dbg_path, "r") as f:
                content = f.read()
                # cycles: 993901343 (993.9 Mhz)
                match = re.search(r"\(([\d\.]+)\s*Mhz\)", content, re.IGNORECASE)
                if match:
                    return int(float(match.group(1)))
    except Exception:
        pass

    return 0


def get_gpu_bo_memory_mb() -> float:
    """Read GPU buffer objects allocated size in MB."""
    try:
        bo_path = "/sys/kernel/debug/dri/0/bo_stats"
        if os.path.exists(bo_path):
            with open(bo_path, "r") as f:
                for line in f:
                    if "allocated bo size (kb):" in line.lower():
                        kb = int(line.split(":")[-1].strip())
                        return round(kb / 1024.0, 1)
    except Exception:
        pass

    # Fallback: vcgencmd get_mem gpu
    try:
        out = subprocess.check_output(["vcgencmd", "get_mem", "gpu"], text=True)
        # gpu=8M
        val = out.strip().replace("gpu=", "").replace("M", "")
        return float(val)
    except Exception:
        pass

    return 0.0


def _sample_proc_drm_ns() -> dict:
    """Read cumulative drm-engine nanoseconds for each PID."""
    pids = {}
    try:
        proc_entries = os.listdir("/proc")
        for entry in proc_entries:
            if not entry.isdigit():
                continue
            pid = int(entry)
            fdinfo_dir = os.path.join("/proc", entry, "fdinfo")
            if not os.path.isdir(fdinfo_dir):
                continue
            pid_ns = 0
            try:
                for fd in os.listdir(fdinfo_dir):
                    fd_path = os.path.join(fdinfo_dir, fd)
                    try:
                        with open(fd_path, "r", errors="ignore") as f:
                            for line in f:
                                if line.startswith("drm-engine-"):
                                    parts = line.split(":")
                                    if len(parts) >= 2:
                                        val = int(parts[1].strip().split()[0])
                                        pid_ns += val
                    except Exception:
                        pass
            except Exception:
                pass
            if pid_ns > 0:
                pids[pid] = pid_ns
    except Exception:
        pass
    return pids


def get_process_name(pid: int) -> str:
    """Resolve process name cleanly from /proc/<pid>/comm or cmdline."""
    try:
        with open(f"/proc/{pid}/comm", "r") as f:
            comm = f.read().strip()
        if comm.startswith("python"):
            with open(f"/proc/{pid}/cmdline", "r") as f:
                cmd = f.read().replace("\x00", " ")
            if "main.py" in cmd or "spi1-system-monitor" in cmd:
                return "spi1-sysmon"
        return comm
    except Exception:
        pass
    try:
        import psutil
        return psutil.Process(pid).name()
    except Exception:
        pass
    return f"PID {pid}"


def get_gpu_utilization_and_process() -> tuple:
    """
    Calculate GPU utilization percentage and identify the process
    actively causing GPU load using DRM fdinfo engine counters.
    Returns (utilization_percent, active_process_name, active_proc_percent).
    """
    global _last_sample_time, _last_engine_ns, _last_pid_ns
    current_time = time.time()
    current_pid_ns = _sample_proc_drm_ns()
    found_any = len(current_pid_ns) > 0
    total_engine_ns = sum(current_pid_ns.values())

    usage_percent = 0.0
    top_proc = "Idle"
    top_proc_pct = 0.0

    if found_any and _last_sample_time > 0 and current_time > _last_sample_time:
        delta_sec = current_time - _last_sample_time
        delta_ns = total_engine_ns - _last_engine_ns
        if delta_sec > 0 and delta_ns >= 0:
            usage = (delta_ns / (delta_sec * 1e9)) * 100.0
            usage_percent = min(100.0, max(0.0, round(usage, 1)))

        # Find process with largest engine ns delta
        deltas = {}
        for pid, curr_ns in current_pid_ns.items():
            prev_ns = _last_pid_ns.get(pid, 0)
            diff = curr_ns - prev_ns
            if diff > 0:
                deltas[pid] = diff

        if deltas and delta_sec > 0:
            top_pid = max(deltas, key=deltas.get)
            top_diff = deltas[top_pid]
            top_proc_pct = min(100.0, max(0.0, round((top_diff / (delta_sec * 1e9)) * 100.0, 1)))
            top_proc = get_process_name(top_pid)

    _last_sample_time = current_time
    _last_engine_ns = total_engine_ns
    _last_pid_ns = current_pid_ns

    # If DRM engine counters are unavailable or 0, estimate from dynamic clock speed
    if not found_any or usage_percent == 0.0:
        clk = get_v3d_clock_mhz()
        if clk > 200 and not found_any:
            scaled = ((clk - 200) / 760.0) * 100.0
            usage_percent = min(100.0, max(0.0, round(scaled, 1)))

    if usage_percent < 0.5:
        top_proc = "Idle"
        top_proc_pct = 0.0

    return usage_percent, top_proc, top_proc_pct


def get_gpu_utilization_percent() -> float:
    """Calculate GPU utilization percentage (backwards compatibility)."""
    util, _, _ = get_gpu_utilization_and_process()
    return util


def get_gpu_metrics() -> dict:
    """Collect full GPU metrics for Raspberry Pi 5 including active process."""
    clock_mhz = get_v3d_clock_mhz()
    memory_mb = get_gpu_bo_memory_mb()
    utilization, active_proc, active_proc_pct = get_gpu_utilization_and_process()

    return {
        "utilization_percent": utilization,
        "clock_mhz": clock_mhz,
        "memory_mb": memory_mb,
        "active_process": active_proc,
        "active_proc_percent": active_proc_pct,
    }


# Initial baseline sampling on module load
try:
    _last_sample_time = time.time()
    _last_pid_ns = _sample_proc_drm_ns()
    _last_engine_ns = sum(_last_pid_ns.values())
except Exception:
    pass


if __name__ == "__main__":
    time.sleep(0.5)
    print("GPU Metrics:", get_gpu_metrics())
