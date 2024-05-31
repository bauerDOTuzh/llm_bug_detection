import os
import csv
import openai
import pickle
from tqdm import tqdm
import time
import re
import multiprocessing
from more_itertools import unique_everseen
import concurrent.futures
import sys
import pandas as pd
import json
from collections import defaultdict
from scipy.stats import spearmanr
import statsmodels.api as sm
import matplotlib.pyplot as plt
import numpy as np
import sys
import ast

model = sys.argv[1]
cwe_id = sys.argv[2]
bug_window_size = int(sys.argv[3])

only_check_removed_lines_in_patch = False
only_provide_bug_window = True
# bug_window_size = 6500 # characters

n_processes = multiprocessing.cpu_count()*20
openai_api_key = "..."
temperature = 0
file_path = f'../../1_all_files_analysis/files_CWE-{cwe_id}.csv'

# source_variable = 'Bug Line' # 'Input Length'
# target_variable = 'TP'

cwe_id_label_dict = {
	'22': 'Improper Limitation of a Pathname to a Restricted Directory: Path Traversal',
	'79': 'Improper Neutralization of Input During Web Page Generation: Cross-site Scripting',
	'89': 'Improper Neutralization of Special Elements used in an SQL Command: SQL Injection',
}
########################################################
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
########################################################
# prompt = """Analyze the file content below and tell me if there's any line that may contain a bug of type CWE-{bug_type_id} ({bug_type_label}). Your output must adhere to the following structure.

# Expected Output Structure:
# SE: Short Explanation of why the line may contain a bug of type CWE-{bug_type_id} (e.g., The 'user_input' is directly concatenated into HTML content without sanitation).
# BL: the Bugged Line, if any is found, else none (e.g., `response = "<html><body><h1>Welcome, " + user_input + "!</h1></body></html>"`).

# File Content:
# {file_content}
# """
########################################################
# prompt = """"Analyze the file content below and tell me if there's any line which may contain a bug of type CWE-{bug_type_id} ({bug_type_label}). Your output must adhere to the following structure.

# Expected Output:
# SE: very Short Explanation of why the line may contain a bug of type CWE-{bug_type_id}.
# BL: the Bugged Line, if any is found, else none.

# File Content:
# {file_content}
# """
########################################################
# prompt = """Analyze the file content provided below and determine if there's any line that might contain a bug of type CWE-{bug_type_id} ({bug_type_label}). Your output must adhere to the following structure.

# Example:
# def create_response(user_input):
# 	response = "<html><body><h1>Welcome, " + user_input + "!</h1></body></html>"
# 	return response

# Expected Output Structure:
# SE: The 'user_input' is directly concatenated into HTML content without sanitation, potentially allowing script injection.
# BL: response = "<html><body><h1>Welcome, " + user_input + "!</h1></body></html>"

# File Content:
# {file_content}
# """
########################################################

def get_removed_lines(patch):
	# Extract lines starting with -
	removed_lines = re.findall(r'^-.*$', patch, re.MULTILINE)
	# Remove the leading - character from each line
	return [line[1:] for line in removed_lines]

chatgpt_client = openai.OpenAI(api_key=openai_api_key)

bug_line_pattern = re.compile(r'(Bugged\s*)?[ -]*(Line|BL)\s*[:#]\s*(.*?)(?=BUG FOUND:)', re.IGNORECASE | re.DOTALL)
bug_line_pattern_simple = re.compile(r'(Bugged)?[ -]*(Line|BL) *[:#]', re.IGNORECASE)

data = pd.read_csv(file_path)

id_list = data['file_id'].tolist()
patch_list = data['patch'].tolist()
buggy_content_list = list(map('\n'.join, map(ast.literal_eval, data['file_before'].tolist())))
correct_content_list = list(map('\n'.join, map(ast.literal_eval, data['file_after'].tolist())))
patch_line_regexp = r'@@ -(\d+,\d+) \+(\d+,\d+) @@' # Regular expression pattern to match line numbers in the diff
patch_line_list = list(map(lambda x: list(map(int,map(lambda y: y[0].split(',')[0], re.findall(patch_line_regexp, x)))), patch_list))
buggy_lines_list = list(map('\n'.join, map(get_removed_lines, patch_list)))

