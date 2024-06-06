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
# import ast
from pathlib import Path
from dotenv import load_dotenv
import enum
import sys

env_path = Path('..') / '.env'
load_dotenv(env_path)


class Models(enum.Enum):
    GPT3_5 = "gpt-3.5-turbo"
    GPT4 = "gpt-4-turbo"
    GPT4o = "gpt-4o"
    LLAMA3 = "llama3-70b-8192"
    MIXTRAL8_7 = "mixtral-8x7b-32768"
    MIXTRAL8_22 = 'mixtral-8x22b-65536'

anyscale_names = {
    Models.LLAMA3.value: "meta-llama/Meta-Llama-3-70B-Instruct",
    Models.MIXTRAL8_7.value: "mistralai/Mixtral-8x7B-Instruct-v0.1",
    Models.MIXTRAL8_22.value: "mistralai/Mixtral-8x22B-Instruct-v0.1"
}

# input names
model_mapping = {
    "gpt-3.5-turbo": Models.GPT3_5,
    "gpt-4-turbo": Models.GPT4,
    "gpt-4o": Models.GPT4o,
    "llama3": Models.LLAMA3,
    "mixtral8x7": Models.MIXTRAL8_7,
    "mixtral8x22": Models.MIXTRAL8_22
}
model = model_mapping.get(sys.argv[1])


#cwe_id = sys.argv[2]
#bug_window_size = int(sys.argv[3]) # 6500 # characters

if not model:
	raise ValueError(f"Model {sys.argv[1]} is not supported")
else:
	model = model.value #cast model to string

bug_window_size_list = [
	# 13000, 
	6500, 
	3000, 
	1500, 
	500
]
cwe_id_list = ['22', '89', '79']

n_processes = multiprocessing.cpu_count()*20 if model not in anyscale_names else 30 #anyscale supports only 30 concurent processes
openai_api_key = os.getenv("OPENAI_API_KEY")
anyscale_api_key = os.getenv("ANYSCALE_API_KEY")
temperature = 0

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

def get_removed_lines(patch):
	# Extract lines starting with -
	removed_lines = re.findall(r'^-.*$', patch, re.MULTILINE)
	# Remove the leading - character from each line
	return [line[1:] for line in removed_lines]

if model in anyscale_names:
	chatgpt_client = openai.OpenAI(base_url="https://api.endpoints.anyscale.com/v1", api_key=anyscale_api_key)
	print("anyscale endpoint selected")
else:
	chatgpt_client = openai.OpenAI(api_key=openai_api_key)

def chunk_string(s, chunk_size=500, start=0, end=None):
	# Limit the string to the first 10000 characters
	s = s[start:end]
	# Create chunks of 500 characters each
	return [s[i:i+chunk_size] for i in range(0, len(s), chunk_size)]
	
