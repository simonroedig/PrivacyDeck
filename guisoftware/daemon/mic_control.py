"""
Microphone mute/unmute control — macOS, Linux, Windows.
"""
import platform
import subprocess


def set_mic_mute(muted: bool) -> None:
    """Mute or unmute the default system microphone input."""
    system = platform.system()

    if system == "Darwin":
        # macOS: set input volume via AppleScript (0 = mute, 100 = unmute)
        volume = 0 if muted else 100
        script = f"set volume input volume {volume}"
        subprocess.run(["osascript", "-e", script], check=True, capture_output=True)

    elif system == "Linux":
        # Linux: toggle ALSA capture via amixer
        if muted:
            subprocess.run(
                ["amixer", "set", "Capture", "nocap"],
                check=True, capture_output=True,
            )
        else:
            subprocess.run(
                ["amixer", "set", "Capture", "cap"],
                check=True, capture_output=True,
            )

    elif system == "Windows":
        # Windows: use pycaw or nircmd
        try:
            import subprocess as sp
            action = "mutesysvolume 1" if muted else "mutesysvolume 0"
            sp.run(["nircmd.exe"] + action.split(), check=True, capture_output=True)
        except Exception:
            raise NotImplementedError("set_mic_mute() on Windows requires nircmd.exe")

    else:
        raise NotImplementedError(f"set_mic_mute() not implemented for {system}")