buggy_content_len_list = list(map(len, buggy_content_list))
patch_line_len_list = list(map(len, patch_list))
print('content size stats:', {
	'size':len(buggy_content_len_list), 
	'list':buggy_content_len_list, 
	'mean':np.mean(buggy_content_len_list), 
	'std':np.std(buggy_content_len_list), 
	'lower_quartile':np.quantile(buggy_content_len_list,.25), 
	'median':np.quantile(buggy_content_len_list,.5), 
	'upper_quartile':np.quantile(buggy_content_len_list,.75)
})
print('patch size stats:', {
	'size':len(patch_line_len_list), 
	'list':patch_line_len_list, 
	'mean':np.mean(patch_line_len_list), 
	'std':np.std(patch_line_len_list), 
	'lower_quartile':np.quantile(patch_line_len_list,.25), 
	'median':np.quantile(patch_line_len_list,.5), 
	'upper_quartile':np.quantile(patch_line_len_list,.75)
})

def extract_around_line(p, b, x):
	lines = b.splitlines()  # Split the content into lines
	if p < 0 or p >= len(lines):
		raise ValueError("Line index out of range")

	line_at_p = lines[p]
	k = (x - len(line_at_p)) // 2

	# Join all lines into a single string to facilitate character indexing
	full_text = b
	
	# Find the start and end index of the line at p in the full text
	start_of_p = sum(len(lines[i]) + 1 for i in range(p)) if p > 0 else 0
	end_of_p = start_of_p + len(line_at_p)
	
	# Calculate the number of characters to extract before and after line p
	before_start_index = max(0, start_of_p - k)
	after_end_index = min(len(full_text), end_of_p + k)
	
	# Extract characters
	before_text = full_text[before_start_index:start_of_p]
	after_text = full_text[end_of_p:after_end_index]
	
	# Adjust if necessary due to boundary limits
	if len(before_text) < k:
		extra_needed = k - len(before_text)
		after_end_index = min(len(full_text), after_end_index + extra_needed)
		after_text = full_text[end_of_p:after_end_index]
	elif len(after_text) < k:
		extra_needed = k - len(after_text)
		before_start_index = max(0, before_start_index - extra_needed)
		before_text = full_text[before_start_index:start_of_p]
	
	return before_text + line_at_p + after_text

buggy_window_list = [
	extract_around_line(p_list[0], b, bug_window_size) if p_list else ''
	for p_list,b in zip(patch_line_list,buggy_content_list)
]

print('File chunk sizes:', list(map(len,buggy_window_list)))
# print(json.dumps(buggy_window_list, indent=4))

correct_window_list = [
	extract_around_line(p_list[0], b, bug_window_size) if p_list else ''
	for p_list,b in zip(patch_line_list,correct_content_list)
]


datapoint_dict_list = [
	{
		'file_id': _id,
		'file_content': _content,
		'patch': _patch,
		'buggy_lines': _buggy_lines,
		'patch_line': _patch_line,
		'prompt': prompt.format(bug_type_id=cwe_id, bug_type_label=cwe_id_label_dict[cwe_id], file_content=_window if only_provide_bug_window else _content),
		'type': 'buggy',
	}
	for _id, _patch, _buggy_lines, _patch_line, _content, _window in zip(id_list,patch_list,buggy_lines_list,patch_line_list,buggy_content_list,buggy_window_list)
	if _patch_line
] + [
	{
		'file_id': _id,
		'file_content': _content,
		'prompt': prompt.format(bug_type_id=cwe_id, bug_type_label=cwe_id_label_dict[cwe_id], file_content=_window if only_provide_bug_window else _content),
		'type': 'not_buggy',
	}
	for _id, _content, _window, _patch_line in zip(id_list,correct_content_list,correct_window_list,patch_line_list)	
	if _patch_line
]
prompt_list = [d['prompt'] for d in datapoint_dict_list]
# print(prompt_list[0])

def create_cache(file_name, create_fn):
	print(f'Creating cache <{file_name}>..')
	result = create_fn()
	with open(file_name, 'wb') as f:
		pickle.dump(result, f)
	return result

def load_cache(file_name):
	if os.path.isfile(file_name):
		print(f'Loading cache <{file_name}>..')
		with open(file_name,'rb') as f:
			return pickle.load(f)
	return None

def load_or_create_cache(file_name, create_fn):
	result = load_cache(file_name)
	if result is None:
		result = create_cache(file_name, create_fn)
	return result

