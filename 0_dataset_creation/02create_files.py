#!/usr/bin/env python
# coding: utf-8

# # GitHub Vulnerability File Processor
# 
# This Jupyter notebook is designed to process vulnerability data from GitHub repositories. It fetches file contents before and after a commit to analyze the changes and their impact. The main steps include loading existing data, counting tokens in file content, fetching file content from GitHub, and processing each vulnerability to extract relevant information.
# 
# ## Prerequisites
# - Ensure you have a GitHub token environment variable set as `GITHUB_TOKEN`.
# - Install the necessary libraries using the provided `pip` install command.
# 
# ## Key Variables
# - `ANALYZE_EXTENSIONS`: List of file extensions to analyze.
# - `MAX_VULNERABILITY_FILES`: Threshold for the number of files to analyze to avoid commits with too many files.
# - `GITHUB_TOKEN`: Token for authenticating with GitHub API.
# 
# ## Functions
# - `load_existing_data`: Loads data from a CSV file.
# - `baseToString`: Decodes a base64 encoded string.
# - `getFileContent`: Fetches the content of a file from GitHub.
# - `process_vulnerability`: Processes each vulnerability to extract file changes.
# - `file_exists`: Checks if a file already exists in the processed data.
# 
# ## Steps
# 1. Load vulnerabilities data from a CSV file.
# 2. Load existing files data to determine the starting file ID.
# 3. Process vulnerabilities and save the results.
# 4. Filter and generate datasets for single file commits grouped by CWE ID.

# In[1]:


get_ipython().run_line_magic('pip', 'install requests pandas python-dotenv tqdm')


# In[2]:


import requests
import pandas as pd
import os
import base64
#from dotenv import load_dotenv
import json
from tqdm import tqdm
from pathlib import Path

# Load environment variables
#env_path = Path('..') / '.env'
#load_dotenv()


# In[3]:


ANALYZE_EXTENSIONS = ['php', 'tsx', 'ts', 'js', 'jsx', 'html', 'java', 'go', 'py', 'rb', 'c']
MAX_VULNERABILITY_FILES = 15 #threshold for number of files to analyze -> aims to avoid commits with too many files
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")


# In[4]:


def load_existing_data(file_name):
    try:
        return pd.read_csv(file_name)
    except FileNotFoundError:
        return pd.DataFrame()

def baseToString(encoded_data):
    decoded_data = base64.b64decode(encoded_data)
    decoded_array = decoded_data.decode('utf-8').split('\n')
    return decoded_array

# Function to get file content from GitHub
def getFileContent(repo, path, ref, raw=False):
    url = f"https://api.github.com/repos/{repo}/contents/{path}?ref={ref}"
    headers = {'Authorization': f'token {GITHUB_TOKEN}'}
    if raw:
        headers['Accept'] = 'application/vnd.github.raw+json'
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        return response.text if raw else baseToString(response.json()["content"])
    return None

# Function to process each vulnerability
def process_vulnerability(row, unique_id_start, existing_keys):
    patches = json.loads(row['files'])
    commit_id = row['commit']
    processed_files = []

    if len(patches) > MAX_VULNERABILITY_FILES:
        return processed_files, unique_id_start
    for patch in patches:
        filename = patch["filename"]
        ending = filename.split(".")[-1]
        if ending not in ANALYZE_EXTENSIONS:
            continue
        if file_exists(existing_keys, (row['vulnerability_id'], filename)):
            continue
        try:
            new_file = getFileContent(row['repo'], filename, commit_id, raw=True)
            old_file = getFileContent(row['repo'], filename, f"{commit_id}^", raw=True) if "status" in patch and patch["status"] == "modified" else None
            processed_files.append({
                'file_id': unique_id_start,
                'vulnerability_id': row['vulnerability_id'],
                "cwe_id": row["cwe_id"],
                "cve_id": row["cve_id"],
                'filename': filename,
                'file_before': old_file,
                'file_after': new_file,
                'patch': patch.get("patch"),
            })
            unique_id_start += 1
        except Exception as e:
            print(f"Error processing file {filename} in commit {commit_id}: {str(e)}")
    return processed_files, unique_id_start

def file_exists(existing_keys, key):
    return key in existing_keys


# # Fetch proper github file content

# In[5]:


# Load vulnerabilities data from CSV
input_csv = 'vulnerabilities.csv'
vulnerabilities = load_existing_data(input_csv)

# Load existing files data to determine the starting file_id
existing_files_csv = 'files.csv'
existing_files = load_existing_data(existing_files_csv)
if not existing_files.empty:
    last_file_id = existing_files['file_id'].max()
    unique_id_start = last_file_id + 1
    existing_keys = set(existing_files[['vulnerability_id', 'filename']].apply(tuple, axis=1))
else:
    unique_id_start = 1
    existing_keys = set()

# Process vulnerabilities and save results
all_processed_files = []
for index, row in tqdm(vulnerabilities.iterrows(), total=vulnerabilities.shape[0], desc="Processing vulnerabilities"):
    processed_files, unique_id_start = process_vulnerability(row, unique_id_start, existing_keys)
    all_processed_files.extend(processed_files)
# Convert to DataFrame and save to CSV
output_df = pd.DataFrame(all_processed_files)

# If the files.csv already exists, append to it; otherwise, create it
if not existing_files.empty:
    combined_df = pd.concat([existing_files, output_df], ignore_index=True)
else:
    combined_df = output_df

combined_df.to_csv(existing_files_csv, index=False)


# In[6]:


combined_df.head()


# # Create datasets for single file in commit CWE

# In[7]:


vuln_counts = combined_df['vulnerability_id'].value_counts()
single_occurrence_vulns = vuln_counts[vuln_counts == 1].index

filtered_df = combined_df[combined_df['vulnerability_id'].isin(single_occurrence_vulns)]

# filter out all files which have file_tokens under 18000 by openai tokenizer (artifical border)
#! attention: In previous gathering we used codellama tokenizer therefore there can be slightly differences in file_tokens and therefore in selected files
filtered_df = filtered_df[filtered_df['file_tokens'] <= 18000]

# Generate the 3 CSV files grouped by CWE_ID
for cwe_id, group_df in filtered_df.groupby('cwe_id'):
    output_csv = f'files_{cwe_id}.csv'
    group_df[['file_id', 'file_tokens', 'file_before', 'file_after', 'patch', 'cwe_id']].to_csv(output_csv, index=False)

print("CSV files created grouped by CWE_ID")

