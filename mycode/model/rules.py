import numpy as np
from copy import deepcopy
from collections import Counter

"""Script containing functions to check whether metapaths match with rules, and 
    modify the reward accordingly
"""

"""The following three functions are used to update the rule confidences based on the piecewise empirical probabilities"""


def sum_dicts(dict1, dict2):
    """Gets the sum of the values in the two dicts"""
    new_dict = dict()
    for key in set(dict1.keys()) & set(dict2.keys()):
        new_dict[key] = dict1[key] + dict2[key]
    for key in set(dict1.keys()) - set(dict2.keys()):
        new_dict[key] = dict1[key]
    for key in set(dict2.keys()) - set(dict1.keys()):
        new_dict[key] = dict2[key]
    return new_dict
        

def get_metapath_chunks(path):
    """Gets all of the two-hop pieces of a metapath, returns them as a dictionary like (rel1, rel2):occurences """
    empirical_nums = dict()
    for rel in range(len(path)-1):
        if path[rel] == 'NO_OP':
            continue
        elif path[rel+1] == 'NO_OP':
            if rel+1 != len(path)-1:
                key = (path[rel], path[rel+2])
            else:
                continue
        else:
            key = (path[rel], path[rel+1])

        if key in empirical_nums:
            empirical_nums[key] += 1
        else:
            empirical_nums[key] = 1
    return empirical_nums

def piecewise_probability(mpath, empirical_probs):
    """Compute the piecewise probability of a metapath, given the empirical probabilities of its two-hop chunks
    :param mpath: the full metapath, in terms the relations it constitutes
    :param empirical_probs: the dictionary of batch-specific empirical probabilities of length-2 metapaths
    """
    prob = 1
    chunks = get_metapath_chunks(mpath)
    for key, val in chunks.items():
        chunk_prob = empirical_probs[key] if key in empirical_probs else 0
        prob *= chunk_prob ** val
    return prob


def update_confs_piecewise(rule_dict, empirical_probs, alpha=0.1):
    """Updates the confidences in the rule list based on piecewise empirical probabilities computed during the batch
    :param rule_dict
    :param empirical_probs: the dictionary of batch-specific empirical probabilities of length-2 metapaths
    :param alpha: the parameter that controls how drastically the confidences are updated
    """
    expected = 1 / len(empirical_probs)  ## the expected probability of each chunk
    for head in rule_dict.keys():
        for count, mpath in enumerate(rule_dict[head]):
            old_conf = float(rule_dict[head][count][0])
            # get the piecewise probability
            pw_prob = piecewise_probability(mpath[2::], empirical_probs)
            normed_prob = pw_prob / (expected ** len(mpath[2::]))  ## normalize it by the prob we expect
            # get the average of the new and old confidences
            adjustment = map_ratio_to_penalty(normed_prob, alpha)
            new_conf = old_conf + (old_conf * adjustment)
            rule_dict[head][count][0] = str(max(min(1, new_conf), 0))  # bounds it between 0 and 1
    return rule_dict


def update_confs_basic(rule_dict, no_rule_instances, rule_count, alpha=0.1):
    """Updates confidences the basic way, based on number of occurrences of each rule"""
    num_rules = len(sum([val for val in rule_dict.values()], []))
    expected_prob = 1 / num_rules

    for rule_head, rule_bodies in no_rule_instances.items():
        for rule_body, num_instances in rule_bodies.items():
            observed_prob = num_instances / rule_count
            adjustment = map_ratio_to_penalty(observed_prob / expected_prob, alpha)
            old_conf = float(rule_dict[rule_head][rule_body][0])
            new_conf = old_conf + (old_conf * adjustment)
            rule_dict[rule_head][rule_body][0] = str(max(min(1, new_conf), 0))  # bounds it between 0 and 1

    return rule_dict


def map_ratio_to_penalty(ratio, alpha=0.1):
    """This function was written by ChatGPT
    
    It maps an observed/expected ratio to some penalty (-1, 1) in which a ratio > 1 gets a positive penalty, and 
    a ratio < 1 gets a negative penalty. The penalty is scaled by the ratio, so that the penalty is more dramatic.
    """
    # Ensure ratio is within a valid range
    ratio = max(0.001, min(1000, ratio))  # Avoid division by zero and extreme values

    # Map ratio to penalty between -1 and 1
    penalty = 2 * (ratio - 1) / (ratio + 1)

    return penalty * alpha


def compute_subgraph_penalty(subgraphs, entities, sg_penalty):
    """Computes the subgraph penalty for a given path
    :param subgraphs: a list of set, where each set comprises the proteins in a given subgraph/pathway
    :param entities: a set of entities in the found path
    :param sg_penalty: the penalty imposed for crossing subgraphs / pathways while traversing the graph
    """
    crosses = -1
    for subgraph in subgraphs:
        if bool(subgraph & entities):
            crosses += 1
    if crosses <= 0: ## if it does not cross 2+ subgraphs,
        return 0
    return crosses * sg_penalty



def get_entities(argument):
    body = set(argument[1::2])  # get all entities, no relations
    return body


