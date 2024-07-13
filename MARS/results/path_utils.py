import os.path as osp
import os
import statistics
from collections import Counter
import json
import numpy as np
from collections import defaultdict
import re
import matplotlib.pyplot as plt

"""Processes the results into a more human-readable format"""


def write_json(filepath, data_dict):
    """Writes dict to json"""
    with open(filepath, "w") as json_file:
        json.dump(data_dict, json_file, indent=4)


def get_rel_mapping(item_to_map, meta_mapping=None):
    """Gets the relation mapping for the KG."""
    capital_groups = re.findall('[A-Z]+', item_to_map)
    predicate = re.findall('[a-z]+', item_to_map)[0]
    if meta_mapping:
        capital_groups = [meta_mapping[i] for i in capital_groups]
        predicate = meta_mapping[predicate]
    mapped_item = f"-{predicate}-".join(capital_groups)
    if "_" in item_to_map:
        mapped_item += "*"
    return mapped_item


def get_paths(file_path, correct_only=True):
    """Extracts the paths from PoLo's output paths file.
    :param file_path: the path of the output file
    :param correct_only: boolean flag to determine whether or not to extract paths from correct matches only.

    returns a dict of the test pairs as keys and lists of the path patterns traversed as keys
    """
    with open(file_path, "r") as file:
        lines = file.readlines()

    breakpoints = [
        i for i, line in enumerate(lines) if line.startswith("#####################")
    ]

    chunks = []
    startpoint = 0
    for brk in breakpoints:
        chunk = lines[startpoint:brk]
        if not correct_only:
            chunks.append(chunk)
        elif correct_only and chunk[1].strip() == "Reward:1":
            chunks.append(chunk)
        startpoint = brk + 1

    pred_paths = dict()

    for chunk in chunks:
        srt = 0
        current_pair = tuple(chunk[0].split())
        pred_paths[current_pair] = {"nodes": [], "relations": []}
        chunk = chunk[2::]
        breakpoints = [i for i, line in enumerate(chunk) if line.startswith("___")]
        for brk in breakpoints:
            entry = chunk[srt:brk]
            if entry[2].strip() == "1":
                pred_paths[current_pair]["nodes"].append(entry[0].strip().split("\t"))
                pred_paths[current_pair]["relations"].append(
                    entry[1].strip().split("\t")
                )
            srt = brk + 1

    return pred_paths


def get_pattern_breakdown(pred_paths, meta_mapping=None, key=None):
    """Gets a counter of all the path patterns found.

    If key is passed, returns the counter only for that particular test pair.
    """
    if key:
        patterns_traversed = pred_paths[key]["relations"]

    else:
        patterns_traversed = []
        for val in pred_paths.values():
            patterns_traversed.extend(val["relations"])

    patterns_traversed = [
        [rel for rel in i if rel != "NO_OP"] for i in patterns_traversed
    ]
    patterns_traversed = [[get_rel_mapping(rel, meta_mapping) for rel in i] for i in patterns_traversed]
    patterns_traversed = [" -> ".join(i) for i in patterns_traversed]
    return Counter(patterns_traversed)


def plot_pattern_breakdown(pattern_counter, output_path):
    """Makes a histogram of the pattern counts (code written by ChatGPT)"""
    # Separate keys and values
    keys, values = zip(*pattern_counter.items())

    #plt.figure(figsize=(30, 18))

    # Create a histogram
    plt.barh(keys, values)

    # Add labels and a title
    plt.xlabel("Correct Predictions")
    plt.ylabel("Metapaths")
    plt.title("Metapath Instances Traversed Between True Pairs")

    # Rotate x-axis labels by 45 degrees
    plt.xticks(rotation=45)

    # Save the plot to a file (e.g., 'histogram.png')
    plt.savefig(output_path)

    # Close the plot to free up resources
    plt.close()


def process_mars_paths(experiment_dir, meta_mapping, correct_only=True):
    """Wrapper function for all above functions

    Goes through all runs of the experiment and outputs collective results in directory.
    """
    paths_path = osp.join(experiment_dir, "paths.json")
    patterns_path = osp.join(experiment_dir, "pattern_counts.json")
    patterns_hist_path = osp.join(experiment_dir, "pattern_counts.png")
    #moa_matches_path = osp.join(experiment_dir, "moa_matches.json")

    paths = dict()
    patterns = Counter()
    #matches = dict()

    # all experimental runs
    runs = os.listdir(experiment_dir)

    for run in runs:
        current_run = osp.join(experiment_dir, run)
        if not osp.isdir(current_run) or 'TEST' not in current_run:
            continue
        # for each run in an experiment dir, get the paths dir
        fpath = osp.join(experiment_dir, f"{run}/test_beam/paths_CtBP")

        # get all of the paths per pair
        pred_paths = get_paths(file_path=fpath, correct_only=correct_only)
        for key, val in pred_paths.items():
            if key not in paths:
                paths[key] = val
            else:
                paths[key]["nodes"].extend(pred_paths[key]["nodes"])
                paths[key]["relations"].extend(pred_paths[key]["relations"])

        # get the pattern counts
        patterns_traversed = get_pattern_breakdown(pred_paths,
                                                   meta_mapping)
        patterns = patterns + patterns_traversed

        # get the matches against the DrugMechDB
        #moa_matches = moa_comparison(pred_paths, validation_paths)
        #for key, val in moa_matches.items():
        #    if key not in matches:
        #        matches[key] = val
        #    else:
        #        matches[key].extend(val)

    # write everything to files
    paths = {str(key): val for key, val in paths.items()}
    #matches = {str(key): val for key, val in matches.items()}

    write_json(paths_path, paths)
    write_json(patterns_path, patterns)
    plot_pattern_breakdown(patterns, patterns_hist_path)
    #write_json(moa_matches_path, matches)