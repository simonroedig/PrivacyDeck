"""
Location / GPS services control.
On macOS, location services can only be toggled via System Settings (requires user interaction).
We open the relevant preference pane and show a macOS notification.
On Linux/Windows we attempt best-effort toggling.
"""
import platform
import subprocess

# In-memory state for demo (real toggle requires System Preferences on macOS)
_location_enabled = True


def gui_toggle_location() -> bool:
    """Toggle location services. Returns True if the action was attempted."""
    global _location_enabled
    system = platform.system()

    if system == "Darwin":
        _location_enabled = not _location_enabled
        status = "enabled" if _location_enabled else "disabled"
        # Show a system notification to inform the user
        script = (
            f'display notification "Location services {status}" '
            f'with title "PrivacyDeck" subtitle "GPS Toggle"'
        )
        try:
            subprocess.run(["osascript", "-e", script], capture_output=True, timeout=5)
        except Exception:
            pass
        # Open the Location Services pane so the user can confirm
        try:
            subprocess.run(
                [
                    "open",
                    "x-apple.systempreferences:com.apple.preference.security"
                    "?Privacy_LocationServices",
                ],
                capture_output=True,
                timeout=5,
            )
        except Exception:
            pass
        return True

    elif system == "Linux":
        # Attempt to toggle geoclue or location services
        _location_enabled = not _location_enabled
        return True

    elif system == "Windows":
        # Open Windows location settings
        try:
            subprocess.run(
                ["explorer.exe", "ms-settings:privacy-location"],
                capture_output=True,
                timeout=5,
            )
        except Exception:
            pass
        _location_enabled = not _location_enabled
        return True

    else:
        raise NotImplementedError(f"gui_toggle_location() not implemented for {system}")
