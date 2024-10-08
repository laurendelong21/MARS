import numpy as np
import networkx as nx
from MARS.data.grapher import RelationEntityGrapher
from MARS.data.feed_data import RelationEntityBatcher

"""Script which defines an Episode which retains information about the state of the search"""

class Episode(object):
    """Object defining the span of the agent trying to find a path 20-30 times"""
    def __init__(self, graph, data, params):
        """Initializes Episode object, which defines the state of the search
        :param graph: the KG, made from the grapher module (RelationEntityGrapher)
        :param data: a 4-part tuple from RelationEntityBatcher containing
            - e1: a list of source nodes taking part in batch triples
            - r: a list of all relations taking part in batch triples
            - e2: a list of sink nodes taking part in batch triples
            - all_answers: a mapping from sink nodes (keys) to tuples of source nodes and relations from which they are reachable
        :param params: user specified configs
        """
        self.grapher = graph
        self.batch_size, self.path_len, num_rollouts, test_rollouts, positive_reward, negative_reward, mode, \
        batcher = params
        self.mode = mode
        if self.mode == 'train':
            self.rollouts = num_rollouts
        else:
            self.rollouts = test_rollouts
        self.current_hop = 0
        self.positive_reward = positive_reward
        self.negative_reward = negative_reward
        # e1s, all relations, e2s, and a mapping from e2s back to all possible source nodes
        start_entities, query_relation,  end_entities, all_answers = data
        self.no_examples = start_entities.shape[0]
        # below creates arrays of all things where it is like [1,1,1,2,2,2,...] which repeats with the num rollouts
        # so num_rollouts is the number of times 
        self.start_entities = np.repeat(start_entities, self.rollouts)
        self.query_relations = np.repeat(query_relation, self.rollouts)
        self.end_entities = np.repeat(end_entities, self.rollouts)
        # starts as the same as start entities, but updates in the call
        self.current_entities = np.repeat(start_entities, self.rollouts)
        self.all_answers = all_answers

        # this returns the self.array_store from grapher which tells us all next possible moves
        next_actions = self.grapher.return_next_actions(self.current_entities, self.start_entities,
                                                        self.query_relations, self.end_entities, self.all_answers,
                                                        self.current_hop == self.path_len - 1, self.rollouts)
        self.states = dict()
        self.states['next_relations'] = next_actions[:, :, 1]
        self.states['next_entities'] = next_actions[:, :, 0]
        self.states['current_entities'] = self.current_entities

    def get_states(self):
        return self.states

    def get_query_relations(self):
        return self.query_relations

    def get_query_objects(self):
        return self.end_entities

    def get_rewards(self):
        """ Returns a rewards list which contains positive values where it found the
            final entity, and negative rewards where it did not
        """
        rewards = (self.current_entities == self.end_entities)
        # Set the True and False values to the values of positive and negative rewards
        condlist = [rewards == True, rewards == False]
        choicelist = [self.positive_reward, self.negative_reward]
        rewards = np.select(condlist, choicelist)   # [B,]
        return rewards

    def __call__(self, action):
        """The function which updates the state of the agent based on each hop"""
        self.current_hop += 1
        # NOTE: self.no_examples * self.rollouts is the num of starting entities times the number of times a query is done
        self.current_entities = self.states['next_entities'][np.arange(self.no_examples * self.rollouts), action]
        next_actions = self.grapher.return_next_actions(self.current_entities, self.start_entities,
                                                        self.query_relations, self.end_entities, self.all_answers,
                                                        self.current_hop == self.path_len - 1, self.rollouts)
        # update the states
        self.states['next_relations'] = next_actions[:, :, 1]
        self.states['next_entities'] = next_actions[:, :, 0]
        self.states['current_entities'] = self.current_entities
        return self.states


class Env(object):
    """sets up the whole environment in which the agent will work"""
    def __init__(self, params, mode='train'):
        self.batch_size = params['batch_size']
        self.num_rollouts = params['num_rollouts']
        self.test_rollouts = params['test_rollouts']
        self.positive_reward = params['positive_reward']
        self.negative_reward = params['negative_reward']
        self.mode = mode
        self.path_len = params['path_length']
        input_dir = params['input_dir']
        output_dir = params['base_output_dir']
        triple_store = input_dir + 'graph.txt'
        nx_output = output_dir + 'nx_graph.graphml'
        pruned_output = output_dir + 'pruned_graph.graphml'
        np_output = output_dir + 'np_graph.npy'

        # create the KG
        if mode == 'train':
            self.grapher = RelationEntityGrapher(triple_store=triple_store,
                                                entity_vocab=params['entity_vocab'],
                                                relation_vocab=params['relation_vocab'],
                                                max_branching=params['max_branching'],
                                                graph_output_file=nx_output,
                                                pruned_output_file=pruned_output,
                                                np_graph_file=np_output,
                                                class_threshhold=params['class_threshhold'])
            
        else:
            self.grapher = RelationEntityGrapher(triple_store=triple_store,
                                                entity_vocab=params['entity_vocab'],
                                                relation_vocab=params['relation_vocab'],
                                                max_branching=params['max_branching'],
                                                nx_graph_obj=nx.read_graphml(nx_output,
                                                                             node_type=int,
                                                                             edge_key_type=int,
                                                                             force_multigraph=True),
                                                pruned_graph_obj=nx.read_graphml(pruned_output,
                                                                             node_type=int,
                                                                             edge_key_type=int,
                                                                             force_multigraph=True),
                                                np_graph_array=np.load(np_output))

        
        self.batcher = RelationEntityBatcher(input_dir=input_dir,
                                                batch_size=params['batch_size'],
                                                entity_vocab=params['entity_vocab'],
                                                relation_vocab=params['relation_vocab'],
                                                path_len=self.path_len,
                                                nx_graph=self.grapher.return_directed_graph(),
                                                mode=mode,
                                                output_dir=output_dir)
        
        if mode != 'train':       
            self.total_no_examples = self.batcher.store.shape[0]
            self.batcher.write_set_file()


    def get_episodes(self):
        params = self.batch_size, self.path_len, self.num_rollouts, self.test_rollouts, self.positive_reward, \
                 self.negative_reward, self.mode, self.batcher
        if self.mode == 'train':
            for data in self.batcher.yield_next_batch_train():
                yield Episode(self.grapher, data, params)
        else:
            for data in self.batcher.yield_next_batch_test():
                if data is None:
                    return
                yield Episode(self.grapher, data, params)
