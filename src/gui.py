import threading
import customtkinter as ctk
from tkinter import messagebox, simpledialog

from src.profiles import ProfileManager
from src.switcher import switch_profile


class MainWindow(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Antigravity Profile Switcher")
        self.geometry("420x480")
        self.resizable(False, False)
        ctk.set_appearance_mode("dark")

        self.pm = ProfileManager()
        self._build_ui()
        self._refresh_list()

    def _build_ui(self):
        # Header
        ctk.CTkLabel(self, text="Profiles", font=("", 18, "bold")).pack(pady=(15, 5))

        # Profile list frame
        self.list_frame = ctk.CTkScrollableFrame(self, width=380, height=280)
        self.list_frame.pack(padx=15, pady=10, fill="both", expand=True)

        # Buttons
        btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        btn_frame.pack(padx=15, pady=(0, 15), fill="x")

        ctk.CTkButton(btn_frame, text="Save Current Account", command=self._save_current).pack(fill="x", pady=3)
        ctk.CTkButton(btn_frame, text="Delete Selected", fg_color="#b33", hover_color="#900", command=self._delete_selected).pack(fill="x", pady=3)

    def _refresh_list(self):
        for w in self.list_frame.winfo_children():
            w.destroy()

        self._selected = None
        profiles = self.pm.list_profiles()

        if not profiles:
            ctk.CTkLabel(self.list_frame, text="No profiles saved yet.\nClick 'Save Current Account' to add one.", text_color="gray").pack(pady=40)
            return

        for p in profiles:
            is_active = p["name"] == self.pm.active_profile
            frame = ctk.CTkFrame(self.list_frame)
            frame.pack(fill="x", pady=2, padx=2)

            indicator = "● " if is_active else "  "
            label_text = f"{indicator}{p['name']}  ({p.get('email', '?')})"
            label = ctk.CTkLabel(frame, text=label_text, anchor="w")
            label.pack(side="left", padx=10, pady=8, fill="x", expand=True)

            if not is_active:
                ctk.CTkButton(frame, text="Switch", width=70, command=lambda n=p["name"]: self._switch(n)).pack(side="right", padx=5, pady=5)
            else:
                ctk.CTkLabel(frame, text="Active", text_color="green", width=70).pack(side="right", padx=5, pady=5)

            ctk.CTkButton(frame, text="✕", width=30, fg_color="#b33", hover_color="#900", command=lambda n=p["name"]: self._delete(n)).pack(side="right", padx=(0, 5), pady=5)

    def _save_current(self):
        name = simpledialog.askstring("Save Profile", "Profile name:", parent=self)
        if not name:
            return
        try:
            self.pm.save_current(name.strip())
            self._refresh_list()
        except FileNotFoundError as e:
            messagebox.showerror("Error", str(e), parent=self)

    def _switch(self, name: str):
        self._set_busy(True)
        threading.Thread(target=self._do_switch, args=(name,), daemon=True).start()

    def _do_switch(self, name: str):
        try:
            switch_profile(self.pm, name)
            self.after(0, self._refresh_list)
        except Exception as e:
            self.after(0, lambda: messagebox.showerror("Switch Failed", str(e), parent=self))
        finally:
            self.after(0, lambda: self._set_busy(False))

    def _delete(self, name: str):
        if messagebox.askyesno("Confirm", f"Delete profile '{name}'?", parent=self):
            self.pm.delete_profile(name)
            self._refresh_list()

    def _delete_selected(self):
        # Fallback if no inline delete used
        profiles = self.pm.list_profiles()
        if not profiles:
            return
        messagebox.showinfo("Tip", "Use the ✕ button next to each profile to delete it.", parent=self)

    def _set_busy(self, busy: bool):
        state = "disabled" if busy else "normal"
        for w in self.winfo_children():
            try:
                w.configure(state=state)
            except Exception:
                pass
