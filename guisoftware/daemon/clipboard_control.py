"""
Clipboard history wipe control — macOS, Linux, Windows.
"""
import platform
import subprocess


def wipe_clipboard_history() -> None:
    """Clear the system clipboard contents."""
    system = platform.system()

    if system == "Darwin":
        # macOS: pipe empty string through pbcopy to clear the clipboard
        subprocess.run(["pbcopy"], input=b"", check=True)

    elif system == "Linux":
        # Try xclip first, then xsel
        try:
            subprocess.run(
                ["xclip", "-selection", "clipboard", "-i"],
                input=b"",
                check=True,
                capture_output=True,
            )
        except FileNotFoundError:
            subprocess.run(
                ["xsel", "--clipboard", "--clear"],
                check=True,
                capture_output=True,
            )

    elif system == "Windows":
        subprocess.run(["cmd", "/c", "echo.|clip"], check=True, capture_output=True)

    else:
        raise NotImplementedError(f"wipe_clipboard_history() not implemented for {system}")
