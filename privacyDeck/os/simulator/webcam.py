import platform
import tkinter as tk


try:
	import cv2
except ImportError:
	cv2 = None


PREVIEW_WIDTH = 160
PREVIEW_HEIGHT = 128
TARGET_ASPECT = PREVIEW_WIDTH / PREVIEW_HEIGHT


def _rgb_frame_to_photoimage(rgb_frame):
	ppm_header = f"P6\n{PREVIEW_WIDTH} {PREVIEW_HEIGHT}\n255\n".encode("ascii")
	ppm_data = ppm_header + rgb_frame.tobytes()
	return tk.PhotoImage(data=ppm_data, format="PPM")


def _center_crop_to_aspect(frame):
	height, width = frame.shape[:2]
	if height <= 0 or width <= 0:
		return frame

	current_aspect = width / height

	if abs(current_aspect - TARGET_ASPECT) < 1e-6:
		return frame

	if current_aspect > TARGET_ASPECT:
		new_width = int(height * TARGET_ASPECT)
		start_x = (width - new_width) // 2
		return frame[:, start_x:start_x + new_width]

	new_height = int(width / TARGET_ASPECT)
	start_y = (height - new_height) // 2
	return frame[start_y:start_y + new_height, :]


class WebcamController:
	def __init__(self, parent: tk.Widget):
		self._parent = parent
		self._is_on = False
		self._capture = None
		self._after_job = None

		self._frame = tk.Frame(parent)
		self._frame.pack(pady=6)

		self._title = tk.Label(self._frame, text="Webcam (160x128)")
		self._title.pack(pady=(0, 4))

		self._preview = tk.Label(
			self._frame,
			bg="black",
			relief="sunken",
			bd=1,
		)
		self._preview.pack()

		self._status = tk.Label(self._frame, text="OFF", fg="gray")
		self._status.pack(pady=(4, 0))

		self._preview_img = tk.PhotoImage(width=PREVIEW_WIDTH, height=PREVIEW_HEIGHT)
		self._preview.configure(image=self._preview_img)
		self._show_black_frame()

	@property
	def is_on(self) -> bool:
		return self._is_on

	def toggle(self) -> bool:
		if self._is_on:
			self.stop()
		else:
			self.start()
		return self._is_on

	def start(self) -> bool:
		if self._is_on:
			return True

		if cv2 is None:
			print(">> OpenCV (cv2) nicht installiert. Webcam kann nicht gestartet werden.")
			return False

		self._capture = self._open_camera()
		if self._capture is None or not self._capture.isOpened():
			self._capture = None
			self._status.configure(text="NO CAM", fg="red")
			print(">> Kamera konnte nicht geöffnet werden")
			return False

		self._capture.set(cv2.CAP_PROP_FRAME_WIDTH, PREVIEW_WIDTH)
		self._capture.set(cv2.CAP_PROP_FRAME_HEIGHT, PREVIEW_HEIGHT)

		self._is_on = True
		self._status.configure(text="ON", fg="green")
		self._schedule_next_frame()
		print(">> Webcam gestartet")
		return True

	def stop(self):
		self._is_on = False

		if self._after_job is not None:
			self._parent.after_cancel(self._after_job)
			self._after_job = None

		if self._capture is not None:
			self._capture.release()
			self._capture = None

		self._show_black_frame()
		self._status.configure(text="OFF", fg="gray")
		print(">> Webcam gestoppt")

	def _open_camera(self):
		if cv2 is None:
			return None

		os_type = platform.system()
		backends = []

		if os_type == "Windows":
			backends = [cv2.CAP_DSHOW, cv2.CAP_MSMF]
		elif os_type == "Linux":
			backends = [cv2.CAP_V4L2]

		backends.append(None)

		for backend in backends:
			if backend is None:
				cap = cv2.VideoCapture(0)
			else:
				cap = cv2.VideoCapture(0, backend)

			if cap is not None and cap.isOpened():
				return cap

			if cap is not None:
				cap.release()

		return None

	def _schedule_next_frame(self):
		if not self._is_on:
			return
		self._update_frame()
		self._after_job = self._parent.after(33, self._schedule_next_frame)

	def _update_frame(self):
		if self._capture is None:
			return

		ok, frame = self._capture.read()
		if not ok:
			return

		frame = _center_crop_to_aspect(frame)
		frame = cv2.resize(frame, (PREVIEW_WIDTH, PREVIEW_HEIGHT))
		frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

		self._preview_img = _rgb_frame_to_photoimage(frame)
		self._preview.configure(image=self._preview_img)

	def _show_black_frame(self):
		black = b"\x00" * (PREVIEW_WIDTH * PREVIEW_HEIGHT * 3)
		ppm_header = f"P6\n{PREVIEW_WIDTH} {PREVIEW_HEIGHT}\n255\n".encode("ascii")
		self._preview_img = tk.PhotoImage(data=ppm_header + black, format="PPM")
		self._preview.configure(image=self._preview_img)
