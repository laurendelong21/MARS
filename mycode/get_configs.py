import os
import json

best_configs = None
best_score = 0

top_configs = dict()

# Specify the parent directory
parent_directory = '../output/MOA-net'

# Loop through subdirectories
for subdir in os.listdir(parent_directory):
    subdir_path = os.path.join(parent_directory, subdir)
    
    # Check if it's a directory and starts with "14"
    if os.path.isdir(subdir_path) and subdir.startswith("15"):
        scores_file_path = os.path.join(subdir_path, "scores.txt")
        configs_file_path = os.path.join(subdir_path, "config.txt")
        
        # Check if "scores.txt" exists
        if os.path.exists(scores_file_path):
            with open(scores_file_path, 'r') as scores_file:
                lines = scores_file.readlines()
                
                # Search for "Hits@10:" and print the last occurrence
                for line in reversed(lines):
                    if "Hits@10:" in line:
                        print("Subdirectory:", subdir_path)
                        metric = float(line.split()[1])
                        print(f"Hits@10: {metric}")
                        if metric > best_score:
                            best_score = metric
                            best_configs = configs_file_path
                        top_configs[metric] = configs_file_path

print("Best configs file:")
print(best_configs)

print("Top 5 configs files:")
largest_keys = sorted(top_configs.keys(), reverse=True)[:5]
for key in largest_keys:
    print(top_configs[key])
    print(key)
