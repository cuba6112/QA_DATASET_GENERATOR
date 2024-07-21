import ttkbootstrap as ttk
import json
import os


class OpenAISettingsPage(ttk.Frame):
    def __init__(self, parent, *args, **kwargs):
        super().__init__(parent, *args, **kwargs)
        self.parent = parent
        self.settings = self.load_settings()
        self.create_widgets()

    def create_widgets(self):
        self.columnconfigure(1, weight=1)

        # Note about API Key
        ttk.Label(self, text="Note: OpenAI API Key is set via environment variable OPENAI_API_KEY",
                  wraplength=300).grid(row=0, column=0, columnspan=2, padx=5, pady=5, sticky="w")

        # Model Selection
        ttk.Label(self, text="Model:").grid(
            row=1, column=0, padx=5, pady=5, sticky="w")
        self.model_var = ttk.StringVar(
            value=self.settings.get("openai_model", "gpt-3.5-turbo"))
        self.model_combo = ttk.Combobox(self, textvariable=self.model_var, values=[
            "gpt-3.5-turbo",
            "gpt-4",
            "gpt-4-32k",
        ])
        self.model_combo.grid(row=1, column=1, padx=5, pady=5, sticky="ew")

        # Temperature
        ttk.Label(self, text="Temperature:").grid(
            row=2, column=0, padx=5, pady=5, sticky="w")
        self.temperature = ttk.Scale(
            self, from_=0.0, to=2.0, orient="horizontal", length=200)
        self.temperature.set(self.settings.get("openai_temperature", 0.7))
        self.temperature.grid(row=2, column=1, padx=5, pady=5, sticky="ew")
        self.temp_value = ttk.StringVar(value=f"{self.temperature.get():.2f}")
        ttk.Label(self, textvariable=self.temp_value, width=5).grid(
            row=2, column=2, padx=5, pady=5)
        self.temperature.config(command=self.update_temp_value)

        # Max Tokens
        ttk.Label(self, text="Max Tokens:").grid(
            row=3, column=0, padx=5, pady=5, sticky="w")
        self.max_tokens = ttk.Spinbox(self, from_=1, to=4096, width=5)
        self.max_tokens.set(self.settings.get("openai_max_tokens", 150))
        self.max_tokens.grid(row=3, column=1, padx=5, pady=5, sticky="w")

        # Save Button
        ttk.Button(self, text="Save Settings", command=self.save_settings,
                   style='success.TButton').grid(row=4, column=0, columnspan=3, padx=5, pady=20)

    def update_temp_value(self, event=None):
        self.temp_value.set(f"{self.temperature.get():.2f}")

    def load_settings(self):
        if os.path.exists("settings.json"):
            with open("settings.json", "r") as f:
                return json.load(f)
        return {}

    def save_settings(self):
        settings = {
            "openai_model": self.model_var.get(),
            "openai_temperature": float(self.temperature.get()),
            "openai_max_tokens": int(self.max_tokens.get()),
        }
        with open("settings.json", "r+") as f:
            existing_settings = json.load(f)
            existing_settings.update(settings)
            f.seek(0)
            json.dump(existing_settings, f, indent=4)
            f.truncate()
        self.parent.event_generate("<<SettingsUpdated>>")
