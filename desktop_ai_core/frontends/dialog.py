"""Error dialog helper — safe to call from any thread."""


def show_error_dialog(title: str, message: str) -> None:
    """Pop a modal error dialog. Safe to call from any thread.

    A fresh Tk root is created inside a daemon thread on each call so it never
    contends with the pystray/GTK main loop that runs in app mode. Degrades
    gracefully if Tk is unavailable (logs to stdout instead).
    """
    import threading

    def _run():
        try:
            import tkinter as tk
            from tkinter import messagebox
            root = tk.Tk()
            root.withdraw()
            root.attributes("-topmost", True)
            messagebox.showerror(title, message)
            root.destroy()
        except Exception as exc:
            print(f"[error dialog failed: {exc!r}] {title}: {message}")

    threading.Thread(target=_run, daemon=True).start()
