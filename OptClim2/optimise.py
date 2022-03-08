import argparse
from pathlib import Path
import nlopt
import sys
import logging

from .config import OptclimConfig
from .common import OptClimPreliminaryRun, OptClimNewRun, OptClimWaiting

# In case we are using a stochastic method, use a "deterministic"
# sequence of pseudorandom numbers, to be repeatable:
nlopt.srand(1)


class NLOptClimConfig(OptclimConfig):
    defaultCfgStr = OptclimConfig.defaultCfgStr + """
    [nlopt]
    algorithm = string()
    """

    def __init__(self, fname: Path) -> None:
        super().__init__(fname)
        self._log = logging.getLogger('OptClim2.optimisecfg')
        self._opt = None

    @property
    def optimiser(self):
        if self._opt is None:
            try:
                alg = getattr(nlopt, self.cfg['nlopt']['algorithm'])
            except AttributeError:
                e = 'no such algorithm {}'.format(
                    self.cfg['nlopt']['algorithm'])
                self._log.error(e)
                raise RuntimeError(e)
            self._opt = nlopt.opt(
                alg, self.objectiveFunction.num_active_params)
            self._opt.set_lower_bounds(self.objectiveFunction.lower_bounds)
            self._opt.set_upper_bounds(self.objectiveFunction.upper_bounds)
            self._opt.set_min_objective(self.objectiveFunction)
            self._opt.set_stopval(-0.1)
            self._opt.set_xtol_rel(1e-2)
        return self._opt


def main():
    logging.basicConfig(level=logging.INFO)
    log = logging.getLogger('OptClim2.optimise')

    parser = argparse.ArgumentParser()
    parser.add_argument('config', type=Path,
                        help='name of configuration file')
    args = parser.parse_args()

    cfg = NLOptClimConfig(args.config)
    opt = cfg.optimiser

    # run optimiser twice to detect whether new parameter set is stable
    for i in range(2):
        # start with lower bounds
        try:
            x = opt.optimize(
                cfg.objectiveFunction.params2values(cfg.values,
                                                    include_constant=False))
        except OptClimPreliminaryRun:
            log.info('new parameter set')
            continue
        except OptClimNewRun:
            print('new')
            sys.exit(1)
        except OptClimWaiting:
            print('waiting')
            sys.exit(2)

        minf = opt.last_optimum_value()
        results = opt.last_optimize_result()

        if results == 1:
            break

    log.info(f"minimum value {minf}")
    log.info(f"result code {results}")
    log.info(f"optimum at {x}")

    print('done')


if __name__ == '__main__':
    main()
