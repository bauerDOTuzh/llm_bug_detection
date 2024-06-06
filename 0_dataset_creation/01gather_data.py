# %% [markdown]
# # GitHub Vulnerability Scraper
# 
# This Jupyter notebook is designed to scrape and process vulnerability data from the NIST National Vulnerability Database (NVD) and GitHub. It fetches CVE details and commit information to analyze vulnerabilities and their impact.
# 
# ## Prerequisites
# - Ensure you have a GitHub token saved in a `.env` file as `GITHUB_TOKEN`.
# - Install the necessary libraries using the provided `pip` install command.
# 
# ## Key Variables
# - `GITHUB_TOKEN`: Token for authenticating with GitHub API.
# - `BASE_URL`: Base URL for the NIST API.
# 
# ## Functions
# - `is_github`: Checks if a URL is a GitHub URL.
# - `url_type`: Determines the type of GitHub URL (commit, pull, etc.).
# - `call_api`: Calls the NIST API to fetch vulnerability data.
# - `get_commit_info`: Gets commit info from GitHub API.
# - `get_commit_info_from_url`: Extracts commit info from a GitHub URL.
# - `parse_github_commit_url`: Parses a GitHub commit URL.
# - `parse_vulnerability`: Parses vulnerability data to extract relevant information.
# - `scrape_between`: Scrapes data for a specific CWE ID between given dates.
# - `generate_monthly_ranges_pd`: Generates monthly date ranges for scraping.
# - `load_existing_data`: Loads existing data from a CSV file.
# 
# ## Steps
# 1. Define the start and end dates for scraping.
# 2. Define the CWE IDs to scrape.
# 3. Load existing data to avoid duplicate entries.
# 4. Scrape data for each CWE ID and save the results to a CSV file.

# %%
%pip install requests pandas python-dotenv --quiet

# %%
import requests
import pandas as pd
from datetime import datetime
import os
from dotenv import load_dotenv
import json
import time
from urllib.parse import urlparse
from pathlib import Path

# Load environment variables
env_path = Path('..') / '.env'
load_dotenv()

# GitHub token
GITHUB_TOKEN = os.environ.get('GITHUB_TOKEN')

# Define base URL for the NIST API
BASE_URL = "https://services.nvd.nist.gov/rest/json/cves/2.0"

# %% [markdown]
# ## Functions to execute call to NIST API

# %%
def is_github(url):
    return "github.com" in url

# Function to determine the type of URL: commit, pull, or none
def url_type(url):
    search = ["commit", "pull", 'issues', 'releases', 'security/advisories']
    for i in search:
        if i in url:
            return i
    return "none"

# Function to call the NIST API
def call_api(cwe_id, start_date, end_date):
    vulnerabilities = []
    start_index = 0
    results_per_page = 2000
    nr_fails = 0

    while True:
        params = {
            "cweId": cwe_id,
            "pubStartDate": start_date,
            "pubEndDate": end_date,
            "resultsPerPage": results_per_page,
            "startIndex": start_index
        }
        response = requests.get(BASE_URL, params=params)
        if response.status_code != 200:
            nr_fails += 1
            if nr_fails > 2:
                print(f"Failed to retrieve data after multiple attempts: {response.status_code} - {response.text}")
                break
            print(f"Failed to retrieve data: {response.status_code} - {response.text}")
            time.sleep(10)
            continue

        data = response.json()
        vulnerabilities.extend(data["vulnerabilities"])

        if start_index + results_per_page >= data["totalResults"]:
            break
        start_index += results_per_page

    return vulnerabilities

# %% [markdown]
# ## Functions to process GITHUB data

# %%
# Function to get commit info from GitHub API
def get_commit_info(owner, repo, commit_sha):
    url = f"https://api.github.com/repos/{owner}/{repo}/commits/{commit_sha}"
    headers = {
        'Authorization': f'bearer {GITHUB_TOKEN}'
    }
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    data = response.json()
    return {
        "nr_files_changed": len(data['files']),
        "commit": commit_sha,
        "parent_commit": data['parents'][0]['sha'],
        "repo": f"{owner}/{repo}",
        "files": data['files'],
    }

# Function to get commit info from URL
def get_commit_info_from_url(url):
    owner, repo, commit_sha = parse_github_commit_url(url)
    return get_commit_info(owner, repo, commit_sha)

# Function to parse GitHub commit URL
def parse_github_commit_url(url):
    parsed_url = urlparse(url)
    path_parts = parsed_url.path.split('/')
    if len(path_parts) >= 5 and path_parts[3] == "commit":
        owner = path_parts[1]
        repo = path_parts[2]
        commit_sha = path_parts[4]
        return owner, repo, commit_sha
    else:
        raise ValueError("Invalid GitHub commit URL.")

# %% [markdown]
# # Support Function to gather data

