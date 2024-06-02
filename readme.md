

## How to Setup this Repository

### .env variables
1. Copy `.env.example` to `.env`.
2. Edit the `.env` file with the following API keys:
   - **GitHub**: Required for accessing GitHub repositories.
   - **OpenAI**: Needed for token counting and other AI functionalities.
   - **Anyscale**: Used for scalable processing tasks.
   - **Grok**: Not required but can be useful for testing some prompts.

*If you don't have an account with any of these providers, create one and follow the instructions on their respective websites to obtain your API token: [GitHub](https://github.com/), [OpenAI](https://openai.com/), [Anyscale](https://www.anyscale.com/), [Groq](https://groq.com/).*

### Python Environment using Conda
1. Create a new conda environment using the provided `environment.yml` file:
   ```bash
   conda env create -f environment.yml
   ```
2. Activate the environment:
   ```bash
    conda activate llm_bug_detection
    ```
  
## About this Repository

### Folder Structure: `./0_dataset_creation`

- **Purpose**: This folder contains the code to create the dataset for the task of bug detection in code.
- **Files**:
  - `01gather_data.ipynb`: Contains the code to gather data from the NIST database and save it.
  - `02create_files.ipynb`: Contains the code to create the files for the dataset via GitHub scraping.
- **Output**: The product of these two scripts are three CSV files containing single commit files of CWE-79, CWE-89, and CWE-22.

### Folder Structure: `./1_all_files_analysis`

This folder contains various scripts and data files for analyzing the dataset and evaluating different models for bug detection.

#### Key Files and Scripts

- **CSV Files**: 
  - `files_CWE-22.csv`, `files_CWE-79.csv`, `files_CWE-89.csv`: Contain the original data for each CWE.

- **Python Scripts**:
  - `get_bugline_from_gpt.py`: Calls all available models based on the input (model, desired CWE number).
  - `analyse_results.ipynb`: Concatenates all needed results and performs analysis on the data.

#### Data Folder

- **Data Folder**: `data`
  - Contains results across all models.

### Folder Structure: `./2_code_in_the_haystack`

This folder contains various scripts, data files, and analysis results for evaluating different models for bug detection and performing comprehensive analysis on the dataset.

#### Subfolders and Key Files

- **Subfolder: `runs`**
  - Contains all runs performed for each model.

- **Notebook: `create_files_with_padding.ipynb`**
  - Deploys an algorithm that creates files given source files, adding necessary padding.

- **Subfolder: `source_files`**
  - Contains 15 source files organized by programming languages.
  - Each file has an assigned ID and contains multiple versions:
    - **originalFile**: The original, unmodified file.
    - **originalBuggy**: The smallest buggy snippet identified (on the function level).
    - **smallestBuggy**: The smallest buggy file, refactored.
    - **modifiedFile**: The modified file without the bug. If the buggy function was extracted, it includes a refactored main function and added comments for clear separation.
    - **additional_padding**: A complete gathering of files to add for padding from the same repository, separated by function with clear separation comments.

- **Notebook: `analyse_data.ipynb`**
  - Gathers all important information across all models and visualizes the data through graphics.
  - Classifies the results to provide comprehensive insights.

- **Notebook: `run_inference.ipynb`**
  - Allows the user to define the model, provider, and desired output.
  - Runs the inference file based on the defined parameters.

#### Other Key Files

- `files.csv`: Main data file generated via the padding algorithm used for LLM calls.
