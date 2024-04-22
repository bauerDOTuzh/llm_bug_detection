import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
import statsmodels.api as sm
import sys

gpt_id = sys.argv[1]
model = f'gpt-{gpt_id}-turbo'

target_variable = 'tp'
bug_line_type = 'min_bug_line_pos'

# Load the data from the uploaded CSV files
data_cwe_22 = pd.read_csv(f'../data/data_CWE-22_model-{model}.csv')
data_cwe_79 = pd.read_csv(f'../data/data_CWE-79_model-{model}.csv')
data_cwe_89 = pd.read_csv(f'../data/data_CWE-89_model-{model}.csv')

# Function to plot logistic regression with significance testing
def plot_logistic_regression(data, x_col, y_col, label, ax, color):
    # Prepare data: Add a constant term for the intercept
    X = sm.add_constant(data[x_col])
    y = data[y_col]
    
    # Fit logistic regression model
    model = sm.Logit(y, X).fit(disp=0)  # disp=0 suppresses fit information
    
    # Generate predictions for a range of input values
    x_values = np.linspace(data[x_col].min(), data[x_col].max(), 300)
    x_values_with_const = sm.add_constant(x_values)
    y_probs = model.predict(x_values_with_const)
    
    # Plot
    ax.plot(x_values, y_probs, label=f"{label} (p={model.pvalues[x_col]:.3f})", color=color, linewidth=2)
    
    return model

# Create figure for plots
fig, axes = plt.subplots(1, 2, figsize=(16, 7), dpi=100)

# Colors for the plots
colors = ['blue', 'orange', 'green']

# Plot logistic regressions for file length vs TP
plot_logistic_regression(data_cwe_22, 'input_len', target_variable, 'CWE-22: Path Traversal', axes[0], colors[0])
plot_logistic_regression(data_cwe_89, 'input_len', target_variable, 'CWE-89: SQL Injection', axes[0], colors[1])
plot_logistic_regression(data_cwe_79, 'input_len', target_variable, 'CWE-79: XSS', axes[0], colors[2])
axes[0].set_xlabel('File Size')
axes[0].set_ylabel('Probability of Finding the Bug')
axes[0].set_title('File Size vs Probability of Finding the Bug')
axes[0].legend()

# Plot logistic regressions for bug line vs TP
plot_logistic_regression(data_cwe_22, bug_line_type, target_variable, 'CWE-22: Path Traversal', axes[1], colors[0])
plot_logistic_regression(data_cwe_89, bug_line_type, target_variable, 'CWE-89: SQL Injection', axes[1], colors[1])
plot_logistic_regression(data_cwe_79, bug_line_type, target_variable, 'CWE-79: XSS', axes[1], colors[2])
axes[1].set_xlabel('Bug-Line Position')
axes[1].set_ylabel('Probability of Finding the Bug')
axes[1].set_title('Bug-Line Position vs Probability of Finding the Bug')
axes[1].legend()

# Adding a general title
plt.suptitle(f'Logistic Regression Analysis of Bug Detection - ChatGPT {gpt_id}', fontsize=16, y=1.05)

# Enhance layout and display plot
plt.tight_layout()
# plt.show()
plt.savefig(f'logistic-regression_model-{model}_target-{target_variable}.pdf')

# Data for the frequency of each CWE type
cwe_frequencies = {
    "CWE-22 (Path Traversal)": len(data_cwe_22),
    "CWE-89 (SQL Injection)": len(data_cwe_89),
    "CWE-79 (XSS)": len(data_cwe_79)
}

# Create a bar chart for the frequencies
fig, ax = plt.subplots(figsize=(10, 6))

# Colors for the bar chart
bar_colors = [colors[0], colors[1], colors[2]]

# Plotting the bar chart
ax.bar(cwe_frequencies.keys(), cwe_frequencies.values(), color=bar_colors)

# Adding labels and title
# ax.set_xlabel('Bug Type (CWE)', fontsize=12)
ax.set_ylabel('Frequency (Number of Files)', fontsize=12)
ax.set_title('Frequency of Different Bug Types', fontsize=16)
ax.set_ylim(0, 600)  # Set y-axis limit to make space for text annotations

