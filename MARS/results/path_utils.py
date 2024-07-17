import os.path as osp
import os
from collections import Counter
import json
import networkx as nx
import re
import matplotlib.pyplot as plt
import pandas as pd
from collections import defaultdict

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
    answer_positions = dict()

    for chunk in chunks:
        srt = 0
        current_pair = tuple(chunk[0].split())
        pred_paths[current_pair] = {"nodes": [], "relations": []}
        answer_position = int(chunk[2].strip().split(':')[1])
        answer_positions[current_pair] = answer_position
        chunk = chunk[3::]
        breakpoints = [i for i, line in enumerate(chunk) if line.startswith("___")]
        for brk in breakpoints:
            entry = chunk[srt:brk]
            if (not correct_only) or (correct_only and entry[2].strip() == "1"):
                pred_paths[current_pair]["nodes"].append(entry[0].strip().split("\t"))
                pred_paths[current_pair]["relations"].append(
                    entry[1].strip().split("\t")
                )
            srt = brk + 1

    return pred_paths, answer_positions


def get_shortest_path_lengths(kg_file, test_edges, max_path_length):
    """Gets a dictionary mapping of the shortest path lengths between the test edges"""
    G = get_nx_graph(kg_file)
    test_edges = pd.read_csv(test_edges, sep="\t", header=None)

    unmatched_pairs = set()

    path_lengths = defaultdict(set)

    for i, row in test_edges.iterrows():
        if not nx.has_path(G, row[0], row[2]):
            unmatched_pairs.add(i)
            continue
        if nx.shortest_path_length(G, row[0], row[2]) > max_path_length:
            unmatched_pairs.add(i)
        path_lengths[nx.shortest_path_length(G, row[0], row[2])].add((row[0], row[2]))

    print(f'WARNING: {len(unmatched_pairs)} test pairs could not be matched with a path of length <= {max_path_length}')

    return path_lengths


def get_nx_graph(kg_file):
    """Breaks down the KG into a networkx graph"""
    kg = pd.read_csv(kg_file, sep="\t", header=None)

    G = nx.DiGraph()

    for i, row in kg.iterrows():
        src_id = row[0]
        trgt_id = row[2]
        if src_id not in G.nodes:
            G.add_node(src_id)
        if trgt_id not in G.nodes:
            G.add_node(trgt_id)
        G.add_edge(src_id, trgt_id, type=row[1])
        G.add_edge(trgt_id, src_id, type=f"_{row[1]}")

    return G


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


def moa_comparison(pred_paths, validation_paths):
    """Compares the MOAS between the results and the DrugMechDB

    :param pred_paths: the dictionary of predicted paths from the first function
    :param validation_paths: the dictionary of validation paths from the DrugMechDB, which should be included in this repo.
    """
    found_keys = set(pred_paths.keys()) & validation_paths.keys()
    real_moas = {
        key: val["nodes"] for key, val in validation_paths.items() if key in found_keys
    }
    pred_moas = {
        key: val["nodes"] for key, val in pred_paths.items() if key in found_keys
    }

    matches = dict()
    for key in found_keys:
        true_prots = {i for i in real_moas[key] if i.startswith("ncbigene:")}
        matches[key] = []
        for pred in pred_moas[key]:
            pred_prots = {i for i in pred if i.startswith("ncbigene:")}
            matches[key].append(
                len(true_prots.intersection(pred_prots)) / len(true_prots)
            )

    return matches


def process_mars_paths(experiment_dir, meta_mapping, validation_paths, correct_only=True):
    """Wrapper function for all above functions

    Goes through all runs of the experiment and outputs collective results in directory.
    """
    paths_path = osp.join(experiment_dir, "paths.json")
    patterns_path = osp.join(experiment_dir, "pattern_counts.json")
    patterns_hist_path = osp.join(experiment_dir, "pattern_counts.png")
    moa_matches_path = osp.join(experiment_dir, "moa_matches.json")

    paths = dict()
    patterns = Counter()
    matches = dict()

    # all experimental runs
    runs = os.listdir(experiment_dir)

    for run in runs:
        current_run = osp.join(experiment_dir, run)
        if not osp.isdir(current_run) or 'TEST' not in current_run:
            continue
        # for each run in an experiment dir, get the paths dir
        fpath = osp.join(experiment_dir, f"{run}/test_beam/paths_CtBP")

        # get all of the paths per pair
        pred_paths, answer_positions = get_paths(file_path=fpath, correct_only=correct_only)
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

        if validation_paths:
            # get the matches against the DrugMechDB
            moa_matches = moa_comparison(pred_paths, validation_paths)
            for key, val in moa_matches.items():
                if key not in matches:
                    matches[key] = val
                else:
                    matches[key].extend(val)
            matches = {str(key): val for key, val in matches.items()}
            write_json(moa_matches_path, matches)

        print(answer_positions)

    # write paths to files
    paths = {str(key): val for key, val in paths.items()}

    write_json(paths_path, paths)
    write_json(patterns_path, patterns)
    plot_pattern_breakdown(patterns, patterns_hist_path)

    return paths