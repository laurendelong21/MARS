import numpy as np
from copy import deepcopy

"""Script containing functions to check whether metapaths match with rules, and 
    modify the reward accordingly
"""

def adjust_conf_score(score: float, alpha: float = 0.01):
    """Adjust the confidence score to incrementally increase
    :param score: the confidence score to increment
    :param alpha: adjustable parameter to change the increment
    """
    new_score = score + (alpha * (1 - score))
    return new_score


def map_to_penalty(score: float, alpha: float = 0.1):
    """
    :param score: the observed/expected ratio to map
    :param alpha: adjustable parameter to change how dramatic the penalty is"""
    return alpha * (np.tanh(score-1))**3



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
        retval = ((body == rule[2:]) and (obj == obj_string))  # checks if te end entity is correct
    return retval


def modify_rewards(rule_list, arguments, query_rel_string, obj_string, rule_base_reward, rewards, only_body):
    """Modifies the rewards according to whether the metapath corresponds to a rule
    :param rule_list: 2D array containing rules and corresponding confidences 
    :param arguments: a string which is like a list, alternating between the next possible relation and entity
    :param query_rel_string: all possible rule heads (relations) from each entity
    :param obj_string: all possible sink entities from each sourch entity
    :param rule_base_reward: the reward value assigned for getting a matching path
    :param rewards: array containing rewards for each entity
    :param only_body: Either 0 or 1. Flag to check whether the extracted paths should only be compared against
        the body of the rules, or if the correctness of the end entity should also be taken into account.
    """
    rule_count = 0
    rule_count_body = 0
    # get the total number of rules
    num_rules = len(sum([val for val in rule_list.values()], []))
    print(f"Total Num rules: {num_rules}")
    expected_prob = 1 / num_rules
    # to store the number of occurrences of each rule:
    no_rule_instances = {key: {i: 0 for i in range(len(val))} for key, val in rule_list.items()}
    # to store the rule instances
    # rule_instances = {key: dict() for key in rule_list.keys()}
    for k in range(len(obj_string)):
        # get all of the relations/ rule heads applicable from k
        query_rel = query_rel_string[k]
        if query_rel in rule_list:
            # get all rules in which that query_rel is the head
            rel_rules = rule_list[query_rel]
            argument_temp = [arguments[i][k] for i in range(len(arguments))]
            # separate into relation sequence, last entity
            body, obj = prepare_argument(argument_temp)
            # now, loop through the metapaths and add a reward if the path matches metapath
            # the rule added corresponds to the metapath confidence
            for j in range(len(rel_rules)):  # for each rule body corresponding to that rule head:
                if check_rule(body, obj, obj_string[k], rel_rules[j], only_body):
                    add_reward = rule_base_reward * float(rel_rules[j][0])  # the 0th element is the confidence
                    rewards[k] += add_reward
                    # now adjust that confidence score
                    #print(f"Old conf score is: {rule_list[query_rel][j][0]}")
                    #rule_list[query_rel][j][0] = str(adjust_conf_score(float(rel_rules[j][0])))
                    #print(f"New conf score is: {rule_list[query_rel][j][0]}")
                    break
            for j in range(len(rel_rules)):
                if check_rule(body, obj, obj_string[k], rel_rules[j], only_body=True):  # only checks if the metapath matches
                    rule_count_body += 1
                    if check_rule(body, obj, obj_string[k], rel_rules[j], only_body=False):  # checks if the last entity is a true sink node
                        rule_count += 1
                        # count the number of instances for each rule
                        no_rule_instances[query_rel][j] += 1
                    break

    # update the rule confidences here
    if rule_count > 0:
        for rule_head, rule_bodies in no_rule_instances.items():
            for rule_body, num_instances in rule_bodies.items():
                # TODO: does it make sense to use rule_count rather than rule_count_body?
                observed_prob = num_instances / rule_count
                adjustment = map_to_penalty(observed_prob / expected_prob)
                old_conf = float(rule_list[rule_head][rule_body][0])
                rule_list[rule_head][rule_body][0] = str(old_conf + (adjustment * old_conf))

    return rewards, rule_count, rule_count_body, rule_list
