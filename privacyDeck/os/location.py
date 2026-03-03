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
	if os_type == "Linux":
		return _linux_toggle_location()

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


def _linux_toggle_location() -> bool:
	"""Best-effort toggle of location services on Linux.

	Tries `gsettings` targets first, then `systemctl` for geoclue.service,
	then `pkill`/`pgrep` as a last resort. Returns True if any action succeeded.
	"""
	if not (shutil.which("gsettings") or shutil.which("systemctl") or shutil.which("pkill") or shutil.which("pgrep")):
		print(">> Linux: no supported tools (gsettings/systemctl/pkill/pgrep) found")
		return False

	# Try gsettings candidates
	candidates = [
		("org.gnome.settings-daemon.plugins.location", "active"),
		("org.gnome.system.location", "enabled"),
		("org.gnome.desktop.location", "enabled"),
	]
	for schema, key in candidates:
		if not shutil.which("gsettings"):
			break
		try:
			res = subprocess.run(["gsettings", "get", schema, key], capture_output=True, text=True)
			if res.returncode == 0:
				val = res.stdout.strip().lower()
				if val in ("true", "false"):
					new = "false" if val == "true" else "true"
					setres = subprocess.run(["gsettings", "set", schema, key, new], capture_output=True, text=True)
					if setres.returncode == 0:
						print(f">> Linux: Location set to {new} via gsettings ({schema} {key})")
						return True
					else:
						print(f">> gsettings set failed ({schema} {key}): {setres.stderr.strip()}")
		except Exception:
			continue

	# Try systemctl for geoclue
	if shutil.which("systemctl"):
		for scope in ("--user", ""):
			try:
				status_cmd = ["systemctl", scope, "is-active", "geoclue.service"] if scope else ["systemctl", "is-active", "geoclue.service"]
				status = subprocess.run(status_cmd, capture_output=True, text=True)
				if status.returncode == 0:
					state = status.stdout.strip()
					action = "stop" if state == "active" else "start"
					cmd = ["systemctl", scope, action, "geoclue.service"] if scope else ["systemctl", action, "geoclue.service"]
					res = subprocess.run(cmd, capture_output=True, text=True)
					if res.returncode == 0:
						print(f">> Linux: geoclue.service {action}ed ({'off' if action=='stop' else 'on'})")
						return True
			except Exception:
				continue

	# Try pkill/pgrep for geoclue process
	if shutil.which("pgrep") and shutil.which("pkill"):
		try:
			pg = subprocess.run(["pgrep", "-f", "geoclue"], capture_output=True, text=True)
			if pg.returncode == 0:
				# process running -> kill to disable
				res = subprocess.run(["pkill", "-f", "geoclue"], capture_output=True, text=True)
				if res.returncode == 0:
					print(">> Linux: geoclue processes killed (location OFF)")
					return True
		except Exception:
			pass

	print(">> Linux: Unable to toggle location services with available methods")
	return False

