## How to setup this repository

copy .env.example to .env

additionallly you will need following api keys to edit in the .env file
1) Github
2) OpenAI
3) Anyscale
4) Grok (not needed but can be useful for testing of some prompts)


## About this repository
### Folder ./0_dataset_creation
- This folder contains the code to create the dataset for the task of bug detection in code.
- `./0_dataset_creation/01gather_data.ipynb` contains the code to gather the data from the nist database and save them
- `./0_dataset_creation/02create_files.ipynb` contains the code to create the files for the dataset -> gia github scraping
- Product of these 2 scripts are 3 csv files containing single commit files of CWE-79, CWE-89, and CWE-22



## last prompt:
```python
prompt = """Analyze the file content below and tell me if there's any line that may contain a bug of type CWE-{bug_type_id} ({bug_type_label}). Your output must adhere to the following structure.

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
"""
```