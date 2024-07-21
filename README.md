This application generates question-answer pairs for training language models. It supports both Ollama and OpenAI APIs for content generation.

Features
Generate QA pairs on specified topics
Export datasets to JSON
Support for multiple AI models (Ollama and OpenAI)
User-friendly GUI
Installation
Clone the repository
Install dependencies: pip install -r requirements.txt
Run the application: python main.py
Usage Instructions
Starting the Application

Run the application by executing python main.py in your terminal from the project's root directory.
The main GUI window will open.
Configuring Settings

Click on the "Ollama Settings" or "OpenAI Settings" tab to configure API-specific settings.
For Ollama:
Set the API URL, model, temperature, and other parameters.
For OpenAI:
Ensure your OpenAI API key is set as an environment variable OPENAI_API_KEY.
Select the model, set temperature and max tokens.
Click "Save Settings" after making changes.
Generating QA Pairs

In the "Main" tab:
Enter the number of entries you want to generate.
Specify topics (comma-separated) for question generation.
Set the database path where the QA pairs will be stored.
Choose the API to use (Ollama or OpenAI) from the dropdown.
Click "Generate Dataset" to start the generation process.
The progress bar will show the status of generation.
You can stop the generation at any time by clicking "Stop Generation".
Exporting Dataset

After generation, you can export the dataset to a JSON file.
Set the JSON file path in the "JSON path" field.
Click "Export to JSON" to create the file.
Viewing Logs

The log output at the bottom of the window shows detailed information about the generation process.
Dark Mode

Toggle between light and dark themes using the "Dark Mode" option in the settings.
Error Handling

If any errors occur during generation or export, they will be displayed in the status bar and logged in the log output.
Note: Ensure you have the necessary API access and credentials set up before using the application. For OpenAI, make sure your API key is correctly set as an environment variable.

Contributing
Contributions are welcome! Please feel free to submit a Pull Request.
