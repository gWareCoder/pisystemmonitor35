#!/usr/bin/env python3
"""Utility script to install labwc window rules and autostart entry for SPI-1 System Monitor."""
import os
import sys
import shutil
import xml.etree.ElementTree as ET
import subprocess

RC_XML_PATH = os.path.expanduser("~/.config/labwc/rc.xml")
AUTOSTART_DIR = os.path.expanduser("~/.config/autostart")
DESKTOP_ENTRY_PATH = os.path.join(AUTOSTART_DIR, "spi1-system-monitor.desktop")

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
MAIN_SCRIPT = os.path.join(CURRENT_DIR, "main.py")
RUN_SCRIPT = os.path.join(CURRENT_DIR, "run.sh")


def configure_labwc_rule(target_output: str = "SPI-1"):
    """Inject windowRule into ~/.config/labwc/rc.xml for spi1-system-monitor."""
    ET.register_namespace("", "http://openbox.org/3.4/rc")
    if not os.path.exists(RC_XML_PATH):
        print(f"Creating default labwc config at {RC_XML_PATH}")
        os.makedirs(os.path.dirname(RC_XML_PATH), exist_ok=True)
        root = ET.Element("openbox_config", xmlns="http://openbox.org/3.4/rc")
    else:
        # Backup existing rc.xml
        backup_path = RC_XML_PATH + ".bak"
        shutil.copyfile(RC_XML_PATH, backup_path)
        print(f"Backed up {RC_XML_PATH} to {backup_path}")

        try:
            tree = ET.parse(RC_XML_PATH)
            root = tree.getroot()
        except Exception as e:
            print(f"Error parsing existing {RC_XML_PATH}: {e}")
            return False

    # Find or create <windowRules>
    window_rules = root.find("windowRules")
    if window_rules is None:
        window_rules = ET.SubElement(root, "windowRules")

    # Check if rule for spi1-system-monitor already exists
    existing = False
    for rule in window_rules.findall("windowRule"):
        if rule.get("identifier") == "spi1-system-monitor":
            existing = True
            break

    if not existing:
        rule = ET.SubElement(
            window_rules,
            "windowRule",
            identifier="spi1-system-monitor",
            serverDecoration="no"
        )
        action_move = ET.SubElement(rule, "action", name="MoveToOutput", output=target_output)
        action_snap = ET.SubElement(rule, "action", name="SnapToRegion", region="output")
        print(f"Added windowRule for 'spi1-system-monitor' moving to output '{target_output}'")

        # Format and save
        ET.indent(root, space="  ")
        tree = ET.ElementTree(root)
        tree.write(RC_XML_PATH, encoding="utf-8", xml_declaration=True)
        print(f"Successfully updated {RC_XML_PATH}")
    else:
        print("Rule for 'spi1-system-monitor' already present in labwc config.")

    # Reload labwc if possible
    try:
        subprocess.run(["killall", "-SIGHUP", "labwc"], check=False)
        print("Sent SIGHUP to labwc to reload config.")
    except Exception:
        pass

    return True


def install_autostart_entry():
    """Create .desktop file in ~/.config/autostart."""
    os.makedirs(AUTOSTART_DIR, exist_ok=True)
    content = f"""[Desktop Entry]
Type=Application
Name=SPI-1 System Monitor
Comment=3.5 inch System Monitor on SPI-1
Exec={RUN_SCRIPT}
Terminal=false
Categories=Utility;System;
X-GNOME-Autostart-enabled=true
"""
    with open(DESKTOP_ENTRY_PATH, "w") as f:
        f.write(content)
    os.chmod(DESKTOP_ENTRY_PATH, 0o755)
    print(f"Created autostart entry at {DESKTOP_ENTRY_PATH}")


def remove_autostart_entry():
    """Remove .desktop file from ~/.config/autostart."""
    if os.path.exists(DESKTOP_ENTRY_PATH):
        os.remove(DESKTOP_ENTRY_PATH)
        print(f"Removed autostart entry from {DESKTOP_ENTRY_PATH}")


