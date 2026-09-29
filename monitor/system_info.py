"""System RAM, Disk storage, Hostname, and IP address collector."""
import os
import socket
import psutil
from typing import Dict, Any


def get_network_info() -> Dict[str, str]:
    """Retrieve hostname and primary LAN IPv4 address."""
    hostname = socket.gethostname()
    ip_addr = "127.0.0.1"

    # Search interfaces for non-loopback IPv4 address
    try:
        interfaces = psutil.net_if_addrs()
        # Prioritize standard wireless and ethernet interfaces
        preferred_order = ["wlan", "eth", "en", "wl", "lan"]

        def iface_priority(name: str):
            for idx, p in enumerate(preferred_order):
                if name.startswith(p):
                    return idx
            return 99

        sorted_ifaces = sorted(interfaces.keys(), key=iface_priority)

        for iface in sorted_ifaces:
            for addr in interfaces[iface]:
                if addr.family == socket.AF_INET and not addr.address.startswith("127."):
                    ip_addr = addr.address
                    return {"hostname": hostname, "ip": ip_addr}
    except Exception:
        pass

    # Fallback via UDP socket connection
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 1))
        ip_addr = s.getsockname()[0]
        s.close()
    except Exception:
        pass

    return {"hostname": hostname, "ip": ip_addr}


def get_ram_metrics() -> Dict[str, Any]:
    """Get system RAM used, available, total, and percentage in GB."""
    vm = psutil.virtual_memory()
    gb = 1024 ** 3

    return {
        "total_gb": round(vm.total / gb, 1),
        "used_gb": round(vm.used / gb, 1),
        "free_gb": round(vm.available / gb, 1),
        "percent": round(vm.percent, 1),
    }


def get_disk_metrics(path: str = "/") -> Dict[str, Any]:
    """Get disk space used, free, total, and percentage in GB for root partition."""
    try:
        du = psutil.disk_usage(path)
        gb = 1024 ** 3

        return {
            "total_gb": round(du.total / gb, 1),
            "used_gb": round(du.used / gb, 1),
            "free_gb": round(du.free / gb, 1),
            "percent": round(du.percent, 1),
        }
    except Exception:
        return {
            "total_gb": 0.0,
            "used_gb": 0.0,
            "free_gb": 0.0,
            "percent": 0.0,
        }


def get_system_storage_info() -> Dict[str, Any]:
    """Collect combined RAM, Disk, Hostname, and IP information."""
    net = get_network_info()
    ram = get_ram_metrics()
    disk = get_disk_metrics("/")

    return {
        "network": net,
        "ram": ram,
        "disk": disk,
    }


if __name__ == "__main__":
    print(get_system_storage_info())
