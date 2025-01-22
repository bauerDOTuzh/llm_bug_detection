# %% [markdown]
# # Script Documentation
# 
# ## Overview
# This script automates the analysis of code files to identify security vulnerabilities related to specific Common Weakness Enumerations (CWEs). It uses advanced language models like GPT-4 from various endpoints and supports multi-threaded execution for efficiency.
# 
# ## Configuration
# Set the following variables in the script:
# - `ENDPOINT`: Choose between `OPENAI` or `ANYSCALE`.
# - `LLM_MODEL`: Select a model such as `GPT4`, `LLAMA3`, or `MIXTRAL8_22`.
# 
# ## Key Parameters
# - `CWES`: List of CWEs to analyze.
# - `ENDPOINT_TOKENS_LIMIT`: Max tokens for the endpoint.
# - `LENGTH_LIMIT`: Max file content length.
# - `WORKERS`: Number of worker threads.
# - `RESULTS_CSV_FOLDER`: Directory to save results.
# - `INPUT_CSV`: Path to the input CSV file with files to analyze.
# 
# ## Execution Workflow
# 1. **Load Existing Results**: Avoid reprocessing already analyzed files.
# 2. **Select Files**: Filter files based on specified CWEs and length.
# 3. **Initialize Workers**: Start multiple threads for processing files.
# 4. **Rate Limit Management**: Manage API token usage effectively.
# 5. **Save Results**: Store analysis results in CSV files.
# 
# ## Notes
# - Change models and root folder paths as necessary.
# - The script avoids redundant API calls by checking existing results first.
# 
# Simply adjust the variables and run the script to perform security analysis in a Jupyter notebook environment.

# %%
%pip install langchain-core pandas python-dotenv tiktoken openai tqdm

# %%
# Import required modules
from langchain_core.prompts import ChatPromptTemplate
import pandas as pd
import os
from dotenv import load_dotenv
import tiktoken
import openai
from tqdm import tqdm
from queue import Queue
import threading
import time
from threading import Lock
import enum
from pathlib import Path

# Load environment variables
env_path = Path('..') / '.env'
if env_path.exists():
    load_dotenv(dotenv_path=env_path)

OLLAMA_API_KEY = os.getenv('OLLAMA_API_KEY')
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
OLLAMA_ENDPOINT = os.getenv('OLLAMA_ENDPOINT')

# Check if the environment variables are loaded
if not all([OLLAMA_API_KEY, OPENAI_API_KEY, OLLAMA_ENDPOINT]):
    raise EnvironmentError("Some environment variables are missing")



# %%
class Models(enum.Enum):
    GPT3_5 = "gpt-3.5-turbo"
    GPT4 = "gpt-4-turbo"
    GPT4o = "gpt-4o"
    LLAMA3 = "llama3-70b-8192"
    MIXTRAL8_7 = "mixtral-8x7b-32768"
    MIXTRAL8_22 = 'mixtral-8x22b-65536'

ollama_names = {
    Models.LLAMA3.value: os.getenv('OLLAMA_llama3-70b_NAME'),
    Models.MIXTRAL8_7.value: os.getenv('OLLAMA_mixtral-8_7b_NAME'),
    Models.MIXTRAL8_22.value: os.getenv('OLLAMA_mixtral-8_22b_NAME'),
}

class Endpoints(enum.Enum):
    OLLAMA = "OLLAMA"
    OPENAI = "OPENAI"

# %%
# Configuration
# ENDPOINT = Endpoints.OPENAI
# LLM_MODEL = Models.GPT4

ENDPOINT = Endpoints.OLLAMA
LLM_MODEL = Models.MIXTRAL8_7 

CWES = ["CWE-22", "CWE-79", "CWE-89"]
ENDPOINT_TOKENS_LIMIT = 8000000
LENGTH_LIMIT = 250000 #maximal number of characters from files to execute
WORKERS = 100
RESULTS_CSV_FOLDER = "./runs/run5/inference"
INPUT_CSV = "./data_to_process/files.csv"

# %%
def load_existing_results():
    all_results = pd.DataFrame(columns=['file_id', 'model'])
    for model in Models:
        print(f"Loading results for {model.value}")  # Use the lock to safely
        model_csv_path = f"{RESULTS_CSV_FOLDER}/{model.value}.csv"
        if os.path.exists(model_csv_path):
            model_results = pd.read_csv(model_csv_path)
            all_results = pd.concat([all_results, model_results[['file_id', 'model']]], ignore_index=True)
    return all_results.drop_duplicates()

# Load existing results
existing_results = load_existing_results()

# Function to select files
def select_all_files(CWEs): 
    df = pd.read_csv(INPUT_CSV)
    df = df[(df['CWE_ID'].isin(CWEs))]
    # Apply length filter based on model
    length_limit = LENGTH_LIMIT
    df = df[df['target_length'] <= length_limit]
    
    return df

df_selected_files = select_all_files(CWES)

# Check if file exists in database
def file_exists(file_id, model):
    return not existing_results[(existing_results['file_id'] == file_id) & (existing_results['model'] == model)].empty

# Calculate number of tokens
def num_tokens_from_string(string: str, encoding_name='cl100k_base') -> int:
    encoding = tiktoken.get_encoding(encoding_name)
    return len(encoding.encode(string))

