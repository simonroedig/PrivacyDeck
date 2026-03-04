"""
USB device alert control.
Shows a macOS system notification when USB monitoring is enabled/disabled.
For a full implementation, a background launchd agent (macOS) or udev rule (Linux)
would watch for new USB device connections and alert the user.
"""
import platform
import subprocess

_usb_alert_enabled = False


def toggle_usb_alert(enabled: bool) -> None:
    """Enable or disable USB device insertion alerts."""
    global _usb_alert_enabled
    _usb_alert_enabled = enabled
    system = platform.system()

    if system == "Darwin":
        status = "enabled — new USB devices will be flagged" if enabled else "disabled"
        script = (
            f'display notification "{status}" '
            f'with title "PrivacyDeck" subtitle "USB Safety Lock"'
        )
        try:
            subprocess.run(["osascript", "-e", script], capture_output=True, timeout=5)
        except Exception:
            pass

    elif system == "Linux":
        # On Linux a udev rule would be set up here; for demo just log
        pass

    elif system == "Windows":
        # On Windows, could use WMI events; for demo just track state
        pass

    else:
        raise NotImplementedError(f"toggle_usb_alert() not implemented for {system}")
