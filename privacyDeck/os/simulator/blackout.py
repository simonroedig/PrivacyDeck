import os
import tkinter as tk
from PIL import Image, ImageTk


def show_blackout_image():
	base_dir = os.path.dirname(os.path.abspath(__file__))
	image_path = os.path.join(base_dir, "blackout_images", "img1.jpg")

	if not os.path.exists(image_path):
		print(f">> Bild nicht gefunden: {image_path}")
		return False

	win = tk.Toplevel()
	win.title("Blackout")
	win.configure(bg="black")
	win.attributes("-fullscreen", True)
	win.lift()
	win.focus_force()

	screen_w = win.winfo_screenwidth()
	screen_h = win.winfo_screenheight()

	image = Image.open(image_path).convert("RGB")
	img_w, img_h = image.size

	scale = min(screen_w / img_w, screen_h / img_h)
	new_w = max(1, int(img_w * scale))
	new_h = max(1, int(img_h * scale))
	resized = image.resize((new_w, new_h), Image.Resampling.LANCZOS)

	photo = ImageTk.PhotoImage(resized)
	label = tk.Label(win, image=photo, bg="black")
	label.image = photo
	label.pack(expand=True)

	win.bind("<Escape>", lambda _event: win.destroy())
	win.bind("<Button-1>", lambda _event: win.destroy())

	print(">> Blackout-Bild im Fullscreen geöffnet")
	return True

