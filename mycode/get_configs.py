import os
import json

best_configs = None
best_score = 0

# Specify the parent directory
parent_directory = '../output/MOA-net'

# Loop through subdirectories
for subdir in os.listdir(parent_directory):
    subdir_path = os.path.join(parent_directory, subdir)
    
    # Check if it's a directory and starts with "14"
    if os.path.isdir(subdir_path) and subdir.startswith("14"):
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
                        print("Last Hits@10 line:", line.strip())
                        metric = int(line.split()[1])
                        if metric > best_score:
                            best_score = metric
                            # read json file
                            with open(configs_file_path, 'r') as configs_file:
                                best_configs = json.load(configs_file)

# write a json file
best_configs_filepath = os.path.join(parent_directory, "best_configs.json")
with open(best_configs_filepath, 'w') as best_configs_file:
    json.dump(best_configs, best_configs_file)