def extract_chunks(p, b, x):
	lines = b.splitlines()  # Split the content into lines
	if p < 0 or p >= len(lines):
		raise ValueError("Line index out of range")

	chunk_list = []
	buggy_chunk = None
	current_chunk = ''
	current_chunk_is_buggy = False
	for i,line in enumerate(lines):
		if len(current_chunk) + len(line) > x:
			if current_chunk_is_buggy:
				buggy_chunk = current_chunk
				current_chunk_is_buggy = False
			else:
				chunk_list.append(current_chunk)
			current_chunk = ''
		if i==p:
			current_chunk_is_buggy = True
		current_chunk += line + '\n'
	if current_chunk_is_buggy:
		buggy_chunk = current_chunk
	else:
		chunk_list.append(current_chunk)
	return chunk_list, buggy_chunk

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
	# print('max_tokens', max_tokens)
	def fetch_fn(missing_prompt):
		messages = [ {"role": "user", "content": missing_prompt} ]
		prompt_max_tokens = max_tokens
		if adjust_max_tokens:
			prompt_max_tokens -= int(3*len(missing_prompt.split(' \n')))
		if prompt_max_tokens < 1:
			return missing_prompt, None
		try:
			model_name = anyscale_names.get(model, model) #if no anyscale name, stick to model name -> gpt has no mapping
			response = chatgpt_client.chat.completions.create(model=model_name,
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
	gpt_cache_name = f"cache/_{model.replace('-','_')}_cache.pkl"
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

############################################################
############################################################

bug_line_pattern = re.compile(r'(Bugged\s*)?[ -]*(Line|BL)\s*[:#]\s*(.*?)(?=BUG FOUND:)', re.IGNORECASE | re.DOTALL)
bug_line_pattern_simple = re.compile(r'(Bugged)?[ -]*(Line|BL) *[:#]', re.IGNORECASE)

results_dict_list = []
for cwe_id in cwe_id_list:
	data = pd.read_csv(f'../1_all_files_analysis/cve_data/files_CWE-{cwe_id}.csv')

	id_list = data['file_id'].tolist()
	patch_list = data['patch'].tolist()
	# buggy_content_list = list(map('\n'.join, map(ast.literal_eval, data['file_before'].tolist())))
	# correct_content_list = list(map('\n'.join, map(ast.literal_eval, data['file_after'].tolist())))
	buggy_content_list = data['file_before'].tolist()
	correct_content_list = data['file_after'].tolist()
	patch_line_regexp = r'@@ -(\d+,\d+) \+(\d+,\d+) @@' # Regular expression pattern to match line numbers in the diff
	patch_line_list = list(map(lambda x: list(map(int,map(lambda y: y[0].split(',')[0], re.findall(patch_line_regexp, x)))), patch_list))
	buggy_lines_list = list(map('\n'.join, map(get_removed_lines, patch_list)))

	buggy_content_len_list = list(map(len, buggy_content_list))
	patch_line_len_list = list(map(len, patch_list))
	# print('content size stats:', {
	# 	'size':len(buggy_content_len_list), 
	# 	# 'list':buggy_content_len_list, 
	# 	'mean':np.mean(buggy_content_len_list), 
	# 	'std':np.std(buggy_content_len_list), 
	# 	'lower_quartile':np.quantile(buggy_content_len_list,.25), 
	# 	'median':np.quantile(buggy_content_len_list,.5), 
	# 	'upper_quartile':np.quantile(buggy_content_len_list,.75)
	# })
	# print('patch size stats:', {
	# 	'size':len(patch_line_len_list), 
	# 	# 'list':patch_line_len_list, 
	# 	'mean':np.mean(patch_line_len_list), 
	# 	'std':np.std(patch_line_len_list), 
	# 	'lower_quartile':np.quantile(patch_line_len_list,.25), 
	# 	'median':np.quantile(patch_line_len_list,.5), 
	# 	'upper_quartile':np.quantile(patch_line_len_list,.75)
	# })

	make_prompt = lambda x: prompt.format(bug_type_id=cwe_id, bug_type_label=cwe_id_label_dict[cwe_id], file_content=x)

	print('#'*10)
	print('CWE-ID:', cwe_id)

	for bug_window_size in bug_window_size_list:
		datapoint_dict_list = []
		p_count = 0
		for _id, _patch, _buggy_lines, _patch_line, _content in zip(id_list,patch_list,buggy_lines_list,patch_line_list,buggy_content_list):
			if not _patch_line:
				continue

			extra_list, _window = extract_chunks(_patch_line[0], _content, bug_window_size)
			datapoint_dict_list.append(
				{
					'file_id': _id,
					'file_content': _content,
					'chunk_content': _window,
					'patch': _patch,
					'buggy_lines': _buggy_lines,
					'patch_line': _patch_line,
					'prompt': make_prompt(_window),
					'type': 'buggy',
				}
			)
			p_count += 1
			datapoint_dict_list += [
				{
					'file_id': _id,
					'file_content': _content,
					'chunk_content': c,
					'prompt': make_prompt(c),
					'type': 'not_buggy',
				}
				for c in extra_list
			]
		# for _id, _content, _patch_line in zip(id_list,correct_content_list,patch_line_list):
		# 	if not _patch_line:
		# 		continue
		# 	_, _window = extract_chunks(_patch_line[0], _content, bug_window_size)
		# 	datapoint_dict_list.append(
		# 		{
		# 			'file_id': _id,
		# 			'file_content': _content,
		# 			'chunk_content': _window,
		# 			'prompt': make_prompt(_window),
		# 			'type': 'not_buggy',
		# 		}
		# 	)
		# print(list(map(lambda x: len(x['chunk_content']), datapoint_dict_list)))
		prompt_list = [d['prompt'] for d in datapoint_dict_list]
		# print(prompt_list[0])

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
				# print(model_output)
			elif classification == 'TP':
				tp += 1
			elif classification == 'FN':
				fn+=1
			elif classification == 'TN':
				tn += 1

		print('-'*10)
		print('\tContext Window:', bug_window_size)
		print('\tPoints:', len(prompt_list))
		try:
			accuracy = (tp + tn) / (tp + tn + fp + fn)
		except ZeroDivisionError:
			accuracy = float('nan')  # Not a Number, used for undefined values
		print("\tAccuracy:", accuracy)
		try:
			precision = tp / (tp + fp)
		except ZeroDivisionError:
			precision = float('nan')
		print("\tPrecision:", precision)
		try:
			recall = tp / (tp + fn)
		except ZeroDivisionError:
			recall = float('nan')
		print("\tRecall:", recall)
		try:
			if precision + recall == 0:
				f1_score = float('nan')
			else:
				f1_score = 2 * (precision * recall) / (precision + recall)
		except ZeroDivisionError:
			f1_score = float('nan')
		print("\tF1-Score:", f1_score)

		results_dict_list.append({
			'model': model,
			'cwe': cwe_id,
			'context_window': bug_window_size,
			'prompts_count': len(prompt_list),
			'accuracy': accuracy,
			'precision': precision,
			'recall': recall,
			'f1_score': f1_score
		})

# Convert list of dictionaries to DataFrame
df = pd.DataFrame(results_dict_list)

# Save DataFrame to CSV file
df.to_csv(f'./results/{model}.csv', index=False)