# Text annotation for frequencies
for i, v in enumerate(cwe_frequencies.values()):
    ax.text(i, v + 25, str(v), color='black', ha='center')

# Show the plot
plt.tight_layout()
# plt.show()
plt.savefig(f'frequency_bar_chart.pdf')

# import pandas as pd
# import numpy as np
# import matplotlib.pyplot as plt
# import statsmodels.api as sm

# # Load the data
# data_cwe_22 = pd.read_csv('data_CWE-22_model-gpt-3.5-turbo.csv')
# data_cwe_22_gpt4 = pd.read_csv('data_CWE-22_model-gpt-4-turbo.csv')
# data_cwe_79 = pd.read_csv('data_CWE-79_model-gpt-3.5-turbo.csv')
# data_cwe_79_gpt4 = pd.read_csv('data_CWE-79_model-gpt-4-turbo.csv')
# data_cwe_89 = pd.read_csv('data_CWE-89_model-gpt-3.5-turbo.csv')
# data_cwe_89_gpt4 = pd.read_csv('data_CWE-89_model-gpt-4-turbo.csv')

# # Function to perform logistic regression and plot
# def plot_logistic_regression_combined(data_gpt35, data_gpt4, x_col, y_col, label_base, ax, colors):
#     # Normalize bug line position by dividing by max_line to get proportion of position for both versions
#     data_gpt35['normalized_bug_line'] = data_gpt35[x_col] / data_gpt35['max_line']
#     data_gpt4['normalized_bug_line'] = data_gpt4[x_col] / data_gpt4['max_line']
    
#     # Prepare data and fit logistic regression model for GPT-3.5
#     X_35 = sm.add_constant(data_gpt35['normalized_bug_line'])
#     y_35 = data_gpt35[y_col]
#     model_35 = sm.Logit(y_35, X_35).fit(disp=0)
#     x_values_35 = np.linspace(0, 1, 300)
#     y_probs_35 = model_35.predict(sm.add_constant(x_values_35))
    
#     # Prepare data and fit logistic regression model for GPT-4
#     X_4 = sm.add_constant(data_gpt4['normalized_bug_line'])
#     y_4 = data_gpt4[y_col]
#     model_4 = sm.Logit(y_4, X_4).fit(disp=0)
#     x_values_4 = np.linspace(0, 1, 300)
#     y_probs_4 = model_4.predict(sm.add_constant(x_values_4))
    
#     # Plot both models on the same axes
#     ax.plot(x_values_35, y_probs_35, label=f'{label_base} GPT-3.5', color=colors[0], linestyle='-', linewidth=2)
#     ax.plot(x_values_4, y_probs_4, label=f'{label_base} GPT-4', color=colors[1], linestyle='--', linewidth=2)

# # Create figure for the combined plot
# fig, ax = plt.subplots(figsize=(12, 7), dpi=100)

# # Colors for each CWE type
# color_sets = [
#     ('royalblue', 'lightblue'),    # Colors for CWE-22
#     ('darkorange', 'navajowhite'), # Colors for CWE-89
#     ('forestgreen', 'limegreen')  # Colors for CWE-79
# ]

# # Plot all models on the same axes
# plot_logistic_regression_combined(data_cwe_22, data_cwe_22_gpt4, 'bug_line', 'tp', 'CWE-22 (Easy)', ax, color_sets[0])
# plot_logistic_regression_combined(data_cwe_89, data_cwe_89_gpt4, 'bug_line', 'tp', 'CWE-89 (Medium)', ax, color_sets[1])
# plot_logistic_regression_combined(data_cwe_79, data_cwe_79_gpt4, 'bug_line', 'tp', 'CWE-79 (Hard)', ax, color_sets[2])

# # Setting labels, title and legend
# ax.set_xlabel('Normalized Bug Line Position (Proportion of File Length)')
# ax.set_ylabel('Probability of TP')
# ax.set_title('Comparative Probability of Bug Detection vs Normalized Bug Line Position')
# ax.legend()

# # Show the plot
# plt.show()
