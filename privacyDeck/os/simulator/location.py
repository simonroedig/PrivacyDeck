import platform
import subprocess
import time
import ctypes


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


def open_privacy_security_settings():
	os_type = platform.system()
	if os_type != "Windows":
		print(f">> {os_type}: Funktion nur für Windows verfügbar")
		return

	uri = "ms-settings:privacy"
	subprocess.run(["start", uri], shell=True)
	print(">> Windows: Privacy & Security Settings geöffnet")


def gui_toggle_location() -> bool:
	"""
	Öffnet Windows Privacy & Security und führt GUI-Sequenz aus:
	4x TAB, 8x DOWN, ENTER, TAB, SPACE, ENTER, ALT+F4.
	"""
	os_type = platform.system()
	if os_type != "Windows":
		print(f">> {os_type}: GUI-Automation nur unter Windows verfügbar")
		return False

	open_privacy_security_settings()
	time.sleep(1.2)
	_focus_settings_window()
	time.sleep(0.4)

	for _ in range(4):
		_key_tap(VK_TAB)
		time.sleep(0.05)

	for _ in range(8):
		_key_tap(VK_DOWN)
		time.sleep(0.05)

	_key_tap(VK_RETURN)
	time.sleep(0.1)
	_key_tap(VK_TAB)
	time.sleep(0.1)
	_key_tap(VK_SPACE)
	time.sleep(0.1)
	_key_tap(VK_RETURN)
	time.sleep(0.2)
	_alt_f4()

	print(">> Location GUI-Sequenz ausgeführt")
	return True

