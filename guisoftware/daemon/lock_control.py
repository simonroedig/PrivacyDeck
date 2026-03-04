"""
OS screen-lock control — macOS, Linux, Windows.
"""
import platform
import subprocess


def lock_os() -> None:
    """Lock the operating system screen immediately."""
    system = platform.system()

    if system == "Darwin":
        # macOS: use CGSession to suspend the session (most reliable)
        cgsession = (
            "/System/Library/CoreServices/Menu Extras/User.menu"
            "/Contents/Resources/CGSession"
        )
        try:
            subprocess.run([cgsession, "-suspend"], check=True, capture_output=True, timeout=5)
        except Exception:
            # Fallback: put display to sleep
            subprocess.run(["pmset", "displaysleepnow"], capture_output=True)

    elif system == "Linux":
        # Try common Linux screen lockers in order of preference
        lockers = [
            ["loginctl", "lock-session"],
            ["gnome-screensaver-command", "--lock"],
            ["xdg-screensaver", "lock"],
            ["xscreensaver-command", "-lock"],
            ["i3lock"],
        ]
        for cmd in lockers:
            try:
                subprocess.run(cmd, check=True, capture_output=True, timeout=5)
                return
            except (subprocess.CalledProcessError, FileNotFoundError, subprocess.TimeoutExpired):
                continue
        raise NotImplementedError("No supported screen locker found on Linux")

    elif system == "Windows":
        import ctypes
        ctypes.windll.user32.LockWorkStation()

    else:
        raise NotImplementedError(f"lock_os() not implemented for {system}")
