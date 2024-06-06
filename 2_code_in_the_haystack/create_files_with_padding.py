#!/usr/bin/env python
# coding: utf-8

# # Script Documentation
# 
# ## Overview
# This script is designed to generate code files with specific padding and buggy lines for testing purposes. It uses predefined file structures and Common Weakness Enumerations (CWEs) to create variations of files with different bug positions. The script supports generating these files with specific constraints and tolerances.
# 
# ## Configuration
# Set the following variables in the script:
# - `directory_file`: Directory containing the source files.
# 
# ## Key Variables
# - `files_dict`: Dictionary containing details about each file, including paths, buggy lines, split strings, and CWE IDs.
# 
# ## Functions
# - **`item_tracking_knapsack(capacity, items, n=None)`**: Implements a knapsack algorithm to select items (snippets) that fit within a given capacity.
# - **`parse_file(filename, split_string)`**: Parses a file to extract snippets based on a split string.
# - **`get_padding_content(file_id, filename)`**: Retrieves padding content for a given file ID and filename.
# - **`make_file_with_padding(file_id, target_chars, target_bug_position, tolerance=0, debug=False, allow_duplicated_padding=False)`**: Generates a file with specified padding and buggy line position.
# - **`is_bug_in_correct_position(file_content, buggy_line, target_bug_position)`**: Checks if the buggy line is in the desired position in the generated file.
# - **`generate_file_with_padding_for_one_id(file_id)`**: Generates files with bugs at various positions for a specified file ID.
# 
# ## Execution Workflow
# 1. **Generate Files with Padding**: For each file ID, generate files with the bug placed at various positions, using specified padding and tolerance.
# 2. **Validate Bug Position**: Ensure the bug is placed within the desired position range.
# 3. **Combine and Save Results**: Combine new and existing data, avoid duplicates, and save results to a CSV file.
# 
# ## Usage
# 1. Set the `directory_file` variable to the path containing the source files.
# 2. Define the `files_dict` dictionary with appropriate file paths, buggy lines, and CWE IDs.
# 3. Run the script to generate files and validate their content.

# In[ ]:


import pandas as pd

directory_file = directory  = 'source_files'


# In[ ]:


