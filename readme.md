# Large Language Models for In-File Vulnerability Localization are "Lost in the End"

Welcome to the replication package for the ASE 2024 paper titled: Large Language Models for In-File Vulnerability Localization are "Lost in the End".

## Abstract

Researchers are increasingly investigating the use of Large language models (LLMs) for vulnerability detection. Traditionally, vulnerability detection has primarily targeted individual functions due to earlier language model technologies’ limitations in handling large inputs. This function-level focus is cost-effective, time-efficient, and reduces the noise from irrelevant data. However, this approach can be too simplistic, as vulnerabilities and their fixes often affect multiple functions and extend beyond a single code block. Hence, our study shifts the focus to in-file localization, evaluating the effectiveness of state-of-the-art LLMs in detecting vulnerabilities within an entire file (i.e., in-file) rather than limiting them to individual functions. Using a novel “code-in-the-haystack” methodology and considering XSS, SQL injection, and path traversal vulnerabilities, we investigate how the performance of these LLMs varies with the size of the input and the location of the vulnerability within files. Our findings confirm that LLMs have significant potential, yet their effectiveness in detecting vulnerabilities is highly influenced by both the location within the file and the overall size of the input they analyze. Specifically, we find that LLMs tend to underperform in detecting vulnerabilities towards the end of large files—a behavior we name “lost-in-the-end”. Additionally, we investigate how to identify the safest input size for a given LLM and vulnerability type, and show how adjusting the input size significantly improves vulnerability detection across all the considered models, with average increases in recall of 32% reaching up to 103%.

## How to Setup this Repository

### System Specifications

This repository is tested and recommended on:

- OS: Linux (Debian 5.10.179 or newer) and macOS (13.2.1 Ventura or newer)
- Python version: 3.11 or newer

### Installation of GitHub, OpenAI, and AnyScale Keys

TTo use this package, you must set up three environment variables: `GITHUB_TOKEN`, `ANYSCALE_API_KEY`, and `OPENAI_API_KEY`. These variables represent your personal access credentials for GitHub, Anyscale, and OpenAI respectively. By setting these environment variables, you ensure that your development environment can securely interact with these services without hardcoding sensitive information into your codebase. This approach enhances security and simplifies configuration management, making it easier to update credentials or share projects without exposing private keys.*

### Steps to Set Up

1. Copy `.env.example` to `.env`:
   ```bash
   cp .env.example .env
    ```
2. Open the `.env` file in your favorite text editor and replace the placeholder values with your actual credentials:
    ```bash
    GITHUB_TOKEN=your_github_token
    ANYSCALE_API_KEY=your_anyscale_api_key
    OPENAI_API_KEY=your_openai_api_key
    ```
Alternatively, you could set up the environment by directly setting environment variables. However, this setup is not suggested as you might need to persist your environment variables, which might interfere with your other projects. Additionally, you might need to modify scripts to avoid loading the initial setup.

*If you don't have an account with any of these providers, create one and follow the instructions on their respective websites to obtain your API token: [GitHub](https://github.com/), [OpenAI](https://openai.com/), [Anyscale](https://www.anyscale.com/).*

### Python Environment using Conda
1. Create a new conda environment using the provided `environment.yml` file:
   ```bash
   conda env create -f environment.yml
   ```
2. Activate the environment:
   ```bash
    conda activate infile_vulnerability_localization
    ```
  
## About this Repository

### Supported LLMs

All the following script are designed to run experiments for these LLMs:
- gpt-3.5-turbo
- gpt-4-turbo
- gpt-4o
- llama3-70b-8192
- mixtral-8x7b-32768
- mixtral-8x22b-65536

### Folder: `./0_dataset_creation`

- **Purpose**: This folder contains the code to extract the dataset for the task of bug detection in code.
- **Files**:
  - `01gather_data.py`: Contains the code to gather data from the NIST database and save it.
  - `02create_files.py`: Contains the code to create the files for the dataset via GitHub scraping.
- **Output**: The product of these two scripts are three CSV files containing single commit files of CWE-79, CWE-89, and CWE-22.

### Folder: `./1_all_files_analysis`

This folder contains various scripts and data files for analyzing the dataset and evaluating different models for bug detection.

#### Key Files and Scripts

- **Data Folder**: `cve_data`: 
  - `files_CWE-22.csv`, `files_CWE-79.csv`, `files_CWE-89.csv`: Contain the vulnerabilities (and their patches) we extracted for each CWE.

- **Python Scripts**:
  - `run_prompts.py`: Calls all available models based on the input (model, desired CWE number).
  - `analyse_results.py`: Concatenates all needed results and performs analysis on the data.
  - `count_functions.py`: Computes functions' statistics: number per file and average size.

#### Cached Model Outputs

- **Data Folder**: `model_outputs`
  - Contains results across all models.

### Folder: `./2_code_in_the_haystack`

This folder contains various scripts, data files, and analysis results for evaluating different models for bug detection and performing comprehensive analysis on the dataset.

#### Subfolders and Key Files

- **Subfolder: `runs`**
  - Contains all runs performed for each model.

- **Python Script: `create_files_with_padding.py`**
  - Deploys an algorithm that creates files given source files, adding necessary padding.

- **Subfolder: `source_files`**
  - Contains 15 source files organized by programming languages.
  - Each file has an assigned ID and contains multiple versions:
    - **originalFile**: The original, unmodified file.
    - **originalBuggy**: The smallest buggy snippet identified (on the function level).
    - **smallestBuggy**: The smallest buggy file, refactored.
    - **modifiedFile**: The modified file without the bug. If the buggy function was extracted, it includes a refactored main function and added comments for clear separation.
    - **additional_padding**: A complete gathering of files to add for padding from the same repository, separated by function with clear separation comments.

- **Python Script: `analyse_data.py`**
  - Gathers all important information across all models and visualizes the data through graphics.
  - Classifies the results to provide comprehensive insights.

- **Python Script: `run_inference.py`**
  - Allows the user to define the model, provider, and desired output.
  - Runs the inference file based on the defined parameters.

#### Other Key Files

- `data_to_process/files.csv`: Main data file generated via the padding algorithm used for LLM calls.

### Folder: `./3_optimal_position`

- **Purpose**: This folder contains the code to run the experiment of the third research question.
- **Script**:
  - `run_prompts.py`: It runs the prompts for all the CWE types once provided the model name as a parameter.