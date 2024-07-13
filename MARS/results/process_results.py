from MARS.results.path_utils import process_mars_paths
from MARS.results.metrics_utils import get_metrics_dict
from MARS.options import read_options
import os
import json
import logging
import sys


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
    return meta_mapping, experiment_dir


def main():
    meta_mapping, experiment_dir = get_filepaths()
    scores = get_metrics_dict(experiment_dir)
    process_mars_paths(experiment_dir, meta_mapping)

    print(scores)


if __name__ == '__main__':
    main()