files_dict = {
    406: {
        "main_padding": "/php/406/406_modifiedFile.php",
        "buggy_content": "/php/406/406_smallestBuggy.php",
        "buggy_line": "$selectedIds = explode(',', $selectedIds);",
        "split_string": "// -x-",
        "CWE_ID": "CWE-89"
    },
    408: {
        'main_padding': '/php/408/408_modifiedFile.php',
        "additional_padding": ["/php/408/additional_padding.php"],
        "buggy_content": "/php/408/408_smallestBuggy.php",
        "buggy_line": '''SELECT * FROM ' . static::table_name() . ' WHERE ' . $property .  ''',
        "split_string": "// -x-",
        "CWE_ID": "CWE-89"
    },
    405: {
        'main_padding': '/php/405/405_modifiedFile.php',
        "additional_padding": ["/php/405/additional_padding.php"],
        "buggy_content": "/php/405/405_smallestBuggy.php",
        "buggy_line": '''$where = "WHERE group_ID = {$group_id}";''',
        "split_string": "// -x-",
        "CWE_ID": "CWE-89"
    },
    4921: {
        'main_padding': '/go/4921/4921_modifiedFile.go',
        "additional_padding": ["/go/4921/additional_padding.go"],
        "buggy_content": "/go/4921/4921_smallestBuggy.go",
        "buggy_line": '''order := fmt.Sprintf("`%s` %s", DefaultQuery(c, "sort_by", "id"), sort)''',
        "split_string": "// -x-",
        "CWE_ID": "CWE-89"
    },
    4928: {
        'main_padding': '/php/4928/4928_modifiedFile.php',
        "additional_padding": ["/php/4928/additional_padding.php"],
        "buggy_content": "/php/4928/4928_smallestBuggy.php",
        "buggy_line": '''return @mysqli_real_escape_string($fmdb->dbh, $data);''',
        "split_string": "// -x-",
        "CWE_ID": "CWE-89"
    },
    3989:{
        'main_padding': '/js/3989/3989_modifiedFile.js',
        "additional_padding": ["/js/3989/additional_padding.js"],
        "buggy_content": "/js/3989/3989_smallestBuggy.js",
        "buggy_line": '''`window[${idJSON}].push(${serializedCacheArgs});`,''',
        "split_string": "// -x-",
        "CWE_ID": "CWE-79"
    },
    3976:{
        'main_padding': '/js/3976/3976_modifiedFile.js',
        "additional_padding": ["/js/3976/additional_padding.js"],
        "buggy_content": "/js/3976/3976_smallestBuggy.js",
        "buggy_line": '''const header = container.querySelector(`h${level}`);''',
        "split_string": "// -x-",
        "CWE_ID": "CWE-79"
    },
    3968:{
        'main_padding': '/php/3968/3968_modifiedFile.php',
        "additional_padding": ["/php/3968/additional_padding.php"],
        "buggy_content": "/php/3968/3968_smallestBuggy.php",
        "buggy_line": '''$response['data']['path'] = $model->path;''',
        "split_string": "// -x-",
        "CWE_ID": "CWE-79"
    },
    300:{
        'main_padding': '/php/300/300_modifiedFile.php',
        "additional_padding": ["/php/300/additional_padding.php"],
        "buggy_content": "/php/300/300_smallestBuggy.php",
        "buggy_line": '''<td>' . $item->id . '</td>''',
        "split_string": "// -x-",
        "CWE_ID": "CWE-79"
    },
    302:{
        'main_padding': '/rb/302/302_modifiedFile.rb',
        "additional_padding": ["/rb/302/additional_padding.rb"],
        "buggy_content": "/rb/302/302_smallestBuggy.rb",
        "buggy_line": '''@filter = params[:filter] || "*"''',
        "split_string": "# -x-",
        "CWE_ID": "CWE-79"
    },
    5422:{
        'main_padding': '/go/5422/5422_modifiedFile.go',
        "additional_padding": ["/go/5422/additional_padding.go"],
        "buggy_content": "/go/5422/5422_smallestBuggy.go",
        "buggy_line": '''outdir := filepath.Join(basePath, name)''',
        "split_string": "// -x-",
        "CWE_ID": "CWE-22"
    },
    5396:{
        'main_padding': '/java/5396/5396_modifiedFile.java',
        "additional_padding": ["/java/5396/additional_padding.java"],
        "buggy_content": "/java/5396/5396_smallestBuggy.java",
        "buggy_line": '''URI uri = toURI(fileUri);''',
        "split_string": "// -x-",
        "CWE_ID": "CWE-22"
    },
    5404:{
        'main_padding': '/go/5404/5404_modifiedFile.go',
        "additional_padding": ["/go/5404/additional_padding.go"],
        "buggy_content": "/go/5404/5404_smallestBuggy.go",
        "buggy_line": '''target := filepath.Join(dst, name)''',
        "split_string": "// -x-",
        "CWE_ID": "CWE-22"
    },
    5414:{
        'main_padding': '/js/5414/5414_modifiedFile.js',
        "additional_padding": ["/js/5414/additional_padding.js"],
        "buggy_content": "/js/5414/5414_smallestBuggy.js",
        "buggy_line": '''var filename = path.join(__dirname, "public", req.url.path_list.join("/"));''',
        "split_string": "// -x-",
        "CWE_ID": "CWE-22"
    },
    493:{
        'main_padding': '/py/493/493_modifiedFile.py',
        "additional_padding": ["/py/493/additional_padding.py"],
        "buggy_content": "/py/493/493_smallestBuggy.py",
        "buggy_line": '''return FileResponse(f"user_images/pfp/{username}", media_type='image/gif')''',
        "split_string": "# -x-",
        "CWE_ID": "CWE-22"
    },
}


# In[ ]:


def item_tracking_knapsack(capacity, items, n=None): 
    if n is None:
        n = len(items)
     
    # Making the dp array 
    dp = [0 for i in range(capacity+1)] 
    
    # Initializing an array to track the items included in the knapsack
    item_tracker = [[] for _ in range(capacity + 1)]
 
    # Taking first i elements 
    for i in range(1, n+1): 
         
        # Starting from back, 
        # so that we also have data of 
        # previous computation when taking i-1 items 
        for w in range(capacity, 0, -1): 
            if items[i-1]['size'] <= w: 
                
                # Value if we include this item
                new_val = dp[w - items[i - 1]['size']] + items[i - 1]['size']
                # Compare the new potential value with the current value at dp[w]
                if new_val > dp[w]:
                    dp[w] = new_val
                    # Update the tracker to include this item along with the items that were included to achieve new_val
                    item_tracker[w] = item_tracker[w - items[i - 1]['size']] + [items[i-1]]
     
    # Returning the maximum value of knapsack 
    assert dp[capacity] <= capacity
    return item_tracker[capacity]

