# main.py

import threading
import tkinter as tk
from tkinter import ttk, filedialog, messagebox, simpledialog
from tkinter.scrolledtext import ScrolledText
from pathlib import Path
import webbrowser

from organizer_core import (
    safe_copy_folder, plan_moves, execute_plan, undo_last_actions,
    load_last_actions, load_last_actions as load_last, load_rules, human_size
)
import rules_manager

BASE = Path(__file__).parent.resolve()
LOGS_DIR = BASE / "logs"

# -------------------------
# Styling (light/dark mode)
# -------------------------
def apply_dark_theme(root):
    style = ttk.Style(root)
    # Use default theme then configure
    style.theme_use("clam")
    bg = "#2b2b2b"
    fg = "#eaeaea"
    accent = "#2aa198"
    style.configure(".", background=bg, foreground=fg, fieldbackground=bg)
    style.configure("TLabel", background=bg, foreground=fg)
    style.configure("TFrame", background=bg)
    style.configure("TButton", background=bg, foreground=fg)
    style.configure("TEntry", fieldbackground="#3a3a3a", foreground=fg)
    style.map("TButton",
              background=[("active", "#3c7fb1")])
    root.configure(background=bg)

def apply_light_theme(root):
    style = ttk.Style(root)
    style.theme_use("clam")
    bg = "#f0f0f0"
    fg = "#202020"
    accent = "#3a7bd5"
    style.configure(".", background=bg, foreground=fg, fieldbackground="#ffffff")
    style.configure("TLabel", background=bg, foreground=fg)
    style.configure("TFrame", background=bg)
    style.configure("TButton", background=bg, foreground=fg)
    style.configure("TEntry", fieldbackground="#ffffff", foreground=fg)
    style.map("TButton", background=[("active", "#b0c4de")])
    root.configure(background=bg)


