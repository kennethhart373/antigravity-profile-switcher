import threading
import sys

from src.gui import MainWindow
from src.tray import TrayApp


class App:
    def __init__(self):
        self.window = None
        self.tray = None

    def run(self):
        self.window = MainWindow()
        self.window.protocol("WM_DELETE_WINDOW", self._hide_window)

        self.tray = TrayApp(
            show_window_callback=self._show_window,
            quit_callback=self._quit,
        )
        tray_thread = threading.Thread(target=self.tray.run, daemon=True)
        tray_thread.start()

        self.window.mainloop()

    def _show_window(self):
        if self.window:
            self.window.after(0, self.window.deiconify)
            self.window.after(0, self.window.lift)

    def _hide_window(self):
        if self.window:
            self.window.withdraw()

    def _quit(self):
        if self.tray:
            self.tray.stop()
        if self.window:
            self.window.after(0, self.window.destroy)
