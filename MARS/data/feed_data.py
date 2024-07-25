import csv
import networkx as nx
import numpy as np
from collections import defaultdict


"""The data loader script which separates the indication triples into training and test datasets"""


class RelationEntityBatcher(object):
    def __init__(self, input_dir, batch_size, entity_vocab, relation_vocab, nx_graph, mode="train"):
        """Creates the training or test dataset
        :param input_dir: the input directory where the data files are
        :param batch_size: the size of the sampled batch (specified by user in configs)
        :param entity_vocab: dictionary mapping the entities to their unique IDs
        :param relation_vocab: dictionary mapping the relations to their unique IDs
        :param nx_graph = the networkx graph object representing the whole KG
        :param mode: whether it should be for the training set or the test set
        """
        self.input_dir = input_dir
        # get the appropriate training or test data, split beforehand
        self.input_file = input_dir+'{}.txt'.format(mode)
        self.batch_size = batch_size
        print('Reading vocab...')
        self.entity_vocab = entity_vocab
        self.relation_vocab = relation_vocab
        self.KG = nx_graph
        self.mode = mode
        self.create_triple_store(self.input_file)
        print("Batcher loaded.")

    def get_next_batch(self):
        """generator which yields the next batch of data"""
        if self.mode == 'train':
            yield self.yield_next_batch_train()
        else:
            yield self.yield_next_batch_test()

    def create_triple_store(self, input_file):
        """Creates two data types: 
            - self.store_all_correct , which contains all possible reachable sink nodes, given an entity and relation
            - self.store , a list of all the triples (as nested lists) in the considered set
        """
        # store_all_correct contains, for each entity and relation, a set of sink entities reachable 
        self.store_all_correct = defaultdict(set)
        # store simply contains all triples in the KG
        self.store = []
        with open(input_file) as raw_input_file:
            csv_file = csv.reader(raw_input_file, delimiter='\t')
            no_path = 0
            if self.mode == 'train':
                for line in csv_file:
                    # read in each triple and map it to its unique ID
                    e1 = self.entity_vocab[line[0]]
                    r = self.relation_vocab[line[1]]
                    e2 = self.entity_vocab[line[2]]
                    if e1 in self.KG and e2 in self.KG and nx.has_path(self.KG, e1, e2) and nx.shortest_path_length(self.KG, e1, e2) <= 4:
                        self.store.append([e1, r, e2])
                        # this line is unique to the training set- we only want the labels in the training set so no leakage
                        self.store_all_correct[(e1, r)].add(e2)
                    else:
                        no_path += 1
                self.store = np.array(self.store)
            else:
                for line in csv_file:
                    e1 = line[0]
                    r = line[1]
                    e2 = line[2]
                    if (e1 in self.entity_vocab) and (e2 in self.entity_vocab):
                        e1 = self.entity_vocab[e1]
                        r = self.relation_vocab[r]
                        e2 = self.entity_vocab[e2]
                        if e1 in self.KG and e2 in self.KG and nx.has_path(self.KG, e1, e2) and nx.shortest_path_length(self.KG, e1, e2) <= 4:
                            self.store.append([e1, r, e2])
                        else:
                            no_path += 1
                self.store = np.array(self.store)

                # all files which store triples of some form
                fact_files = ['train', 'dev', 'test', 'graph']
                for f in fact_files:
                    with open(self.input_dir + f + '.txt') as raw_input:
                        csv_file = csv.reader(raw_input, delimiter='\t')
                        for line in csv_file:
                            e1 = line[0]
                            r = line[1]
                            e2 = line[2]
                            if (e1 in self.entity_vocab) and (e2 in self.entity_vocab):
                                e1 = self.entity_vocab[e1]
                                r = self.relation_vocab[r]
                                e2 = self.entity_vocab[e2]
                                if e1 in self.KG and e2 in self.KG and nx.has_path(self.KG, e1, e2) and nx.shortest_path_length(self.KG, e1, e2) <= 4:
                                    # here, we now store ALL possible labels 
                                    self.store_all_correct[(e1, r)].add(e2)

            if no_path > 0:
                print(f'WARNING: {no_path} triples in the {self.mode} are disconnected and were ommitted.')
                

    def yield_next_batch_train(self):
        """Generates the next batch of training data as unique IDs:
        - e1 is a list of all triple source nodes in the batch
        - r is a list of all triple relations in the batch
        - e2 is a list of all triple sink nodes in the batch
        - all_e2s is a list of sets, in which each set corresponds to all possible sink nodes which are reachable
            from the source node and relation in the corresponding index of the e1 and r lists

        this generator has no limit and can therefore loop until training terminates
        """
        while True:
            batch_idx = np.random.randint(0, self.store.shape[0], size=self.batch_size)
            # get the triples in this batch
            batch = self.store[batch_idx, :]
            e1 = batch[:, 0]  # the 0th element of each nested list
            r = batch[:, 1]  # the 1st element of each nested list
            e2 = batch[:, 2]  # the 2nd element of each nested list
            all_e2s = []
            for i in range(e1.shape[0]):
                all_e2s.append(self.store_all_correct[(e1[i], r[i])])
            assert e1.shape[0] == e2.shape[0] == r.shape[0] == len(all_e2s)
            yield e1, r, e2, all_e2s

    def yield_next_batch_test(self):
        """Generates the next batch of test data as unique IDs:
        - e1 is a list of all triple source nodes in the batch
        - r is a list of all triple relations in the batch
        - e2 is a list of all triple sink nodes in the batch
        - all_e2s is a list of sets, in which each set corresponds to all possible sink nodes which are reachable
            from the source node and relation in the corresponding index of the e1 and r lists

        this generator stops when all test data has been used.
        """
        remaining_triples = self.store.shape[0]
        current_idx = 0
        while True:
            # runs out when all test data has been used
            if remaining_triples == 0:
                return
            if remaining_triples - self.batch_size > 0:
                batch_idx = np.arange(current_idx, current_idx + self.batch_size)
                current_idx += self.batch_size
                remaining_triples -= self.batch_size
            else:
                batch_idx = np.arange(current_idx, self.store.shape[0])
                remaining_triples = 0
            batch = self.store[batch_idx, :]
            e1 = batch[:, 0]
            r = batch[:, 1]
            e2 = batch[:, 2]
            all_e2s = []
            for i in range(e1.shape[0]):
                all_e2s.append(self.store_all_correct[(e1[i], r[i])])
            assert e1.shape[0] == e2.shape[0] == r.shape[0] == len(all_e2s)
            yield e1, r, e2, all_e2s