# -------------------------
# App
# -------------------------
class App:
    def __init__(self, root):
        self.root = root
        root.title("Smart File Organizer v3.0")
        root.geometry("760x560")
        root.resizable(False, False)
        apply_dark_theme(root)

        self.selected_folder = tk.StringVar()
        self.mode = tk.StringVar(value="Type")
        self.theme = tk.StringVar(value="Dark")
        self._build_ui()
        # ensure rules file exists
        rules_manager.load_rules()

    def _build_ui(self):
        pad = {"padx": 12, "pady": 8}

        header = ttk.Label(self.root, text="Smart File Organizer", font=("Segoe UI", 18, "bold"))
        header.pack(pady=(10, 6))

        desc = ttk.Label(self.root, text="Select a folder and organize its safe copy by Type / Date / Size. Original folder is untouched.")
        desc.pack()
        # === Row 1: Folder + Browse (left)  |  Mode + Combo (right) ===

        row = ttk.Frame(self.root)
        row.pack(fill="x", pady=(10, 4), padx=12)

        # Left-side group
        left = ttk.Frame(row)
        left.pack(side="left")

        ttk.Label(left, text="Folder:").pack(side="left")
        self.entry = ttk.Entry(left, textvariable=self.selected_folder, width=70)
        self.entry.pack(side="left", padx=(8, 6))
        ttk.Button(left, text="Browse", command=self.browse).pack(side="left")

        # Right-side group
        right = ttk.Frame(row)
        right.pack(side="right")

        ttk.Label(right, text="Mode:").pack(side="left")
        combo = ttk.Combobox(right, textvariable=self.mode,
                             values=["Type", "Date", "Size"],
                             state="readonly", width=15)
        combo.pack(side="left", padx=(8, 0))


        # control buttons
        frame3 = ttk.Frame(self.root)
        frame3.pack(fill="x", pady=(6, 4), padx=12)

        # centered frame for ALL buttons
        btn_frame = ttk.Frame(frame3)
        btn_frame.pack(expand=True)
        spacing = 15 # spacing between buttons
        ttk.Button(btn_frame, text="Preview", command=self.preview).pack(side="left", padx=spacing)
        ttk.Button(btn_frame, text="Start (Safe Copy)", command=self.start).pack(side="left", padx=spacing)
        ttk.Button(btn_frame, text="Undo Last", command=self.undo).pack(side="left", padx=spacing)
        ttk.Button(btn_frame, text="Open Copy Folder", command=self.open_copy_folder).pack(side="left", padx=spacing)
        ttk.Button(btn_frame, text="Manage Rules", command=self.open_manage_rules).pack(side="left", padx=spacing)
        ttk.Button(btn_frame, text="Open Logs", command=self.open_logs).pack(side="left", padx=spacing)
        ttk.Button(btn_frame, text="theme", command=self.toggle_theme).pack(side="bottom", padx=spacing)
        # progress and label
        prog_frame = ttk.Frame(self.root)
        prog_frame.pack(fill="x", padx=12, pady=(10, 4))
        self.progress = ttk.Progressbar(prog_frame, orient="horizontal", length=580, mode="determinate")
        self.progress.pack(side="left")
        self.prog_label = ttk.Label(prog_frame, text="0 / 0")
        self.prog_label.pack(side="left", padx=(8, 0))

        # text area
        self.text = ScrolledText(self.root, height=18, wrap="word", bg="#1f1f1f", fg="#eaeaea")
        self.text.pack(fill="both", expand=True, padx=12, pady=(6, 12))
        self._write_intro()

        # status bar
        self.status = ttk.Label(self.root, text="Ready.", relief="sunken", anchor="w")
        self.status.pack(fill="x", padx=12, pady=(0, 12))

        # store reference to last created copy path
        self._last_copy = None

     
    def _write_intro(self):
        self.text.delete("1.0", "end")
        intro = (
            "Smart File Organizer v3.0\n\n"
            "Notes:\n"
            "- Start will create a safe copy of the selected folder named <orig>_Organized_Copy and organize that copy.\n"
            "- Original folder remains untouched.\n"
            "- Use Manage Rules to edit categories and extensions.\n\n"
            "Steps:\n1. Browse -> select folder\n2. (Optional) Manage Rules\n3. Preview -> to see planned moves\n4. Start (Safe Copy) -> performs operations on the copied folder\n5. Undo Last -> attempts to restore last operation\n\n"
        )
        self.text.insert("end", intro)

    def browse(self):
        folder = filedialog.askdirectory(title="Select folder to organize")
        if folder:
            self.selected_folder.set(folder)
            self.status.config(text=f"Selected: {folder}")
            self.text.insert("end", f"Selected: {folder}\n")
            self.text.see("end")
    
    def open_logs(self):
        if not LOGS_DIR.exists():
            messagebox.showinfo("Logs", "No logs directory found yet.")
            return
        try:
            webbrowser.open(LOGS_DIR.as_uri())
        except Exception:
            messagebox.showinfo("Logs Path", f"Logs path: {LOGS_DIR}")

    def open_copy_folder(self):
        if not self._last_copy:
            messagebox.showinfo("No Copy", "No copy created yet in this session.")
            return
        try:
            webbrowser.open(Path(self._last_copy).as_uri())
        except Exception:
            messagebox.showinfo("Copy Path", f"Copy path: {self._last_copy}")

    def preview(self):
        folder = self.selected_folder.get().strip()
        if not folder:
            messagebox.showwarning("Select folder", "Please select a folder first.")
            return
        folder = Path(folder)
        if not folder.exists() or not folder.is_dir():
            messagebox.showerror("Invalid", "Selected folder is invalid.")
            return
        # Plan moves on the actual folder (we preview what would happen inside the copy)
        plan = plan_moves(folder, self.mode.get())
        self.text.insert("end", f"Preview: Found {len(plan)} files to organize by {self.mode.get()}.\n")
        counts = {}
        total_size = 0
        for s, d in plan:
            counts.setdefault(d.parent.name, 0)
            counts[d.parent.name] += 1
            total_size += s.stat().st_size
        for k, v in counts.items():
            self.text.insert("end", f"  {k}: {v}\n")
        self.text.insert("end", f"Total size: {human_size(total_size)}\n\n")
        self.text.see("end")
        self.status.config(text=f"Preview ready: {len(plan)} files.")

    def start(self):
        folder = self.selected_folder.get().strip()
        if not folder:
            messagebox.showwarning("Select folder", "Please select a folder first.")
            return
        src = Path(folder)
        if not src.exists() or not src.is_dir():
            messagebox.showerror("Invalid", "Selected folder is invalid.")
            return
        if not messagebox.askyesno("Confirm", f"Create safe copy and organize by {self.mode.get()}?"):
            return
        # run in thread
        thread = threading.Thread(target=self._start_thread, args=(src, self.mode.get()), daemon=True)
        thread.start()

    def _start_thread(self, src: Path, mode: str):
        try:
            self._set_busy(True)
            self.status.config(text="Creating safe copy...")
            self.text.insert("end", f"Creating safe copy of {src}...\n")
            self.text.see("end")
            copy_path = safe_copy_folder(src)
            self._last_copy = str(copy_path)
            self.text.insert("end", f"Copy created at: {copy_path}\n")
            self.status.config(text="Planning moves on copy...")
            self.text.insert("end", f"Planning moves inside copy by {mode}...\n")
            self.text.see("end")
            plan = plan_moves(copy_path, mode)
            total = len(plan)
            if total == 0:
                self.text.insert("end", "No files to organize in copy. Nothing done.\n")
                self.status.config(text="No files to organize.")
                self._set_busy(False)
                return
            self.progress["maximum"] = total
            self.progress["value"] = 0
            self.prog_label.config(text=f"0 / {total}")

            def cb(done, tot):
                self.progress["value"] = done
                self.prog_label.config(text=f"{done} / {tot}")
                if done % 5 == 0 or done == tot:
                    self.root.update_idletasks()

            self.text.insert("end", f"Executing {total} moves inside copy...\n")
            self.text.see("end")
            performed = execute_plan(plan, progress_cb=cb)
            self.text.insert("end", f"Completed. Moved {len(performed)} files inside: {copy_path}\n")
            self.text.insert("end", f"Activity log: logs/activity.log\n")
            self.text.see("end")
            self.status.config(text=f"Organized {len(performed)} files (copy: {copy_path}).")
        except Exception as e:
            self.text.insert("end", f"Error: {e}\n")
            self.status.config(text="Error during start.")
        finally:
            self._set_busy(False)

    def undo(self):
        if not Path(BASE / "logs" / "last_actions.json").exists():
            messagebox.showinfo("Undo", "No recorded last operation to undo.")
            return
        if not messagebox.askyesno("Confirm Undo", "Attempt to restore last operation?"):
            return
        thread = threading.Thread(target=self._undo_thread, daemon=True)
        thread.start()

    def _undo_thread(self):
        try:
            self._set_busy(True)
            self.status.config(text="Undoing last operation...")
            self.text.insert("end", "Starting undo...\n")
            self.text.see("end")
            records = rules_manager  # small jitter to ensure module active
            # call undo
            restored = undo_last_actions(progress_cb=self._progress_cb)
            self.text.insert("end", f"Undo complete. Restored {restored} files.\n")
            self.status.config(text=f"Undo done. Restored {restored} files.")
            self.text.see("end")
        except Exception as e:
            self.text.insert("end", f"Undo error: {e}\n")
            self.status.config(text="Error during undo.")
        finally:
            self._set_busy(False)

    def _progress_cb(self, done, tot):
        self.progress["value"] = done
        self.prog_label.config(text=f"{done} / {tot}")
        if done % 5 == 0 or done == tot:
            self.root.update_idletasks()

    def _set_busy(self, busy=True):
        state = "disabled" if busy else "normal"
        # disable input controls
        try:
            for w in [self.entry]:
                w.config(state=state)
            for child in self.root.winfo_children():
                for sub in child.winfo_children():
                    if isinstance(sub, ttk.Button) or isinstance(sub, ttk.Combobox):
                        try:
                            sub.config(state=state)
                        except Exception:
                            pass
            self.root.config(cursor="watch" if busy else "")
        except Exception:
            pass
    def toggle_theme(self):
        if self.theme.get() == "Dark":
            apply_light_theme(self.root)
            self.theme.set("Light")
        else:
            apply_dark_theme(self.root)
            self.theme.set("Dark")
    # -------------------------
    # Manage Rules Window
    # -------------------------
    def open_manage_rules(self):
        ManageRulesWindow(self)

