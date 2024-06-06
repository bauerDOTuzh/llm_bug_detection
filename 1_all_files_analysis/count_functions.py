import re
import sys
import pandas as pd

cwe_id = sys.argv[1]

def count_functions(file_content, file_extension):
    if file_extension == 'php':
        pattern = r'function\s+\w+\s*\([^)]*\)\s*(:\s*\S+)?\s*\{'
    elif file_extension in ['ts', 'js']:
        pattern = r'(async\s+)?(?:function\s+\w+\s*\(.*?\)\s*\{|(?:\w+\s*=\s*)?\(.*?\)\s*=>\s*\{|[\w\.]+\s*\([\w\s,]*\)\s*\{)'
    elif file_extension == 'html':
        return 0
    elif file_extension == 'java':
        pattern = r'(public|protected|private|static|\s)+[\w<>\[\],\s]+\s+\w+\s*\([\w\s,<>\[\]]*\)\s*\{'
    elif file_extension == 'go':
        pattern = r'func\s+(?:\([\w\s,*]*\)\s*)?\w+\s*\([^)]*\)\s*\{'
    elif file_extension == 'py':
        pattern = r'(?:@[\w\.]+\s*)*def\s+\w+\s*\([^)]*\)\s*:'
    elif file_extension == 'rb':
        pattern = r'def\s+\w+\s*\([^)]*\)\s*'
    elif file_extension == 'c':
        pattern = r'[\w\s*]+\s+\w+\s*\([\w\s,*]*\)\s*\{'
    else:
        return 0

    matches = re.findall(pattern, file_content)
    return len(matches)

# Read the CSV file
file_path = f'./cve_data/files_CWE-{cwe_id}.csv'
df = pd.read_csv(file_path)

# Initialize a list to hold the function counts
function_counts = []

# Process each file in the dataframe
for index, row in df.iterrows():
    file_content = row['file_before']
    file_extension = row['file_extension']
    count = count_functions(file_content, file_extension)
    function_counts.append(count)

# Add the function counts to the dataframe
df['function_count'] = function_counts

# Drop files with no functions
print(len(df))
# 
df = df[df['function_count'] > 0]
print(len(df))


# Calculate the average function count across all files
average_function_count = df['function_count'].mean()

# Calculate the average function size by dividing the file sizes by the number of functions
# First, we need to calculate the size of each file (in terms of characters)
df['file_size'] = df['file_before'].apply(len)

# Avoid division by zero by setting function count to 1 where it is zero
df['adjusted_function_count'] = df['function_count'].apply(lambda x: x if x != 0 else 1)

# Calculate average function size
df['average_function_size'] = df['file_size'] / df['adjusted_function_count']

# Expand each average function size into a list of its size repeated by the adjusted function count
expanded_sizes = []
for _, row in df.iterrows():
    expanded_sizes.extend([row['average_function_size']] * row['adjusted_function_count'])

expanded_series = pd.Series(expanded_sizes)

# Calculate the average function size across all files
average_function_size = df['average_function_size'].mean()

print('average_function_count:', average_function_count)
print('average_function_size:', average_function_size)

# Calculate the median function count across the filtered files
median_function_count = df['function_count'].median()

# Calculate the median function size across the filtered files
median_function_size = df['average_function_size'].median()

print('median_function_count:', median_function_count)
print('median_function_size:', median_function_size)