def get_cached_values(value_list, cache, fetch_fn, cache_name=None, key_fn=lambda x:x, empty_is_missing=True, **args):
	missing_values = tuple(
		q 
		for q in unique_everseen(filter(lambda x:x, value_list), key=key_fn) 
		if key_fn(q) not in cache or (empty_is_missing and not cache[key_fn(q)])
	)
	if len(missing_values) > 0:
		cache.update({
			key_fn(q): v
			for q,v in fetch_fn(missing_values)
		})
		if cache_name:
			create_cache(cache_name, lambda: cache)
	return [
		cache[key_fn(q)] if q else None 
		for q in value_list
	]

_loaded_caches = {}
def instruct_model(prompts, model='gpt-4', n=1, temperature=0.5, top_p=1, frequency_penalty=0, presence_penalty=0, **kwargs):
	max_tokens = None
	adjust_max_tokens = True
	if '32k' in model:
		max_tokens = 32768
	elif '16k' in model:
		max_tokens = 16385
	elif model=='gpt-4o' or 'preview' in model or 'turbo' in model:
		max_tokens = 4096 #128000
		adjust_max_tokens = False
	if not max_tokens:
		if model.startswith('gpt-4'):
			max_tokens = 8192
		else:
			max_tokens = 4096
			adjust_max_tokens = False
	print('max_tokens', max_tokens)
	def fetch_fn(missing_prompt):
		messages = [ {"role": "user", "content": missing_prompt} ]
		prompt_max_tokens = max_tokens
		if adjust_max_tokens:
			prompt_max_tokens -= int(3*len(missing_prompt.split(' \n')))
		if prompt_max_tokens < 1:
			return missing_prompt, None
		try:
			response = chatgpt_client.chat.completions.create(model=model,
				messages=messages,
				max_tokens=prompt_max_tokens,
				n=n,
				stop=None,
				temperature=temperature,
				top_p=top_p,
				frequency_penalty=frequency_penalty, 
				presence_penalty=presence_penalty
			)
			result = [
				r.message.content.strip() 
				for r in response.choices 
				if r.message.content != 'Hello! It seems like your message might have been cut off. How can I assist you today?'
			]
			if len(result) == 1:
				result = result[0]
			return missing_prompt, result # return also the missing_prompt otherwise asynchronous prompting will shuffle the outputs
		except Exception as e:
			print(f'OpenAI returned this error: {e}')
			return missing_prompt, None
	def parallel_fetch_fn(missing_prompt_list):
		# Using ThreadPoolExecutor to run queries in parallel with tqdm for progress tracking
		with concurrent.futures.ThreadPoolExecutor(max_workers=max(1,n_processes)) as executor:
			futures = [executor.submit(fetch_fn, prompt) for prompt in missing_prompt_list]
			for e,future in enumerate(tqdm(concurrent.futures.as_completed(futures), total=len(missing_prompt_list), desc="Sending prompts to OpenAI")):
				i,o=future.result()
				yield i,o
	gpt_cache_name = f"_{model.replace('-','_')}_cache.pkl"
	if gpt_cache_name not in _loaded_caches:
		_loaded_caches[gpt_cache_name] = load_or_create_cache(gpt_cache_name, lambda: {})
	__gpt_cache = _loaded_caches[gpt_cache_name]
	return get_cached_values(
		prompts, 
		__gpt_cache, 
		parallel_fetch_fn, 
		# key_fn=lambda x: (x,model,n,temperature,top_p,frequency_penalty,presence_penalty), 
		key_fn=lambda x: (x,model,temperature,top_p,frequency_penalty,presence_penalty,n), 
		empty_is_missing=True,
		cache_name=gpt_cache_name,
	)

def extract_code_or_return_original(text):
	# This regex matches text enclosed in triple backticks, capturing the content after the initial language specifier.
	pattern = r"```([a-zA-Z]+)\n(.*?)```"
	matches = list(re.finditer(pattern, text, re.DOTALL))

	if not matches:
		# No code block found, return the original text
		return text

	# If matches are found, extract and return them
	results = []
	for match in matches:
		# Extract the code content, excluding the language name
		results.append(match.group(2).strip())

	# Join extracted code blocks with newlines, if there are multiple blocks
	return "\n".join(results)

def clean_patch(patch):
	# remova all + and - at the behinning of lines
	return re.sub(r'^[+-]', '', patch, flags=re.MULTILINE)

