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
from pathlib import Path
from dotenv import load_dotenv

from models import Models, anyscale_names, model_mapping

env_path = Path('..') / '.env'
load_dotenv(env_path)

cwe_id = sys.argv[2]
model = model_mapping.get(sys.argv[1])

if not model:
	raise ValueError(f"Model {sys.argv[1]} is not supported")
else:
	model = model.value #cast model to string

only_check_removed_lines_in_patch = False
only_provide_bug_window = False
bug_window_size = 10

n_processes = multiprocessing.cpu_count()*20 if model not in anyscale_names else 30 #anyscale supports only 30 concurent processes
openai_api_key = os.getenv("OPENAI_API_KEY")
anyscale_api_key = os.getenv("ANYSCALE_API_KEY")
temperature = 0
file_path = f'../files_CWE-{cwe_id}.csv'

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

if model in anyscale_names:
	chatgpt_client = openai.OpenAI(base_url="https://api.endpoints.anyscale.com/v1", api_key=anyscale_api_key)
	print("anyscale endpoint selected")
else:
	chatgpt_client = openai.OpenAI(api_key=openai_api_key)

bug_line_pattern = re.compile(r'(Bugged)?[ -]*(Line|BL) *[:#]\s*(.*?)(?=BUG FOUND:)', re.IGNORECASE | re.DOTALL)

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

buggy_window_list = [
	'\n\n'.join([
		'\n'.join(b.split('\n')[p-bug_window_size:p+bug_window_size])
		for p in p_list
	])
	for p_list,b in zip(patch_line_list,buggy_content_list)
]