# -------------------------
# Manage Rules Window Class
# -------------------------
class ManageRulesWindow:
    def __init__(self, parent_app: App):
        self.parent = parent_app
        self.win = tk.Toplevel(parent_app.root)
        self.win.title("Manage Rules")
        self.win.geometry("600x420")
        self.win.resizable(False, False)
        apply_dark_theme(self.win)
        # load rules
        self.rules = rules_manager.load_rules()
        self._build()

    def _build(self):
        top = ttk.Frame(self.win)
        top.pack(fill="both", expand=True, padx=12, pady=12)

        left = ttk.Frame(top)
        left.pack(side="left", fill="y", padx=(0,12))

        ttk.Label(left, text="Categories:").pack(anchor="w")
        self.lst = tk.Listbox(left, height=18, width=28, bg="#1f1f1f", fg="#eaeaea")
        self.lst.pack(fill="y")
        for k in sorted(self.rules.keys()):
            self.lst.insert("end", k)
        self.lst.bind("<<ListboxSelect>>", self.on_select)

        mid = ttk.Frame(top)
        mid.pack(side="left", fill="both", expand=True)

        ttk.Label(mid, text="Extensions (comma separated):").pack(anchor="w")
        self.ext_entry = ttk.Entry(mid, width=50)
        self.ext_entry.pack(pady=(6,12))
        ttk.Button(mid, text="Add / Update Category", command=self.add_update).pack(anchor="w")
        ttk.Button(mid, text="Delete Category", command=self.delete_category).pack(anchor="w", pady=(6,0))

        bottom = ttk.Frame(self.win)
        bottom.pack(fill="x", padx=12, pady=(0,12))
        ttk.Button(bottom, text="Save & Apply", command=self.save_apply).pack(side="left")
        ttk.Button(bottom, text="Close", command=self.win.destroy).pack(side="right")

        # preselect first
        if self.lst.size() > 0:
            self.lst.selection_set(0)
            self.on_select()

    def on_select(self, evt=None):
        sel = self.lst.curselection()
        if not sel:
            self.ext_entry.delete(0, "end")
            return
        key = self.lst.get(sel[0])
        exts = self.rules.get(key, [])
        self.ext_entry.delete(0, "end")
        self.ext_entry.insert(0, ", ".join(exts))

    def add_update(self):
        sel = self.lst.curselection()
        if sel:
            key = self.lst.get(sel[0])
        else:
            key = simpledialog.askstring("New Category", "Enter new category name:", parent=self.win)
            if not key:
                return
        exts_raw = self.ext_entry.get().strip()
        exts = [e.strip().lower() for e in exts_raw.split(",") if e.strip()]
        # normalize
        exts_norm = []
        for e in exts:
            if not e.startswith("."):
                e = "." + e
            exts_norm.append(e)
        self.rules[key.strip()] = sorted(list(set(exts_norm)))
        # refresh listbox if new
        if sel:
            # keep selection
            pass
        else:
            self.lst.insert("end", key.strip())
        self.text_feedback(f"Added/Updated {key.strip()}")

    def delete_category(self):
        sel = self.lst.curselection()
        if not sel:
            messagebox.showinfo("Delete", "Select a category to delete.")
            return
        key = self.lst.get(sel[0])
        if messagebox.askyesno("Confirm", f"Delete category '{key}'?"):
            self.rules.pop(key, None)
            self.lst.delete(sel[0])
            self.ext_entry.delete(0, "end")
            self.text_feedback(f"Deleted {key}")

    def save_apply(self):
        rules_manager.save_rules(self.rules)
        self.text_feedback("Saved rules to config/rules.json")
        # close and notify parent that rules changed
        messagebox.showinfo("Saved", "Rules saved. They will be used in next operations.")
        self.win.destroy()

    def text_feedback(self, msg):
        self.parent.text.insert("end", f"[Rules] {msg}\n")
        self.parent.text.see("end")

# -------------------------
# Run app
# -------------------------
def main():
    root = tk.Tk()
    app = App(root)
    root.mainloop()

if __name__ == "__main__":
    main()
