"""Bluetooth peripheral battery monitor using BlueZ D-Bus and UPower."""
from typing import List, Dict, Any, Optional

try:
    import dbus
except ImportError:
    dbus = None


def get_bluez_devices() -> List[Dict[str, Any]]:
    """Query BlueZ over System D-Bus for connected devices and battery percentage."""
    if dbus is None:
        return []

    devices = []
    try:
        bus = dbus.SystemBus()
        manager = dbus.Interface(
            bus.get_object("org.bluez", "/"),
            "org.freedesktop.DBus.ObjectManager"
        )
        objects = manager.GetManagedObjects()

        for path, interfaces in objects.items():
            if "org.bluez.Device1" in interfaces:
                dev = interfaces["org.bluez.Device1"]
                connected = bool(dev.get("Connected", False))
                if not connected:
                    continue

                name = str(dev.get("Alias", dev.get("Name", "Bluetooth Device")))
                icon = str(dev.get("Icon", "bluetooth"))
                address = str(dev.get("Address", ""))

                battery = None
                if "org.bluez.Battery1" in interfaces:
                    battery_val = interfaces["org.bluez.Battery1"].get("Percentage")
                    if battery_val is not None:
                        battery = int(battery_val)

                devices.append({
                    "name": name,
                    "battery": battery,
                    "icon": icon,
                    "address": address,
                    "connected": True,
                })
    except Exception:
        # Expected if D-Bus service is unavailable or in sandboxed environments
        pass

    return devices


def get_upower_devices() -> List[Dict[str, Any]]:
    """Fallback: Query UPower over System D-Bus for battery devices."""
    if dbus is None:
        return []

    devices = []
    try:
        bus = dbus.SystemBus()
        upower = bus.get_object("org.freedesktop.UPower", "/org/freedesktop/UPower")
        dev_paths = upower.EnumerateDevices(dbus_interface="org.freedesktop.UPower")

        for dev_path in dev_paths:
            dev_obj = bus.get_object("org.freedesktop.UPower", dev_path)
            props = dbus.Interface(dev_obj, "org.freedesktop.DBus.Properties")
            dev_type = props.Get("org.freedesktop.UPower.Device", "Type")
            # Type 2 = Battery, 3 = UPS, 4 = Monitor, 5 = Mouse, 6 = Keyboard, 7 = PDA, 8 = Phone
            if dev_type in (2, 5, 6, 7, 8):
                model = str(props.Get("org.freedesktop.UPower.Device", "Model"))
                pct = float(props.Get("org.freedesktop.UPower.Device", "Percentage"))
                is_present = bool(props.Get("org.freedesktop.UPower.Device", "IsPresent"))
                native_path = str(props.Get("org.freedesktop.UPower.Device", "NativePath"))

                # Check if it is a peripheral or bluetooth device
                if is_present and ("bluez" in native_path.lower() or dev_type in (5, 6)):
                    devices.append({
                        "name": model or "Peripheral",
                        "battery": int(round(pct)),
                        "icon": "input-mouse" if dev_type == 5 else "input-keyboard",
                        "address": "",
                        "connected": True,
                    })
    except Exception:
        pass

    return devices


def get_bluetooth_batteries() -> List[Dict[str, Any]]:
    """Get all connected Bluetooth devices with their remaining battery."""
    devices = get_bluez_devices()

    if not devices:
        upower_devs = get_upower_devices()
        if upower_devs:
            devices = upower_devs

    return devices


if __name__ == "__main__":
    devs = get_bluetooth_batteries()
    print("Connected Bluetooth Devices:", devs)
