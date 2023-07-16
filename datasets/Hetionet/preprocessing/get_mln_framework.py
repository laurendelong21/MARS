import json
import re


with open('../rules.txt') as f:
    rules = json.load(f)
    

def get_predicate_mapping(rule_dict):
    """Gets all the predicates from the PoLo rules and converts them to logical predicates"""
    preds = {}
    for val in rule_dict.values():
        for mpath in val:
            for medge in set(mpath[2:]):
                if '_' not in medge:
                    involved = [i.lower() for i in re.split('[^A-Z]', medge)]
                    preds[medge] = f"{medge}({involved[0]}, {involved[-1]})"
                    preds['_' + medge] = f"{'_' + medge}({involved[-1]}, {involved[0]})"
    preds['CtD'] = ('CtD(c, d)')
    preds['_CtD'] = ('_CtD(d, c)')

    return preds


def rules2fol(rule_dict, pred_mapping):
    """Changes PoLo metapath rules to FOL rules
    :param rule_dict: PoLo format rule dictionary
    :param pred_mapping: mapping from metaedge notation to FOL predicates
    """
    fol_rules = []
    for head, val in rule_dict.items():
        for mpath in val:
            body = [pred_mapping[i] for i in mpath[2:]]
            body = ' ^ '.join(body)
            fol_rules.append(f'0 ({body}) => {preds[head]}')

    return fol_rules


mlnet = {}
preds = get_predicate_mapping(rules)
mlnet['predicates'] = list(preds.values())
fol_rules = rules2fol(rules, preds)
mlnet['fol_rules'] = fol_rules
with open('../mln_rules.json', 'w') as f:
    json.dump(mlnet, f)
