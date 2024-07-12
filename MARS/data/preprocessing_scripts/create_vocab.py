import json
import csv
import os


"""
    This script creates the vocab json files which map each entity and relation
    to unique IDs within the dataset directories.
"""


# TODO: fix so it is not relative path
dataset_dir = '../../../datasets/Hetionet/'
vocab_dir = dataset_dir + 'vocab/'

if not os.path.isdir(vocab_dir):
    os.makedirs(vocab_dir)

entity_vocab = {}
relation_vocab = {}

entity_vocab['PAD'] = len(entity_vocab)  # why did they not just say 0 and 1?
entity_vocab['UNK'] = len(entity_vocab)  # 1
relation_vocab['PAD'] = len(relation_vocab)  # 0
relation_vocab['DUMMY_START_RELATION'] = len(relation_vocab)  # 1
relation_vocab['NO_OP'] = len(relation_vocab)  # 2
relation_vocab['UNK'] = len(relation_vocab)  # 3

entity_counter = len(entity_vocab)  # 2
relation_counter = len(relation_vocab)  # 4

for f in ['train.txt', 'dev.txt', 'test.txt', 'graph.txt']:
    with open(dataset_dir + f) as raw_file:
        csv_file = csv.reader(raw_file, delimiter='\t')
        for line in csv_file:
            e1, r, e2 = line
            # TODO below: change to entity_vocab[e1] = len(entity_vocab) if e1 not in entity_vocab
            if e1 not in entity_vocab:
                entity_vocab[e1] = entity_counter
                entity_counter += 1
            if e2 not in entity_vocab:
                entity_vocab[e2] = entity_counter
                entity_counter += 1
            if r not in relation_vocab:
                relation_vocab[r] = relation_counter
                relation_counter += 1

with open(vocab_dir + 'entity_vocab.json', 'w') as fout:
    json.dump(entity_vocab, fout)

with open(vocab_dir + 'relation_vocab.json', 'w') as fout:
    json.dump(relation_vocab, fout)


