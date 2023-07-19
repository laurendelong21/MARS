import json
import os.path as osp

from pracmln import MLN
from pracmln import Database

from pracmln.utils.project import PRACMLNConfig
from pracmln.utils import config, locs
from pracmln.utils.config import global_config_filename
import os
from pracmln.mlnlearn import MLNLearn
from pracmln.utils.project import PRACMLNConfig
from pracmln.utils import config, locs
from pracmln.utils.config import global_config_filename
import os
from pracmln.mlnlearn import MLNLearn

import time


INPUT_DIR = 'datasets/MOA-net'
MLN_RULES = osp.join(INPUT_DIR, 'mln_rules.json')
# TODO: replace the next line with some input that comes from PoLo
MLN_DB = osp.join(INPUT_DIR, 'instances.txt')


def create_mln(preds, rules):
    """Generates MLN instance
    :param preds: list of predicates as strings (ex- ['Interacts(protein, protein)', 'Activates(drug, protein)', 'Treats(drug, bp)'])
    :param rules: list of FOL rules as strings (ex- ['0 Activates(x, y) ^ Interacts(y, z) ^ InvolvedIn(z, a) => Treats(x, a)'])
    """
    # TODO: make it so this isn't done
    mln = MLN(grammar='StandardGrammar',logic='FirstOrderLogic')

    # Predicate Declaration
    for pred in preds:
        print(pred)
        mln << pred

    # Rules

    for rule in rules:
        mln << rule

    mln.write()

    return mln 


def create_db(mln, instances):
    db = Database(mln)
    for i in instances:
        db << i

    db.write()
    return db


def update_configs(mln, db):

    # get the default configs
    DEFAULT_CONFIG = os.path.join(locs.user_data, global_config_filename)
    conf = PRACMLNConfig(DEFAULT_CONFIG)

    config = {}
    config['verbose'] = True
    #config['qpreds'] = 'CtBP'
    #config['discr_preds'] = 0
    config['db'] = db
    config['mln'] = mln
    config['ignore_zero_weight_formulas'] = 0
    config['ignore_unknown_preds'] = 1
    config['incremental'] = 0
    config['grammar'] = 'StandardGrammar'
    config['logic'] = 'FirstOrderLogic'
    #Other Methods: EnumerationAsk, MC-SAT, WCSPInference, GibbsSampler
    config['method'] = 'BPLL'
    config['multicore'] = 1
    config['profile'] = 0
    config['shuffle'] = 0
    config['save'] = 0
    config['use_initial_weights'] = 0
    config['use_prior'] = 0
    conf.update(config)

    return conf


def learn_mln(mln, db, conf):
    learn = MLNLearn(conf, mln=mln, db=db)
    result = learn.run()
    result.write()


if __name__ == "__main__":
    start = time.time()
    with open(MLN_RULES, 'r') as f:
        mln_input = json.load(f)

    rules = mln_input['fol_rules']['2']
    preds =  mln_input['predicates']

    # TODO: this will be replaced by data provided by PoLo
    #write code that reads that list back in
    with open(MLN_DB, 'r') as f:
        instances = f.read().splitlines()

    mln = create_mln(preds, rules)
    db = create_db(mln, instances)
    conf = update_configs(mln, db)
    learn_mln(mln, db, conf)

    end = time.time()

    print(f"Time elapsed: {(end - start) / 60} minutes.")
