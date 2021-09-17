#!/bin/env python3

import OptClim2
import argparse
from pathlib import Path
import nlopt
import sys
import logging

logging.basicConfig(level=logging.INFO)

parser = argparse.ArgumentParser()
parser.add_argument('config', type=Path,
                    help='name of configuration file')
args = parser.parse_args()

cfg = OptClim2.OptclimConfig(args.config)
objfun = cfg.objectiveFunction

# In case we are using a stochastic method, use a "deterministic"
# sequence of pseudorandom numbers, to be repeatable:
nlopt.srand(1)

# opt = nlopt.opt(nlopt.LN_BOBYQA, objfun.num_params)
opt = nlopt.opt(nlopt.LN_COBYLA, objfun.num_params)
opt.set_lower_bounds(objfun.lower_bounds)
opt.set_upper_bounds(objfun.upper_bounds)
opt.set_min_objective(objfun)
opt.set_xtol_rel(1e-2)
opt.set_stopval(-0.1)
for i in range(2):
    # start with lower bounds
    try:
        x = opt.optimize(objfun.lower_bounds)
    except OptClim2.OptClimNewRun:
        print('new')
        sys.exit(0)
    except OptClim2.OptClimWaiting:
        print('waiting')
        sys.exit(0)

    minf = opt.last_optimum_value()
    results = opt.last_optimize_result()

    if results == 1:
        break


logging.info(f"optimum at {x}")
logging.info(f"minimum value {minf}")
logging.info(f"result code {results}")

print('done')
