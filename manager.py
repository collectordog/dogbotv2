import tkinter as tk
from tkinter import ttk, messagebox
import json
import os
import subprocess

COMMANDS_FILE = os.path.join(os.path.dirname(__file__), "commands.json")


def load_commands():
    if not os.path.exists(COMMANDS_FILE):
        return {}
    with open(COMMANDS_FILE, "r") as f:
        return json.load(f)


def save_commands(cmds):
    with open(COMMANDS_FILE, "w") as f:
        json.dump(cmds, f, indent=4)


class ManagerApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Discord Bot — Command Manager")
        self.resizable(False, False)
        self.configure(bg="#2b2d31")
        self._build_ui()
        self.refresh_list()

    def _build_ui(self):
        pad = {"padx": 10, "pady": 6}

        # --- Title ---
        tk.Label(
            self, text="Discord Bot Commands", bg="#2b2d31", fg="white",
            font=("Segoe UI", 14, "bold")
        ).grid(row=0, column=0, columnspan=3, pady=(14, 4))

        # --- Command list ---
        frame = tk.Frame(self, bg="#2b2d31")
        frame.grid(row=1, column=0, columnspan=3, padx=12, pady=6)

        self.listbox = tk.Listbox(
            frame, width=50, height=12, bg="#1e1f22", fg="white",
            selectbackground="#5865f2", font=("Consolas", 11),
            activestyle="none", relief="flat"
        )
        self.listbox.pack(side="left", fill="both")
        self.listbox.bind("<<ListboxSelect>>", self.on_select)

        scrollbar = ttk.Scrollbar(frame, orient="vertical", command=self.listbox.yview)
        scrollbar.pack(side="right", fill="y")
        self.listbox.config(yscrollcommand=scrollbar.set)

        # --- Input fields ---
        tk.Label(self, text="!command", bg="#2b2d31", fg="#b5bac1",
                 font=("Segoe UI", 10)).grid(row=2, column=0, **pad, sticky="w")
        tk.Label(self, text="Response", bg="#2b2d31", fg="#b5bac1",
                 font=("Segoe UI", 10)).grid(row=2, column=1, columnspan=2, **pad, sticky="w")

        self.cmd_var = tk.StringVar()
        self.resp_var = tk.StringVar()

        self.cmd_entry = tk.Entry(
            self, textvariable=self.cmd_var, width=16, bg="#1e1f22", fg="white",
            insertbackground="white", relief="flat", font=("Consolas", 11)
        )
        self.cmd_entry.grid(row=3, column=0, padx=(12, 4), pady=2, sticky="ew")

        self.resp_entry = tk.Entry(
            self, textvariable=self.resp_var, width=34, bg="#1e1f22", fg="white",
            insertbackground="white", relief="flat", font=("Consolas", 11)
        )
        self.resp_entry.grid(row=3, column=1, columnspan=2, padx=(4, 12), pady=2, sticky="ew")

        # --- Buttons ---
        btn_opts = {"font": ("Segoe UI", 10, "bold"), "relief": "flat", "cursor": "hand2", "pady": 6}

        btn_frame = tk.Frame(self, bg="#2b2d31")
        btn_frame.grid(row=4, column=0, columnspan=3, pady=10, padx=12, sticky="ew")

        tk.Button(
            btn_frame, text="Add / Update", bg="#5865f2", fg="white",
            command=self.add_or_update, **btn_opts
        ).pack(side="left", expand=True, fill="x", padx=(0, 4))

        tk.Button(
            btn_frame, text="Delete", bg="#ed4245", fg="white",
            command=self.delete_cmd, **btn_opts
        ).pack(side="left", expand=True, fill="x", padx=(4, 4))

        tk.Button(
            btn_frame, text="Clear", bg="#4f545c", fg="white",
            command=self.clear_fields, **btn_opts
        ).pack(side="left", expand=True, fill="x", padx=(4, 0))

        # --- Deploy button ---
        tk.Button(
            self, text="Save & Deploy to GitHub", bg="#3ba55d", fg="white",
            command=self.deploy, **btn_opts
        ).grid(row=5, column=0, columnspan=3, padx=12, pady=(0, 14), sticky="ew")

        self.status = tk.Label(self, text="", bg="#2b2d31", fg="#b5bac1",
                               font=("Segoe UI", 9))
        self.status.grid(row=6, column=0, columnspan=3, pady=(0, 8))

    def refresh_list(self):
        self.listbox.delete(0, "end")
        cmds = load_commands()
        for cmd, resp in cmds.items():
            self.listbox.insert("end", f"!{cmd:<20} {resp}")
        self._cmds_cache = cmds

    def on_select(self, _event=None):
        sel = self.listbox.curselection()
        if not sel:
            return
        idx = sel[0]
        cmd = list(self._cmds_cache.keys())[idx]
        self.cmd_var.set(cmd)
        self.resp_var.set(self._cmds_cache[cmd])

    def add_or_update(self):
        cmd = self.cmd_var.get().strip().lstrip("!").lower()
        resp = self.resp_var.get().strip()
        if not cmd or not resp:
            messagebox.showwarning("Missing input", "Fill in both the command and the response.")
            return
        cmds = load_commands()
        cmds[cmd] = resp
        save_commands(cmds)
        self.refresh_list()
        self.clear_fields()
        self.set_status(f'Saved "!{cmd}"')

    def delete_cmd(self):
        cmd = self.cmd_var.get().strip().lstrip("!").lower()
        if not cmd:
            messagebox.showwarning("No selection", "Select a command first.")
            return
        cmds = load_commands()
        if cmd not in cmds:
            messagebox.showwarning("Not found", f'Command "!{cmd}" does not exist.')
            return
        if not messagebox.askyesno("Confirm", f'Delete "!{cmd}"?'):
            return
        del cmds[cmd]
        save_commands(cmds)
        self.refresh_list()
        self.clear_fields()
        self.set_status(f'Deleted "!{cmd}"')

    def clear_fields(self):
        self.cmd_var.set("")
        self.resp_var.set("")
        self.listbox.selection_clear(0, "end")

    def deploy(self):
        repo_dir = os.path.dirname(__file__)
        try:
            subprocess.run(["git", "add", "commands.json"], cwd=repo_dir, check=True)
            result = subprocess.run(
                ["git", "diff", "--cached", "--quiet"], cwd=repo_dir
            )
            if result.returncode == 0:
                self.set_status("No changes to deploy.")
                return
            subprocess.run(
                ["git", "commit", "-m", "Update bot commands"],
                cwd=repo_dir, check=True
            )
            subprocess.run(["git", "push"], cwd=repo_dir, check=True)
            self.set_status("Deployed! Railway will redeploy automatically.")
        except subprocess.CalledProcessError as e:
            messagebox.showerror("Deploy failed", str(e))

    def set_status(self, msg):
        self.status.config(text=msg)
        self.after(4000, lambda: self.status.config(text=""))


if __name__ == "__main__":
    app = ManagerApp()
    app.mainloop()
