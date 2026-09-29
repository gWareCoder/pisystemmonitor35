"""GPU metrics collector for Raspberry Pi 5 (VideoCore VII / v3d)."""
import os
import time
import subprocess
import re

_last_sample_time = 0.0
_last_engine_ns = 0


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


def get_gpu_utilization_percent() -> float:
    """
    Calculate GPU utilization percentage using DRM fdinfo engine counters.
    Fallback to clock load if DRM profiling is inactive.
    """
    global _last_sample_time, _last_engine_ns
    current_time = time.time()
    total_engine_ns = 0
    found_any = False

    # Scan /proc/*/fdinfo/* for drm-engine-* counters
    try:
        proc_entries = os.listdir("/proc")
        for entry in proc_entries:
            if not entry.isdigit():
                continue
            fdinfo_dir = os.path.join("/proc", entry, "fdinfo")
            if not os.path.isdir(fdinfo_dir):
                continue
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
                                        total_engine_ns += val
                                        found_any = True
                    except Exception:
                        pass
            except Exception:
                pass
    except Exception:
        pass

    usage_percent = 0.0
    if found_any and _last_sample_time > 0 and current_time > _last_sample_time:
        delta_sec = current_time - _last_sample_time
        delta_ns = total_engine_ns - _last_engine_ns
        if delta_sec > 0 and delta_ns >= 0:
            # 1 second = 1e9 ns
            usage = (delta_ns / (delta_sec * 1e9)) * 100.0
            usage_percent = min(100.0, max(0.0, round(usage, 1)))

    _last_sample_time = current_time
    _last_engine_ns = total_engine_ns

    # If DRM engine counters are unavailable or 0, estimate from dynamic clock speed
    # VideoCore VII scales between 200MHz (idle) and 960MHz (full load)
    if not found_any or usage_percent == 0.0:
        clk = get_v3d_clock_mhz()
        if clk > 200:
            # Rough scaling estimate between 200MHz and 960MHz
            scaled = ((clk - 200) / 760.0) * 100.0
            usage_percent = min(100.0, max(0.0, round(scaled, 1)))

    return usage_percent


def get_gpu_metrics() -> dict:
    """Collect full GPU metrics for Raspberry Pi 5."""
    clock_mhz = get_v3d_clock_mhz()
    memory_mb = get_gpu_bo_memory_mb()
    utilization = get_gpu_utilization_percent()

    return {
        "utilization_percent": utilization,
        "clock_mhz": clock_mhz,
        "memory_mb": memory_mb,
    }


if __name__ == "__main__":
    get_gpu_utilization_percent()
    time.sleep(0.5)
    print("GPU Metrics:", get_gpu_metrics())