write_lock = threading.Lock()
# Save result to CSV
def save_result(file_id, prompt, response, model):
    model_csv_path = f"{RESULTS_CSV_FOLDER}/{model}.csv"
    os.makedirs(RESULTS_CSV_FOLDER, exist_ok=True)  # Ensure the directory exists
    with write_lock:  # Use the lock to safely write to the file
        result = pd.DataFrame([[file_id, prompt, response, model]], columns=['file_id', 'prompt', 'model_output', 'model'])
        result.to_csv(model_csv_path, mode='a', header=not os.path.exists(model_csv_path), index=False)

# %%
df_selected_files 

# %%
def get_model_response(prompt, data):
    prompt_whole = prompt.format(**data)
    if ENDPOINT == Endpoints.OLLAMA or ENDPOINT == Endpoints.OPENAI:
        client = openai.OpenAI(api_key=OPENAI_API_KEY)
        model = LLM_MODEL.value if LLM_MODEL in [Models.GPT3_5, Models.GPT4, Models.GPT4o] else None
        if not model:
            model = ollama_names.get(LLM_MODEL)
            if not model:
                raise ValueError(f"Model {LLM_MODEL} is not supported by anyscale")
            
            client = openai.OpenAI(base_url=OLLAMA_ENDPOINT, api_key=OLLAMA_API_KEY)
        resp = client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": prompt.format(**data)}],
            temperature=0,
            max_tokens=700
        )
        # print(resp)
        response = resp.model_dump()["choices"][0]["message"]["content"]
        return prompt_whole, response
    else:
        # throw error
        raise ValueError(f"Endpoint {ENDPOINT} is not supported")

# %%
def run_inference(file_content, cwe_id="79", github_repo=''):
    cwe_labels = {
        'CWE-79': 'Improper Neutralization of Input During Web Page Generation: Cross-Site Scripting',
        'CWE-89': "Improper Neutralization of Special Elements used in an SQL Command ('SQL Injection')",
        'CWE-22': 'Improper Limitation of a Pathname to a Restricted Directory ("Path Traversal")',
    }
    data = {'cwe_type': cwe_id, 'file_content': file_content, 'github_repo': github_repo, "cwe_label": cwe_labels[cwe_id]}
    prompt = '''Analyze the file content below and tell me if there's any line that may contain a bug of type {cwe_type} ({cwe_label}). Your output must adhere to the following structure.

Expected Output Structure:
SE: very Short Explanation of why the line may contain a bug of given type (e.g., The 'user_input' is directly concatenated into HTML content without sanitation).
BL: the Bugged Line, if any is found, else none (e.g., `response = "<html><body><h1>Welcome, " + user_input + "!</h1></body></html>"`).
BUG FOUND: YES if a bug is found, else NO.

Example output:
SE: The 'user_input' is directly concatenated into HTML content without sanitation.
BL: `response = "<html><body><h1>Welcome, " + user_input + "!</h1></body></html>"`
BUG FOUND: YES

File Content:
{file_content}
    '''
    return get_model_response(prompt, data)

# %% [markdown]
# ## Define workers

# %%
class TokenDecayLimiter:
    def __init__(self, max_tokens, rate_decay):
        self.max_tokens = max_tokens
        self.tokens = max_tokens
        self.rate_decay = rate_decay  # rate per second
        self.last_check = time.time()
        self.lock = Lock()

    def acquire(self, tokens_needed):
        with self.lock:
            current_time = time.time()
            elapsed_time = current_time - self.last_check
            self.tokens = min(self.max_tokens, self.tokens + int(elapsed_time * self.rate_decay))
            self.last_check = current_time
            if tokens_needed <= self.tokens:
                self.tokens -= tokens_needed
                return True
            return False

    def try_acquire(self, tokens_needed):
        while not self.acquire(tokens_needed):
            time.sleep(1)
        return True
            
    def release(self, tokens):
        with self.lock:
            self.tokens += tokens

# Worker function
def worker(limiter, pbar=None):
    while True:
        file = work_queue.get()
        if file is None:  # Stop signal
            work_queue.task_done()
            break
        if file_exists(file['file_id'], LLM_MODEL.value):
            if pbar:
                pbar.update(1)
            work_queue.task_done()
            continue
        tokens_needed = num_tokens_from_string(file['content']) + 205 #205 for prompt 
        if limiter.try_acquire(tokens_needed):
            try:
                prompt, response = run_inference(file['content'], file['CWE_ID'])
                save_result(file['file_id'], prompt, response, LLM_MODEL.value)
                if pbar:
                    pbar.update(1)
            except Exception as e:
                print(f"Thread {threading.current_thread().name}: Issues with file {file['file_id']}: {str(e)}")
            finally:
                work_queue.task_done()

# %% [markdown]
# ## Main Execution

# %%
# Main execution
work_queue = Queue()
for _, file in df_selected_files.iterrows():
    work_queue.put(file)

pbar = tqdm(total=df_selected_files.shape[0])
limiter = TokenDecayLimiter(ENDPOINT_TOKENS_LIMIT, ENDPOINT_TOKENS_LIMIT / 60)

# Start worker threads
threads = []
for _ in range(WORKERS):
    t = threading.Thread(target=worker, args=(limiter, pbar))
    t.start()
    threads.append(t)

# Wait for all tasks to be processed
for t in threads:
    work_queue.put(None)  # Signal to threads to stop

for t in threads:
    t.join()

# Ensure the progress bar is closed after all threads complete
pbar.close()
print("All files processed.")