def clean_whitespace(text):
	# Replace all newlines with a single space
	text = text.replace('\n', ' ')
	# Replace all sequences of whitespace with a single space
	text = re.sub(r'\s+', ' ', text)
	return text.strip().strip('`.')

def extract_bug_line(model_output):
	# todo maybe not right? -> look then into df's
	# if there is second from the end take it otherwise the last one

	# TODO this is fix for second prompt where we have no BUG FOUND: -> maybe we should have a better check for this
	if(len(re.split(bug_line_pattern, model_output)) < 3):
		bug_line = re.split(bug_line_pattern_simple, model_output)[-1].strip()
	else:
		bug_line = re.split(bug_line_pattern, model_output)[-2].strip()

	# bug_line = re.split(bug_line_pattern, model_output, 1)[-2]
	bug_line = extract_code_or_return_original(bug_line).strip()

	# if there is a string which is in ` ` extract it, otherwise use as it is
	match = re.search(r'`([^`]+)`', bug_line)
	if match:
		bug_line =  match.group(0)  # Return content inside the backticks

	bug_line = clean_whitespace(bug_line)
	return bug_line

def remove_spaces(text):
	return text.replace(' ', '')

def has_bug_line(model_output):
	code = extract_code_or_return_original(model_output)

	_has_bug_line = bool(bug_line_pattern.search(model_output)) #or bool(bug_line_pattern_simple.search(model_output))

	# TODO might need some improval on this 
	if not _has_bug_line:
		return False
	
	# extract bug line
	bug_line = extract_bug_line(model_output)
	# strip remove spaces
	bug_line = remove_spaces(clean_whitespace(bug_line)).strip()

	if(len(bug_line) == 0):
		return False

	if(_has_bug_line and ('BL: None'.lower() not in model_output.lower() or "BUG FOUND: NO".lower() not in model_output.lower())):
		return True
	
	if code and code != model_output:
		return True

def classify(record, model_output):
	_type = record['type']
	patch = record.get('patch',None)

	classification = None
	bug_line = None
	patch_removal = None

	pattern_yes = re.compile(r"bug\s*found\s*:\s*yes", re.IGNORECASE)
	pattern_no = re.compile(r"bug\s*found\s*:\s*no", re.IGNORECASE)

	# Check for matches
	has_bug_true_indication = bool(re.search(pattern_yes, model_output))
	has_bug_false_indication = bool(re.search(pattern_no, model_output))
	_has_bug_line = has_bug_line(model_output)

	# stronger conditions -> lets rely purely on model_output under Bug found
	if _type == 'not_buggy':
		if has_bug_true_indication: 
			classification = 'FP'
		else:
			classification = 'TN'
	elif _type == 'buggy' and has_bug_false_indication: 
		classification = 'FN'
	else:
		# weaker decision based in bugged_line
		if not _has_bug_line:
			classification = 'FN'
		else:
			bug_line = remove_spaces(extract_bug_line(model_output))
			# patch_removal = remove_spaces(clean_whitespace(get_removed_lines(patch)))
			cleaned_patch = remove_spaces(clean_whitespace(clean_patch(patch)))

			bug_line_in_patch = bug_line in cleaned_patch

			if (len(bug_line) > 0 and bug_line_in_patch):
				classification = 'TP'
			else:
				classification = 'FN' 
				
	return classification

tp=0
tn=0
fp=0
fn=0
for i,model_output in enumerate(instruct_model(prompt_list, model=model, temperature=temperature)):
	if not model_output:
		continue

	datapoint_dict = datapoint_dict_list[i]
	classification = classify(datapoint_dict, model_output)

	if classification == 'FP':
		fp+=1
	elif classification == 'TP':
		tp += 1
	elif classification == 'FN':
		fn+=1
	elif classification == 'TN':
		tn += 1

try:
	accuracy = (tp + tn) / (tp + tn + fp + fn)
except ZeroDivisionError:
	accuracy = float('nan')  # Not a Number, used for undefined values
print("Accuracy:", accuracy)
try:
	precision = tp / (tp + fp)
except ZeroDivisionError:
	precision = float('nan')
print("Precision:", precision)
try:
	recall = tp / (tp + fn)
except ZeroDivisionError:
	recall = float('nan')
print("Recall:", recall)
try:
	if precision + recall == 0:
		f1_score = float('nan')
	else:
		f1_score = 2 * (precision * recall) / (precision + recall)
except ZeroDivisionError:
	f1_score = float('nan')
print("F1-Score:", f1_score)