def prepare_argument(argument, string='NO_OP'):
    """ Takes a path and returns the relation sequence, last entity"""
    body = argument[::2]  # Remove all entities and keep relations
    # TODO: what does NO_OP mean?
    str_idx = [i for i, x in enumerate(body) if x == string]  # Find NO_OPs
    body = [element for i, element in enumerate(body) if i not in str_idx]  # Remove NO_OPs
    return body, argument[-1]  # return relation sequence, last entity


def check_rule(body, obj, obj_string, rule, only_body):
    """
    Compare the argument with a rule.
    """
    if only_body:  # Compare only the body of the rule to the argument
        retval = (body == rule[2:])
    else:
        retval = ((body == rule[2:]) and (obj == obj_string))  # checks if the end entity is correct
    return retval


def init_empirical_nums(rule_dict):
    """Initializes the empirical nums dict: initializes each with 1 to avoid division by 0"""
    empirical_nums = dict()
    for head in rule_dict.keys():
        for count, mpath in enumerate(rule_dict[head]):
            empirical_nums = Counter(get_metapath_chunks(mpath[2::])) + Counter(empirical_nums)

    empirical_nums = {key: 1 for key in empirical_nums.keys()}
    return empirical_nums


def modify_rewards(rule_list, arguments, query_rel_string, obj_string, rule_base_reward, 
                   rewards, only_body, update_confs, alpha, sg_penalty, subgraphs):
    """Modifies the rewards according to whether the metapath corresponds to a rule
    :param rule_list: 2D array containing rules and corresponding confidences 
    :param arguments: a string which is like a list, alternating between the next possible relation and entity
    :param query_rel_string: all possible rule heads (relations) from each entity
    :param obj_string: all possible sink entities from each sourch entity
    :param rule_base_reward: the reward value assigned for getting a matching path
    :param rewards: array containing rewards for each entity
    :param only_body: Either 0 or 1. Flag to check whether the extracted paths should only be compared against
        the body of the rules, or if the correctness of the end entity should also be taken into account.
    :param update_confs: 0 indicates no conf updates, 1 indicates frequency-based conf updates, 2 indicates piecewise
    :param alpha: if doing confidence updates, alpha controls how drastically the confidences are updated
    :param sg_penalty: the penalty imposed for crossing subgraphs / pathways while traversing the graph
    :param subgraphs: a list of sets, where each set comprises the proteins in a given subgraph/pathway
    """
    rule_count = 0
    rule_count_body = 0
    if update_confs == 2:
        empirical_nums = init_empirical_nums(rule_list)
    if update_confs == 1:
        # to store the number of occurrences of each rule:
        no_rule_instances = {key: {i: 0 for i in range(len(val))} for key, val in rule_list.items()}
    for k in range(len(obj_string)):
        # get all of the relations/ rule heads applicable from k
        query_rel = query_rel_string[k]
        if query_rel in rule_list:
            # get all rules in which that query_rel is the head
            rel_rules = rule_list[query_rel]
            argument_temp = [arguments[i][k] for i in range(len(arguments))]
            # separate into relation sequence, last entity
            body, obj = prepare_argument(argument_temp)
            
            
            if sg_penalty > 0:  # if we are penalizing subgraph crossings, get the proteins from the path
                entities = get_entities(argument_temp)
            
            for j in range(len(rel_rules)):
                if check_rule(body, obj, obj_string[k], rel_rules[j], only_body=True):  # only checks if the metapath matches
                    rule_count_body += 1
                    penalty = compute_subgraph_penalty(subgraphs, entities, sg_penalty) if sg_penalty > 0 else 0
                    # possible penalty
                    take_penalty = penalty * abs(rewards[k])  ## reward can be negative, so abs val necessary
                    rewards[k] -= take_penalty

                    if check_rule(body, obj, obj_string[k], rel_rules[j], only_body=False):  # checks if the last entity is a true sink node
                        rule_count += 1
                        if update_confs == 1:
                            # count the number of instances for each rule
                            no_rule_instances[query_rel][j] += 1
                        if update_confs == 2:
                            # get all of the 2-hop chunks that helped make a match
                            empirical_nums = sum_dicts(empirical_nums, get_metapath_chunks(body))
                    break

            # now, loop through the metapaths and add a reward if the path matches metapath
            # the rule added corresponds to the metapath confidence
            for j in range(len(rel_rules)):  # for each rule body corresponding to that rule head:
                if check_rule(body, obj, obj_string[k], rel_rules[j], only_body):
                    # additional reward for matching rule body
                    add_reward = rule_base_reward * float(rel_rules[j][0])  # the 0th element is the confidence
                    rewards[k] += add_reward
                    break

    print(f"Total bodies matched: {rule_count_body}")
    print(f"Total complete matches: {rule_count}")

    # the naive / simple option
    if update_confs == 1 and rule_count > 0:
        rule_list = update_confs_basic(rule_list, no_rule_instances, rule_count, alpha)

    # the piecewise option
    if update_confs == 2:
        total_count = sum(empirical_nums.values())
        if total_count > 0:
            empirical_probs = {key: val/total_count for key, val in empirical_nums.items()}
            rule_list = update_confs_piecewise(rule_list, empirical_probs, alpha)

    return rewards, rule_count, rule_count_body, rule_list