# %%
# Function to parse vulnerabilities and check for GitHub commits
def parse_vulnerability(vuln, cwe_id):
    cve = vuln['cve']
    cve_id = cve['id']
    published_date = cve.get('published', '')
    description = next((desc['value'] for desc in cve.get('descriptions', []) if desc['lang'] == "en"), None)
    references = cve.get('references', [])
    github_commits = [ref['url'] for ref in references if is_github(ref['url']) and url_type(ref['url']) == "commit"]

    if len(github_commits) != 1:
        return None

    commit_info = get_commit_info_from_url(github_commits[0])
    
    return {
        "nr_files_changed": commit_info['nr_files_changed'],
        "commit": commit_info['commit'],
        "parent_commit": commit_info['parent_commit'],
        "repo": commit_info['repo'],
        "files": json.dumps(commit_info['files']),
        'cve_id': cve_id,
        'cwe_id': cwe_id,
        'published_date': published_date,
        'description': description,
        'references': json.dumps(references),
        'github_commit': github_commits[0]
    }

# Function to scrape data between given dates for a specific CWE ID
def scrape_between(start_date: datetime, end_date: datetime, cwe_id: int) -> pd.DataFrame:
    date_ranges = generate_monthly_ranges_pd(start_date, end_date)
    all_vulnerabilities = []

    for start, end in date_ranges:
        vulnerabilities = call_api(cwe_id, start, end)
        print(f"Scraped {len(vulnerabilities)} vulnerabilities between {start} and {end}")
        for vuln in vulnerabilities:
            parsed_vuln = parse_vulnerability(vuln, cwe_id)
            if parsed_vuln:
                all_vulnerabilities.append(parsed_vuln)

    return pd.DataFrame(all_vulnerabilities)

# Function to generate monthly ranges
def generate_monthly_ranges_pd(start_date: datetime, end_date: datetime):
    start = pd.to_datetime(start_date)
    end = pd.to_datetime(end_date)
    ranges = []

    if start.month == end.month and start.year == end.year:
        ranges.append((start.strftime("%Y-%m-%dT00:00:00.000"), end.strftime("%Y-%m-%dT23:59:59.999")))
    else:
        months_start = pd.date_range(start=start, end=end, freq='MS')
        months_end = pd.date_range(start=start, end=end, freq='ME')
        if end > months_end[-1]:
            months_end = months_end[:-1].append(pd.Index([end]))
        elif end < months_end[-1]:
            months_end = months_end[:-1]
            months_end = months_end.append(pd.Index([end]))

        ranges = [(start.strftime("%Y-%m-%dT00:00:00.000"), end.strftime("%Y-%m-%dT23:59:59.999")) for start, end in zip(months_start, months_end)]

    return ranges

# Function to load existing CSV data
def load_existing_data(filepath):
    if os.path.exists(filepath):
        return pd.read_csv(filepath)
    else:
        return pd.DataFrame()


# %% [markdown]
# # Main Execution

# %% [markdown]
# - As for usage of this repository it is important to define start and end date
# - This enures smaller chunking of data as well as the code ensures that the data is not duplicated

# %%
# Define the start and end dates
start_date = datetime(2024, 1, 1)
end_date = datetime(2024, 1, 10)

# Define the CWE IDs
cwe_ids = ["CWE-89", "CWE-79", "CWE-22"]

# Define the existing file name
existing_file = 'vulnerabilities.csv'

# Function to load existing data
def load_existing_data(file_name):
    try:
        return pd.read_csv(file_name)
    except FileNotFoundError:
        return pd.DataFrame()

# Load existing data
existing_data = load_existing_data(existing_file)
existing_keys = set(existing_data[['cwe_id', 'cve_id']].apply(tuple, axis=1)) if not existing_data.empty else set()

# Determine the starting vulnerability ID
if not existing_data.empty:
    last_vulnerability_id = existing_data['vulnerability_id'].max()
else:
    last_vulnerability_id = 0

all_dataframes = []
new_entries = []

for cwe_id in cwe_ids:
    print(f"Scraping data for {cwe_id} between {start_date} and {end_date}")
    df = scrape_between(start_date, end_date, cwe_id)
    if not df.empty:
        df['vulnerability_id'] = range(last_vulnerability_id + 1, last_vulnerability_id + 1 + len(df))
        new_entries_df = df[~df[['cwe_id', 'cve_id']].apply(tuple, axis=1).isin(existing_keys)]
        new_entries.extend(new_entries_df.to_dict(orient='records'))
        all_dataframes.append(new_entries_df)
        last_vulnerability_id += len(df)

if all_dataframes:
    combined_new_df = pd.concat(all_dataframes, ignore_index=True)
    if not existing_data.empty:
        combined_df = pd.concat([existing_data, combined_new_df], ignore_index=True)
    else:
        combined_df = combined_new_df
    combined_df.to_csv(existing_file, index=False)
    print("Data saved to vulnerabilities.csv")
else:
    print("No new entries found.")

# %%
combined_df.head()