correct_window_list = [
	'\n\n'.join([
		'\n'.join(b.split('\n')[p-bug_window_size:p+bug_window_size])
		for p in p_list
	])
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
] + [
	{
		'file_id': _id,
		'file_content': _content,
		'prompt': prompt.format(bug_type_id=cwe_id, bug_type_label=cwe_id_label_dict[cwe_id], file_content=_window if only_provide_bug_window else _content),
		'type': 'not_buggy',
	}
	for _id, _content, _window in zip(id_list,correct_content_list,correct_window_list)	
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

def clean_whitespace(text):
	# Replace all newlines with a single space
	text = text.replace('\n', ' ')
	# Replace all sequences of whitespace with a single space
	text = re.sub(r'\s+', ' ', text)
	# text = text.replace(' ', '')
	text = text.replace('\\', '')
	return text.strip().strip('`.')

tp=0
tn=0
fp=0
fn=0
# Dictionary to hold input length and outcome counts
length_outcomes = []
results = []
for i,model_output in enumerate(instruct_model(prompt_list, model=model, temperature=temperature)):
	if not model_output:
		continue

	datapoint_dict = datapoint_dict_list[i]
	results.append({
		'file_id': datapoint_dict['file_id'],
		'model_output': model_output,
		'type':  datapoint_dict['type']
	})

	code = extract_code_or_return_original(model_output)
	has_bug_line = (bool(bug_line_pattern.search(model_output)) and 'BL: None'.lower() not in model_output.lower()) or (code and code != model_output) and 'BUG FOUND: YES'.lower() in model_output
	input_len = len(datapoint_dict['file_content'])
	max_line = datapoint_dict['file_content'].count('\n')
	if datapoint_dict['type'] == 'not_buggy':
		if has_bug_line:
			fp+=1
			# length_outcomes.append({'input_len':input_len, 'max_line': max_line, 'tp': 0, 'tn': 0, 'fp': 1, 'fn': 0, 'f': 1, 't': 0})
		else:
			tn+=1
			# length_outcomes.append({'input_len':input_len, 'max_line': max_line, 'tp': 0, 'tn': 1, 'fp': 0, 'fn': 0, 'f': 0, 't': 1})
	else:
		if not datapoint_dict['patch_line']:
			continue
		# print(model_output)
		# print('#'*10)
		file_content_lines = datapoint_dict['file_content'].split('\n')
		min_bug_pos = len('\n'.join(file_content_lines[:datapoint_dict['patch_line'][0]]))
		max_bug_pos = len('\n'.join(file_content_lines[:datapoint_dict['patch_line'][-1]]))
		avg_bug_pos = (min_bug_pos+max_bug_pos)//2
		if has_bug_line:
			bug_line = re.split(bug_line_pattern, model_output, 1)[-2]
			bug_line = extract_code_or_return_original(bug_line).strip()

			# if clean_whitespace(bug_line).replace(' ', '') in clean_whitespace(datapoint_dict['patch']).replace(' ', '') and not (clean_whitespace(bug_line).replace(' ', '') in clean_whitespace(datapoint_dict['buggy_lines']).replace(' ', '')):
			# 	print(bug_line)
			# 	print('$'*10)
			# 	print(datapoint_dict['patch'])
			# 	print('*'*10)
			# 	print(datapoint_dict['buggy_lines'])
			# 	print('#'*10)

			bug_line = clean_whitespace(bug_line)
			if only_check_removed_lines_in_patch:
				patch = clean_whitespace(datapoint_dict['buggy_lines']) # giving many false negatives
			else:
				patch = clean_whitespace(datapoint_dict['patch'])

			# print(bug_line in patch, json.dumps({'prompt': prompt_list[i], 'prediction': bug_line, 'ground_truth': patch}, indent=4))
			# tp+=1
			# length_outcomes.append({'input_len':input_len, 'tp': 1, 'tn': 0, 'fp': 0, 'fn': 0})
			if bug_line.replace(' ', '') in patch.replace(' ', ''):
				tp+=1
				length_outcomes.append({'input_len':input_len, 'max_line': max_line, 'min_bug_pos': min_bug_pos, 'max_bug_pos': max_bug_pos, 'avg_bug_pos': avg_bug_pos, 'tp': 1, 'tn': 0, 'fp': 0, 'fn': 0, 'f': 0, 't': 1})
			else:
				# print('#'*10)
				# print(bug_line)
				fn+=1
				length_outcomes.append({'input_len':input_len, 'max_line': max_line, 'min_bug_pos': min_bug_pos, 'max_bug_pos': max_bug_pos, 'avg_bug_pos': avg_bug_pos, 'tp': 0, 'tn': 0, 'fp': 0, 'fn': 1, 'f': 1, 't': 0})
		else:
			# print('-'*10)
			# print(model_output)
			fn+=1
			length_outcomes.append({'input_len':input_len, 'max_line': max_line, 'min_bug_pos': min_bug_pos, 'max_bug_pos': max_bug_pos, 'avg_bug_pos': avg_bug_pos, 'tp': 0, 'tn': 0, 'fp': 0, 'fn': 1, 'f': 1, 't': 0})

# Create a DataFrame from the list length_outcomes
df = pd.DataFrame(length_outcomes)
# Define the filename for the CSV file
csv_filename = f'../data/lr_CWE-{cwe_id}_model-{model}.csv'
# Save the DataFrame to a CSV file
df.to_csv(csv_filename, index=False)

df = pd.DataFrame(results)
csv_filename = f'../data/data_CWE-{cwe_id}_{model}.csv'
df.to_csv(csv_filename, index=False)

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

# Create a DataFrame from the length-outcome counts
data = []
for counts in length_outcomes:
	data.append([counts['input_len'], counts['min_bug_pos'], counts['max_bug_pos'], counts['avg_bug_pos'], counts['tp'], counts['tn'], counts['fp'], counts['fn'], counts['fp']+counts['fn']])

df = pd.DataFrame(data, columns=['Input Length', 'Min Bug Position', 'Max Bug Position', 'Average Bug Position', 'TP', 'TN', 'FP', 'FN', 'F'])
# print(df.head())

# You can use statistical methods to analyze the correlation
correlations = df.corr(method='spearman')
print(correlations)

# # Logistic regression to predict TP based on Input Length
# df['Intercept'] = 1  # add an intercept (beta_0) to our model

# # Specify the regression model and fit it
# logit_model = sm.Logit(df[target_variable], df[['Intercept', source_variable]])
# result = logit_model.fit()

# # Print the summary of the regression results
# print(result.summary())

# # Generate a range of input lengths for prediction
# x_range = np.linspace(df[source_variable].min(), df[source_variable].max(), 300)
# x_pred = sm.add_constant(x_range)  # add a constant as we did in the model

# # Predict the probabilities
# y_pred = result.predict(x_pred)

# # Plotting
# plt.figure(figsize=(10, 6))
# plt.scatter(df[source_variable], df[target_variable], alpha=0.3, label=f'Data Points ({target_variable} = 1 or 0)')
# plt.plot(x_range, y_pred, color='red', label='Logistic Regression Fit')
# plt.title(f'Probability of {target_variable} vs. {source_variable}')
# plt.xlabel(source_variable)
# plt.ylabel(f'Probability of {target_variable}')
# plt.legend()
# plt.grid(True)
# plt.savefig(f'logistic-regression_CWE-{cwe_id}_model-{model}_source-{source_variable}_target-{target_variable}.pdf')

