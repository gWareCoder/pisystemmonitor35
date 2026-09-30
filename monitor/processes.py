"""Process monitor for top CPU and Memory consuming processes."""
import psutil
from typing import Dict, List, Any


def get_top_processes(top_n: int = 2) -> Dict[str, List[Dict[str, Any]]]:
    """
    Get top N processes for CPU and Memory usage.
    Returns:
        {
            "cpu": [{"pid": ..., "name": ..., "cpu_percent": ..., "mem_percent": ...}],
            "memory": [{"pid": ..., "name": ..., "cpu_percent": ..., "mem_percent": ..., "rss_mb": ...}]
        }
    """
    procs = []
    # Collect process details
    for p in psutil.process_iter(["pid", "name", "cpu_percent", "memory_percent", "memory_info"]):
        try:
            info = p.info
            if not info or not info.get("name"):
                continue

            rss_mb = 0.0
            if info.get("memory_info"):
                rss_mb = round(info["memory_info"].rss / (1024 * 1024), 1)

            procs.append({
                "pid": info["pid"],
                "name": info["name"],
                "cpu_percent": round(info["cpu_percent"] or 0.0, 1),
                "memory_percent": round(info["memory_percent"] or 0.0, 1),
                "rss_mb": rss_mb,
            })
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            continue

    # Filter out current monitor process if desired, or keep all
    top_cpu = sorted(procs, key=lambda x: x["cpu_percent"], reverse=True)[:top_n]
    top_mem = sorted(procs, key=lambda x: x["memory_percent"], reverse=True)[:top_n]

    return {
        "cpu": top_cpu,
        "memory": top_mem,
    }


if __name__ == "__main__":
    # Prime cpu_percent measurements
    for p in psutil.process_iter(["cpu_percent"]):
        pass
    import time
    time.sleep(0.5)
    res = get_top_processes(2)
    print("Top 2 CPU:", res["cpu"])
    print("Top 2 Memory:", res["memory"])
