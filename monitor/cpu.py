"""CPU metrics collector for Raspberry Pi 5."""
import os
import subprocess
import psutil


def get_cpu_temp() -> float:
    """Read CPU temperature in Celsius."""
    # Method 1: thermal_zone0
    try:
        thermal_path = "/sys/class/thermal/thermal_zone0/temp"
        if os.path.exists(thermal_path):
            with open(thermal_path, "r") as f:
                return round(int(f.read().strip()) / 1000.0, 1)
    except Exception:
        pass

    # Method 2: vcgencmd measure_temp
    try:
        out = subprocess.check_output(["vcgencmd", "measure_temp"], text=True)
        # temp=58.2'C
        val = out.strip().replace("temp=", "").replace("'C", "")
        return float(val)
    except Exception:
        pass

    return 0.0


def get_cpu_frequency() -> int:
    """Get current CPU clock frequency in MHz."""
    try:
        freq_path = "/sys/devices/system/cpu/cpu0/cpufreq/scaling_cur_freq"
        if os.path.exists(freq_path):
            with open(freq_path, "r") as f:
                return int(int(f.read().strip()) / 1000)
    except Exception:
        pass

    try:
        freq = psutil.cpu_freq()
        if freq and freq.current:
            return int(freq.current)
    except Exception:
        pass

    return 0


def get_cpu_metrics() -> dict:
    """Collect full CPU metrics."""
    overall = psutil.cpu_percent(interval=None)
    per_core = psutil.cpu_percent(interval=None, percpu=True)
    temp = get_cpu_temp()
    freq = get_cpu_frequency()

    return {
        "overall": round(overall, 1),
        "per_core": [round(c, 1) for c in per_core],
        "temperature": temp,
        "frequency_mhz": freq,
        "cores": len(per_core),
    }


if __name__ == "__main__":
    # Test execution
    import time
    psutil.cpu_percent(interval=0.1)
    time.sleep(0.5)
    print("CPU Metrics:", get_cpu_metrics())
