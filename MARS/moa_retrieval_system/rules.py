import numpy as np
from copy import deepcopy
from collections import Counter

"""Script containing functions to check whether metapaths match with rules, and 
    modify the reward accordingly
"""

"""The following three functions are used to update the rule confidences based on the P2H empirical probabilities"""


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
    chunks_dict = dict()
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

        if key in chunks_dict:
            chunks_dict[key] += 1
        else:
            chunks_dict[key] = 1
    return chunks_dict


def p2h_probability(mpath, empirical_probs):
    """Compute the P2H probability of a metapath, given the empirical probabilities of its two-hop chunks
    :param mpath: the full metapath, in terms the relations it constitutes
    :param empirical_probs: the dictionary of batch-specific empirical probabilities of length-2 metapaths
    """
    prob = 1
    chunks = get_metapath_chunks(mpath)
    for key, val in chunks.items():
        chunk_prob = empirical_probs[key] if key in empirical_probs else 0
        prob *= chunk_prob ** val
    return prob


def update_confs_P2H(rule_dict, empirical_probs, alpha=0.1, min_ratio=0.001, max_ratio=1000, ratios=[]):
    """Updates the confidences in the rule list based on P2H empirical probabilities computed during the batch
    :param rule_dict: the rules and corresponding confidences
    :param empirical_probs: the dictionary of batch-specific empirical probabilities of length-2 metapaths
    :param alpha: the parameter that controls how drastically the confidences are updated
    :param min_ratio: the minimum ratio of observed to expected probability that is allowed (prevents zero division)
    :param max_ratio: the maximum ratio of observed to expected probability that is allowed (prevents extreme values)
    """
    expected = 1 / len(empirical_probs)  ## the expected probability of each chunk
    for rule_head in rule_dict.keys():
        for rule_body_num, mpath in enumerate(rule_dict[rule_head]):
            old_conf = float(rule_dict[rule_head][rule_body_num][0])
            # get the P2H probability
            p2h_prob = p2h_probability(mpath[2::], empirical_probs)
            normed_prob = p2h_prob / (expected ** (len(mpath[2::])-1))  ## normalize it by the prob we expect
            ratios.append(normed_prob)  # store the ratio for debugging
            # get new confidence value
            adjustment = map_ratio_to_penalty(normed_prob, alpha, min_ratio, max_ratio)
            new_conf = old_conf + (old_conf * adjustment)
            rule_dict[rule_head][rule_body_num][0] = str(max(min(1, new_conf), 0))  # bounds it between 0 and 1
    return rule_dict, ratios


def update_confs_basic(rule_dict, no_rule_instances, rule_count, alpha=0.1, min_ratio=0.001, max_ratio=1000, ratios=[]):
    """Updates confidences the basic way, based on number of occurrences of each rule
    :param rule_dict: the rules and corresponding confidences
    :param no_rule_instances: the number of instances of each rule
    :param alpha: the parameter that controls how drastically the confidences are updated
    :param min_ratio: the minimum ratio of observed to expected probability that is allowed (prevents zero division)
    :param max_ratio: the maximum ratio of observed to expected probability that is allowed (prevents extreme values)
    """
    num_rules = len(sum([val for val in rule_dict.values()], []))
    expected_prob = 1 / num_rules

    for rule_head, rule_bodies in no_rule_instances.items():
        for rule_body_num, num_instances in rule_bodies.items():
            observed_prob = num_instances / rule_count
            normed_prob = observed_prob / expected_prob
            ratios.append(normed_prob)  # store the ratio for debugging
            adjustment = map_ratio_to_penalty(normed_prob, alpha, min_ratio, max_ratio)
            old_conf = float(rule_dict[rule_head][rule_body_num][0])
            new_conf = old_conf + (old_conf * adjustment)
            rule_dict[rule_head][rule_body_num][0] = str(max(min(1, new_conf), 0))  # bounds it between 0 and 1

    return rule_dict, ratios


