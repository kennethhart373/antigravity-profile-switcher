import threading
from PIL import Image, ImageDraw
import pystray
from pystray import MenuItem, Menu

from src.profiles import ProfileManager
from src.switcher import switch_profile


def _create_icon_image():
    """Generate a simple tray icon (colored circle)."""
    img = Image.new("RGBA", (64, 64), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    draw.ellipse([8, 8, 56, 56], fill=(80, 180, 255))
    draw.text((22, 18), "AG", fill="white")
    return img


class TrayApp:
    def __init__(self, show_window_callback, quit_callback):
        self.pm = ProfileManager()
        self._show_window = show_window_callback
        self._quit = quit_callback
        self.icon = None

    def _build_menu(self):
        items = []
        profiles = self.pm.list_profiles()

        for p in profiles:
            name = p["name"]
            is_active = name == self.pm.active_profile
            label = f"● {name}" if is_active else f"  {name}"
            items.append(MenuItem(label, lambda _, n=name: self._on_switch(n), enabled=not is_active))

        if profiles:
            items.append(Menu.SEPARATOR)

        items.append(MenuItem("Open Manager", lambda _: self._show_window()))
        items.append(MenuItem("Quit", lambda _: self._on_quit()))
        return Menu(*items)

    def _on_switch(self, name: str):
        threading.Thread(target=self._do_switch, args=(name,), daemon=True).start()

    def _do_switch(self, name: str):
        try:
            switch_profile(self.pm, name)
        except Exception:
            pass
        # Refresh menu after switch
        if self.icon:
            self.icon.update_menu()

    def _on_quit(self):
        if self.icon:
            self.icon.stop()
        self._quit()

    def run(self):
        self.icon = pystray.Icon(
            "AntigravityProfileSwitcher",
            icon=_create_icon_image(),
            title="Antigravity Profile Switcher",
            menu=self._build_menu(),
        )
        self.icon.run()

    def stop(self):
        if self.icon:
            self.icon.stop()

    def update_menu(self):
        """Refresh the tray menu (e.g., after profile changes)."""
        if self.icon:
            self.icon.menu = self._build_menu()
            self.icon.update_menu()
