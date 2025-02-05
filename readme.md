# Large Language Models for In-File Vulnerability Localization are "Lost in the End"

Welcome to the replication package for the ASE 2024 paper titled: [Large Language Models for In-File Vulnerability Localization are "Lost in the End"](https://doi.org/10.1145/3715758).

**DOI:** [https://doi.org/10.1145/3715758](https://doi.org/10.1145/3715758)

## Table of Contents

1. [Abstract](#abstract)
2. [How to Setup this Repository](#how-to-setup-this-repository)
   - [System Specifications](#system-specifications)
   - [Installation of GitHub, OpenAI, and Ollama](#installation-of-github-openai-and-ollama)
   - [Steps to Set Up](#steps-to-set-up)
   - [Python Environment using Conda](#python-environment-using-conda)
   - [Jupyter Notebook Setup](#jupyter-notebook-setup)
3. [About this Repository](#about-this-repository)
   - [Supported LLMs](#supported-llms)
   - [Folder: `./0_dataset_creation`](#folder-0_dataset_creation)
   - [Folder: `./1_all_files_analysis`](#folder-1_all_files_analysis)
   - [Folder: `./2_code_in_the_haystack`](#folder-2_code_in_the_haystack)
   - [Folder: `./3_optimal_position`](#folder-3_optimal_position)
4. [Supplementary Information](#supplementary-information)
   - [RQ2: Statistical Analysis of Vulnerability Detection Performance](#rq2-statistical-analysis-of-vulnerability-detection-performance)

## Abstract

Researchers are increasingly investigating the use of Large language models (LLMs) for vulnerability detection. Traditionally, vulnerability detection has primarily targeted individual functions due to earlier language model technologies’ limitations in handling large inputs. This function-level focus is cost-effective, time-efficient, and reduces the noise from irrelevant data. However, this approach can be too simplistic, as vulnerabilities and their fixes often affect multiple functions and extend beyond a single code block. Hence, our study shifts the focus to in-file localization, evaluating the effectiveness of state-of-the-art LLMs in detecting vulnerabilities within an entire file (i.e., in-file) rather than limiting them to individual functions. Using a novel “code-in-the-haystack” methodology and considering XSS, SQL injection, and path traversal vulnerabilities, we investigate how the performance of these LLMs varies with the size of the input and the location of the vulnerability within files. Our findings confirm that LLMs have significant potential, yet their effectiveness in detecting vulnerabilities is highly influenced by both the location within the file and the overall size of the input they analyze. Specifically, we find that LLMs tend to underperform in detecting vulnerabilities towards the end of large files—a behavior we name “lost-in-the-end”. Additionally, we investigate how to identify the safest input size for a given LLM and vulnerability type, and show how adjusting the input size significantly improves vulnerability detection across all the considered models, with average increases in recall of 32% reaching up to 103%.

## How to Setup this Repository

### System Specifications

This repository is tested and recommended on:

- OS: Windows 11 (version 23H2, build 22631.3593), Linux (Debian 5.10.179 or newer) and macOS (13.2.1 Ventura or newer)
- Python version: 3.11 or newer

### Installation of GitHub, OpenAI and Ollama

To use this package, you must set up three environment variables: `GITHUB_TOKEN` and `OPENAI_API_KEY`. These variables represent your personal access credentials for GitHub and OpenAI. By setting these environment variables, you ensure that your development environment can securely interact with these services without hardcoding sensitive information into your codebase. This approach enhances security and simplifies configuration management, making it easier to update credentials or share projects without exposing private keys.

To use open-source models, you can use any API compatible with the OpenAI package. However, to minimize changes to your current setup, we recommend using **Ollama**. To install Ollama, follow the installation steps on their [official website](https://ollama.com/). 
If you prefer to use a different provider, you'll need to adjust environment variables—such as model aliases, endpoint configurations, and the API key—to match your chosen service.

### Steps to Set Up

1. Copy `.env.example` to `.env`:
   ```bash
   cp .env.example .env
    ```
2. Open the `.env` file in your favorite text editor and replace the placeholder values with your actual credentials:
    ```bash
    GITHUB_TOKEN=your_github_token
    OPENAI_API_KEY=your_openai_api_key
    ```
    
Alternatively, you could set up the environment by directly setting environment variables. However, this only works with a UNIX-like OS.

On UNIX-like Operating Systems (Linux, MacOS):
1. Open your terminal.
2. To set the `OPENAI_API_KEY` variable, run:
   ```bash
   export OPENAI_API_KEY='your_api_key'
   ```
3. To set the `GITHUB_TOKEN ` variable, run:
   ```bash
   export GITHUB_TOKEN ='your_github_key'
   ```
4. These commands will set the environment variables for your current session. If you want to make them permanent, you can add the above lines to your shell profile (`~/.bashrc`, `~/.bash_profile`, `~/.zshrc`, etc.)

To ensure you've set up the environment variables correctly:

1. In your terminal or command prompt, run:
   ```bash
   echo $OPENAI_API_KEY
   ```
   This should display your OpenAI API key.

*If you don't have an account with any of these providers, create one and follow the instructions on their respective websites to obtain your API token: [GitHub](https://github.com/), [OpenAI](https://openai.com/)*

### Python Environment using Conda
1. Create a new conda environment using the provided `environment.yml` file:
   ```bash
   conda env create -f environment.yml
   ```
2. Activate the environment:
   ```bash
    conda activate infile_vulnerability_localization
    ```
    
### Jupyter Notebook Setup

Many scripts in this repository are Jupyter Notebooks (`.ipynb` files). To install and set up Jupyter Notebook:

1. Install Jupyter Notebook within the conda environment:
   ```bash
   conda install -c conda-forge jupyterlab
   ```
2. Launch Jupyter Notebook:
   ```bash
   jupyter notebook
   ```
3. A new browser window should open with the Jupyter Notebook interface, allowing you to run and edit the `.ipynb` files.

To ensure Jupyter is correctly installed, you can check the version:
   ```bash
   jupyter --version
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
  - `01gather_data.ipynb`: Jupyter Notebook containing the code to gather data from the NIST database and save it.
  - `02create_files.ipynb`: Contains the code to create the files for the dataset via GitHub scraping.
- **Output**: The product of these two scripts are three CSV files containing single commit files of CWE-79, CWE-89, and CWE-22.

### Folder: `./1_all_files_analysis`

This folder contains various scripts and data files for analyzing the dataset and evaluating different models for bug detection.

#### Key Files and Scripts

- **Data Folder**: `cve_data`: 
  - `files_CWE-22.csv`, `files_CWE-79.csv`, `files_CWE-89.csv`: Contain the vulnerabilities (and their patches) we extracted for each CWE.

- **Python Scripts**:
  - `run_prompts.py`: Calls all available models based on the input (model, desired CWE number).
  - `analyse_results.ipynb`: Concatenates all needed results and performs analysis on the data.
  - `count_functions.py`: Computes functions' statistics: number per file and average size.

#### Cached Model Outputs

- **Data Folder**: `model_outputs`
  - Contains results across all models.

### Folder: `./2_code_in_the_haystack`

This folder contains various scripts, data files, and analysis results for evaluating different models for bug detection and performing comprehensive analysis on the dataset.

#### Subfolders and Key Files

- **Subfolder: `runs`**
  - Contains all runs performed for each model.

- **Python Script: `create_files_with_padding.ipynb`**
  - Deploys an algorithm that creates files given source files, adding necessary padding.

- **Subfolder: `source_files`**
  - Contains 15 source files organized by programming languages.
  - Each file has an assigned ID and contains multiple versions:
    - **originalFile**: The original, unmodified file.
    - **originalBuggy**: The smallest buggy snippet identified (on the function level).
    - **smallestBuggy**: The smallest buggy file, refactored.
    - **modifiedFile**: The modified file without the bug. If the buggy function was extracted, it includes a refactored main function and added comments for clear separation.
    - **additional_padding**: A complete gathering of files to add for padding from the same repository, separated by function with clear separation comments.

- **Python Script: `analyse_data.ipynb`**
  - Gathers all important information across all models and visualizes the data through graphics.
  - Classifies the results to provide comprehensive insights.

- **Python Script: `run_inference.ipynb`**
  - Allows the user to define the model, provider, and desired output.
  - Runs the inference file based on the defined parameters.

#### Other Key Files

- `data_to_process/files.csv`: Main data file generated via the padding algorithm used for LLM calls.

### Folder: `./3_optimal_position`

- **Purpose**: This folder contains the code to run the experiment of the third research question.
- **Script**:
  - `run_prompts.py`: It runs the prompts for all the CWE types once provided the model name as a parameter.

## Supplementary information 

Below, we provide the appendix of the paper, which comprises supplementary information that could not be included in the main paper due to page constraints.

### RQ2: Statistical Analysis of Vulnerability Detection Performance

We hereby follow APA guidelines to report the regression coefficients, 95% confidence intervals, effect sizes (i.e., odds ratios), and p-values for each model term (intercept and predictors). Additionally, we conclude with a paragraph interpreting the statistics in relation to the paper's claims, as recommended by APA guidelines.

Below are the tables with the regression results of Fig. 2 (see paper):

Model: mixtral-8x7b
| CWE    | Term                | B      | 95% CI             | p-value | Odds Ratio |
|--------|---------------------|--------|--------------------|---------|------------|
| CWE-22 | intercept           | 0.49   | [-0.21, 1.18]      | 0.173   | 1.632      |
|   ""   | file_len            | -0.13  | [-0.20, -0.05]     | 0.001   | 0.878      |
| CWE-22 | intercept           | 0.45   | [-0.16, 1.06]      | 0.144   | 1.568      |
|   ""   | bug_pos             | -0.52  | [-0.82, -0.21]     | 0.001   | 0.595      |
| CWE-89 | intercept           | 0.48   | [-0.10, 1.07]      | 0.106   | 1.616      |
|   ""   | file_len            | -0.14  | [-0.22, -0.07]     | 0.000   | 0.869      |
| CWE-89 | intercept           | 0.06   | [-0.43, 0.55]      | 0.809   | 1.062      |
|   ""   | bug_pos             | -0.28  | [-0.45, -0.10]     | 0.002   | 0.756      |
| CWE-79 | intercept           | -0.90  | [-1.22, -0.58]     | 0.000   | 0.407      |
|   ""   | file_len            | -0.06  | [-0.09, -0.03]     | 0.000   | 0.942      |
| CWE-79 | intercept           | -1.03  | [-1.31, -0.75]     | 0.000   | 0.357      |
|   ""   | bug_pos             | -0.14  | [-0.21, -0.07]     | 0.000   | 0.869      |

Model: mixtral-8x22b
| CWE    | Term       | B     | 95% CI           | p-value | Odds Ratio |
|--------|------------|-------|------------------|---------|------------|
| CWE-22 | intercept  | 0.65  | [0.03, 1.28]     | 0.041   | 1.915      |
|   ""   | file_len   | -0.07 | [-0.13, -0.02]   | 0.005   | 0.933      |
| CWE-22 | intercept  | 0.51  | [-0.01, 1.03]    | 0.056   | 1.665      |
|   ""   | bug_pos    | -0.20 | [-0.34, -0.07]   | 0.003   | 0.818      |
| CWE-89 | intercept  | 0.48  | [-0.00, 0.96]    | 0.052   | 1.617      |
|   ""   | file_len   | -0.07 | [-0.10, -0.03]   | 0.000   | 0.933      |
| CWE-89 | intercept  | 0.25  | [-0.17, 0.67]    | 0.239   | 1.284      |
|   ""   | bug_pos    | -0.13 | [-0.20, -0.05]   | 0.001   | 0.878      |
| CWE-79 | intercept  | -0.22 | [-0.54, 0.10]    | 0.176   | 0.802      |
|   ""   | file_len   | -0.10 | [-0.14, -0.07]   | 0.000   | 0.905      |
| CWE-79 | intercept  | -0.55 | [-0.81, -0.28]   | 0.000   | 0.577      |
|   ""   | bug_pos    | -0.20 | [-0.28, -0.12]   | 0.000   | 0.818      |

Model: llama-3-70b
| CWE    | Term                | B      | 95% CI             | p-value  | Odds Ratio |
|--------|---------------------|--------|--------------------|----------|------------|
| CWE-22 | intercept           | 0.57   | [-0.11, 1.24]      | 0.103    | 1.768      |
|   ""   | file_len            | -0.10  | [-0.17, -0.03]     | 0.004    | 0.905      |
| CWE-22 | intercept           | 0.09   | [-0.42, 0.60]      | 0.736    | 1.094      |
|   ""   | bug_pos             | -0.13  | [-0.26, -0.01]     | 0.039    | 0.878      |
| CWE-89 | intercept           | 0.52   | [0.00, 1.05]       | 0.050    | 1.681      |
|   ""   | file_len            | -0.07  | [-0.12, -0.02]     | 0.004    | 0.934      |
| CWE-89 | intercept           | 0.47   | [0.01, 0.92]       | 0.046    | 1.600      |
|   ""   | bug_pos             | -0.19  | [-0.31, -0.06]     | 0.003    | 0.827      |
| CWE-79 | intercept           | -0.45  | [-0.78, -0.11]     | 0.010    | 0.638      |
|   ""   | file_len            | -0.09  | [-0.13, -0.05]     | 0.000    | 0.914      |
| CWE-79 | intercept           | -0.79  | [-1.07, -0.52]     | 0.000    | 0.454      |
|   ""   | bug_pos             | -0.12  | [-0.19, -0.06]     | 0.000    | 0.888      |

Model: gpt-3.5-turbo
| CWE    | Term       | B     | 95% CI            | p-value | Odds Ratio |
|--------|------------|-------|-------------------|---------|------------|
| CWE-22 | intercept  | 0.13  | [-0.49, 0.74]     | 0.685   | 1.139      |
|   ""   | file_len   | -0.05 | [-0.10, -0.00]    | 0.044   | 0.951      |
| CWE-22 | intercept  | 0.06  | [-0.45, 0.57]     | 0.818   | 1.062      |
|   ""   | bug_pos    | -0.16 | [-0.29, -0.03]    | 0.017   | 0.852      |
| CWE-89 | intercept  | 0.84  | [0.32, 1.35]      | 0.001   | 2.320      |
|   ""   | file_len   | -0.09 | [-0.14, -0.05]    | 0.000   | 0.914      |
| CWE-89 | intercept  | 0.32  | [-0.09, 0.73]     | 0.131   | 1.378      |
|   ""   | bug_pos    | -0.11 | [-0.17, -0.04]    | 0.002   | 0.896      |
| CWE-79 | intercept  | -0.73 | [-1.06, -0.40]    | 0.000   | 0.482      |
|   ""   | file_len   | -0.08 | [-0.11, -0.04]    | 0.000   | 0.923      |
| CWE-79 | intercept  | -1.00 | [-1.28, -0.72]    | 0.000   | 0.368      |
|   ""   | bug_pos    | -0.13 | [-0.20, -0.06]    | 0.000   | 0.878      |

Model: gpt-4-turbo
| CWE    | Term                | B      | 95% CI             | p-value | Odds Ratio |
|--------|---------------------|--------|--------------------|---------|------------|
| CWE-22 | intercept           | 0.95   | [0.34, 1.56]       | 0.002   | 2.585      |
|   ""   | file_len            | -0.05  | [-0.09, -0.01]     | 0.021   | 0.951      |
| CWE-22 | intercept           | 1.01   | [0.46, 1.55]       | 0.000   | 2.749      |
|   ""   | bug_pos             | -0.18  | [-0.29, -0.06]     | 0.002   | 0.835      |
| CWE-89 | intercept           | 0.77   | [0.27, 1.27]       | 0.002   | 2.160      |
|   ""   | file_len            | -0.08  | [-0.12, -0.04]     | 0.000   | 0.923      |
| CWE-89 | intercept           | 0.56   | [0.13, 1.00]       | 0.011   | 1.752      |
|   ""   | bug_pos             | -0.18  | [-0.28, -0.08]     | 0.000   | 0.835      |
| CWE-79 | intercept           | -0.54  | [-0.83, -0.25]     | 0.000   | 0.583      |
|   ""   | file_len            | -0.06  | [-0.08, -0.03]     | 0.000   | 0.941      |
| CWE-79 | intercept           | -0.52  | [-0.79, -0.26]     | 0.000   | 0.594      |
|   ""   | bug_pos             | -0.19  | [-0.27, -0.12]     | 0.000   | 0.827      |

Model: gpt-4o
| CWE    | Term                | B      | 95% CI             | p-value | Odds Ratio |
|--------|---------------------|--------|--------------------|---------|------------|
| CWE-22 | intercept           | 0.83   | [0.23, 1.43]       | 0.007   | 2.294      |
|   ""   | file_len            | -0.05  | [-0.09, -0.01]     | 0.022   | 0.951      |
| CWE-22 | intercept           | 0.87   | [0.33, 1.40]       | 0.001   | 2.389      |
|   ""   | bug_pos             | -0.17  | [-0.29, -0.06]     | 0.003   | 0.844      |
| CWE-89 | intercept           | 0.92   | [0.42, 1.42]       | 0.000   | 2.510      |
|   ""   | file_len            | -0.07  | [-0.11, -0.04]     | 0.000   | 0.933      |
| CWE-89 | intercept           | 0.50   | [0.09, 0.91]       | 0.017   | 1.649      |
|   ""   | bug_pos             | -0.09  | [-0.15, -0.04]     | 0.001   | 0.914      |
| CWE-79 | intercept           | -0.22  | [-0.49, 0.06]      | 0.121   | 0.802      |
|   ""   | file_len            | -0.05  | [-0.07, -0.03]     | 0.000   | 0.951      |
| CWE-79 | intercept           | -0.20  | [-0.44, 0.05]      | 0.112   | 0.819      |
|   ""   | bug_pos             | -0.18  | [-0.24, -0.12]     | 0.000   | 0.835      |


Below are the tables with the regression results of Fig. 4:

Model: mixtral-8x7b
| CWE    | Term       | B      | 95% CI             | p-value | Odds Ratio |
|--------|------------|--------|--------------------|---------|-----------------|
| CWE-22 | intercept  | 0.04   | [-0.17, 0.25]      | 0.706   | 1.041           |
|   ""   | file_len   | -0.05  | [-0.06, -0.03]     | 0.000   | 0.951           |
| CWE-22 | intercept  | -0.19  | [-0.32, -0.05]     | 0.006   | 0.827           |
|   ""   | bug_pos    | -0.07  | [-0.08, -0.06]     | 0.000   | 0.933           |
| CWE-89 | intercept  | -0.66  | [-0.89, -0.43]     | 0.000   | 0.517           |
|   ""   | file_len   | -0.04  | [-0.05, -0.03]     | 0.000   | 0.961           |
| CWE-89 | intercept  | -0.80  | [-0.95, -0.65]     | 0.000   | 0.449           |
|   ""   | bug_pos    | -0.07  | [-0.08, -0.05]     | 0.000   | 0.933           |
| CWE-79 | intercept  | -0.34  | [-0.56, -0.13]     | 0.002   | 0.712           |
|   ""   | file_len   | -0.04  | [-0.05, -0.03]     | 0.000   | 0.961           |
| CWE-79 | intercept  | -0.87  | [-1.01, -0.73]     | 0.000   | 0.420           |
|   ""   | bug_pos    | -0.02  | [-0.03, -0.00]     | 0.015   | 0.980           |

Model: mixtral-8x22b
| CWE    | Term         | B      | 95% CI             | p-value | Odds Ratio |
|--------|--------------|--------|--------------------|---------|------------|
| CWE-22 | intercept    | 0.31   | [0.11, 0.52]       | 0.003   | 1.363      |
|   ""   | file_len     | -0.06  | [-0.07, -0.05]     | 0.000   | 0.942      |
| CWE-89 | intercept    | 0.01   | [-0.21, 0.23]      | 0.941   | 1.010      |
|   ""   | file_len     | -0.08  | [-0.09, -0.07]     | 0.000   | 0.923      |
| CWE-79 | intercept    | 0.14   | [-0.06, 0.35]      | 0.164   | 1.150      |
|   ""   | file_len     | -0.02  | [-0.03, -0.01]     | 0.001   | 0.980      |
| CWE-22 | intercept    | -0.28  | [-0.41, -0.15]     | 0.000   | 0.756      |
|   ""   | bug_pos      | -0.05  | [-0.07, -0.04]     | 0.000   | 0.951      |
| CWE-89 | intercept    | -0.12  | [-0.27, 0.03]      | 0.113   | 0.887      |
|   ""   | bug_pos      | -0.18  | [-0.20, -0.16]     | 0.000   | 0.835      |
| CWE-79 | intercept    | 0.13   | [0.01, 0.26]       | 0.042   | 1.139      |
|   ""   | bug_pos      | -0.04  | [-0.05, -0.02]     | 0.000   | 0.961      |

Model: llama-3-70b
| CWE    | Term       | B      | 95% CI             | p-value | Odds Ratio |
|--------|------------|--------|--------------------|---------|------------|
| CWE-22 | intercept  | 0.78   | [0.57, 0.99]       | 0.000   | 2.181      |
|   ""   | file_len   | -0.04  | [-0.05, -0.03]     | 0.000   | 0.961      |
| CWE-89 | intercept  | 0.20   | [-0.02, 0.43]      | 0.072   | 1.222      |
|   ""   | file_len   | -0.09  | [-0.11, -0.08]     | 0.000   | 0.914      |
| CWE-79 | intercept  | -0.16  | [-0.37, 0.05]      | 0.135   | 0.852      |
|   ""   | file_len   | -0.03  | [-0.04, -0.02]     | 0.000   | 0.971      |
| CWE-22 | intercept  | 0.29   | [0.16, 0.42]       | 0.000   | 1.336      |
|   ""   | bug_pos    | -0.03  | [-0.04, -0.02]     | 0.000   | 0.971      |
| CWE-89 | intercept  | -0.06  | [-0.21, 0.09]      | 0.440   | 0.941      |
|   ""   | bug_pos    | -0.20  | [-0.22, -0.17]     | 0.000   | 0.819      |
| CWE-79 | intercept  | -0.49  | [-0.62, -0.36]     | 0.000   | 0.612      |
|   ""   | bug_pos    | -0.02  | [-0.04, -0.01]     | 0.000   | 0.980      |

Model: gpt-3.5-turbo
| CWE    | Term      | B     | 95% CI           | p-value | Odds Ratio |
|--------|-----------|-------|------------------|---------|-------|
| CWE-22 | intercept | 0.51  | [0.31, 0.72]     | 0.000   | 1.665 |
| ""     | file_len  | -0.03 | [-0.04, -0.02]   | 0.000   | 0.970 |
| CWE-89 | intercept | -0.63 | [-0.88, -0.38]   | 0.000   | 0.533 |
| ""     | file_len  | -0.07 | [-0.08, -0.05]   | 0.000   | 0.932 |
| CWE-79 | intercept | -1.14 | [-1.39, -0.89]   | 0.000   | 0.320 |
| ""     | file_len  | -0.02 | [-0.03, -0.01]   | 0.002   | 0.980 |
| CWE-22 | intercept | -0.00 | [-0.13, 0.12]    | 0.963   | 1.000 |
| ""     | bug_pos   | -0.01 | [-0.02, -0.00]   | 0.033   | 0.990 |
| CWE-89 | intercept | -0.71 | [-0.88, -0.54]   | 0.000   | 0.492 |
| ""     | bug_pos   | -0.16 | [-0.19, -0.14]   | 0.000   | 0.852 |
| CWE-79 | intercept | -1.50 | [-1.66, -1.33]   | 0.000   | 0.223 |
| ""     | bug_pos   | -0.00 | [-0.02, 0.01]    | 0.897   | 1.000 |

Model: gpt-4-turbo
| CWE    | Term                | B      | 95% CI             | p-value  | Odds Ratio |
|--------|---------------------|--------|--------------------|----------|------------|
| CWE-22 | intercept           | 1.34   | [1.11, 1.56]       | 0.000    | 3.822      |
|   ""   | file_len            | -0.04  | [-0.06, -0.03]     | 0.000    | 0.961      |
| CWE-89 | intercept           | 0.42   | [0.21, 0.62]       | 0.000    | 1.522      |
|   ""   | file_len            | -0.05  | [-0.06, -0.04]     | 0.000    | 0.951      |
| CWE-79 | intercept           | 0.21   | [0.01, 0.42]       | 0.040    | 1.233      |
|   ""   | file_len            | -0.01  | [-0.02, 0.00]      | 0.086    | 0.990      |
| CWE-22 | intercept           | 1.14   | [1.01, 1.28]       | 0.000    | 3.128      |
|   ""   | bug_pos             | -0.07  | [-0.08, -0.06]     | 0.000    | 0.933      |
| CWE-89 | intercept           | 0.04   | [-0.09, 0.16]      | 0.595    | 1.041      |
|   ""   | bug_pos             | -0.07  | [-0.08, -0.05]     | 0.000    | 0.933      |
| CWE-79 | intercept           | 0.13   | [0.00, 0.25]       | 0.048    | 1.139      |
|   ""   | bug_pos             | -0.01  | [-0.02, 0.00]      | 0.123    | 0.990      |

Model: gpt-4o
| CWE    | Term                | B      | 95% CI             | p-value | Odds Ratio |
|--------|---------------------|--------|--------------------|---------|------------|
| CWE-22 | intercept           | 0.53   | [0.32, 0.75]       | 0.000   | 1.699      |
|   ""   | file_len            | -0.09  | [-0.11, -0.08]     | 0.000   | 0.914      |
| CWE-89 | intercept           | 0.94   | [0.73, 1.16]       | 0.000   | 2.563      |
|   ""   | file_len            | -0.11  | [-0.12, -0.10]     | 0.000   | 0.896      |
| CWE-79 | intercept           | 0.75   | [0.54, 0.96]       | 0.000   | 2.117      |
|   ""   | file_len            | -0.02  | [-0.03, -0.01]     | 0.000   | 0.980      |
| CWE-22 | intercept           | 0.42   | [0.27, 0.57]       | 0.000   | 1.521      |
|   ""   | bug_pos             | -0.23  | [-0.25, -0.20]     | 0.000   | 0.793      |
| CWE-89 | intercept           | 0.76   | [0.60, 0.91]       | 0.000   | 2.137      |
|   ""   | bug_pos             | -0.26  | [-0.28, -0.24]     | 0.000   | 0.771      |
| CWE-79 | intercept           | 0.61   | [0.48, 0.74]       | 0.000   | 1.840      |
|   ""   | bug_pos             | -0.03  | [-0.04, -0.01]     | 0.000   | 0.970      |

The results indicate a negative association between both bug position and file size with the probability of bug detection. For instance:
- The significant negative coefficients for bug_pos (e.g., -0.52 for CWE-22 in mixtral-8x7b) suggest that as the bug's position moves further within a file, the likelihood of detection decreases.
- Similarly, negative coefficients for file_len (e.g., -0.13 for CWE-22 in mixtral-8x7b) indicate that larger files are less likely to have their bugs detected.
- Bug position generally shows larger coefficients (in absolute terms) than file length. This suggests that bug position has a stronger effect on bug detection probability than file length.

Additionally, we also include the results of a *multiple logistic regression* (i.e., combining both predictors), which remain consistent with those obtained from *simple logistic regression* above.

### Processing CWE-22 with mixtral-8x7b
**Predictors:** `target_length`, `target_bug_position`
- **Regression term:** const, **Odds Ratio** = 1.05, **95% CI** [0.85, 1.29], **p** = 0.678
- **Regression term:** target_length, **Odds Ratio** = 0.98, **95% CI** [0.97, 0.99], **p** = 0.005
- **Regression term:** target_bug_position, **Odds Ratio** = 0.94, **95% CI** [0.93, 0.96], **p** = 0.000

### Processing CWE-89 with mixtral-8x7b
**Predictors:** `target_length`, `target_bug_position`
- **Regression term:** const, **Odds Ratio** = 0.52, **95% CI** [0.41, 0.66], **p** = 0.000
- **Regression term:** target_length, **Odds Ratio** = 0.99, **95% CI** [0.97, 1.00], **p** = 0.098
- **Regression term:** target_bug_position, **Odds Ratio** = 0.94, **95% CI** [0.92, 0.96], **p** = 0.000

### Processing CWE-79 with mixtral-8x7b
**Predictors:** `target_length`, `target_bug_position`
- **Regression term:** const, **Odds Ratio** = 0.71, **95% CI** [0.57, 0.88], **p** = 0.002
- **Regression term:** target_length, **Odds Ratio** = 0.96, **95% CI** [0.94, 0.97], **p** = 0.000
- **Regression term:** target_bug_position, **Odds Ratio** = 1.01, **95% CI** [1.00, 1.03], **p** = 0.174

### Processing CWE-22 with mixtral-8x22b
**Predictors:** `target_length`, `target_bug_position`
- **Regression term:** const, **Odds Ratio** = 1.36, **95% CI** [1.11, 1.68], **p** = 0.003
- **Regression term:** target_length, **Odds Ratio** = 0.95, **95% CI** [0.94, 0.97], **p** = 0.000
- **Regression term:** target_bug_position, **Odds Ratio** = 0.98, **95% CI** [0.96, 0.99], **p** = 0.003

### Processing CWE-89 with mixtral-8x22b
**Predictors:** `target_length`, `target_bug_position`
- **Regression term:** const, **Odds Ratio** = 1.16, **95% CI** [0.92, 1.45], **p** = 0.219
- **Regression term:** target_length, **Odds Ratio** = 0.98, **95% CI** [0.96, 0.99], **p** = 0.003
- **Regression term:** target_bug_position, **Odds Ratio** = 0.85, **95% CI** [0.83, 0.87], **p** = 0.000

### Processing CWE-79 with mixtral-8x22b
**Predictors:** `target_length`, `target_bug_position`
- **Regression term:** const, **Odds Ratio** = 1.15, **95% CI** [0.94, 1.41], **p** = 0.184
- **Regression term:** target_length, **Odds Ratio** = 1.00, **95% CI** [0.99, 1.01], **p** = 0.937
- **Regression term:** target_bug_position, **Odds Ratio** = 0.97, **95% CI** [0.95, 0.98], **p** = 0.000

### Processing CWE-22 with llama-3-70b
**Predictors:** `target_length`, `target_bug_position`
- **Regression term:** const, **Odds Ratio** = 2.17, **95% CI** [1.76, 2.67], **p** = 0.000
- **Regression term:** target_length, **Odds Ratio** = 0.96, **95% CI** [0.95, 0.98], **p** = 0.000
- **Regression term:** target_bug_position, **Odds Ratio** = 0.99, **95% CI** [0.98, 1.00], **p** = 0.137

### Processing CWE-89 with llama-3-70b
**Predictors:** `target_length`, `target_bug_position`
- **Regression term:** const, **Odds Ratio** = 1.44, **95% CI** [1.14, 1.81], **p** = 0.002
- **Regression term:** target_length, **Odds Ratio** = 0.97, **95% CI** [0.95, 0.98], **p** = 0.000
- **Regression term:** target_bug_position, **Odds Ratio** = 0.84, **95% CI** [0.82, 0.86], **p** = 0.000

### Processing CWE-79 with llama-3-70b
**Predictors:** `target_length`, `target_bug_position`
- **Regression term:** const, **Odds Ratio** = 0.85, **95% CI** [0.69, 1.05], **p** = 0.131
- **Regression term:** target_length, **Odds Ratio** = 0.97, **95% CI** [0.96, 0.99], **p** = 0.000
- **Regression term:** target_bug_position, **Odds Ratio** = 0.99, **95% CI** [0.98, 1.01], **p** = 0.373

### Processing CWE-22 with gpt-3.5-turbo
**Predictors:** `target_length`, `target_bug_position`
- **Regression term:** const, **Odds Ratio** = 1.67, **95% CI** [1.36, 2.05], **p** = 0.000
- **Regression term:** target_length, **Odds Ratio** = 0.96, **95% CI** [0.95, 0.97], **p** = 0.000
- **Regression term:** target_bug_position, **Odds Ratio** = 1.01, **95% CI** [1.00, 1.03], **p** = 0.092

### Processing CWE-89 with gpt-3.5-turbo
**Predictors:** `target_length`, `target_bug_position`
- **Regression term:** const, **Odds Ratio** = 0.59, **95% CI** [0.46, 0.77], **p** = 0.000
- **Regression term:** target_length, **Odds Ratio** = 0.98, **95% CI** [0.97, 1.00], **p** = 0.058
- **Regression term:** target_bug_position, **Odds Ratio** = 0.86, **95% CI** [0.83, 0.88], **p** = 0.000

### Processing CWE-79 with gpt-3.5-turbo
**Predictors:** `target_length`, `target_bug_position`
- **Regression term:** const, **Odds Ratio** = 0.32, **95% CI** [0.25, 0.41], **p** = 0.000
- **Regression term:** target_length, **Odds Ratio** = 0.97, **95% CI** [0.96, 0.99], **p** = 0.000
- **Regression term:** target_bug_position, **Odds Ratio** = 1.02, **95% CI** [1.00, 1.04], **p** = 0.059

### Processing CWE-22 with gpt-4o
**Predictors:** `target_length`, `target_bug_position`
- **Regression term:** const, **Odds Ratio** = 3.76, **95% CI** [2.99, 4.71], **p** = 0.000
- **Regression term:** target_length, **Odds Ratio** = 0.99, **95% CI** [0.97, 1.00], **p** = 0.047
- **Regression term:** target_bug_position, **Odds Ratio** = 0.94, **95% CI** [0.93, 0.95], **p** = 0.000

### Processing CWE-89 with gpt-4o
**Predictors:** `target_length`, `target_bug_position`
- **Regression term:** const, **Odds Ratio** = 1.52, **95% CI** [1.23, 1.86], **p** = 0.000
- **Regression term:** target_length, **Odds Ratio** = 0.97, **95% CI** [0.96, 0.98], **p** = 0.000
- **Regression term:** target_bug_position, **Odds Ratio** = 0.95, **95% CI** [0.94, 0.97], **p** = 0.000

### Processing CWE-79 with gpt-4o
**Predictors:** `target_length`, `target_bug_position`
- **Regression term:** const, **Odds Ratio** = 1.24, **95% CI** [1.01, 1.51], **p** = 0.041
- **Regression term:** target_length, **Odds Ratio** = 0.99, **95% CI** [0.98, 1.01], **p** = 0.297
- **Regression term:** target_bug_position, **Odds Ratio** = 1.00, **95% CI** [0.98, 1.01], **p** = 0.469

### Processing CWE-22 with gpt-4-turbo
**Predictors:** `target_length`, `target_bug_position`
- **Regression term:** const, **Odds Ratio** = 2.14, **95% CI** [1.70, 2.69], **p** = 0.000
- **Regression term:** target_length, **Odds Ratio** = 0.97, **95% CI** [0.96, 0.99], **p** = 0.000
- **Regression term:** target_bug_position, **Odds Ratio** = 0.81, **95% CI** [0.79, 0.83], **p** = 0.000

### Processing CWE-89 with gpt-4-turbo
**Predictors:** `target_length`, `target_bug_position`
- **Regression term:** const, **Odds Ratio** = 3.53, **95% CI** [2.79, 4.47], **p** = 0.000
- **Regression term:** target_length, **Odds Ratio** = 0.96, **95% CI** [0.95, 0.97], **p** = 0.000
- **Regression term:** target_bug_position, **Odds Ratio** = 0.79, **95% CI** [0.77, 0.81], **p** = 0.000

### Processing CWE-79 with gpt-4-turbo
**Predictors:** `target_length`, `target_bug_position`
- **Regression term:** const, **Odds Ratio** = 2.10, **95% CI** [1.70, 2.59], **p** = 0.000
- **Regression term:** target_length, **Odds Ratio** = 0.99, **95% CI** [0.98, 1.00], **p** = 0.127
- **Regression term:** target_bug_position, **Odds Ratio** = 0.98, **95% CI** [0.97, 0.99], **p** = 0.004