def update_confs_mixed(rule_dict, no_rule_instances, rule_count, empirical_probs,
                       alpha=0.1, min_ratio_naive=0.001, max_ratio_naive=1000, 
                       min_ratio_p2h=0.001, max_ratio_p2h=1000, 
                       mixing_ratio=0.5, ratios=[]):
    """Updates the confidences in the rule list based on a mix between 
                    P2H empirical probabilities and frequency-based probabilities
    :param rule_dict: the rules and corresponding confidences
    :param no_rule_instances: the number of instances of each rule
    :param empirical_probs: the dictionary of batch-specific empirical probabilities of length-2 metapaths
    :param alpha: the parameter that controls how drastically the confidences are updated
    :param min_ratio_naive: the minimum ratio of observed to expected probability that is allowed (prevents zero division)
    :param max_ratio_naive: the maximum ratio of observed to expected probability that is allowed (prevents extreme values)
    :param min_ratio_p2h: the minimum ratio of observed to expected probability that is allowed (prevents zero division)
    :param max_ratio_p2h: the maximum ratio of observed to expected probability that is allowed (prevents extreme values)
    :param mixing_ratio: the ratio of the first penalty to the second penalty; default of 0.5 means equal weighting
    """
    expected_p2h = 1 / len(empirical_probs)  ## the expected probability of each chunk
    num_rules = len(sum([val for val in rule_dict.values()], []))
    expected_naive = 1 / num_rules  ## the expected probability of each rule

    for rule_head, rule_bodies in no_rule_instances.items():

        adjustment_dict = dict()

        for rule_body_num, num_instances in rule_bodies.items():
            # frequency-based updates:
            observed_naive = num_instances / rule_count
            normed_naive = observed_naive / expected_naive
            ratios.append(normed_naive)  # store the ratio for debugging
            adjustment_naive = map_ratio_to_penalty(normed_naive, alpha, min_ratio_naive, max_ratio_naive)
            adjustment_dict[rule_body_num] = adjustment_naive

        # P2H-based updates:
        for rule_body_num, mpath in enumerate(rule_dict[rule_head]):
            p2h_prob = p2h_probability(mpath[2::], empirical_probs)
            normed_p2h = p2h_prob / (expected_p2h ** (len(mpath[2::])-1))  ## normalize it by the prob we expect
            ratios.append(normed_p2h)  # store the ratio for debugging
            # get new confidence value
            adjustment_p2h = map_ratio_to_penalty(normed_p2h, alpha, min_ratio_p2h, max_ratio_p2h)
            adjustment_dict[rule_body_num] = mix_penalties(adjustment_dict[rule_body_num], 
                                                                        adjustment_p2h, mixing_ratio)
            
        for rule_body_num, adjustment in adjustment_dict.items():
            old_conf = float(rule_dict[rule_head][rule_body_num][0])
            new_conf = old_conf + (old_conf * adjustment)
            rule_dict[rule_head][rule_body_num][0] = str(max(min(1, new_conf), 0))

    return rule_dict, ratios

    

def map_ratio_to_penalty(ratio, alpha=0.1, min_ratio=0.001, max_ratio=1000):
    """This function maps an observed/expected ratio to some penalty (-1, 1)
    in which a ratio > 1 gets a positive penalty, and 
    a ratio < 1 gets a negative penalty. 
    The penalty is scaled by alpha, so that the penalty is less dramatic.
    :param ratio: the observed/expected ratio
    :param alpha: the parameter that controls how drastically the confidences are updated
    :param min_ratio: the minimum ratio of observed to expected probability that is allowed (prevents zero division)
    :param max_ratio: the maximum ratio of observed to expected probability that is allowed (prevents extreme values)
    """
    # Ensure ratio is within a valid range
    ratio = max(min_ratio, min(max_ratio, ratio))  # Avoid division by zero and extreme values

    # Map ratio to penalty between -1 and 1
    penalty = 2 * (ratio - 1) / (ratio + 1)

    return penalty * alpha


def mix_penalties(penalty1, penalty2, mixing_ratio=0.5):
    """Mixes the penalties from two different methods, with a specified mixing ratio
    :param penalty1: the penalty from the first method
    :param penalty2: the penalty from the second method
    :param mixing_ratio: the ratio of the first penalty to the second penalty; default of 0.5 means equal weighting
    """
    return (penalty1 * mixing_ratio) + (penalty2 * (1 - mixing_ratio))


def get_entities(argument):
    body = set(argument[1::2])  # get all entities, no relations
    return body


def prepare_argument(argument, string='NO_OP'):
    """ Takes a path and returns the relation sequence, last entity"""
    body = argument[::2]  # Remove all entities and keep relations
    str_idx = [i for i, x in enumerate(body) if x == string]  # Find NO_OPs
    body = [element for i, element in enumerate(body) if i not in str_idx]  # Remove NO_OPs
    return body, argument[-1]  # return relation sequence, last entity


def check_rule(body, obj, obj_string, rule, only_body):
    """
    Compare the argument with a rule. only_body=False checks whether the end entity makes it a true pair
    """
    if only_body:  # Compare only the body of the rule to the argument
        retval = (body == rule[2:])
    else:
        retval = ((body == rule[2:]) and (obj == obj_string))  # checks if the end entity is correct
    return retval


def init_empirical_nums(rule_dict):
    """Initializes the empirical nums dict, where each 2-hop chunk is assigned to a value of zero."""
    empirical_nums = dict()
    for head in rule_dict.keys():
        for count, mpath in enumerate(rule_dict[head]):
            empirical_nums = Counter(get_metapath_chunks(mpath[2::])) + Counter(empirical_nums)

    empirical_nums = {key: 0 for key in empirical_nums.keys()}
    return empirical_nums


