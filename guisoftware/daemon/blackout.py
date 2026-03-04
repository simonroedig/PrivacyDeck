"""
Screen blackout control — full-screen black overlay for presentation privacy.
Covers all screens; click or press any key to dismiss.
"""
import threading


def show_blackout_image() -> None:
    """Cover all displays with a full-screen black overlay (non-blocking)."""
    t = threading.Thread(target=_show_blackout, daemon=True)
    t.start()


def _show_blackout() -> None:
    try:
        import tkinter as tk

        root = tk.Tk()
        root.withdraw()  # hide root window

        screens: list[tk.Toplevel] = []

        # Determine number of monitors — fall back to single if unavailable
        try:
            from screeninfo import get_monitors
            monitors = get_monitors()
        except Exception:
            monitors = None  # type: ignore

        def _close_all(event=None):
            for w in screens:
                try:
                    w.destroy()
                except Exception:
                    pass
            try:
                root.destroy()
            except Exception:
                pass

        def _make_screen(x: int, y: int, w: int, h: int):
            win = tk.Toplevel(root)
            win.geometry(f"{w}x{h}+{x}+{y}")
            win.configure(bg="black")
            win.attributes("-fullscreen", True)
            win.attributes("-topmost", True)
            win.overrideredirect(True)

            # "Click or press any key to exit" hint
            tk.Label(
                win,
                text="🔒  Privacy Blackout  —  click or press any key to exit",
                fg="#333333",
                bg="black",
                font=("SF Pro Display", 13),
            ).place(relx=0.5, rely=0.97, anchor="center")

            win.bind("<Button-1>", _close_all)
            win.bind("<Key>", _close_all)
            win.focus_set()
            screens.append(win)

        if monitors:
            for m in monitors:
                _make_screen(m.x, m.y, m.width, m.height)
        else:
            # Cover primary screen
            sw = root.winfo_screenwidth()
            sh = root.winfo_screenheight()
            _make_screen(0, 0, sw, sh)

        root.mainloop()

    except Exception:
        pass
