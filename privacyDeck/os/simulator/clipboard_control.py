import platform
import os
import subprocess
import ctypes
import time


VK_TAB = 0x09
VK_RETURN = 0x0D
VK_ESCAPE = 0x1B
VK_V = 0x56
VK_LWIN = 0x5B

OS_TYPE = platform.system()


def _key_tap(vk_code: int, hold: float = 0.04):
    ctypes.windll.user32.keybd_event(vk_code, 0, 0, 0)
    time.sleep(hold)
    ctypes.windll.user32.keybd_event(vk_code, 0, 0x0002, 0)


def _open_clipboard_history_panel():
    ctypes.windll.user32.keybd_event(VK_LWIN, 0, 0, 0)
    time.sleep(0.03)
    _key_tap(VK_V)
    time.sleep(0.03)
    ctypes.windll.user32.keybd_event(VK_LWIN, 0, 0x0002, 0)

def wipe_clipboard_history():
    """
    Löscht die Clipboard History abhängig vom Betriebssystem.
    Funktioniert als Button-Action.
    """
    try:
        if OS_TYPE == "Windows":
            _open_clipboard_history_panel()
            time.sleep(0.25)
            _key_tap(VK_TAB)
            time.sleep(0.08)
            _key_tap(VK_TAB)
            time.sleep(0.08)
            _key_tap(VK_RETURN)
            time.sleep(0.12)
            _key_tap(VK_ESCAPE)
            print(">> Windows: Clipboard History GUI-Sequenz ausgeführt")

        elif OS_TYPE == "Linux":
            # Linux: xclip/xsel
            # Prüfen, ob xclip installiert ist
            if subprocess.run(["which", "xclip"], capture_output=True).returncode == 0:
                subprocess.run("echo -n | xclip -selection clipboard", shell=True)
                print(">> Linux: Clipboard geleert (xclip)")
            elif subprocess.run(["which", "xsel"], capture_output=True).returncode == 0:
                subprocess.run("xsel --clear --clipboard", shell=True)
                print(">> Linux: Clipboard geleert (xsel)")
            else:
                print(">> Linux: Kein xclip oder xsel installiert, Clipboard konnte nicht geleert werden")

        elif OS_TYPE == "Darwin":
            # macOS: pbcopy
            subprocess.run("pbcopy < /dev/null", shell=True)
            print(">> macOS: Clipboard geleert")

        else:
            print(f">> {OS_TYPE}: Clipboard-Wipe nicht unterstützt")

    except Exception as e:
        print(f"Fehler beim Wipen der Clipboard History: {e}")
