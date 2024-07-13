from MARS.results.path_utils import process_mars_paths
from MARS.results.metrics_utils import get_metrics_dict
from MARS.options import read_options
import os
import json
import logging
import sys
import ast


logger = logging.getLogger(__name__)
logging.basicConfig(stream=sys.stdout, level=logging.DEBUG)


def get_filepaths():
    options = read_options()
    experiment_dir = options['base_output_dir']
    vocab_dir = options['input_dir'] + 'vocab/'
    if os.path.exists(vocab_dir + 'meta_mapping.json'):
        meta_mapping = json.load(open(vocab_dir + 'meta_mapping.json'))
    else:
        meta_mapping = None
    if os.path.exists(options['input_dir'] + 'validation_paths.json'):
        validation_paths = json.load(open(options['input_dir'] + 'validation_paths.json'))
        validation_paths = {ast.literal_eval(key): val for key, val in validation_paths.items()}
    else:
        validation_paths = None
    return experiment_dir, meta_mapping, validation_paths


def main():
    experiment_dir, meta_mapping, validation_paths = get_filepaths()
    process_mars_paths(experiment_dir, meta_mapping, validation_paths)
    get_metrics_dict(experiment_dir)


if __name__ == '__main__':
    main()