# RVTools Synthetic Data Generator

This script generates a synthetic RVTools export (a ZIP file containing multiple CSVs) that mimics the output of the popular RVTools utility used for VMware vSphere environment documentation. The generated data can be used for testing, development, demonstrations, or any scenario where realistic-looking VMware infrastructure data is needed without access to a live environment.

## Features

*   **Multiple CSV Generation**: Creates over 20 common CSV files found in an RVTools export (e.g., vInfo, vDisk, vNetwork, vHost, vCluster, vDatastore, etc.).
*   **Configurable Complexity**: Control the size and intricacy of the generated environment using complexity levels (`simple`, `medium`, `fancy`) or specific counts (e.g., number of VMs).
*   **Scenario-Based Generation**: Define specific environment layouts, naming conventions, and hardware/VM profiles using a YAML configuration file.
*   **AI-Assisted Data Generation**: Optionally leverage AI (OpenAI or local Ollama models via LangChain) to generate more realistic and context-aware data points for certain CSV types.
*   **Cross-CSV Consistency**: Data points (like VM names, host names, cluster names) are generally consistent across different CSV files.
*   **Customizable Output**: Specify output directory and ZIP filename.
*   **Basic GUI**: An optional Tkinter-based GUI provides an easy way to set common generation parameters.
*   **Threading for Performance**: Utilizes threading for parallel generation of independent CSV files to speed up the process.

## AI-Assisted Data Generation

This script can leverage Large Language Models (LLMs) via OpenAI or local Ollama instances to generate more realistic and context-aware data for certain aspects of the VMware environment. This is an optional feature.

For detailed setup instructions for using AI providers, please see [AI_CONFIGURATION.md](./AI_CONFIGURATION.md).

## Prerequisites

*   Python 3.7+
*   Required Python packages (install via `pip install -r requirements.txt` if a `requirements.txt` is provided, or install manually):
    *   `PyYAML` (for scenario file processing)
    *   `tqdm` (for progress bars)
    *   *(Optional for AI features)* `langchain`, `langchain-openai`, `langchain-community`
    *   *(Optional for GUI)* `tkinter` (usually included with Python, but ensure it's available)

## Usage

```bash
python rvtools_data_generator.py [OPTIONS]
```

**Common Options:**

*   `--num_vms <number>`: Number of VMs to generate (used if no scenario file or if scenario doesn't specify total).
*   `--complexity <simple|medium|fancy>`: Overall complexity of the generated environment. Default: `medium`.
*   `--config_file <path_to_scenario.yaml>`: Path to a YAML scenario configuration file to define the environment structure.
*   `--output_dir <directory>`: Directory to save the output ZIP file. Default: `RV_TOOL_ZIP_OUTPUT`.
*   `--zip_filename <filename_template>`: Filename template for the output ZIP. Default: `RVTools_export_{timestamp}.zip`.
*   `--use_ai`: Enable AI-assisted data generation.
*   `--ai_provider <mock|openai|ollama>`: Specify the AI provider. Default: `mock`.
*   `--ollama_model_name <model_name>`: Specify the Ollama model if using `ollama` provider. Default: `llama3`.
*   `--gui`: Launch the basic Tkinter GUI.
*   `--help`: Show the full list of options.

Refer to `AI_CONFIGURATION.md` for more details on setting up and using AI features.

## Development

(Placeholder for future development notes, contribution guidelines, etc.)

## License

(Placeholder for license information - e.g., MIT License)
```
