from MARS.results.path_utils import process_mars_paths, get_shortest_path_lengths
from MARS.results.metrics_utils import get_metrics_by_length, get_metrics_dict
from MARS.options import read_options
import os
import json
import logging
import sys
import ast
import numpy as np


logger = logging.getLogger(__name__)
logging.basicConfig(stream=sys.stdout, level=logging.DEBUG)


def get_filepaths():

    options = read_options()
    path_length = int(options['path_length'][0])
    experiment_dir = options['base_output_dir']
    vocab_dir = options['input_dir'] + 'vocab/'

    kg_file = options['input_dir'] + 'graph.txt'
    test_edges = options['input_dir'] + 'test.txt'
    if os.path.exists(vocab_dir + 'meta_mapping.json'):
        meta_mapping = json.load(open(vocab_dir + 'meta_mapping.json'))
    else:
        meta_mapping = None
    if os.path.exists(options['input_dir'] + 'validation_paths.json'):
        validation_paths = json.load(open(options['input_dir'] + 'validation_paths.json'))
        validation_paths = {ast.literal_eval(key): val for key, val in validation_paths.items()}
    else:
        validation_paths = None
    return experiment_dir, path_length, kg_file, test_edges, meta_mapping, validation_paths


def main():
    # get the file paths from the input configs
    experiment_dir, path_length, kg_file, test_edges, meta_mapping, validation_paths = get_filepaths()
    _, answer_positions = process_mars_paths(experiment_dir, meta_mapping, validation_paths)
    # get summary metrics across multiple runs in the output folder
    _, metrics_df = get_metrics_dict(experiment_dir)
    spath_lengths = get_shortest_path_lengths(kg_file, test_edges, path_length)
    metrics_by_len = get_metrics_by_length(answer_positions, spath_lengths)

    print('+++++++++  OVERALL METRICS:  +++++++++')
    print(metrics_df)

    print('\n')
    print('+++++++++  METRICS BY PATH LENGTH:  +++++++++')
    print(metrics_by_len)


if __name__ == '__main__':
    main()