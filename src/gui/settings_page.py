import ttkbootstrap as ttk
from ttkbootstrap.constants import *
import json
import os


class SettingsPage(ttk.Frame):
    def __init__(self, parent, toggle_theme_callback, *args, **kwargs):
        super().__init__(parent, *args, **kwargs)
        self.parent = parent
        self.toggle_theme_callback = toggle_theme_callback
        self.settings = self.load_settings()
        self.create_widgets()

    def create_widgets(self):
        self.columnconfigure(1, weight=1)

        # Temperature
        ttk.Label(self, text="Temperature:").grid(
            row=0, column=0, padx=5, pady=5, sticky="w")
        self.temperature = ttk.Scale(
            self, from_=0.1, to=1.0, orient="horizontal", length=200)
        self.temperature.set(self.settings.get("temperature", 0.7))
        self.temperature.grid(row=0, column=1, padx=5, pady=5, sticky="ew")
        self.temp_value = ttk.StringVar(value=f"{self.temperature.get():.2f}")
        ttk.Label(self, textvariable=self.temp_value, width=5).grid(
            row=0, column=2, padx=5, pady=5)
        self.temperature.config(command=self.update_temp_value)

        # Top P
        ttk.Label(self, text="Top P:").grid(
            row=1, column=0, padx=5, pady=5, sticky="w")
        self.top_p = ttk.Scale(self, from_=0.1, to=1.0,
                               orient="horizontal", length=200)
        self.top_p.set(self.settings.get("top_p", 0.9))
        self.top_p.grid(row=1, column=1, padx=5, pady=5, sticky="ew")
        self.top_p_value = ttk.StringVar(value=f"{self.top_p.get():.2f}")
        ttk.Label(self, textvariable=self.top_p_value, width=5).grid(
            row=1, column=2, padx=5, pady=5)
        self.top_p.config(command=self.update_top_p_value)

        # Max Retries
        ttk.Label(self, text="Max Retries:").grid(
            row=2, column=0, padx=5, pady=5, sticky="w")
        self.max_retries = ttk.Spinbox(self, from_=1, to=10, width=5)
        self.max_retries.set(self.settings.get("max_retries", 3))
        self.max_retries.grid(row=2, column=1, padx=5, pady=5, sticky="w")

        # Timeout
        ttk.Label(self, text="Timeout (seconds):").grid(
            row=3, column=0, padx=5, pady=5, sticky="w")
        self.timeout = ttk.Spinbox(self, from_=5, to=60, width=5)
        self.timeout.set(self.settings.get("timeout", 30))
        self.timeout.grid(row=3, column=1, padx=5, pady=5, sticky="w")

        # Model Selection
        ttk.Label(self, text="Model:").grid(
            row=4, column=0, padx=5, pady=5, sticky="w")
        self.model_var = ttk.StringVar(
            value=self.settings.get("model", "llama3:latest"))
        self.model_combo = ttk.Combobox(self, textvariable=self.model_var, values=[
            "dolphin-llama3:latest",
            "gurubot/llama3-guru-uncensored:latest",
            "starcoder2:3b",
            "codellama:34b",
            "deepseek-coder-v2:latest",
            "llama3:latest"
        ])
        self.model_combo.grid(row=4, column=1, padx=5, pady=5, sticky="ew")

        # API URL
        ttk.Label(self, text="API URL:").grid(
            row=5, column=0, padx=5, pady=5, sticky="w")
        self.api_url_var = ttk.StringVar(value=self.settings.get(
            "api_url", "http://47.18.235.71:11434/api/generate"))
        self.api_url_entry = ttk.Entry(self, textvariable=self.api_url_var)
        self.api_url_entry.grid(row=5, column=1, padx=5, pady=5, sticky="ew")

        # Dark Mode Toggle
        ttk.Label(self, text="Dark Mode:").grid(
            row=6, column=0, padx=5, pady=5, sticky="w")
        self.dark_mode_var = ttk.BooleanVar(
            value=self.settings.get("dark_mode", False))
        self.dark_mode_toggle = ttk.Checkbutton(
            self, variable=self.dark_mode_var, command=self.toggle_theme, text="Enable Dark Mode")
        self.dark_mode_toggle.grid(row=6, column=1, padx=5, pady=5, sticky="w")

        # Save Button
        ttk.Button(self, text="Save Settings", command=self.save_settings,
                   style='success.TButton').grid(row=7, column=0, columnspan=3, padx=5, pady=20)

    def update_temp_value(self, event=None):
        self.temp_value.set(f"{self.temperature.get():.2f}")

    def update_top_p_value(self, event=None):
        self.top_p_value.set(f"{self.top_p.get():.2f}")

    def toggle_theme(self):
        self.toggle_theme_callback()

    def load_settings(self):
        if os.path.exists("settings.json"):
            with open("settings.json", "r") as f:
                return json.load(f)
        return {}

    def save_settings(self):
        settings = {
            "temperature": float(self.temperature.get()),
            "top_p": float(self.top_p.get()),
            "max_retries": int(self.max_retries.get()),
            "timeout": int(self.timeout.get()),
            "dark_mode": self.dark_mode_var.get(),
            "model": self.model_var.get(),
            "api_url": self.api_url_var.get()
        }
        with open("settings.json", "w") as f:
            json.dump(settings, f)
        self.parent.event_generate("<<SettingsUpdated>>")
