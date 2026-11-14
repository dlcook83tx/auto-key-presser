import customtkinter as ctk
import json
import threading
import time
from tkinter import filedialog, messagebox
from pynput import keyboard, mouse
from pynput.keyboard import Key, Controller as KeyboardController, GlobalHotKeys
from pynput.mouse import Button, Controller as MouseController

# ---------- Config ----------
CONFIG_FILE = "auto_key_config.json"
DEFAULT_HOTKEY = "<f9>"
DEFAULT_REPEAT_INTERVAL = 1000

class AutoKeyPresser(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("Auto Key & Mouse Presser")
        self.geometry("820x680")
        self.minsize(800, 800)

        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")

        self.keyboard = KeyboardController()
        self.mouse = MouseController()
        self.running = False
        self.sequence = []          # list of {"type": "key"/"mouse", "value": str, "delay": int}
        self.hotkey_listener = None
        self.worker_thread = None

        self.load_config()
        self.build_ui()
        self.start_hotkey_listener()

    # ---------- UI ----------
    def build_ui(self):
        # Header
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(fill="x", padx=20, pady=(20, 10))

        ctk.CTkLabel(header, text="Auto Key & Mouse Presser",
                     font=ctk.CTkFont(size=24, weight="bold")).pack(side="left")

        self.status_label = ctk.CTkLabel(header, text="● Stopped", text_color="#ff6b6b",
                                         font=ctk.CTkFont(size=14, weight="bold"))
        self.status_label.pack(side="right")

        # Main content
        main = ctk.CTkFrame(self, fg_color="transparent")
        main.pack(fill="both", expand=True, padx=20, pady=10)

        # Left column - Sequence builder
        left = ctk.CTkFrame(main)
        left.pack(side="left", fill="both", expand=True, padx=(0, 10))

        ctk.CTkLabel(left, text="Action Sequence",
                     font=ctk.CTkFont(size=16, weight="bold")).pack(anchor="w", padx=15, pady=(15, 8))

        # Add action row
        add_frame = ctk.CTkFrame(left, fg_color="transparent")
        add_frame.pack(fill="x", padx=15, pady=5)

        self.action_type = ctk.CTkOptionMenu(add_frame, values=["Key", "Mouse"], width=90,
                                             command=self.on_type_change)
        self.action_type.set("Key")
        self.action_type.pack(side="left", padx=(0, 8))

        self.key_entry = ctk.CTkEntry(add_frame, placeholder_text="Key (a, space, f1...)", width=160)
        self.key_entry.pack(side="left", padx=(0, 8))

        self.mouse_combo = ctk.CTkOptionMenu(add_frame, values=["Left Click", "Right Click", "Middle Click"],
                                             width=140)
        self.mouse_combo.set("Left Click")
        # Initially hidden
        self.mouse_combo.pack_forget()

        self.delay_entry = ctk.CTkEntry(add_frame, placeholder_text="Delay ms", width=85)
        self.delay_entry.insert(0, "100")
        self.delay_entry.pack(side="left", padx=(0, 8))

        ctk.CTkButton(add_frame, text="Add", width=70, command=self.add_action).pack(side="left")

        # Sequence list
        self.seq_frame = ctk.CTkScrollableFrame(left, height=320)
        self.seq_frame.pack(fill="both", expand=True, padx=15, pady=10)

        # Sequence buttons
        btn_row = ctk.CTkFrame(left, fg_color="transparent")
        btn_row.pack(fill="x", padx=15, pady=(0, 15))

        ctk.CTkButton(btn_row, text="Clear All", fg_color="#c0392b", hover_color="#e74c3c",
                      command=self.clear_sequence).pack(side="left")
        ctk.CTkButton(btn_row, text="Remove Last", command=self.remove_last).pack(side="left", padx=8)

        # Right column - Settings & Controls
        right = ctk.CTkFrame(main, width=270)
        right.pack(side="right", fill="y")
        right.pack_propagate(False)

        ctk.CTkLabel(right, text="Settings",
                     font=ctk.CTkFont(size=16, weight="bold")).pack(anchor="w", padx=15, pady=(15, 10))

        # Repeat interval
        ctk.CTkLabel(right, text="Repeat interval (ms)").pack(anchor="w", padx=15)
        self.repeat_entry = ctk.CTkEntry(right)
        self.repeat_entry.insert(0, str(self.repeat_interval))
        self.repeat_entry.pack(fill="x", padx=15, pady=(0, 15))

        # Hotkey
        ctk.CTkLabel(right, text="Start / Stop Hotkey").pack(anchor="w", padx=15)
        self.hotkey_entry = ctk.CTkEntry(right)
        self.hotkey_entry.insert(0, self.hotkey)
        self.hotkey_entry.pack(fill="x", padx=15, pady=(0, 5))

        ctk.CTkLabel(right, text="Examples: <f9>  <ctrl>+<shift>+a",
                     font=ctk.CTkFont(size=11), text_color="gray").pack(anchor="w", padx=15, pady=(0, 10))

        ctk.CTkButton(right, text="Apply Hotkey", command=self.apply_hotkey).pack(fill="x", padx=15, pady=(0, 20))

        # Save / Load
        ctk.CTkLabel(right, text="Sequences",
                     font=ctk.CTkFont(size=16, weight="bold")).pack(anchor="w", padx=15, pady=(5, 10))

        ctk.CTkButton(right, text="💾  Save Sequence", command=self.save_sequence_file).pack(fill="x", padx=15, pady=4)
        ctk.CTkButton(right, text="📂  Load Sequence", command=self.load_sequence_file).pack(fill="x", padx=15, pady=4)

        # Control buttons
        ctk.CTkLabel(right, text="Controls",
                     font=ctk.CTkFont(size=16, weight="bold")).pack(anchor="w", padx=15, pady=(20, 10))

        self.start_btn = ctk.CTkButton(right, text="▶  Start", height=42,
                                       fg_color="#27ae60", hover_color="#2ecc71",
                                       command=self.start)
        self.start_btn.pack(fill="x", padx=15, pady=5)

        self.stop_btn = ctk.CTkButton(right, text="■  Stop", height=42,
                                      fg_color="#c0392b", hover_color="#e74c3c",
                                      command=self.stop, state="disabled")
        self.stop_btn.pack(fill="x", padx=15, pady=5)

        info = ctk.CTkLabel(right, text="Tip: Hotkey works even when\nthis window is not focused.",
                            font=ctk.CTkFont(size=12), text_color="gray", justify="left")
        info.pack(side="bottom", padx=15, pady=20)

        self.refresh_sequence_display()

    def on_type_change(self, choice):
        if choice == "Key":
            self.mouse_combo.pack_forget()
            self.key_entry.pack(side="left", padx=(0, 8), before=self.delay_entry)
        else:
            self.key_entry.pack_forget()
            self.mouse_combo.pack(side="left", padx=(0, 8), before=self.delay_entry)

    # ---------- Sequence management ----------
    def add_action(self):
        action_type = self.action_type.get()
        try:
            delay = int(self.delay_entry.get().strip() or "100")
        except ValueError:
            delay = 100

        if action_type == "Key":
            key = self.key_entry.get().strip().lower()
            if not key:
                return
            self.sequence.append({"type": "key", "value": key, "delay": delay})
            self.key_entry.delete(0, "end")
        else:
            mouse_map = {
                "Left Click": "left",
                "Right Click": "right",
                "Middle Click": "middle"
            }
            value = mouse_map[self.mouse_combo.get()]
            self.sequence.append({"type": "mouse", "value": value, "delay": delay})

        self.refresh_sequence_display()
        self.save_config()

    def remove_last(self):
        if self.sequence:
            self.sequence.pop()
            self.refresh_sequence_display()
            self.save_config()

    def clear_sequence(self):
        self.sequence.clear()
        self.refresh_sequence_display()
        self.save_config()

    def move_up(self, index):
        if index > 0:
            self.sequence[index], self.sequence[index - 1] = self.sequence[index - 1], self.sequence[index]
            self.refresh_sequence_display()
            self.save_config()

    def move_down(self, index):
        if index < len(self.sequence) - 1:
            self.sequence[index], self.sequence[index + 1] = self.sequence[index + 1], self.sequence[index]
            self.refresh_sequence_display()
            self.save_config()

    def update_delay(self, index, new_delay_str):
        try:
            new_delay = int(new_delay_str.strip())
            if new_delay >= 0:
                self.sequence[index]["delay"] = new_delay
                self.save_config()
        except ValueError:
            pass

    def refresh_sequence_display(self):
        for widget in self.seq_frame.winfo_children():
            widget.destroy()

        if not self.sequence:
            ctk.CTkLabel(self.seq_frame, text="No actions yet — add some above",
                         text_color="gray").pack(pady=40)
            return

        for i, item in enumerate(self.sequence):
            row = ctk.CTkFrame(self.seq_frame, fg_color=("gray90", "gray20"))
            row.pack(fill="x", pady=3, padx=2)

            # Number
            ctk.CTkLabel(row, text=f"{i+1}.", width=28).pack(side="left", padx=(8, 0))

            # Action text
            if item["type"] == "key":
                display = f"Key: {item['value']}"
                color = "#3498db"
            else:
                display = f"Mouse: {item['value'].capitalize()} Click"
                color = "#e67e22"

            ctk.CTkLabel(row, text=display, width=150, anchor="w",
                         text_color=color).pack(side="left", padx=5)

            # Editable delay
            delay_var = ctk.StringVar(value=str(item["delay"]))
            delay_entry = ctk.CTkEntry(row, width=70, textvariable=delay_var)
            delay_entry.pack(side="left", padx=5)
            delay_entry.bind("<FocusOut>", lambda e, idx=i, var=delay_var: self.update_delay(idx, var.get()))
            delay_entry.bind("<Return>", lambda e, idx=i, var=delay_var: self.update_delay(idx, var.get()))

            ctk.CTkLabel(row, text="ms", text_color="gray").pack(side="left")

            # Move buttons
            btn_frame = ctk.CTkFrame(row, fg_color="transparent")
            btn_frame.pack(side="right", padx=5)

            ctk.CTkButton(btn_frame, text="↑", width=28, height=24,
                          command=lambda idx=i: self.move_up(idx)).pack(side="left", padx=1)
            ctk.CTkButton(btn_frame, text="↓", width=28, height=24,
                          command=lambda idx=i: self.move_down(idx)).pack(side="left", padx=1)

            # Delete button
            ctk.CTkButton(btn_frame, text="✕", width=28, height=24,
                          fg_color="transparent", hover_color="#c0392b",
                          command=lambda idx=i: self.remove_at(idx)).pack(side="left", padx=1)

    def remove_at(self, index):
        if 0 <= index < len(self.sequence):
            self.sequence.pop(index)
            self.refresh_sequence_display()
            self.save_config()

    # ---------- Save / Load external files ----------
    def save_sequence_file(self):
        if not self.sequence:
            messagebox.showwarning("Empty", "There is nothing to save.")
            return

        file_path = filedialog.asksaveasfilename(
            defaultextension=".json",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")],
            title="Save Sequence"
        )
        if file_path:
            data = {
                "sequence": self.sequence,
                "repeat_interval": int(self.repeat_entry.get() or 1000)
            }
            try:
                with open(file_path, "w") as f:
                    json.dump(data, f, indent=2)
                messagebox.showinfo("Saved", f"Sequence saved to:\n{file_path}")
            except Exception as e:
                messagebox.showerror("Error", f"Could not save file:\n{e}")

    def load_sequence_file(self):
        file_path = filedialog.askopenfilename(
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")],
            title="Load Sequence"
        )
        if file_path:
            try:
                with open(file_path, "r") as f:
                    data = json.load(f)
                self.sequence = data.get("sequence", [])
                if "repeat_interval" in data:
                    self.repeat_interval = data["repeat_interval"]
                    self.repeat_entry.delete(0, "end")
                    self.repeat_entry.insert(0, str(self.repeat_interval))
                self.refresh_sequence_display()
                self.save_config()
                messagebox.showinfo("Loaded", "Sequence loaded successfully.")
            except Exception as e:
                messagebox.showerror("Error", f"Could not load file:\n{e}")

    # ---------- Hotkey ----------
    def apply_hotkey(self):
        new_hotkey = self.hotkey_entry.get().strip()
        if not new_hotkey:
            return
        self.hotkey = new_hotkey
        self.restart_hotkey_listener()
        self.save_config()

    def start_hotkey_listener(self):
        try:
            self.hotkey_listener = GlobalHotKeys({
                self.hotkey: self.toggle
            })
            self.hotkey_listener.start()
        except Exception as e:
            print(f"Hotkey error: {e}")

    def restart_hotkey_listener(self):
        if self.hotkey_listener:
            self.hotkey_listener.stop()
        self.start_hotkey_listener()

    def toggle(self):
        if self.running:
            self.stop()
        else:
            self.start()

    # ---------- Start / Stop ----------
    def start(self):
        if not self.sequence or self.running:
            return

        try:
            self.repeat_interval = int(self.repeat_entry.get().strip())
        except ValueError:
            self.repeat_interval = 1000

        self.running = True
        self.status_label.configure(text="● Running", text_color="#2ecc71")
        self.start_btn.configure(state="disabled")
        self.stop_btn.configure(state="normal")

        self.worker_thread = threading.Thread(target=self.run_sequence, daemon=True)
        self.worker_thread.start()
        self.save_config()

    def stop(self):
        self.running = False
        self.status_label.configure(text="● Stopped", text_color="#ff6b6b")
        self.start_btn.configure(state="normal")
        self.stop_btn.configure(state="disabled")

    def run_sequence(self):
        while self.running:
            for item in self.sequence:
                if not self.running:
                    break
                self.perform_action(item)
                time.sleep(item["delay"] / 1000.0)

            if self.running:
                time.sleep(self.repeat_interval / 1000.0)

    def perform_action(self, item):
        if item["type"] == "key":
            self.press_key(item["value"])
        elif item["type"] == "mouse":
            self.click_mouse(item["value"])

    def press_key(self, key_str: str):
        key_str = key_str.lower().strip()

        special = {
            "space": Key.space, "enter": Key.enter, "return": Key.enter,
            "tab": Key.tab, "esc": Key.esc, "escape": Key.esc,
            "backspace": Key.backspace, "delete": Key.delete,
            "up": Key.up, "down": Key.down, "left": Key.left, "right": Key.right,
            "shift": Key.shift, "ctrl": Key.ctrl, "alt": Key.alt,
            "cmd": Key.cmd, "win": Key.cmd,
        }
        for i in range(1, 13):
            special[f"f{i}"] = getattr(Key, f"f{i}")

        try:
            if key_str in special:
                self.keyboard.press(special[key_str])
                self.keyboard.release(special[key_str])
            elif len(key_str) == 1:
                self.keyboard.press(key_str)
                self.keyboard.release(key_str)
            else:
                self.keyboard.press(key_str)
                self.keyboard.release(key_str)
        except Exception as e:
            print(f"Could not press key '{key_str}': {e}")

    def click_mouse(self, button_str: str):
        button_map = {
            "left": Button.left,
            "right": Button.right,
            "middle": Button.middle
        }
        try:
            button = button_map.get(button_str)
            if button:
                self.mouse.click(button)
        except Exception as e:
            print(f"Could not click mouse '{button_str}': {e}")

    # ---------- Config persistence ----------
    def load_config(self):
        try:
            with open(CONFIG_FILE, "r") as f:
                data = json.load(f)
            self.sequence = data.get("sequence", [])
            self.repeat_interval = data.get("repeat_interval", DEFAULT_REPEAT_INTERVAL)
            self.hotkey = data.get("hotkey", DEFAULT_HOTKEY)
        except Exception:
            self.sequence = []
            self.repeat_interval = DEFAULT_REPEAT_INTERVAL
            self.hotkey = DEFAULT_HOTKEY

    def save_config(self):
        data = {
            "sequence": self.sequence,
            "repeat_interval": self.repeat_interval,
            "hotkey": self.hotkey_entry.get().strip() if hasattr(self, "hotkey_entry") else self.hotkey
        }
        try:
            with open(CONFIG_FILE, "w") as f:
                json.dump(data, f, indent=2)
        except Exception:
            pass

    def on_closing(self):
        self.running = False
        if self.hotkey_listener:
            self.hotkey_listener.stop()
        self.save_config()
        self.destroy()


if __name__ == "__main__":
    app = AutoKeyPresser()
    app.protocol("WM_DELETE_WINDOW", app.on_closing)
    app.mainloop()