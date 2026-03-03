import os
import time
import ctypes
from ctypes import wintypes
import platform
import subprocess
import re
try:
	from PIL import Image, ImageTk
	_HAS_PIL = True
except Exception:
	_HAS_PIL = False


VK_F11 = 0x7A
MONITORINFOF_PRIMARY = 0x00000001


class RECT(ctypes.Structure):
	_fields_ = [
		("left", ctypes.c_long),
		("top", ctypes.c_long),
		("right", ctypes.c_long),
		("bottom", ctypes.c_long),
	]


class MONITORINFO(ctypes.Structure):
	_fields_ = [
		("cbSize", wintypes.DWORD),
		("rcMonitor", RECT),
		("rcWork", RECT),
		("dwFlags", wintypes.DWORD),
	]


def _key_tap(vk_code: int, hold: float = 0.04):
	ctypes.windll.user32.keybd_event(vk_code, 0, 0, 0)
	time.sleep(hold)
	ctypes.windll.user32.keybd_event(vk_code, 0, 0x0002, 0)


def _get_primary_monitor_rect():
	user32 = ctypes.windll.user32
	primary_rect = None

	MONITORENUMPROC = ctypes.WINFUNCTYPE(
		ctypes.c_int,
		wintypes.HMONITOR,
		wintypes.HDC,
		ctypes.POINTER(RECT),
		wintypes.LPARAM,
	)

	def enum_proc(hmonitor, _hdc, _lprect, _lparam):
		nonlocal primary_rect
		mi = MONITORINFO()
		mi.cbSize = ctypes.sizeof(MONITORINFO)
		if user32.GetMonitorInfoW(hmonitor, ctypes.byref(mi)):
			if mi.dwFlags & MONITORINFOF_PRIMARY:
				primary_rect = mi.rcMonitor
				return 0
		return 1

	callback = MONITORENUMPROC(enum_proc)
	user32.EnumDisplayMonitors(0, 0, callback, 0)
	return primary_rect


def _wait_for_new_foreground_window(previous_hwnd, timeout_sec: float = 2.5):
	user32 = ctypes.windll.user32
	deadline = time.time() + timeout_sec
	while time.time() < deadline:
		hwnd = user32.GetForegroundWindow()
		if hwnd and hwnd != previous_hwnd:
			return hwnd
		time.sleep(0.05)
	return user32.GetForegroundWindow()


def _move_window_to_primary_monitor(hwnd) -> bool:
	if not hwnd:
		return False

	primary = _get_primary_monitor_rect()
	if primary is None:
		return False

	width = primary.right - primary.left
	height = primary.bottom - primary.top
	return bool(
		ctypes.windll.user32.MoveWindow(
			hwnd,
			primary.left,
			primary.top,
			width,
			height,
			True,
		)
	)


def _get_linux_primary_monitor_geometry():
	"""Get primary monitor geometry on Linux using xrandr."""
	try:
		res = subprocess.run(["xrandr", "--query"], capture_output=True, text=True)
		if res.returncode == 0:
			for line in res.stdout.splitlines():
				if " connected primary " in line:
					m = re.search(r"(\d+)x(\d+)\+(\d+)\+(\d+)", line)
					if m:
						width, height, x, y = map(int, m.groups())
						return x, y, width, height
	except Exception:
		pass
	return None


def show_blackout_image():
	base_dir = os.path.dirname(os.path.abspath(__file__))
	image_path = os.path.join(base_dir, "blackout_images", "img1.jpg")

	if not os.path.exists(image_path):
		print(f">> Bild nicht gefunden: {image_path}")
		return False

	os_type = platform.system()
	if os_type == "Windows":
		previous_hwnd = ctypes.windll.user32.GetForegroundWindow()
		# open with default program
		try:
			os.startfile(image_path)
		except Exception:
			subprocess.run(["start", image_path], shell=True)

		hwnd = _wait_for_new_foreground_window(previous_hwnd)
		_move_window_to_primary_monitor(hwnd)
		time.sleep(0.35)
		_key_tap(VK_F11)

		print(">> Blackout-Bild geöffnet, auf Hauptmonitor verschoben + F11 ausgelöst")
		return True

	# Linux / other platforms: use native image viewer in fullscreen on primary monitor
	try:
		# Get primary monitor geometry
		primary_geom = _get_linux_primary_monitor_geometry()
		
		# Try using common Linux image viewers in fullscreen mode
		viewers = ["eog", "feh", "display"]
		for viewer in viewers:
			try:
				if viewer == "eog":
					subprocess.Popen([viewer, "--fullscreen", image_path])
				elif viewer == "feh":
					if primary_geom:
						x, y, w, h = primary_geom
						subprocess.Popen([viewer, "--fullscreen", "--geometry", f"{w}x{h}+{x}+{y}", image_path])
					else:
						subprocess.Popen([viewer, "--fullscreen", image_path])
				elif viewer == "display":
					if primary_geom:
						x, y, w, h = primary_geom
						subprocess.Popen([viewer, "-fullscreen", "-geometry", f"{w}x{h}+{x}+{y}", image_path])
					else:
						subprocess.Popen([viewer, "-fullscreen", image_path])
				print(f">> Blackout-Bild geöffnet mit {viewer} auf Hauptmonitor")
				return True
			except FileNotFoundError:
				continue
			except Exception as e:
				print(f">> {viewer} fehlgeschlagen: {e}")
				continue

		# Fallback: use xdg-open
		subprocess.Popen(["xdg-open", image_path])
		print(">> Blackout-Bild geöffnet mit xdg-open")
		return True

	except Exception as e:
		print(f">> Image viewer failed: {e}")
		return False

