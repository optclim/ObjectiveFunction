#!/bin/env python3

# compute points on a quadratic surface with equan
# f(x,y) = a*x^2 + b*y^2 + c*x*y + d*x + e*y + f
# for some parameters a, b, c, d, e, f


from .config import OptclimConfig
import argparse
from pathlib import Path
import pandas
import numpy
import time
import logging
import sys
import random


def model(x, y, params):
    """a 2D quadratic test model

    :param x: the x coordinate
    :param y: the y coordinate
    :param params: dictionary of parameters
    :type params: dict
    :return: the z value
    """
    return params['a'] * x * x \
        + params['b'] * y * y \
        + params['c'] * x * y \
        + params['d'] * x \
        + params['e'] * y \
        + params['f']


def main():
    logging.basicConfig(level=logging.INFO)

    parser = argparse.ArgumentParser()
    parser.add_argument('config', type=Path,
                        help='name of configuration file')
    parser.add_argument('-d', '--delay', type=int, default=0, metavar='SEC',
                        help='delay setting results by SEC seconds, default=0')
    parser.add_argument('-s', '--scale', type=float, default=10,
                        help="scale for random noise to add to synthetic data")
    parser.add_argument('-g', '--generate', action='store_true', default=False,
                        help="generate synthetic data")

    args = parser.parse_args()

    cfg = OptclimConfig(args.config)

    dname = cfg.basedir / 'synthetic.data'
    if args.generate:
        logging.info('generating synthetic data')
        # create a random parameter set
        params = {}
        for p in cfg.optimise_parameters:
            # generate a uniformly distributed random value
            # using the range of the parameter
            params[p] = cfg.optimise_parameters[p](
                random.uniform(cfg.optimise_parameters[p].minv,
                               cfg.optimise_parameters[p].maxv))
        # store generated parameters in file
        pname = cfg.basedir / 'parameters.data'
        with pname.open('w') as poutput:
            for p in params:
                poutput.write(f'{p} {params[p]}\n')
        # store synthetic data in file after adding some noise
        with dname.open('w') as output:
            for y in range(100):
                y = y - 50
                for x in range(100):
                    x = x - 50
                    output.write('{0},{1},{2}\n'.format(
                        x, y, model(x, y, params) +  # noqa: W504
                        numpy.random.normal(scale=args.scale)))
    else:
        logging.info('running model')
        objfun = cfg.objectiveFunction
        # get parameter set without result from lookup table
        try:
            params = objfun.get_new()
        except Exception as e:
            logging.error(e)
            sys.exit(1)

        data = pandas.read_csv(dname, names=['x', 'y', 'z'])

        # compute model values for parameter
        data['computed'] = data.apply(lambda row:
                                      model(row['x'], row['y'], params),
                                      axis=1)

        # compute difference between observation and model
        data['diff'] = data['computed'] - data['z']

        if cfg.objfunType == 'misfit':
            # and standard devation
            result = data['diff'].std()
        elif cfg.objfunType == 'residual':
            result = data['diff'].to_numpy()

        if args.delay > 0:
            logging.info(f'waiting {args.delay} seconds')
            time.sleep(args.delay)
        logging.info(f'result {result}')

        # store results for parameter set in lookup table
        objfun.set_result(params, result)


if __name__ == '__main__':
    main()
