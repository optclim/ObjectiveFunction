import argparse
from pathlib import Path
import sys
import logging
from dfols import solve
import numpy

from .config import ObjFunConfig
from .common import PreliminaryRun, NewRun, Waiting


class DFOLSConfig(ObjFunConfig):
    def __init__(self, fname: Path) -> None:
        super().__init__(fname)
        self._log = logging.getLogger('ObjectiveFunction.dfolscfg')
        if self.objfunType not in ['residual', 'simobs']:
            msg = 'objective function type must be either residual or simobs'
            self._log.error(msg)
            raise RuntimeError(msg)


def main():
    logging.basicConfig(level=logging.INFO)
    log = logging.getLogger('ObjectiveFunction.dfols')

    parser = argparse.ArgumentParser()
    parser.add_argument('config', type=Path,
                        help='name of configuration file')
    args = parser.parse_args()

    cfg = DFOLSConfig(args.config)

    # run optimiser twice to detect whether new parameter set is stable
    for i in range(2):
        # start with lower bounds
        try:
            x = solve(
                lambda x: cfg.objectiveFunction(x, numpy.array([])),
                cfg.objectiveFunction.params2values(cfg.values,
                                                    include_constant=False),
                bounds=(
                    cfg.objectiveFunction.lower_bounds,
                    cfg.objectiveFunction.upper_bounds),
                scaling_within_bounds=True
            )
        except PreliminaryRun:
            log.info('new parameter set')
            continue
        except NewRun:
            print('new')
            sys.exit(1)
        except Waiting:
            print('waiting')
            sys.exit(2)

        break

    log.info(f"optimum at {x}")
    print('done')


if __name__ == '__main__':
    main()