def modify_rewards(rule_list, arguments, query_rel_string, obj_string, Lambda, 
                   rewards, only_body, update_confs, alpha, batch_size, rollouts, mixing_ratio):
    """Modifies the rewards according to whether the metapath corresponds to a rule
    :param rule_list: 2D array containing rules and corresponding confidences 
    :param arguments: a string which is like a list, alternating between the next possible relation and entity
    :param query_rel_string: all possible rule heads (relations) from each entity
    :param obj_string: all possible sink entities from each sourch entity
    :param Lambda: the reward value assigned for getting a matching path
    :param rewards: array containing rewards for each entity
    :param only_body: Either 0 or 1. Flag to check whether the extracted paths should only be compared against
        the body of the rules, or if the correctness of the end entity should also be taken into account.
    :param update_confs: 0 indicates no conf updates, 
                        1 indicates frequency-based conf updates, 
                        2 indicates P2H conf updates,
                        3 indicates mixed conf updates
    :param alpha: if doing confidence updates, alpha controls how drastically the confidences are updated
    :param batch_size: batch size
    :param rollouts: number of rollouts
    :param mixing_ratio: the ratio of the first penalty to the second penalty; default of 0.5 means equal weighting
    """
    ratios = []
    rule_count = 0
    rule_count_body = 0
    if update_confs == 2 or update_confs == 3:
        # to store the number of occurrences of each 2-hop chunk:
        empirical_nums = init_empirical_nums(rule_list)
    if update_confs == 1 or update_confs == 3:
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
            
            for j in range(len(rel_rules)):
                if check_rule(body, obj, obj_string[k], rel_rules[j], only_body=True):  # only checks if the metapath matches
                    rule_count_body += 1

                    if check_rule(body, obj, obj_string[k], rel_rules[j], only_body=False):  # checks if the last entity is a true sink node
                        rule_count += 1
                        if update_confs == 1 or update_confs == 3:
                            # count the number of instances for each rule
                            no_rule_instances[query_rel][j] += 1
                        if update_confs == 2 or update_confs == 3:
                            # get all of the 2-hop chunks that helped make a match
                            empirical_nums = sum_dicts(empirical_nums, get_metapath_chunks(body))
                    break

            # now, loop through the metapaths and add a reward if the path matches metapath
            # the rule added corresponds to the metapath confidence
            for j in range(len(rel_rules)):  # for each rule body corresponding to that rule head:
                if check_rule(body, obj, obj_string[k], rel_rules[j], only_body):
                    # additional reward for matching rule body
                    add_reward = Lambda * float(rel_rules[j][0])  # the 0th element is the confidence
                    rewards[k] += add_reward
                    break

    print(f"Total bodies matched: {rule_count_body}")
    print(f"Total complete matches: {rule_count}")

    # UPDATE THE CONFIDENCES: UNIQUE TO MARS

    # mixed option
    if update_confs == 3:
        if rule_count <= 0:  # if no full metapath matches, just do the P2H update
            update_confs = 2
        elif sum(empirical_nums.values()) <= 0:  # if no 2-hop chunks, just do the basic update
            update_confs = 1
        else:
            num_rules = len(sum([val for val in rule_list.values()], []))
            min_ratio_naive = num_rules / (batch_size * rollouts)
            max_ratio_naive = num_rules * batch_size * rollouts

            total_count = sum(empirical_nums.values())
            empirical_probs = {key: val/total_count for key, val in empirical_nums.items()}
            min_ratio_p2h = len(empirical_probs) / (batch_size * rollouts)
            max_ratio_p2h = len(empirical_probs) * batch_size * rollouts

            rule_list, ratios = update_confs_mixed(rule_list, no_rule_instances, rule_count, empirical_probs, 
                                                   alpha, min_ratio_naive, max_ratio_naive, 
                                                   min_ratio_p2h, max_ratio_p2h, mixing_ratio, ratios)

    # the naive / simple option
    if update_confs == 1 and rule_count > 0:
        num_rules = len(sum([val for val in rule_list.values()], []))
        min_ratio = num_rules / (batch_size * rollouts)
        max_ratio = num_rules * batch_size * rollouts
        rule_list, ratios = update_confs_basic(rule_list, no_rule_instances, rule_count, alpha, min_ratio, max_ratio, ratios)

    # the P2H option
    if update_confs == 2:
        total_count = sum(empirical_nums.values())
        if total_count > 0:
            empirical_probs = {key: val/total_count for key, val in empirical_nums.items()}
            min_ratio = len(empirical_probs) / (batch_size * rollouts)
            max_ratio = len(empirical_probs) * batch_size * rollouts
            rule_list, ratios = update_confs_P2H(rule_list, empirical_probs, alpha, min_ratio, max_ratio, ratios)

    

    return rewards, rule_count, rule_count_body, rule_list, ratios
