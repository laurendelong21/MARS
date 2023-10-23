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


def create_mln():
    mln = MLN(grammar='StandardGrammar',logic='FirstOrderLogic')
    # MLN for smoking Network

    # Predicate Declaration
    preds = ['Interacts(protein, protein)', 'Activates(drug, protein)', 'InvolvedIn(protein, bp)', 'Treats(drug, bp)']
    for pred in preds:
        mln << pred

    #mln << 'Interacts(protein, protein)'
    #mln << 'Activates(drug, protein)'
    #mln << 'InvolvedIn(protein, bp)'
    #mln << 'Treats(drug, bp)'
    # Rules
    mln << '0 Activates(x, y) ^ Interacts(y, z) ^ InvolvedIn(z, a) => Treats(x, a)'
    mln.write()
    return mln 


def create_db(mln):
    db = Database(mln)
    db << 'Interacts(Prot1, Prot2)'
    db << 'Interacts(Prot2, Prot3)'

    db << 'Interacts(Prot4, Prot5)'
    db << 'Interacts(Prot5, Prot6)'

    # db << 'Interacts(Prot6, Prot7)'

    db << 'InvolvedIn(Prot3, BP1)'
    db << 'InvolvedIn(Prot6, BP2)'
    # db << 'InvolvedIn(Prot6, BP3)'

    db << 'Activates(Drug1, Prot1)'
    db << 'Activates(Drug2, Prot4)'
    # db << 'Activates(Drug3, Prot6)'

    db << 'Treats(Drug1, BP1)'
    db << 'Treats(Drug2, BP2)'

    db.write()
    return db


def update_configs(mln, db):

    # get the default configs
    DEFAULT_CONFIG = os.path.join(locs.user_data, global_config_filename)
    conf = PRACMLNConfig(DEFAULT_CONFIG)

    config = {}
    config['verbose'] = True
    config['discr_preds'] = 0
    config['db'] = db
    config['mln'] = mln
    config['ignore_zero_weight_formulas'] = 0
    config['ignore_unknown_preds'] = 0
    config['incremental'] = 0
    config['grammar'] = 'StandardGrammar'
    config['logic'] = 'FirstOrderLogic'
    #Other Methods: EnumerationAsk, MC-SAT, WCSPInference, GibbsSampler
    config['method'] = 'BPLL'
    config['multicore'] = 1
    config['profile'] = 0
    config['shuffle'] = 0
    config['prior_mean'] = 0
    config['prior_stdev'] = 6
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
    mln = create_mln()
    db = create_db(mln)
    conf = update_configs(mln, db)
    learn_mln(mln, db, conf)