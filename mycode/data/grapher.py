import csv
import numpy as np
from collections import defaultdict


"""The script responsible for generating the graph structure"""


class RelationEntityGrapher(object):
    def __init__(self, triple_store, entity_vocab, relation_vocab, max_num_actions):
        """Initializes the creation of the graph.
            :param triple_store: the file location of the KG triples
            :param entity_vocab: the file location of the ID mappings for entities
            :param relation_vocab: the file location of the ID mappings for relations
            :param max_num_actions: the max number of outgoing edges from a given entity- why?
                I don't know, maybe to mimimize the graph size. 
        """
        self.ePAD = entity_vocab['PAD']  # the ID of the PAD token for entities
        self.rPAD = relation_vocab['PAD']  # the ID of the PAD token for relations
        self.triple_store = triple_store
        self.entity_vocab = entity_vocab
        self.relation_vocab = relation_vocab
        # self.store is a dictionary storing all the connections from a node
        self.store = defaultdict(list)
        # self.array_store is a 3D array initialized with the PAD values
        # it contains a 2D matrix for entities and relations each
        self.array_store = np.ones((len(entity_vocab), max_num_actions, 2), dtype=np.dtype('int32'))
        self.array_store[:, :, 0] *= self.ePAD
        self.array_store[:, :, 1] *= self.rPAD
        self.masked_array_store = None

        self.rev_entity_vocab = dict([(v, k) for k, v in entity_vocab.items()])
        self.rev_relation_vocab = dict([(v, k) for k, v in relation_vocab.items()])
        self.create_graph()
        print("KG constructed.")

    def create_graph(self):
        """Stores all of the triples in self.array_store so that the matrix values
            are either the receiving node or the relation, and
            the relation connecting the two nodes is in the same position in its
            respective matrix as the entity toward which the edge is going
        """
        with open(self.triple_store) as triple_file_raw:
            triple_file = csv.reader(triple_file_raw, delimiter='\t')
            for line in triple_file:
                # parse and map each to its unique ID
                e1 = self.entity_vocab[line[0]]
                r = self.relation_vocab[line[1]]
                e2 = self.entity_vocab[line[2]]
                # store each connection from the starting node
                self.store[e1].append((r, e2))

        for e1 in self.store:  # (for every key in the dict)
            self.array_store[e1, 0, 1] = self.relation_vocab['NO_OP']
            self.array_store[e1, 0, 0] = e1
            num_actions = 1
            for r, e2 in self.store[e1]:
                # if we reached the max number of actions, stop
                # is the below the ONLY reason we are storing num actions?
                if num_actions == self.array_store.shape[1]:
                    break
                # store the number of the current outgoing edge- but why?
                self.array_store[e1, num_actions, 0] = e2
                self.array_store[e1, num_actions, 1] = r
                num_actions += 1
        # delete self.store because it contains redundant info
        del self.store
        self.store = None

    def return_next_actions(self, current_entities, start_entities, query_relations, answers, all_correct_answers,
                            is_last_step, rollouts):
        """Using the matrices in self.array_store, return the actions that could be taken
            by the agent from a given node.
        :param current_entities: a list of the entities which the agent is currently considering
        :param start_entities: a list of the entities which the agent began with
        :param query_relations: a dictionary?
        :param answers: another dictionary
        :param all_correct_answers:
        :param is_last_step:
        """
        # get only the connections from the entities currently being considered
        ret = self.array_store[current_entities, :, :].copy()
        for i in range(current_entities.shape[0]):
            # if we haven't traversed that node yet, 
            if current_entities[i] == start_entities[i]:
                entities = ret[i, :, 0]
                relations = ret[i, :, 1]
                mask = np.logical_and(relations == query_relations[i], entities == answers[i])
                ret[i, :, 0][mask] = self.ePAD
                ret[i, :, 1][mask] = self.rPAD
            if is_last_step:
                entities = ret[i, :, 0]
                correct_e2 = answers[i]
                for j in range(entities.shape[0]):
                    if entities[j] in all_correct_answers[i // rollouts] and entities[j] != correct_e2:
                        ret[i, :, 0][j] = self.ePAD
                        ret[i, :, 1][j] = self.rPAD
        return ret
