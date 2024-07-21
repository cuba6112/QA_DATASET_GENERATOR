import tkinter as tk
from tkinter import ttk, scrolledtext


class LabeledEntry(ttk.Frame):
    """A widget that combines a ttk.Label and ttk.Entry."""

    def __init__(self, master=None, label="", entry_width=30, **kwargs):
        super().__init__(master, **kwargs)
        self.label = ttk.Label(self, text=label)
        self.label.pack(side=tk.LEFT)
        self.entry = ttk.Entry(self, width=entry_width)
        self.entry.pack(side=tk.LEFT, expand=True, fill=tk.X)

    def get(self):
        return self.entry.get()

    def set(self, value):
        self.entry.delete(0, tk.END)
        self.entry.insert(0, str(value))


class ScrollableFrame(ttk.Frame):
    """A scrollable frame widget."""

    def __init__(self, master=None, **kwargs):
        super().__init__(master, **kwargs)

        self.canvas = tk.Canvas(self)
        self.scrollbar = ttk.Scrollbar(
            self, orient="vertical", command=self.canvas.yview)
        self.scrollable_frame = ttk.Frame(self.canvas)

        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: self.canvas.configure(
                scrollregion=self.canvas.bbox("all"))
        )

        self.canvas.create_window(
            (0, 0), window=self.scrollable_frame, anchor="nw")
        self.canvas.configure(yscrollcommand=self.scrollbar.set)

        self.canvas.pack(side="left", fill="both", expand=True)
        self.scrollbar.pack(side="right", fill="y")


class LoggingText(scrolledtext.ScrolledText):
    """A text widget that can be used for logging."""

    def __init__(self, master=None, **kwargs):
        super().__init__(master, **kwargs)
        self.configure(state='disabled')

    def log(self, message):
        self.configure(state='normal')
        self.insert(tk.END, message + '\n')
        self.see(tk.END)
        self.configure(state='disabled')


class ProgressFrame(ttk.Frame):
    """A frame containing a progress bar and a status label."""

    def __init__(self, master=None, **kwargs):
        super().__init__(master, **kwargs)

        self.progress_var = tk.DoubleVar()
        self.progress_bar = ttk.Progressbar(
            self,
            orient="horizontal",
            length=300,
            mode="determinate",
            variable=self.progress_var
        )
        self.progress_bar.pack(fill=tk.X, padx=5, pady=5)

        self.status_var = tk.StringVar()
        self.status_label = ttk.Label(self, textvariable=self.status_var)
        self.status_label.pack(fill=tk.X, padx=5)

    def update_progress(self, value):
        self.progress_var.set(value)

    def update_status(self, status):
        self.status_var.set(status)


class ControlFrame(ttk.Frame):
    """A frame containing control buttons for the application."""

    def __init__(self, master=None, **kwargs):
        super().__init__(master, **kwargs)

        self.generate_button = ttk.Button(self, text="Generate Dataset")
        self.generate_button.pack(side=tk.LEFT, padx=5)

        self.stop_button = ttk.Button(
            self, text="Stop Generation", state=tk.DISABLED)
        self.stop_button.pack(side=tk.LEFT, padx=5)

        self.export_button = ttk.Button(self, text="Export to JSON")
        self.export_button.pack(side=tk.LEFT, padx=5)

    def set_commands(self, generate_cmd, stop_cmd, export_cmd):
        self.generate_button.config(command=generate_cmd)
        self.stop_button.config(command=stop_cmd)
        self.export_button.config(command=export_cmd)

    def set_generate_state(self, state):
        self.generate_button.config(state=state)

    def set_stop_state(self, state):
        self.stop_button.config(state=state)

    def set_export_state(self, state):
        self.export_button.config(state=state)
