"""
Wi-Fi kill-switch ("airplane mode") — macOS, Linux, Windows.
Toggles the system Wi-Fi interface. Returns True on success.
"""
import platform
import subprocess


def _get_macos_wifi_interface() -> str:
    """Detect the Wi-Fi network interface name on macOS (usually en0 or en1)."""
    try:
        result = subprocess.run(
            ["networksetup", "-listallhardwareports"],
            capture_output=True,
            text=True,
            timeout=5,
        )
        lines = result.stdout.splitlines()
        for i, line in enumerate(lines):
            if "Wi-Fi" in line and i + 1 < len(lines):
                dev_line = lines[i + 1]
                if "Device:" in dev_line:
                    return dev_line.split("Device:")[-1].strip()
    except Exception:
        pass
    return "en0"


def gui_toggle_airplane_mode() -> bool:
    """Toggle Wi-Fi (kill-switch) on or off. Returns True if the toggle succeeded."""
    system = platform.system()

    if system == "Darwin":
        iface = _get_macos_wifi_interface()
        try:
            # Check current power state
            result = subprocess.run(
                ["networksetup", "-getairportpower", iface],
                capture_output=True,
                text=True,
                timeout=5,
            )
            currently_on = "On" in result.stdout
            new_state = "off" if currently_on else "on"
            subprocess.run(
                ["networksetup", "-setairportpower", iface, new_state],
                check=True,
                capture_output=True,
                timeout=10,
            )
            return True
        except Exception:
            return False

    elif system == "Linux":
        try:
            subprocess.run(
                ["nmcli", "radio", "wifi", "off"],
                check=True, capture_output=True, timeout=10,
            )
            return True
        except Exception:
            return False

    elif system == "Windows":
        try:
            subprocess.run(
                ["netsh", "interface", "set", "interface", "Wi-Fi", "disable"],
                check=True, capture_output=True, timeout=10,
            )
            return True
        except Exception:
            return False

    else:
        raise NotImplementedError(f"gui_toggle_airplane_mode() not implemented for {system}")
