from MARS.results.path_utils import process_mars_paths
from MARS.results.metrics_utils import process_mars_metrics
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
    if os.path.exists(vocab_dir + 'meta_mapping.json'):
        meta_mapping = json.load(open(vocab_dir + 'meta_mapping.json'))
    else:
        meta_mapping = None
    return meta_mapping, results_dir


def main():
    meta_mapping, results_dir = get_filepaths()
    process_mars_metrics(results_dir)
    process_mars_paths(results_dir, meta_mapping)


if __name__ == '__main__':
    main()