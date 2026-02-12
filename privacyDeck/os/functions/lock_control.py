import platform
import os

OS_TYPE = platform.system()

def lock_os():
    """Sperrt den Bildschirm abhängig vom OS."""
    if OS_TYPE == "Windows":
        os.system("rundll32.exe user32.dll,LockWorkStation")

    elif OS_TYPE == "Linux":
        os.system("xdg-screensaver lock")

    print(f">> {OS_TYPE}: System gesperrt")
