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


class MLogicNet(object):

    def __init__(self, mln_input):
        """Generates MLN instance
        :param mln_input: a dictionary containting two components:
            - preds: list of predicates as strings (ex- ['Interacts(protein, protein)', 'Activates(drug, protein)', 'Treats(drug, bp)'])
            - rules: list of FOL rules as strings (ex- ['0 Activates(x, y) ^ Interacts(y, z) ^ InvolvedIn(z, a) => Treats(x, a)'])
        """
        self.config = {}

        mln = MLN(grammar='StandardGrammar',logic='FirstOrderLogic')

        # Predicate Declaration
        self.preds = mln_input['predicates']
        for pred in self.preds:
            print(pred)
            mln << pred

        # Rules
        self.rules = mln_input['fol_rules']
        for rule in self.rules:
            mln << rule

        mln.write()

        self.mln = mln

        self.db = None


    def create_db(self, instances):
        self.db = Database(self.mln)
        for i in instances:
            self.db << i

        self.db.write()


    def update_configs(self):

        # get the default configs
        DEFAULT_CONFIG = os.path.join(locs.user_data, global_config_filename)
        self.conf = PRACMLNConfig(DEFAULT_CONFIG)

        self.config['verbose'] = True
        self.config['discr_preds'] = 0
        self.config['db'] = self.db
        self.config['mln'] = self.mln
        self.config['ignore_zero_weight_formulas'] = 0
        self.config['ignore_unknown_preds'] = 0
        self.config['incremental'] = 0
        self.config['grammar'] = 'StandardGrammar'
        self.config['logic'] = 'FirstOrderLogic'
        #Other Methods: EnumerationAsk, MC-SAT, WCSPInference, GibbsSampler, BPLL
        self.config['method'] = 'GibbsSampler'
        self.config['multicore'] = 1
        self.config['profile'] = 0
        self.config['shuffle'] = 0
        self.config['prior_mean'] = 0
        self.config['prior_stdev'] = 6
        self.config['save'] = 0
        self.config['use_initial_weights'] = 0
        self.config['use_prior'] = 0
        self.conf.update(self.config)


    def learn_mln(self):
        start = time.time()
        learn = MLNLearn(self.conf, mln=self.mln, db=self.db)
        result = learn.run()
        result.write()
        end = time.time()
        print(f"Time elapsed: {(end - start) / 60} minutes.")

        return result
