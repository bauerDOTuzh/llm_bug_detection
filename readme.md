# Large Language Models for In-File Vulnerability Localization are "Lost in the End"

Welcome to the replication package for the ASE 2024 paper titled: Large Language Models for In-File Vulnerability Localization are "Lost in the End".

## Abstract

Researchers are increasingly investigating the use of Large language models (LLMs) for vulnerability detection. Traditionally, vulnerability detection has primarily targeted individual functions due to earlier language model technologies’ limitations in handling large inputs. This function-level focus is cost-effective, time-efficient, and reduces the noise from irrelevant data. However, this approach can be too simplistic, as vulnerabilities and their fixes often affect multiple functions and extend beyond a single code block. Hence, our study shifts the focus to in-file localization, evaluating the effectiveness of state-of-the-art LLMs in detecting vulnerabilities within an entire file (i.e., in-file) rather than limiting them to individual functions. Using a novel “code-in-the-haystack” methodology and considering XSS, SQL injection, and path traversal vulnerabilities, we investigate how the performance of these LLMs varies with the size of the input and the location of the vulnerability within files. Our findings confirm that LLMs have significant potential, yet their effectiveness in detecting vulnerabilities is highly influenced by both the location within the file and the overall size of the input they analyze. Specifically, we find that LLMs tend to underperform in detecting vulnerabilities towards the end of large files—a behavior we name “lost-in-the-end”. Additionally, we investigate how to identify the safest input size for a given LLM and vulnerability type, and show how adjusting the input size significantly improves vulnerability detection across all the considered models, with average increases in recall of 32% reaching up to 103%.

## How to Setup this Repository

### System Specifications

This repository is tested and recommended on:

- OS: Linux (Debian 5.10.179 or newer) and macOS (13.2.1 Ventura or newer)
- Python version: 3.8 or newer

### Installation of GitHub, OpenAI, and AnyScale Keys

To use this package, you must set up three environment variables: `GITHUB_TOKEN`, `ANYSCALE_API_KEY`, and `OPENAI_API_KEY`. These variables represent your personal access credentials for GitHub, Anyscale, and OpenAI respectively. By setting these environment variables, you ensure that your development environment can securely interact with these services without hardcoding sensitive information into your codebase. This approach enhances security and simplifies configuration management, making it easier to update credentials or share projects without exposing private keys.

On UNIX-like Operating Systems (Linux, MacOS):
1. Open your terminal.
2. To set the `ANYSCALE_API_KEY ` variable, run:
   ```bash
   export ANYSCALE_API_KEY ='your_anyscale_api_key'
   ```
3. To set the `OPENAI_API_KEY` variable, run:
   ```bash
   export OPENAI_API_KEY='your_api_key'
   ```
4. To set the `GITHUB_TOKEN ` variable, run:
   ```bash
   export GITHUB_TOKEN ='your_github_key'
   ```
5. These commands will set the environment variables for your current session. If you want to make them permanent, you can add the above lines to your shell profile (`~/.bashrc`, `~/.bash_profile`, `~/.zshrc`, etc.)

To ensure you've set up the environment variables correctly:

1. In your terminal or command prompt, run:
   ```bash
   echo $ANYSCALE_API_KEY
   ```
   This should display your AnyScale API key.
   
2. Similarly, verify the OpenAI API key:
   ```bash
   echo $OPENAI_API_KEY
   ```

3. To verify the GitHub API key:
   ```bash
   echo $GITHUB_TOKEN
   ```

Ensure that both values match what you've set.

*If you don't have an account with any of these providers, create one and follow the instructions on their respective websites to obtain your API token: [GitHub](https://github.com/), [OpenAI](https://openai.com/), [Anyscale](https://www.anyscale.com/).*

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
