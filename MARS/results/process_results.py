from MARS.results.path_utils import process_polo_paths
from MARS.results.metrics_utils import process_polo_metrics
from MARS.options import read_options
import os
import json
import logging
import sys


logger = logging.getLogger(__name__)
logging.basicConfig(stream=sys.stdout, level=logging.DEBUG)


def get_filepaths():
    options = read_options()
    results_dir = options['base_output_dir']
    vocab_dir = options['input_dir'] + 'vocab/'
    if os.path.exists(vocab_dir + 'node_mapping.json'):
        node_mapping = json.load(open(vocab_dir + 'node_mapping.json'))
    else:
        node_mapping = None
    if os.path.exists(vocab_dir + 'relation_mapping.json'):
        relation_mapping = json.load(open(vocab_dir + 'relation_mapping.json'))
    else:
        relation_mapping = None
    return node_mapping, relation_mapping, results_dir


def main():
    node_mapping, relation_mapping, results_dir = get_filepaths()
    process_polo_metrics(results_dir)
    process_polo_paths(results_dir, node_mapping, relation_mapping)


if __name__ == '__main__':
    main()