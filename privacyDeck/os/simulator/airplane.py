import platform
import subprocess
import time
import ctypes
import shutil


VK_TAB = 0x09
VK_DOWN = 0x28
VK_RETURN = 0x0D
VK_SPACE = 0x20
VK_MENU = 0x12
VK_F4 = 0x73


def _key_tap(vk_code: int, hold: float = 0.04):
    ctypes.windll.user32.keybd_event(vk_code, 0, 0, 0)
    time.sleep(hold)
    ctypes.windll.user32.keybd_event(vk_code, 0, 0x0002, 0)


def _alt_f4():
    ctypes.windll.user32.keybd_event(VK_MENU, 0, 0, 0)
    time.sleep(0.03)
    _key_tap(VK_F4)
    time.sleep(0.03)
    ctypes.windll.user32.keybd_event(VK_MENU, 0, 0x0002, 0)


def _focus_settings_window() -> bool:
    ps_command = (
        "$wshell = New-Object -ComObject WScript.Shell; "
        "$wshell.AppActivate('Settings')"
    )
    result = subprocess.run(
        ["powershell", "-NoProfile", "-Command", ps_command],
        capture_output=True,
        text=True,
        check=False,
    )
    return result.stdout.strip().lower() == "true"

def open_network_settings():
    """
    Öffnet die Network & Internet Einstellungen in Windows 11.
    Nur aktiv, wenn Windows 11 erkannt wird.
    """
    os_type = platform.system()
    release = platform.release()

    if os_type == "Windows":
        # Nur für Windows 11 (Release 10 = Windows 10/11 intern)
        # Wir prüfen zusätzlich Build-Version für Win11 (ab 22000)
        try:
            build = int(platform.version().split('.')[-1])
        except Exception:
            build = 0

        if build >= 22000:
            # Windows 11 Settings URI für Network & Internet
            uri = "ms-settings:network"
            subprocess.run(["start", uri], shell=True)
            print(">> Windows 11: Network & Internet Settings geöffnet")
        else:
            print(">> Nicht Windows 11, nichts geöffnet")
    else:
        print(f">> {os_type}: Funktion nur für Windows 11 verfügbar")


def gui_toggle_airplane_mode() -> bool:
    """
    Öffnet Windows 11 Network Settings und führt einfache GUI-Automation aus:
    6x TAB, 4x Pfeil runter, ENTER, SPACE, ALT+F4.
    """
    os_type = platform.system()
    if os_type == "Linux":
        return _linux_toggle_airplane()

    if os_type != "Windows":
        print(f">> {os_type}: GUI-Automation nur unter Windows verfügbar")
        return False

    try:
        build = int(platform.version().split('.')[-1])
    except Exception:
        build = 0

    if build < 22000:
        print(">> Nicht Windows 11, GUI-Automation abgebrochen")
        return False

    open_network_settings()
    time.sleep(1.2)
    _focus_settings_window()
    time.sleep(0.4)

    for _ in range(6):
        _key_tap(VK_TAB)
        time.sleep(0.05)

    for _ in range(4):
        _key_tap(VK_DOWN)
        time.sleep(0.05)

    _key_tap(VK_RETURN)
    time.sleep(0.1)
    _key_tap(VK_SPACE)
    time.sleep(0.2)
    _alt_f4()

    print(">> Airplane Mode GUI-Sequenz ausgeführt")
    return True


def _linux_get_states():
    """Return (wifi_state, wwan_state) where each is 'enabled'|'disabled' or None."""
    wifi_state = None
    wwan_state = None
    try:
        res = subprocess.run(["nmcli", "radio", "wifi"], capture_output=True, text=True)
        if res.returncode == 0:
            wifi_state = res.stdout.strip().lower()
    except Exception:
        wifi_state = None

    try:
        res = subprocess.run(["nmcli", "radio", "wwan"], capture_output=True, text=True)
        if res.returncode == 0:
            wwan_state = res.stdout.strip().lower()
    except Exception:
        wwan_state = None

    return wifi_state, wwan_state


def _linux_toggle_airplane() -> bool:
    """Best-effort toggle of airplane mode on Linux using nmcli, fallback to rfkill.

    Returns True on success, False otherwise.
    """
    if not shutil.which("nmcli") and not shutil.which("rfkill"):
        print(">> Linux: neither nmcli nor rfkill found; cannot toggle airplane mode")
        return False

    wifi, wwan = _linux_get_states()
    # consider airplane ON when wifi is disabled and (wwan disabled or missing)
    airplane_on = (wifi == "disabled") and (wwan in (None, "disabled"))

    cmds = []
    # prefer nmcli when available
    if shutil.which("nmcli"):
        if airplane_on:
            if wifi is not None:
                cmds.append(["nmcli", "radio", "wifi", "on"])
            if wwan is not None:
                cmds.append(["nmcli", "radio", "wwan", "on"])
        else:
            if wifi is not None:
                cmds.append(["nmcli", "radio", "wifi", "off"])
            if wwan is not None:
                cmds.append(["nmcli", "radio", "wwan", "off"])

        if not cmds:
            # generic fallback with nmcli
            cmds.append(["nmcli", "radio", "all", "on" if airplane_on else "off"])

        success = True
        for cmd in cmds:
            res = subprocess.run(cmd, capture_output=True, text=True)
            if res.returncode != 0:
                success = False
                print(f">> nmcli failed ({' '.join(cmd)}): {res.stderr.strip()}")
        if success:
            print(f">> Linux: Airplane mode set to {'OFF' if airplane_on else 'ON'} (nmcli)")
            return True

    # nmcli either not available or failed; try rfkill
    if shutil.which("rfkill"):
        try:
            cmd = ["rfkill", "unblock", "all"] if airplane_on else ["rfkill", "block", "all"]
            res = subprocess.run(cmd, capture_output=True, text=True)
            if res.returncode == 0:
                print(f">> Linux: Airplane mode set to {'OFF' if airplane_on else 'ON'} (rfkill)")
                return True
            else:
                print(f">> rfkill failed: {res.stderr.strip()}")
        except Exception as e:
            print(f">> rfkill exception: {e}")

    return False


# ===== TEST =====
if __name__ == "__main__":
    open_network_settings()
