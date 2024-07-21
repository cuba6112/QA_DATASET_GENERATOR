import ttkbootstrap as ttk
from ttkbootstrap.scrolled import ScrolledText
from ttkbootstrap.dialogs import Messagebox
from ..utils.logging_config import QueueHandler
from ..data.database_operations import export_to_json
from ..data.dataset_creator import create_dataset
from .settings_page import SettingsPage
from .openai_settings_page import OpenAISettingsPage
import queue
import threading
import tkinter.filedialog as filedialog
import traceback
import psutil


class Application(ttk.Window):
    def __init__(self, logger):
        super().__init__(themename="litera")

        self.logger = logger
        self.title("QA Dataset Generator")
        self.geometry("900x700")

        self.log_queue = queue.Queue()
        self.queue_handler = QueueHandler(self.log_queue)
        self.logger.addHandler(self.queue_handler)

        self.stop_event = threading.Event()
        self.generate_thread = None

        self.notebook = ttk.Notebook(self)
        self.notebook.pack(expand=True, fill="both", padx=10, pady=10)

        self.main_page = ttk.Frame(self.notebook)
        self.settings_page = SettingsPage(self.notebook, self.toggle_theme)
        self.openai_settings_page = OpenAISettingsPage(self.notebook)

        self.notebook.add(self.main_page, text="Main")
        self.notebook.add(self.settings_page, text="Ollama Settings")
        self.notebook.add(self.openai_settings_page, text="OpenAI Settings")

        self.create_widgets()
        self.after(100, self.poll_log_queue)

        self.bind("<<SettingsUpdated>>", self.on_settings_updated)

        # Set up periodic memory check
        self.after(60000, self.check_memory_usage)  # Check every 60 seconds

        self.protocol("WM_DELETE_WINDOW", self.on_closing)

    def create_widgets(self):
        self.main_page.columnconfigure(1, weight=1)

        # Number of entries
        ttk.Label(self.main_page, text="Number of entries:").grid(
            row=0, column=0, padx=5, pady=5, sticky="w")
        self.num_entries = ttk.Entry(self.main_page)
        self.num_entries.grid(row=0, column=1, padx=5, pady=5, sticky="ew")
        self.num_entries.insert(0, "20")

        # Topics
        ttk.Label(self.main_page, text="Topics (comma-separated):").grid(row=1,
                                                                         column=0, padx=5, pady=5, sticky="w")
        self.topics = ttk.Entry(self.main_page)
        self.topics.grid(row=1, column=1, columnspan=2,
                         padx=5, pady=5, sticky="ew")
        self.topics.insert(0, "math,python,science")

        # Database path
        ttk.Label(self.main_page, text="Database path:").grid(
            row=2, column=0, padx=5, pady=5, sticky="w")
        self.db_path = ttk.Entry(self.main_page)
        self.db_path.grid(row=2, column=1, padx=5, pady=5, sticky="ew")
        self.db_path.insert(0, "qa_dataset.db")
        ttk.Button(self.main_page, text="Browse", command=self.browse_db,
                   style='Outline.TButton').grid(row=2, column=2, padx=5, pady=5)

        # JSON path
        ttk.Label(self.main_page, text="JSON path:").grid(
            row=3, column=0, padx=5, pady=5, sticky="w")
        self.json_path = ttk.Entry(self.main_page)
        self.json_path.grid(row=3, column=1, padx=5, pady=5, sticky="ew")
        self.json_path.insert(0, "qa_dataset.json")
        ttk.Button(self.main_page, text="Browse", command=self.browse_json,
                   style='Outline.TButton').grid(row=3, column=2, padx=5, pady=5)

        # API choice
        ttk.Label(self.main_page, text="API to use:").grid(
            row=4, column=0, padx=5, pady=5, sticky="w")
        self.api_var = ttk.StringVar(value="Ollama")
        self.api_dropdown = ttk.Combobox(
            self.main_page, textvariable=self.api_var, values=["Ollama", "OpenAI"])
        self.api_dropdown.grid(row=4, column=1, padx=5, pady=5, sticky="ew")

        # Generate and Stop buttons
        self.generate_button = ttk.Button(
            self.main_page, text="Generate Dataset", command=self.generate_dataset, style='success.TButton')
        self.generate_button.grid(
            row=5, column=0, columnspan=2, padx=5, pady=20, sticky="ew")

        self.stop_button = ttk.Button(self.main_page, text="Stop Generation",
                                      command=self.stop_generation, state="disabled", style='danger.TButton')
        self.stop_button.grid(row=5, column=2, padx=5, pady=20, sticky="ew")

        # Export button
        self.export_button = ttk.Button(
            self.main_page, text="Export to JSON", command=self.export_dataset, style='info.TButton')
        self.export_button.grid(
            row=6, column=0, columnspan=3, padx=5, pady=5, sticky="ew")

        # Progress bar
        self.progress_var = ttk.DoubleVar()
        self.progress_bar = ttk.Progressbar(
            self.main_page, orient="horizontal", length=600, mode="determinate", variable=self.progress_var)
        self.progress_bar.grid(
            row=7, column=0, columnspan=3, padx=5, pady=5, sticky="ew")

        # Status label
        self.status_var = ttk.StringVar()
        ttk.Label(self.main_page, textvariable=self.status_var).grid(
            row=8, column=0, columnspan=3, padx=5, pady=5, sticky="w")

        # Log output
        self.log_output = ScrolledText(self.main_page, height=10)
        self.log_output.grid(row=9, column=0, columnspan=3,
                             padx=5, pady=5, sticky="nsew")

        self.main_page.rowconfigure(9, weight=1)

    def toggle_theme(self):
        if self.style.theme_use() == 'litera':
            self.style.theme_use('darkly')
        else:
            self.style.theme_use('litera')

    def on_settings_updated(self, event):
        self.logger.info("Settings updated")

    def browse_db(self):
        file_path = filedialog.asksaveasfilename(defaultextension=".db", filetypes=[
                                                 ("SQLite Database", "*.db")])
        if file_path:
            self.db_path.delete(0, ttk.END)
            self.db_path.insert(0, file_path)

    def browse_json(self):
        file_path = filedialog.asksaveasfilename(
            defaultextension=".json", filetypes=[("JSON Files", "*.json")])
        if file_path:
            self.json_path.delete(0, ttk.END)
            self.json_path.insert(0, file_path)

    def generate_dataset(self):
        try:
            num_entries = int(self.num_entries.get())
            db_path = self.db_path.get()
            topics = [topic.strip() for topic in self.topics.get().split(",")]
            api_choice = self.api_var.get().lower()

            if not db_path or not topics:
                raise ValueError(
                    "Please provide valid database path and topics.")

            self.stop_event.clear()
            self.generate_button.config(state="disabled")
            self.stop_button.config(state="normal")

            self.progress_var.set(0)
            self.status_var.set("Generating dataset...")

            self.generate_thread = threading.Thread(
                target=self.generate_dataset_thread,
                args=(num_entries, db_path, topics, api_choice)
            )
            self.generate_thread.start()

        except ValueError as e:
            Messagebox.show_error(str(e), "Input Error")
        except Exception as e:
            self.logger.error(f"Error starting dataset generation: {str(e)}")
            Messagebox.show_error(f"An error occurred: {str(e)}", "Error")

    def generate_dataset_thread(self, num_entries, db_path, topics, api_choice):
        try:
            generated_count = create_dataset(
                num_entries, db_path, topics, self.update_progress, self.stop_event, api_choice
            )
            if self.stop_event.is_set():
                self.logger.info(
                    f"Generation stopped. Generated {generated_count} entries.")
                self.after(0, lambda: self.status_var.set(
                    f"Generation stopped. Generated {generated_count} entries."))
            else:
                self.logger.info(
                    f"Dataset generation complete! Generated {generated_count} entries.")
                self.after(0, lambda: self.status_var.set(
                    f"Dataset generation complete! Generated {generated_count} entries."))
        except Exception as e:
            self.logger.error(f"Error in dataset generation: {str(e)}")
            # Log the full stack trace
            self.logger.error(traceback.format_exc())
            self.after(0, lambda: self.status_var.set(f"Error: {str(e)}"))
        finally:
            self.after(0, self.reset_ui)

    def stop_generation(self):
        if self.generate_thread and self.generate_thread.is_alive():
            self.stop_event.set()
            self.status_var.set("Stopping generation...")
            self.stop_button.config(state="disabled")

    def reset_ui(self):
        self.generate_button.config(state="normal")
        self.stop_button.config(state="disabled")

    def export_dataset(self):
        try:
            db_path = self.db_path.get()
            json_path = self.json_path.get()

            if not db_path or not json_path:
                raise ValueError(
                    "Please provide valid database and JSON paths.")

            self.progress_var.set(0)
            self.status_var.set("Exporting dataset to JSON...")
            self.export_button.config(state="disabled")

            threading.Thread(target=self.export_dataset_thread,
                             args=(db_path, json_path)).start()

        except ValueError as e:
            Messagebox.show_error(str(e), "Input Error")
        except Exception as e:
            self.logger.error(f"Error starting dataset export: {str(e)}")
            Messagebox.show_error(f"An error occurred: {str(e)}", "Error")

    def export_dataset_thread(self, db_path, json_path):
        try:
            export_to_json(db_path, json_path, self.update_progress)
            self.logger.info("Export complete!")
            self.after(0, lambda: self.status_var.set("Export complete!"))
        except Exception as e:
            self.logger.error(f"Export error: {str(e)}")
            self.after(0, lambda: self.status_var.set(
                f"Export error: {str(e)}"))
        finally:
            self.after(0, lambda: self.export_button.config(state="normal"))

    def update_progress(self, current, total):
        progress = (current / total) * 100
        self.after(0, lambda: self.progress_var.set(progress))
        self.after(0, lambda: self.status_var.set(
            f"Processed {current}/{total} entries"))

    def poll_log_queue(self):
        while True:
            try:
                record = self.log_queue.get(block=False)
                self.log_output.insert(ttk.END, record + '\n')
                self.log_output.see(ttk.END)
            except queue.Empty:
                break
        self.after(100, self.poll_log_queue)

    def check_memory_usage(self):
        process = psutil.Process()
        memory_info = process.memory_info()

        # Log memory usage
        self.logger.info(
            f"Memory usage: {memory_info.rss / 1024 / 1024:.2f} MB")

        # If memory usage is too high, you might want to take action
        if memory_info.rss > 500 * 1024 * 1024:  # 500 MB
            self.logger.warning("High memory usage detected!")
            # You could display a warning to the user here

        # Schedule the next check
        self.after(60000, self.check_memory_usage)

    def on_closing(self):
        if self.generate_thread and self.generate_thread.is_alive():
            if Messagebox.yesno("Generation in progress", "Dataset generation is still in progress. Are you sure you want to quit?"):
                self.stop_event.set()
                # Wait for up to 5 seconds for the thread to finish
                self.generate_thread.join(timeout=5)
        self.destroy()