def parse_file(filename, split_string):
    snippets = []
    inside_snippet = False
    snippet_content = []
    

    with open(directory+filename, 'r') as file:
        snippet_type = ''
        for line in file:
            # print(line)
            if split_string in line:
                # determine type "PREPEND ALWAYS, PREPEND ONLY"
                snippet_type = "PREPEND_ONLY" if "PREPEND ONLY" in line else ("PREPEND_ALWAYS" if "PREPEND ALWAYS" in line else "NONE")

                # print("this line has split string")
                if inside_snippet:
                    # End of snippet
                    snippet = ''.join(snippet_content).strip()
                    snippets.append({
                        'size': len(snippet),
                        'snippet': snippet,
                        'type': snippet_type
                    })
                    snippet_content = []
                    inside_snippet = True
                else:
                    inside_snippet = not inside_snippet
            elif inside_snippet:
                snippet_content.append(line)
    
    return snippets

def get_padding_content(file_id, filename):
    file = files_dict[file_id]
    return parse_file(filename, file['split_string'])


# In[ ]:


import random

def make_file_with_padding(file_id, target_chars, target_bug_position, tolerance=0, debug=False, allow_duplicated_padding=False):
    # assert that bug position is not larger than target chars
    assert target_bug_position < target_chars
    # lets assume that we allow only mod 500 for both inputs
    assert target_bug_position % 500 == 0
    assert target_chars % 500 == 0

    additional_padding = False

    with open(directory_file+files_dict[file_id]['buggy_content'], 'r') as file:
        content = file.read()

    snippets = get_padding_content(file_id, files_dict[file_id]['main_padding'])
    buggy_chars = len(content) - len("{prepend_content}\n{append_content}\n")
    
    # find out how many 
    prepend_chars = target_bug_position
    append_chars = target_chars - prepend_chars - buggy_chars

    # count size of all snippets
    total_count = sum(x['size'] for x in snippets)

    if total_count < prepend_chars + append_chars:
        if debug:
            print("Not enough padding, adding more padding from other files")
        for file in files_dict[file_id]['additional_padding']:
            snippets.extend(get_padding_content(file_id,file ))
        additional_padding = True

    # TODO add how many padding comes from other files and from old file (can have also some inpact on something)

    # generate snippets
    # snippets.sort(key=lambda x: x['size'], reverse=True)
    # random.shuffle(snippets)  # This shuffles the list in-place
    prepend_snippets = item_tracking_knapsack(prepend_chars+tolerance//2, snippets) if prepend_chars > 0 else []
    snippets_to_ignore = set([ps['snippet'] for ps in prepend_snippets])
    append_snippets = item_tracking_knapsack(append_chars+tolerance//2, snippets if allow_duplicated_padding else [s for s in snippets if s['snippet'] not in snippets_to_ignore]) if append_chars > 0 else []

    # generate the final content
    prepend_content = '\n'.join([snippet['snippet'] for snippet in prepend_snippets])
    #print('a', len(prepend_content))
    append_content = '\n'.join([snippet['snippet'] for snippet in append_snippets])
    #print('b', len(append_content))
    #print('c', len(append_content)+len(prepend_content)+buggy_chars)

    # insert into content (replace prepend_content and append_content)
    content = content.replace('{prepend_content}', prepend_content, 1)
    content = content.replace('{append_content}', append_content, 1)
    #print('d', len(content), target_chars)

    # get bug position in the content
    bug_position  = content.find(files_dict[file_id]['buggy_line'])
    if(debug):
        print(f"Prepend chars: {prepend_chars}")
        print(f"Append chars: {append_chars}")
        print(f"buggy length: {buggy_chars}")
        print(f"Prepend snippets: {len(prepend_content)}")
        print(f"Append snippets: {len(append_content)}")
        print(f"Total length: {len(content)}")
        print(f"Bug position: {bug_position}")
        print(f"Bug line: {files_dict[file_id]['buggy_line']}")

    # assert that the length is correct with tolerance 
    new_lines_count = len(prepend_snippets) + len(append_snippets)
    if not allow_duplicated_padding and abs(len(content) - target_chars) > tolerance+new_lines_count:
        return make_file_with_padding(file_id, target_chars, target_bug_position, tolerance=tolerance, debug=debug, allow_duplicated_padding=True)
    assert abs(len(content) - target_chars) <= tolerance + new_lines_count, f'{abs(len(content) - target_chars)} <= {tolerance + new_lines_count}'
    # assert bug line is between target_bug_position and target_bug_position + 500
    assert bug_position >= target_bug_position and bug_position <= target_bug_position + 500
    data = {
        'content': content,
        'bug_position': bug_position,
        'length': len(content),
        'additional_padding': additional_padding
    }
    return data 


# # Testing functions

# In[ ]:


file = make_file_with_padding(3968, 28000, 20000, 400, False)
print(len(file['content']))
print(file['content'])


# In[ ]:


def is_bug_in_correct_position(file_content, buggy_line, target_bug_position):
    """Check if the buggy line is in the desired position in the generated file."""
    buggy_position = file_content.find(buggy_line)
    return target_bug_position <= buggy_position < target_bug_position + 500

def generate_file_with_padding_for_one_id(file_id):
    # Define the tolerance for the file length
    tolerance = 400
    tolerance_length = 200

    # Get the file information for the specified file ID
    file_info = files_dict.get(file_id)
    if not file_info:
        print(f"No information found for file ID {file_id}")
        return

    # Define the maximum number of characters for the file
    max_chars = 30000

    # Generate files with bug in range of position 500 to max_chars, with step size of 500
    for target_bug_position in range(500, max_chars, 500):
        try:
            # Generate the file with the desired padding and bug position
            file = make_file_with_padding(file_id, max_chars, target_bug_position, tolerance_length, debug=True)
            file_content = file['content']

            # Check if the bug is in the desired position
            if not is_bug_in_correct_position(file_content, file_info['buggy_line'], target_bug_position):
                print(f"Bug not in correct position for file ID {file_id} with target position {target_bug_position}")

            # Check if the file has the proper length within the given tolerance
            if abs(len(file_content) - max_chars) > tolerance:
                print(f"File length out of tolerance (due to new lines only!) for file ID {file_id} with target position {target_bug_position}: {abs(len(file_content) - max_chars)} > {tolerance}")
            else:
                print(f"File generated successfully for file ID {file_id} with target position {target_bug_position}")

        except AssertionError as e:
            print(f"Assertion error for file ID {file_id} with target position {target_bug_position}: {e}")
        except Exception as e:
            print(f"Error generating file for file ID {file_id} with target position {target_bug_position}: {e}")




# In[ ]:


# Specify the file ID you want to run this for
file_id_to_test = 4921

# Call the function to generate the file for the specified file ID
generate_file_with_padding_for_one_id(file_id_to_test)


# # Generate sample data

# In[ ]:


# for each file generate following range of files
# max chars 30000
# place bug each 500 chars
# place everything into dataframe with content, file_id, target_bug_pos, bug_pos, target_length, length, additional_padding
# save into csv with file_id as first column
files_list = []
max_chars = 25000
tolerance = 200
for file_id in files_dict.keys():
    print("*"*50)
    print(f"Running for file ID {file_id}")
    for i in range(0, max_chars-1, 500):
        print(f"Running for target position {i}")
        file = make_file_with_padding(file_id, max_chars, i, 200, True)
        # add certain infroaation to the dict
        file['database_file_id'] = file_id
        file['target_bug_position'] = i
        file['target_length'] = max_chars
        file['CWE_ID'] = files_dict[file_id]['CWE_ID']
        files_list.append(file)

import pandas as pd
df = pd.DataFrame(files_list)


# In[ ]:


# !Run only if if csv is not existing yet

# df.insert(0, 'file_id', range(0,  len(df)))
# # # save to csv files.csv
# df.to_csv('files.csv', index=False)


# In[ ]:


# Load the existing data
existing_df = pd.read_csv('data_to_process/files.csv')

# Ensure file_id is treated as an integer
existing_df['file_id'] = existing_df['file_id'].fillna(-1).astype(int)  # Use a placeholder if there are NaNs

# Generate new data (assuming new data is in `files_list` as you described)
new_data = pd.DataFrame(files_list)

# Add temporary file_id of -1 to new data to mark them as new
new_data['file_id'] = -1

# Combine old and new data
combined_df = pd.concat([existing_df, new_data], ignore_index=True)

# Drop duplicates based on the specified keys
combined_df.drop_duplicates(subset=['target_length', 'target_bug_position', 'database_file_id'], inplace=True)

# Find the maximum file_id from the existing data
max_file_id = existing_df['file_id'].max()

# Increment file_id for new rows only
new_rows_mask = combined_df['file_id'] == -1
combined_df.loc[new_rows_mask, 'file_id'] = range(max_file_id + 1, max_file_id + 1 + sum(new_rows_mask))

# Ensure the 'file_id' column is the first column
combined_df = combined_df.sort_values('file_id').reset_index(drop=True)

# Save the combined data to CSV
combined_df.to_csv('data_to_process/files.csv', index=False)


# In[ ]:


# verify current dataset
current_df = pd.read_csv('data_to_process/files.csv')
current_df

