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
    mln << 'Friends(person, person)'
    mln << 'Smokes(person)'
    mln << 'Vapes(person)'
    mln << 'Cancer(person)'
    # Rules
    # If you smoke, you get cancer
    mln << '0 Smokes(x) => Cancer(x)'
    mln << '0 Vapes(x) => Cancer(x)'
    # People with friends who smoke, also smoke  and those with friends who don't smoke, don't smoke
    mln << '0 Friends(x, y) => (Smokes(x) <=> Smokes(y))'
    #mln << 'P(Friends(x, y) => (Smokes(x) <=> Smokes(y))) = 0.6'
    mln << '0 Friends(x, y) => (Vapes(x) <=> Vapes(y))'
    mln.write()
    return mln 


def create_db(mln):
    db = Database(mln)
    db << 'Friends(Anna, Bob)'
    db << 'Friends(Bob, Anna)'
    db << 'Friends(Anna, Edward)'
    db << 'Friends(Edward, Anna)'
    db << 'Friends(Anna, Frank)'
    db << 'Friends(Frank, Anna)'
    db << 'Friends(Bob, Chris)'
    db << 'Friends(Chris, Bob)'
    db << 'Friends(Chris, Daniel)'
    db << 'Friends(Daniel, Chris)'
    db << 'Friends(Edward, Frank)'
    db << 'Friends(Frank, Edward)'
    db << 'Friends(Gary, Helen)'
    db << 'Friends(Helen, Gary)'
    db << 'Friends(Gary, Anna)'
    db << 'Friends(Anna, Gary)'   

    db << 'Smokes(Anna)'
    db << 'Smokes(Edward)'
    db << 'Smokes(Frank)'
    db << 'Smokes(Gary)'

    db << 'Vapes(Frank)'
    db << 'Vapes(Gary)'

    db << 'Cancer(Anna)'
    db << 'Cancer(Edward)'

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