def install_desktop_shortcut():
    """Create executable shortcut on ~/Desktop, ~/.local/share/applications, and install multi-size icons."""
    desktop_dir = os.path.expanduser("~/Desktop")
    apps_dir = os.path.expanduser("~/.local/share/applications")
    pixmaps_dir = os.path.expanduser("~/.local/share/pixmaps")
    hicolor_base = os.path.expanduser("~/.local/share/icons/hicolor")

    os.makedirs(desktop_dir, exist_ok=True)
    os.makedirs(apps_dir, exist_ok=True)
    os.makedirs(pixmaps_dir, exist_ok=True)

    # 1. Install all standard icon resolutions (16, 24, 32, 48, 64, 128, 256)
    sizes = [16, 24, 32, 48, 64, 128, 256]
    res_dir = os.path.join(CURRENT_DIR, "resources")

    for sz in sizes:
        sz_dir = os.path.join(hicolor_base, f"{sz}x{sz}", "apps")
        os.makedirs(sz_dir, exist_ok=True)
        src = os.path.join(res_dir, f"icon_{sz}.png")
        if not os.path.exists(src) and sz == 128:
            src = os.path.join(res_dir, "icon.png")

        if os.path.exists(src):
            dst = os.path.join(sz_dir, "spi1-system-monitor.png")
            shutil.copyfile(src, dst)
            # Also create alias for main.py in case taskbar queries script name
            shutil.copyfile(src, os.path.join(sz_dir, "main.py.png"))

    # Also install to pixmaps
    main_icon = os.path.join(res_dir, "icon.png")
    if os.path.exists(main_icon):
        shutil.copyfile(main_icon, os.path.join(pixmaps_dir, "spi1-system-monitor.png"))
        shutil.copyfile(main_icon, os.path.join(pixmaps_dir, "main.py.png"))

    # Try updating icon cache
    try:
        subprocess.run(["gtk-update-icon-cache", "-f", "-t", hicolor_base], check=False, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except Exception:
        pass

    # 2. Desktop file content (Use icon name so GtkIconTheme finds exact size match)
    content = f"""[Desktop Entry]
Type=Application
Version=1.0
Name=3.5" SPI-1 System Monitor
GenericName=System Monitor
Comment=Hardware and System Monitor for 3.5 inch SPI-1 Display
Exec={RUN_SCRIPT}
Icon=spi1-system-monitor
Terminal=false
Categories=System;Monitor;Utility;
StartupNotify=true
StartupWMClass=spi1-system-monitor
Actions=Windowed;

[Desktop Action Windowed]
Name=Open in Windowed Mode
Exec={RUN_SCRIPT} --windowed
"""
    # Write to ~/Desktop
    desktop_file = os.path.join(desktop_dir, "spi1-system-monitor.desktop")
    with open(desktop_file, "w") as f:
        f.write(content)
    os.chmod(desktop_file, 0o755)
    print(f"Created desktop launcher at {desktop_file}")

    # Write to ~/.local/share/applications
    app_file = os.path.join(apps_dir, "spi1-system-monitor.desktop")
    with open(app_file, "w") as f:
        f.write(content)
    os.chmod(app_file, 0o755)
    print(f"Created application menu entry at {app_file}")

    # Also alias main.py.desktop in case compositor looks up script name
    main_py_desktop = os.path.join(apps_dir, "main.py.desktop")
    with open(main_py_desktop, "w") as f:
        f.write(content)
    os.chmod(main_py_desktop, 0o755)


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Configure labwc rules and autostart")
    parser.add_argument("--autostart", action="store_true", help="Enable autostart on desktop login")
    parser.add_argument("--no-autostart", action="store_true", help="Disable autostart")
    parser.add_argument("--output", default="SPI-1", help="Target output (default: SPI-1)")
    args = parser.parse_args()

    configure_labwc_rule(target_output=args.output)
    install_desktop_shortcut()

    if args.autostart:
        install_autostart_entry()
    elif args.no_autostart:
        remove_autostart_entry()
