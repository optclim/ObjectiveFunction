import argparse
from pathlib import Path
import sys
import logging
from dfols import solve
import numpy

from .config import OptclimConfig
from .common import OptClimPreliminaryRun, OptClimNewRun, OptClimWaiting


class DFOLSOptClimConfig(OptclimConfig):
    def __init__(self, fname: Path) -> None:
        super().__init__(fname)
        self._log = logging.getLogger('OptClim2.dfolscfg')
        if self.objfunType != 'residual':
            msg = 'objective function type must be residual'
            self._log.error(msg)
            raise RuntimeError(msg)


def main():
    logging.basicConfig(level=logging.INFO)
    log = logging.getLogger('OptClim2.dfols')

    parser = argparse.ArgumentParser()
    parser.add_argument('config', type=Path,
                        help='name of configuration file')
    args = parser.parse_args()

    cfg = DFOLSOptClimConfig(args.config)

    # run optimiser twice to detect whether new parameter set is stable
    for i in range(2):
        # start with lower bounds
        try:
            x = solve(
                lambda x: cfg.objectiveFunction(x, numpy.array([])),
                cfg.objectiveFunction.params2values(cfg.values),
                bounds=(
                    cfg.objectiveFunction.lower_bounds,
                    cfg.objectiveFunction.upper_bounds),
                scaling_within_bounds=True
            )
        except OptClimPreliminaryRun:
            log.info('new parameter set')
            continue
        except OptClimNewRun:
            print('new')
            sys.exit(1)
        except OptClimWaiting:
            print('waiting')
            sys.exit(2)

    log.info(f"optimum at {x}")
    print('done')


if __name__ == '__main__':
    main()
